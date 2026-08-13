"""
JP Japanese Lab
================

Interactive Japanese study application built with Streamlit + gTTS.

FEATURES
--------
STUDY
    - Hiragana Gojūon
    - Katakana Gojūon
    - On-demand Japanese TTS
    - Autoplay-capable audio player
    - Compact mobile-friendly kana cards
    - Animated KanjiVG stroke-order viewer
    - Essential phrases
    - Grammar / particle reference
    - Counter reference

QUIZ
    - Hiragana
    - Katakana
    - Both Kana
    - Phrases & Sentences
    - Grammar & Particles
    - Counters & Quantifiers
    - 10 / 25 / 50 questions
    - Randomized choices
    - Live progress
    - Live score
    - Star rating
    - Mistake tracking
    - Targeted missed-question review

TECHNICAL
---------
    - Streamlit session_state for persistent quiz state
    - gTTS audio generated into BytesIO
    - No temporary MP3 files
    - Audio cached by Streamlit
    - KanjiVG SVGs fetched and cached
    - Custom Sakura / Cyber-Tokyo themes

RUN
---
pip install -r requirements.txt
streamlit run app.py
"""

from __future__ import annotations

import io
import random
import re
import urllib.request
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import streamlit as st
from gtts import gTTS


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="JP Japanese Lab",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# THEME CONFIGURATION
# =============================================================================

THEMES = {
    "🌸 Sakura": {
        "page_bg": "#FFF9FA",
        "card_bg": "#FFFFFF",
        "text": "#35151E",
        "muted": "#704653",
        "primary": "#D81B60",
        "primary_hover": "#AD144D",
        "secondary": "#FFB7C5",
        "border": "#F0B7C4",
        "accent": "#8D163F",
        "code_bg": "#FFF0F4",
    },
    "🌙 Midnight Cyber-Tokyo": {
        "page_bg": "#121212",
        "card_bg": "#1E1E2E",
        "text": "#F5F7FA",
        "muted": "#B7C1CC",
        "primary": "#FF79C6",
        "primary_hover": "#FF4FB5",
        "secondary": "#8BE9FD",
        "border": "#3C4263",
        "accent": "#8BE9FD",
        "code_bg": "#181825",
    },
}


# =============================================================================
# KANA DATA
# =============================================================================

HIRAGANA_ROWS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ("A", [("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o")]),
    ("K", [("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko")]),
    ("S", [("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so")]),
    ("T", [("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to")]),
    ("N", [("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no")]),
    ("H", [("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho")]),
    ("M", [("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo")]),
    ("Y", [("や", "ya"), ("", ""), ("ゆ", "yu"), ("", ""), ("よ", "yo")]),
    ("R", [("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro")]),
    ("W", [("わ", "wa"), ("", ""), ("", ""), ("", ""), ("を", "o")]),
    ("N", [("ん", "n"), ("", ""), ("", ""), ("", ""), ("", "")]),
]

KATAKANA_ROWS: List[Tuple[str, List[Tuple[str, str]]]] = [
    ("A", [("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o")]),
    ("K", [("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko")]),
    ("S", [("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so")]),
    ("T", [("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to")]),
    ("N", [("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no")]),
    ("H", [("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho")]),
    ("M", [("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo")]),
    ("Y", [("ヤ", "ya"), ("", ""), ("ユ", "yu"), ("", ""), ("ヨ", "yo")]),
    ("R", [("ラ", "ra"), ("リ", "ri"), ("ル", "ru"), ("レ", "re"), ("ロ", "ro")]),
    ("W", [("ワ", "wa"), ("", ""), ("", ""), ("", ""), ("ヲ", "o")]),
    ("N", [("ン", "n"), ("", ""), ("", ""), ("", "")]),
]


# =============================================================================
# STROKE COUNT / HANDWRITING NOTES
# =============================================================================

STROKE_INFO: Dict[str, Tuple[int, str]] = {
    "あ": (3, "Short top stroke → central curved stroke → final sweeping stroke."),
    "い": (2, "Left stroke first → right stroke."),
    "う": (2, "Small top mark → larger curved stroke."),
    "え": (2, "Short top stroke → longer lower stroke."),
    "お": (3, "Left component → crossing stroke → final sweeping curve."),
    "か": (3, "Left component → upper diagonal → final curve."),
    "き": (4, "Top horizontal → second horizontal → crossing stroke → lower curve."),
    "く": (1, "One continuous curved stroke."),
    "け": (3, "Left component → vertical → right crossing stroke."),
    "こ": (2, "Upper horizontal → lower horizontal."),
    "さ": (3, "Top mark → main structure → final curve."),
    "し": (1, "One long curved stroke."),
    "す": (2, "Short top stroke → descending curve."),
    "せ": (3, "Vertical → horizontal → curved ending."),
    "そ": (1, "One flowing stroke."),
    "た": (4, "Upper component → crossing structure → lower curve."),
    "ち": (2, "Short upper stroke → large curved stroke."),
    "つ": (1, "One curved stroke."),
    "て": (1, "One stroke from upper left."),
    "と": (2, "Short diagonal → long curved stroke."),
    "な": (4, "Left component → center structure → lower curve."),
    "に": (3, "Short horizontal strokes → vertical/curved ending."),
    "ぬ": (2, "Main curve → crossing loop."),
    "ね": (4, "Left component → upper/right structure → looped finish."),
    "の": (1, "One continuous rounded stroke."),
    "は": (3, "Left vertical → center structure → right curve."),
    "ひ": (1, "One flowing stroke with a looped finish."),
    "ふ": (4, "Upper marks → central flowing stroke."),
    "へ": (1, "One angular descending stroke."),
    "ほ": (4, "Central structure → right-side strokes."),
    "ま": (3, "Upper component → lower horizontal → looped stroke."),
    "み": (2, "Two connected flowing strokes."),
    "む": (3, "Upper strokes → large looping finish."),
    "め": (2, "Curved stroke → crossing loop."),
    "も": (3, "Two horizontals → lower curve."),
    "や": (3, "Upper strokes → large lower curve."),
    "ゆ": (2, "Left curved stroke → enclosing loop."),
    "よ": (2, "Upper horizontal → lower vertical/curve."),
    "ら": (2, "Short upper stroke → lower curve."),
    "り": (2, "Two separate flowing strokes."),
    "る": (1, "One looping stroke."),
    "れ": (2, "Left component → larger right loop."),
    "ろ": (1, "One looping stroke."),
    "わ": (2, "Curved first stroke → looped ending."),
    "を": (3, "Top component → crossing → sweeping stroke."),
    "ん": (1, "One continuous curved stroke."),

    "ア": (2, "Horizontal stroke → descending diagonal."),
    "イ": (2, "Left diagonal → right diagonal."),
    "ウ": (3, "Top mark → upper structure → descending stroke."),
    "エ": (3, "Top horizontal → vertical → bottom horizontal."),
    "オ": (3, "Horizontal → crossing structure → right diagonal."),
    "カ": (2, "Left descending stroke → right angled stroke."),
    "キ": (3, "Two horizontals → central diagonal."),
    "ク": (2, "Short angled stroke → larger descending stroke."),
    "ケ": (3, "Left diagonal → upper horizontal → right descending stroke."),
    "コ": (2, "Upper stroke → lower stroke."),
    "サ": (3, "Upper strokes → long diagonal."),
    "シ": (3, "Three short descending strokes."),
    "ス": (2, "Short upper stroke → long curve."),
    "セ": (2, "Horizontal → vertical/diagonal stroke."),
    "ソ": (2, "Two diagonal strokes."),
    "タ": (3, "Upper stroke → middle diagonal → lower diagonal."),
    "チ": (3, "Top horizontal → diagonal → lower horizontal."),
    "ツ": (3, "Three short descending strokes."),
    "テ": (3, "Two horizontal strokes → descending stroke."),
    "ト": (2, "Vertical → short diagonal."),
    "ナ": (2, "Horizontal → large diagonal."),
    "ニ": (2, "Two horizontal strokes."),
    "ヌ": (2, "Diagonal → crossing curve."),
    "ネ": (4, "Upper strokes → cross structure → diagonal."),
    "ノ": (1, "One diagonal stroke."),
    "ハ": (2, "Two diagonal strokes."),
    "ヒ": (2, "Horizontal → vertical/curve."),
    "フ": (1, "One descending curve."),
    "ヘ": (1, "One angular stroke."),
    "ホ": (4, "Central cross → side diagonals."),
    "マ": (2, "Upper horizontal → diagonal."),
    "ミ": (3, "Three horizontal strokes."),
    "ム": (2, "Descending stroke → angled base."),
    "メ": (2, "Two crossing diagonals."),
    "モ": (3, "Two horizontals → descending stroke."),
    "ヤ": (2, "Short diagonal → right structure."),
    "ユ": (2, "Vertical curve → lower horizontal."),
    "ヨ": (3, "Three horizontal/vertical segments."),
    "ラ": (2, "Top horizontal → curved lower stroke."),
    "リ": (2, "Two descending strokes."),
    "ル": (2, "Left vertical → right curve."),
    "レ": (1, "One long angled stroke."),
    "ロ": (3, "Top → side → bottom strokes."),
    "ワ": (2, "Upper/left component → descending stroke."),
    "ヲ": (3, "Upper horizontal → middle structure → lower curve."),
    "ン": (2, "Two short diagonal strokes."),
}


# =============================================================================
# PHRASES
# =============================================================================

PHRASES = [
    ("おはようございます", "Good morning"),
    ("こんにちは", "Hello / good afternoon"),
    ("こんばんは", "Good evening"),
    ("おやすみなさい", "Good night"),
    ("ありがとうございます", "Thank you"),
    ("どういたしまして", "You're welcome"),
    ("すみません", "Excuse me / I'm sorry"),
    ("ごめんなさい", "I'm sorry"),
    ("お願いします", "Please"),
    ("はい", "Yes"),
    ("いいえ", "No"),
    ("わかりました", "I understand"),
    ("わかりません", "I don't understand"),
    ("いただきます", "Said before eating"),
    ("ごちそうさまでした", "Said after eating"),
    ("はじめまして", "Nice to meet you"),
    ("よろしくお願いします", "Nice to meet you / Please treat me well"),
]


SENTENCES = [
    ("わたしは学生です。", "I am a student."),
    ("わたしは先生です。", "I am a teacher."),
    ("これは本です。", "This is a book."),
    ("それはペンです。", "That is a pen."),
    ("わたしは水を飲みます。", "I drink water."),
    ("わたしはご飯を食べます。", "I eat rice / a meal."),
    ("わたしは日本語を勉強します。", "I study Japanese."),
    ("田中さんは学校へ行きます。", "Tanaka goes to school."),
    ("わたしは図書館で勉強します。", "I study at the library."),
    ("母は料理をします。", "My mother cooks."),
    ("父は車を運転します。", "My father drives a car."),
    ("猫がいます。", "There is a cat."),
    ("本があります。", "There is a book."),
]


# =============================================================================
# PARTICLES
# =============================================================================

PARTICLE_QUESTIONS = [
    {
        "prompt": "Which particle marks the topic?",
        "japanese": "わたし ___ 学生です。",
        "answer": "は",
        "choices": ["は", "を", "で", "に"],
        "explanation": "は marks the topic. It is pronounced 'wa' when used as a particle.",
    },
    {
        "prompt": "Which particle expresses possession or connection?",
        "japanese": "わたし ___ 本",
        "answer": "の",
        "choices": ["の", "を", "で", "が"],
        "explanation": "の connects nouns and often expresses possession or relationship.",
    },
    {
        "prompt": "Which particle marks the direct object?",
        "japanese": "水 ___ 飲みます。",
        "answer": "を",
        "choices": ["を", "は", "に", "で"],
        "explanation": "を marks the direct object.",
    },
    {
        "prompt": "Which particle marks a destination?",
        "japanese": "学校 ___ 行きます。",
        "answer": "に",
        "choices": ["に", "を", "で", "の"],
        "explanation": "に can mark a destination or target.",
    },
    {
        "prompt": "Which particle marks the place where an action occurs?",
        "japanese": "図書館 ___ 勉強します。",
        "answer": "で",
        "choices": ["で", "に", "を", "が"],
        "explanation": "で marks the location where an action takes place.",
    },
    {
        "prompt": "Which particle commonly marks the grammatical subject?",
        "japanese": "猫 ___ います。",
        "answer": "が",
        "choices": ["が", "を", "で", "の"],
        "explanation": "が often marks the grammatical subject or new information.",
    },
]


# =============================================================================
# COUNTERS
# =============================================================================

COUNTER_QUESTIONS = [
    {
        "prompt": "Which counter is used for people?",
        "japanese": "学生が三 ___ います。",
        "answer": "人（にん）",
        "choices": ["人（にん）", "本（ほん）", "枚（まい）", "冊（さつ）"],
        "explanation": "人 is the standard counter for people.",
    },
    {
        "prompt": "Which counter is commonly used for long cylindrical objects?",
        "japanese": "ペンを三 ___ 買いました。",
        "answer": "本（ほん）",
        "choices": ["本（ほん）", "枚（まい）", "冊（さつ）", "人（にん）"],
        "explanation": "本 is used for long cylindrical objects such as pens and bottles.",
    },
    {
        "prompt": "Which counter is commonly used for flat objects?",
        "japanese": "紙を四 ___ ください。",
        "answer": "枚（まい）",
        "choices": ["枚（まい）", "本（ほん）", "人（にん）", "冊（さつ）"],
        "explanation": "枚 is used for flat, thin objects.",
    },
    {
        "prompt": "Which general counter is used for many ordinary items?",
        "japanese": "りんごを三 ___ ください。",
        "answer": "つ",
        "choices": ["つ", "台（だい）", "冊（さつ）", "人（にん）"],
        "explanation": "つ is a general-purpose counter for many objects.",
    },
    {
        "prompt": "Which counter is used for books and volumes?",
        "japanese": "本を五 ___ 読みました。",
        "answer": "冊（さつ）",
        "choices": ["冊（さつ）", "本（ほん）", "枚（まい）", "台（だい）"],
        "explanation": "冊 is used for bound books and volumes.",
    },
    {
        "prompt": "Which counter is used for vehicles and machines?",
        "japanese": "車が二 ___ あります。",
        "answer": "台（だい）",
        "choices": ["台（だい）", "冊（さつ）", "枚（まい）", "本（ほん）"],
        "explanation": "台 is commonly used for vehicles and many machines.",
    },
]


# =============================================================================
# DATA MODEL
# =============================================================================

@dataclass
class Question:
    question_id: str
    category: str
    prompt: str
    japanese: str
    answer: str
    choices: List[str]
    explanation: str


# =============================================================================
# QUESTION GENERATORS
# =============================================================================

def make_kana_questions(
    rows: Sequence[Tuple[str, Sequence[Tuple[str, str]]]],
    category: str,
    prefix: str,
) -> List[Question]:
    """Generate kana reading and recognition questions."""

    items = [
        (kana, romaji)
        for _, row in rows
        for kana, romaji in row
        if kana
    ]

    symbols = [x[0] for x in items]
    readings = [x[1] for x in items]

    questions: List[Question] = []

    for index, (kana, romaji) in enumerate(items):

        wrong_readings = random.sample(
            [x for x in readings if x != romaji],
            3,
        )

        questions.append(
            Question(
                question_id=f"{prefix}_read_{index}",
                category=category,
                prompt="What is the reading of this kana?",
                japanese=kana,
                answer=romaji,
                choices=[romaji, *wrong_readings],
                explanation=f"{kana} is read as '{romaji}'.",
            )
        )

        wrong_symbols = random.sample(
            [x for x in symbols if x != kana],
            3,
        )

        questions.append(
            Question(
                question_id=f"{prefix}_write_{index}",
                category=category,
                prompt=f"Which kana represents '{romaji}'?",
                japanese=romaji,
                answer=kana,
                choices=[kana, *wrong_symbols],
                explanation=f"'{romaji}' is written as {kana}.",
            )
        )

    return questions


def make_phrase_questions() -> List[Question]:
    """Generate phrase translation questions."""

    result: List[Question] = []

    english = [x[1] for x in PHRASES]
    japanese = [x[0] for x in PHRASES]

    for index, (jp, en) in enumerate(PHRASES):

        wrong = random.sample(
            [x for x in english if x != en],
            3,
        )

        result.append(
            Question(
                question_id=f"phrase_meaning_{index}",
                category="Phrases & Sentences",
                prompt="What does this expression mean?",
                japanese=jp,
                answer=en,
                choices=[en, *wrong],
                explanation=f"{jp} means '{en}'.",
            )
        )

        wrong_jp = random.sample(
            [x for x in japanese if x != jp],
            3,
        )

        result.append(
            Question(
                question_id=f"phrase_reverse_{index}",
                category="Phrases & Sentences",
                prompt=f"Which Japanese expression means '{en}'?",
                japanese="",
                answer=jp,
                choices=[jp, *wrong_jp],
                explanation=f"{jp} means '{en}'.",
            )
        )

    return result


def make_sentence_questions() -> List[Question]:
    """Generate sentence comprehension questions."""

    result: List[Question] = []
    translations = [x[1] for x in SENTENCES]

    for index, (jp, en) in enumerate(SENTENCES):

        wrong = random.sample(
            [x for x in translations if x != en],
            3,
        )

        result.append(
            Question(
                question_id=f"sentence_{index}",
                category="Phrases & Sentences",
                prompt="What does this sentence mean?",
                japanese=jp,
                answer=en,
                choices=[en, *wrong],
                explanation=en,
            )
        )

    return result


def make_particle_questions() -> List[Question]:
    """Create Question objects from particle data."""

    result = []

    for index, item in enumerate(PARTICLE_QUESTIONS):

        choices = item["choices"].copy()
        random.shuffle(choices)

        result.append(
            Question(
                question_id=f"particle_{index}",
                category="Grammar & Particles",
                prompt=item["prompt"],
                japanese=item["japanese"],
                answer=item["answer"],
                choices=choices,
                explanation=item["explanation"],
            )
        )

    return result


def make_counter_questions() -> List[Question]:
    """Create Question objects from counter data."""

    result = []

    for index, item in enumerate(COUNTER_QUESTIONS):

        choices = item["choices"].copy()
        random.shuffle(choices)

        result.append(
            Question(
                question_id=f"counter_{index}",
                category="Counters & Quantifiers",
                prompt=item["prompt"],
                japanese=item["japanese"],
                answer=item["answer"],
                choices=choices,
                explanation=item["explanation"],
            )
        )

    return result


def build_question_bank() -> List[Question]:
    """Build the entire question bank."""

    bank: List[Question] = []

    bank.extend(
        make_kana_questions(
            HIRAGANA_ROWS,
            "Hiragana",
            "hiragana",
        )
    )

    bank.extend(
        make_kana_questions(
            KATAKANA_ROWS,
            "Katakana",
            "katakana",
        )
    )

    bank.extend(make_phrase_questions())
    bank.extend(make_sentence_questions())
    bank.extend(make_particle_questions())
    bank.extend(make_counter_questions())

    return bank


# =============================================================================
# SESSION STATE
# =============================================================================

def initialize_state() -> None:
    """Initialize persistent session values exactly once."""

    defaults = {
        "theme": "🌸 Sakura",
        "page": "Study",
        "question_bank": build_question_bank(),
        "quiz_questions": [],
        "quiz_index": 0,
        "quiz_score": 0,
        "quiz_answered": False,
        "quiz_selected_answer": None,
        "quiz_options": {},
        "missed_questions": [],
        "quiz_mode": "normal",
        "quiz_length": 10,
        "quiz_categories": [
            "Hiragana",
            "Katakana",
            "Both Kana",
            "Phrases & Sentences",
            "Grammar & Particles",
            "Counters & Quantifiers",
        ],
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# =============================================================================
# AUDIO
# =============================================================================

@st.cache_data(
    show_spinner=False,
    max_entries=500,
)
def generate_audio(text: str) -> bytes:
    """
    Generate Japanese speech into memory.

    Nothing is written to disk.
    """

    buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang="ja",
        slow=False,
    )

    tts.write_to_fp(buffer)

    buffer.seek(0)

    return buffer.getvalue()


def render_play_button(
    japanese: str,
    key_suffix: str,
    compact: bool = True,
) -> None:
    """
    Render a 'Play' button and an autoplay-capable audio player.

    The audio player is generated only after the learner explicitly
    requests it. This prevents the Study page from making dozens
    of gTTS requests on initial load.
    """

    if not japanese:
        return

    state_key = f"audio_visible_{key_suffix}"

    label = "▶ Play" if compact else "▶ Play pronunciation"

    if st.button(
        label,
        key=f"play_{key_suffix}",
        help="Generate and play Japanese pronunciation",
    ):
        st.session_state[state_key] = True

    if st.session_state.get(state_key, False):

        try:

            audio_bytes = generate_audio(japanese)

            # Streamlit has a native autoplay option.
            st.audio(
                audio_bytes,
                format="audio/mp3",
                autoplay=True,
            )

            st.caption(
                "Autoplay is attempted automatically. "
                "If your browser blocks it, tap ▶ on the player."
            )

        except Exception:
            st.warning(
                "Unable to generate Japanese audio right now. "
                "Please check your internet connection."
            )


# =============================================================================
# KANJIVG
# =============================================================================

def kanjivg_url(character: str) -> str:
    """Build the official KanjiVG raw SVG URL."""

    return (
        "https://raw.githubusercontent.com/"
        "KanjiVG/kanjivg/master/kanji/"
        f"{ord(character):05x}.svg"
    )


@st.cache_data(
    show_spinner=False,
    max_entries=200,
)
def fetch_stroke_svg(character: str) -> Optional[str]:
    """
    Fetch a KanjiVG SVG and return it as a string.

    The SVG is cached by Streamlit so repeated opens do not repeatedly
    download the same file.
    """

    if not character:
        return None

    try:
        with urllib.request.urlopen(
            kanjivg_url(character),
            timeout=10,
        ) as response:

            raw = response.read()

        return raw.decode(
            "utf-8",
            errors="replace",
        )

    except Exception:
        return None


def animate_svg(svg: str) -> str:
    """
    Add a sequential opacity animation to SVG path elements.

    This creates a simple stroke-by-stroke reveal effect without
    requiring JavaScript.
    """

    if not svg:
        return ""

    paths = list(
        re.finditer(
            r"<path\b[^>]*>",
            svg,
            flags=re.IGNORECASE,
        )
    )

    if not paths:
        return svg

    output = []
    last_position = 0

    for index, match in enumerate(paths):

        original = match.group(0)

        delay = index * 0.45

        if "style=" in original:

            replacement = original.replace(
                'style="',
                f'style="animation-delay:{delay:.2f}s;',
                1,
            )

        else:

            replacement = original.replace(
                ">",
                (
                    f' style="'
                    f"animation:strokeReveal 0.42s ease-out "
                    f"{delay:.2f}s forwards;"
                    f"opacity:0;"
                    f'">'
                ),
                1,
            )

        output.append(
            svg[last_position : match.start()]
        )

        output.append(
            replacement
        )

        last_position = match.end()

    output.append(
        svg[last_position:]
    )

    final_svg = "".join(output)

    # Add animation CSS before the closing SVG tag.
    animation_css = """
    <style>
        @keyframes strokeReveal {
            from {
                opacity: 0;
            }

            to {
                opacity: 1;
            }
        }

        svg {
            max-width: 100%;
            height: auto;
        }
    </style>
    """

    final_svg = final_svg.replace(
        "</svg>",
        animation_css + "</svg>",
    )

    return final_svg


def render_stroke_guide(
    character: str,
) -> None:
    """Render animated stroke guidance for a kana character."""

    stroke_count, note = STROKE_INFO.get(
        character,
        (0, "Stroke information unavailable."),
    )

    st.markdown(
        f"""
        <div class="stroke-panel">
            <div class="stroke-heading">
                ✍ Stroke Order
            </div>

            <div class="stroke-count">
                {stroke_count} stroke{"s" if stroke_count != 1 else ""}
            </div>

            <div class="stroke-note">
                {note}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    svg = fetch_stroke_svg(character)

    if svg:

        animated = animate_svg(svg)

        # st.html renders SVG/CSS directly in the Streamlit page.
        st.html(
            animated,
            width=250,
        )

        st.caption(
            "Stroke reference: KanjiVG • CC BY-SA 3.0"
        )

    else:

        st.warning(
            "Stroke diagram could not be loaded right now."
        )


# =============================================================================
# CSS
# =============================================================================

def inject_css(theme_name: str) -> None:
    """Inject theme and responsive styling."""

    theme = THEMES[theme_name]

    css = f"""
    <style>

    :root {{
        --page-bg: {theme["page_bg"]};
        --card-bg: {theme["card_bg"]};
        --text: {theme["text"]};
        --muted: {theme["muted"]};
        --primary: {theme["primary"]};
        --primary-hover: {theme["primary_hover"]};
        --border: {theme["border"]};
        --accent: {theme["accent"]};
        --code-bg: {theme["code_bg"]};
    }}

    /* ------------------------------------------------------------------
       APP
       ------------------------------------------------------------------ */

    .stApp {{
        background:
            radial-gradient(
                circle at top right,
                rgba(255,183,197,0.12),
                transparent 30%
            ),
            var(--page-bg);

        color: var(--text);
    }}

    .main .block-container {{
        max-width: 1400px;
        padding-top: 1.5rem;
        padding-bottom: 4rem;
    }}

    /* ------------------------------------------------------------------
       TEXT
       ------------------------------------------------------------------ */

    h1, h2, h3, h4, h5, p {{
        color: var(--text) !important;
    }}

    [data-testid="stCaptionContainer"] {{
        color: var(--muted) !important;
    }}

    /* ------------------------------------------------------------------
       BUTTONS
       ------------------------------------------------------------------ */

    .stButton > button {{
        border: 1px solid var(--border);
        border-radius: 11px;

        background: var(--card-bg);
        color: var(--text);

        font-weight: 800;

        min-height: 40px;

        transition:
            transform 0.15s ease,
            border-color 0.15s ease;
    }}

    .stButton > button:hover {{
        border-color: var(--primary);
        color: var(--primary);
        transform: translateY(-1px);
    }}

    /* ------------------------------------------------------------------
       SIDEBAR
       ------------------------------------------------------------------ */

    section[data-testid="stSidebar"] {{
        background: var(--card-bg);
        border-right: 1px solid var(--border);
    }}

    /* ------------------------------------------------------------------
       HERO
       ------------------------------------------------------------------ */

    .hero {{
        background:
            linear-gradient(
                135deg,
                rgba(255,183,197,.16),
                rgba(139,233,253,.08)
            ),
            var(--card-bg);

        border: 1px solid var(--border);
        border-radius: 24px;

        padding: 1.8rem;

        margin-bottom: 1.3rem;

        box-shadow:
            0 12px 35px rgba(0,0,0,.06);
    }}

    .hero-japanese {{
        font-size: clamp(2.5rem, 6vw, 5rem);
        line-height: 1.15;
        font-weight: 900;
        text-align: center;
    }}

    .hero-subtitle {{
        text-align: center;
        color: var(--muted);
        margin-top: .6rem;
    }}

    /* ------------------------------------------------------------------
       KANA CARDS
       ------------------------------------------------------------------ */

    .kana-card {{
        background: var(--card-bg);

        border:
            1px solid var(--border);

        border-radius: 16px;

        padding: .65rem .4rem;

        text-align: center;

        min-height: 115px;

        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;

        box-shadow:
            0 5px 18px rgba(0,0,0,.035);
    }}

    .kana-character {{
        font-family:
            "Noto Sans JP",
            "Yu Gothic",
            "Hiragino Kaku Gothic ProN",
            sans-serif;

        font-size: clamp(2.15rem, 4vw, 3.2rem);
        line-height: 1;

        font-weight: 900;

        color: var(--text);
    }}

    .kana-romaji {{
        font-size: .9rem;
        font-weight: 800;
        color: var(--muted);
        margin-top: .3rem;
    }}

    .row-label {{
        font-size: .85rem;
        font-weight: 900;
        color: var(--primary);
        margin-bottom: .4rem;
    }}

    /* ------------------------------------------------------------------
       STROKE PANEL
       ------------------------------------------------------------------ */

    .stroke-panel {{
        background: var(--code-bg);

        border:
            1px solid var(--border);

        border-radius: 13px;

        padding: .8rem;

        margin-top: .5rem;
    }}

    .stroke-heading {{
        color: var(--primary);
        font-weight: 900;
    }}

    .stroke-count {{
        font-size: 1.15rem;
        font-weight: 900;
        margin-top: .15rem;
    }}

    .stroke-note {{
        color: var(--muted);
        font-size: .83rem;
        line-height: 1.45;
        margin-top: .3rem;
    }}

    /* ------------------------------------------------------------------
       QUIZ JAPANESE PROMPT
       ------------------------------------------------------------------ */

    .japanese-prompt {{
        font-family:
            "Noto Sans JP",
            "Yu Gothic",
            "Hiragino Kaku Gothic ProN",
            sans-serif;

        font-size: clamp(2.4rem, 6vw, 4.8rem);
        line-height: 1.2;

        font-weight: 900;

        text-align: center;

        background: var(--card-bg);

        border:
            2px solid var(--border);

        border-radius: 20px;

        padding: 1.6rem .9rem;

        margin: 1rem 0;

        color: var(--text);

        box-shadow:
            0 10px 30px rgba(0,0,0,.05);
    }}

    /* ------------------------------------------------------------------
       SCORE
       ------------------------------------------------------------------ */

    .score-card {{
        background: var(--card-bg);

        border:
            1px solid var(--border);

        border-radius: 20px;

        padding: 1.7rem;

        text-align: center;
    }}

    .score-stars {{
        font-size: 2.8rem;
    }}

    .score-percent {{
        font-size: 3.2rem;
        font-weight: 900;
        color: var(--primary);
    }}

    /* ------------------------------------------------------------------
       MOBILE
       ------------------------------------------------------------------ */

    @media (max-width: 800px) {{

        .main .block-container {{
            padding-left: .75rem;
            padding-right: .75rem;
        }}

        .hero {{
            padding: 1.2rem;
            border-radius: 18px;
        }}

        .hero-japanese {{
            font-size: 2.4rem;
        }}

        .hero-subtitle {{
            font-size: .9rem;
        }}

        .kana-card {{
            min-height: 98px;
            padding: .45rem .25rem;
            border-radius: 13px;
        }}

        .kana-character {{
            font-size: 2rem;
        }}

        .kana-romaji {{
            font-size: .8rem;
        }}

        .japanese-prompt {{
            font-size: 2.1rem;
            padding: 1.15rem .5rem;
            border-radius: 15px;
        }}

        .stButton > button {{
            min-height: 42px;
        }}
    }}

    </style>
    """

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


inject_css(st.session_state.theme)


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> None:
    """Render navigation, theme and quiz controls."""

    with st.sidebar:

        st.markdown(
            """
            <div style="
                font-size: 1.7rem;
                font-weight: 900;
                margin-bottom: .4rem;
            ">
                🇯🇵 JP Japanese Lab
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Study kana. Listen. Practice. Repeat."
        )

        st.divider()

        # Theme
        theme = st.selectbox(
            "🎨 Appearance",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(
                st.session_state.theme
            ),
        )

        if theme != st.session_state.theme:
            st.session_state.theme = theme
            st.rerun()

        st.divider()

        # Navigation
        page = st.radio(
            "Mode",
            ["Study", "Quiz"],
            index=(
                0
                if st.session_state.page == "Study"
                else 1
            ),
        )

        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()

        st.divider()

        st.subheader("Quiz Settings")

        categories = st.multiselect(
            "Topics",
            [
                "Hiragana",
                "Katakana",
                "Both Kana",
                "Phrases & Sentences",
                "Grammar & Particles",
                "Counters & Quantifiers",
            ],
            default=st.session_state.quiz_categories,
        )

        st.session_state.quiz_categories = categories

        length = st.selectbox(
            "Round length",
            [10, 25, 50],
            index=[10, 25, 50].index(
                st.session_state.quiz_length
            ),
        )

        st.session_state.quiz_length = length

        if st.button(
            "🚀 Start New Quiz",
            use_container_width=True,
            type="primary",
        ):
            start_new_quiz(
                categories,
                length,
            )

            st.session_state.page = "Quiz"

            st.rerun()

        if st.session_state.missed_questions:

            st.markdown(
                f"""
                <div style="
                    margin-top:.7rem;
                    padding:.65rem;
                    border-radius:10px;
                    background:var(--code-bg);
                    font-size:.85rem;
                ">
                    🎯 {len(st.session_state.missed_questions)}
                    missed question(s) ready for review
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "🎯 Practice Missed",
                use_container_width=True,
            ):
                start_missed_quiz()

                st.session_state.page = "Quiz"

                st.rerun()


# =============================================================================
# STUDY COMPONENTS
# =============================================================================

def render_kana_card(
    kana: str,
    romaji: str,
    card_id: str,
) -> None:
    """Render one compact kana card."""

    if not kana:

        st.markdown(
            """
            <div style="
                min-height:98px;
                opacity:.15;
                display:flex;
                align-items:center;
                justify-content:center;
            ">
                ・
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    st.markdown(
        f"""
        <div class="kana-card">

            <div class="kana-character">
                {kana}
            </div>

            <div class="kana-romaji">
                {romaji}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    render_play_button(
        kana,
        f"{card_id}_audio",
    )

    with st.expander(
        "✍ Stroke",
        expanded=False,
    ):

        render_stroke_guide(
            kana
        )


def render_kana_chart(
    rows: Sequence[
        Tuple[str, Sequence[Tuple[str, str]]]
    ],
    chart_id: str,
) -> None:
    """Render the complete kana chart."""

    for row_index, (label, row) in enumerate(rows):

        st.markdown(
            f"""
            <div class="row-label">
                {label}
            </div>
            """,
            unsafe_allow_html=True,
        )

        cols = st.columns(5)

        for col_index, col in enumerate(cols):

            kana, romaji = row[col_index]

            with col:

                render_kana_card(
                    kana,
                    romaji,
                    f"{chart_id}_{row_index}_{col_index}",
                )


def render_expressions() -> None:
    """Render phrase study section."""

    st.subheader("💬 Essential Expressions")

    cols = st.columns(2)

    for index, (jp, en) in enumerate(PHRASES):

        with cols[index % 2]:

            st.markdown(
                f"""
                <div class="study-card">
                    <div class="kana-character"
                         style="font-size:2.0rem;">
                        {jp}
                    </div>

                    <div class="kana-romaji">
                        {en}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_play_button(
                jp,
                f"phrase_{index}",
            )


def render_grammar() -> None:
    """Render particle and counter reference."""

    particle_col, counter_col = st.columns(2)

    with particle_col:

        st.subheader("🧠 Particles")

        st.markdown(
            """
            | Particle | Function | Example |
            |---|---|---|
            | **は** | Topic | わたし**は**学生です。 |
            | **の** | Possession | わたし**の**本 |
            | **を** | Direct object | 水**を**飲みます。 |
            | **に** | Destination / time | 学校**に**行きます。 |
            | **で** | Place of action | 学校**で**勉強します。 |
            | **が** | Subject | 猫**が**います。 |
            """
        )

    with counter_col:

        st.subheader("🔢 Counters")

        st.markdown(
            """
            | Counter | Used for | Example |
            |---|---|---|
            | **人** | People | 三人 |
            | **本** | Long objects | 三本 |
            | **枚** | Flat objects | 三枚 |
            | **つ** | General items | 三つ |
            | **冊** | Books | 三冊 |
            | **台** | Vehicles / machines | 三台 |
            """
        )


# =============================================================================
# STUDY PAGE
# =============================================================================

def render_study_page() -> None:
    """Render the complete Study area."""

    st.markdown(
        """
        <div class="hero">

            <div class="hero-japanese">
                日本語を勉強しましょう！
            </div>

            <div class="hero-subtitle">
                Learn the kana, listen to Japanese pronunciation,
                and practice stroke order.
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(
        [
            "ひらがな Hiragana",
            "カタカナ Katakana",
            "💬 Expressions",
            "🧠 Grammar",
        ]
    )

    with tabs[0]:

        st.subheader("Hiragana Gojūon")

        st.caption(
            "Tap ▶ Play to hear the character. "
            "Open ✍ Stroke for the handwriting guide."
        )

        render_kana_chart(
            HIRAGANA_ROWS,
            "hiragana",
        )

    with tabs[1]:

        st.subheader("Katakana Gojūon")

        st.caption(
            "Useful for loanwords, foreign names, "
            "emphasis and technical vocabulary."
        )

        render_kana_chart(
            KATAKANA_ROWS,
            "katakana",
        )

    with tabs[2]:

        render_expressions()

    with tabs[3]:

        render_grammar()


# =============================================================================
# QUIZ ENGINE
# =============================================================================

def get_quiz_questions(
    categories: Sequence[str],
) -> List[Question]:
    """Return all questions matching selected categories."""

    categories_set = set(categories)

    if "Both Kana" in categories_set:

        categories_set.update(
            {
                "Hiragana",
                "Katakana",
            }
        )

    return [
        q
        for q in st.session_state.question_bank
        if q.category in categories_set
    ]


def start_new_quiz(
    categories: Sequence[str],
    length: int,
) -> None:
    """Create a normal quiz round."""

    available = get_quiz_questions(
        categories
    )

    if not available:

        st.warning(
            "Select at least one quiz category."
        )

        return

    length = min(
        length,
        len(available),
    )

    selected = random.sample(
        available,
        length,
    )

    st.session_state.quiz_questions = selected
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_selected_answer = None
    st.session_state.quiz_options = {}
    st.session_state.missed_questions = []
    st.session_state.quiz_mode = "normal"


def start_missed_quiz() -> None:
    """Create a quiz containing only the previous mistakes."""

    missed = (
        st.session_state.missed_questions.copy()
    )

    if not missed:
        return

    random.shuffle(
        missed
    )

    st.session_state.quiz_questions = missed
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_selected_answer = None
    st.session_state.quiz_options = {}
    st.session_state.missed_questions = []
    st.session_state.quiz_mode = "missed"


def get_stable_options(
    question: Question,
) -> List[str]:
    """
    Return stable randomized options.

    The options are created once and then stored in session_state
    so a Streamlit rerun can't shuffle the answers unexpectedly.
    """

    key = question.question_id

    if key not in st.session_state.quiz_options:

        options = list(
            dict.fromkeys(
                question.choices
            )
        )

        random.shuffle(options)

        st.session_state.quiz_options[key] = options

    return st.session_state.quiz_options[key]


# =============================================================================
# QUIZ PAGE
# =============================================================================

def render_quiz_page() -> None:
    """Render the active quiz."""

    questions = st.session_state.quiz_questions

    if not questions:

        render_quiz_landing()

        return

    if (
        st.session_state.quiz_index
        >= len(questions)
    ):

        render_quiz_results()

        return

    question = questions[
        st.session_state.quiz_index
    ]

    total = len(questions)

    index = st.session_state.quiz_index

    if st.session_state.quiz_mode == "missed":

        st.info(
            "🎯 Targeted Review: "
            "these are questions you previously missed."
        )

    st.subheader(
        f"Question {index + 1} of {total}"
    )

    st.progress(
        index / total,
        text=(
            f"Progress {index}/{total} "
            f"• Score {st.session_state.quiz_score}"
        ),
    )

    score_col, category_col = st.columns(2)

    with score_col:

        st.metric(
            "Score",
            st.session_state.quiz_score,
        )

    with category_col:

        st.metric(
            "Category",
            question.category,
        )

    st.divider()

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:1.1rem;
            font-weight:800;
            color:var(--muted);
        ">
            {question.prompt}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if question.japanese:

        st.markdown(
            f"""
            <div class="japanese-prompt">
                {question.japanese}
            </div>
            """,
            unsafe_allow_html=True,
        )

        render_play_button(
            question.japanese,
            f"quiz_{question.question_id}",
            compact=False,
        )

    options = get_stable_options(
        question
    )

    if not st.session_state.quiz_answered:

        with st.form(
            key=f"quiz_form_{question.question_id}"
        ):

            selected = st.radio(
                "Choose your answer:",
                options=options,
                index=None,
            )

            submitted = st.form_submit_button(
                "✅ Submit Answer",
                use_container_width=True,
                type="primary",
            )

        if submitted:

            if selected is None:

                st.warning(
                    "Choose an answer first."
                )

                st.stop()

            st.session_state.quiz_selected_answer = selected
            st.session_state.quiz_answered = True

            if selected == question.answer:

                st.session_state.quiz_score += 1

            else:

                st.session_state.missed_questions.append(
                    question
                )

            st.rerun()

    else:

        selected = (
            st.session_state.quiz_selected_answer
        )

        if selected == question.answer:

            st.success(
                "🎉 Correct!"
            )

        else:

            st.error(
                f"❌ Incorrect. "
                f"Correct answer: **{question.answer}**"
            )

        st.info(
            f"💡 {question.explanation}"
        )

        if question.japanese:

            render_play_button(
                question.japanese,
                f"quiz_again_{question.question_id}",
                compact=False,
            )

        st.divider()

        last_question = (
            index + 1 >= total
        )

        label = (
            "🏁 Finish Round"
            if last_question
            else "➡️ Next Question"
        )

        if st.button(
            label,
            use_container_width=True,
            type="primary",
        ):

            st.session_state.quiz_index += 1
            st.session_state.quiz_answered = False
            st.session_state.quiz_selected_answer = None

            st.rerun()


# =============================================================================
# QUIZ LANDING
# =============================================================================

def render_quiz_landing() -> None:
    """Render the no-active-quiz state."""

    st.title("📝 Japanese Quiz")

    st.markdown(
        """
        Test yourself on kana, expressions, grammar,
        particles and Japanese counters.
        """
    )

    st.divider()

    cols = st.columns(3)

    with cols[0]:
        st.metric(
            "Round Sizes",
            "10 / 25 / 50",
        )

    with cols[1]:
        st.metric(
            "Categories",
            "6",
        )

    with cols[2]:
        st.metric(
            "Rating",
            "0–3 ⭐",
        )

    st.divider()

    st.info(
        "Choose your topics and round length in the sidebar, "
        "then press Start New Quiz."
    )

    if st.session_state.missed_questions:

        if st.button(
            "🎯 Practice Missed Questions",
            type="primary",
        ):

            start_missed_quiz()

            st.rerun()


# =============================================================================
# RESULTS
# =============================================================================

def get_star_rating(
    percentage: float,
) -> int:
    """Convert percentage into the requested rating."""

    if percentage >= 100:
        return 3

    if percentage >= 70:
        return 2

    if percentage >= 30:
        return 1

    return 0


def render_quiz_results() -> None:
    """Render final score and missed-question review."""

    total = len(
        st.session_state.quiz_questions
    )

    score = (
        st.session_state.quiz_score
    )

    percentage = (
        score / total * 100
        if total
        else 0
    )

    stars = get_star_rating(
        percentage
    )

    stars_text = (
        "🌟" * stars
        if stars
        else "☆☆☆"
    )

    st.title("🏆 Round Complete!")

    st.markdown(
        f"""
        <div class="score-card">

            <div class="score-stars">
                {stars_text}
            </div>

            <div class="score-percent">
                {percentage:.0f}%
            </div>

            <div>
                {score} correct out of {total}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if stars == 3:

        st.success(
            "Perfect score! 日本語が上手ですね！ 🔥"
        )

    elif stars == 2:

        st.success(
            "Great job! You're very close to a perfect round."
        )

    elif stars == 1:

        st.warning(
            "You're getting there. Review your mistakes and try again."
        )

    else:

        st.error(
            "Let's use the mistakes as your study list."
        )

    missed = (
        st.session_state.missed_questions
    )

    with st.expander(
        f"📖 Review Missed Questions ({len(missed)})",
        expanded=bool(missed),
    ):

        if not missed:

            st.success(
                "🎉 No missed questions!"
            )

        else:

            for number, question in enumerate(
                missed,
                start=1,
            ):

                st.markdown(
                    f"### {number}. {question.prompt}"
                )

                if question.japanese:

                    st.markdown(
                        f"""
                        <div class="japanese-prompt"
                             style="font-size:2.4rem;">
                            {question.japanese}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    render_play_button(
                        question.japanese,
                        f"missed_{question.question_id}",
                        compact=False,
                    )

                st.markdown(
                    f"**Correct answer:** "
                    f"`{question.answer}`"
                )

                st.caption(
                    question.explanation
                )

                st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:

        if missed:

            if st.button(
                "🎯 Practice Missed",
                use_container_width=True,
                type="primary",
            ):

                start_missed_quiz()
                st.rerun()

    with col2:

        if st.button(
            "🔄 New Quiz",
            use_container_width=True,
        ):

            start_new_quiz(
                st.session_state.quiz_categories,
                st.session_state.quiz_length,
            )

            st.rerun()

    with col3:

        if st.button(
            "📚 Back to Study",
            use_container_width=True,
        ):

            st.session_state.page = "Study"
            st.rerun()


# =============================================================================
# APP ENTRY POINT
# =============================================================================

def main() -> None:
    """Run the application."""

    render_sidebar()

    if st.session_state.page == "Study":

        render_study_page()

    elif st.session_state.page == "Quiz":

        render_quiz_page()


if __name__ == "__main__":
    main()
