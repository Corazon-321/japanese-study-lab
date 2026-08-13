"""
JP Japanese Lab
===============

A mobile-friendly Japanese study application built with Streamlit.

APP STRUCTURE
-------------
Sidebar
    📚 Study
        ├── あ Hiragana
        ├── カ Katakana
        ├── 💬 Expressions
        └── 🧠 Grammar

    📝 Quiz
        ├── Start Quiz
        ├── Review Missed
        └── ⚙ Quiz Settings

    🎨 Appearance

STUDY FEATURES
--------------
    - Hiragana Gojūon
    - Katakana Gojūon
    - ▶ Play Japanese pronunciation
    - gTTS autoplay attempt
    - Cached audio
    - Mobile-friendly two-column layout
    - Stroke count
    - Animated stroke-order guide
    - Manual stroke-by-stroke practice
    - Essential expressions
    - Particle reference
    - Counter reference

QUIZ FEATURES
-------------
    - Hiragana
    - Katakana
    - Both Kana
    - Phrases & Sentences
    - Grammar & Particles
    - Counters & Quantifiers
    - 10 / 25 / 50 questions
    - Randomized questions
    - Randomized choices
    - Persistent session state
    - Live progress
    - Live score
    - 0–3 star rating
    - Missed-question tracker
    - Targeted re-quiz

TECHNICAL
---------
    - Streamlit
    - gTTS
    - io.BytesIO
    - st.session_state
    - st.cache_data
    - KanjiVG SVG data
    - st.iframe() for interactive stroke player

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
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="JP Japanese Lab",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# THEMES
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
# GOJŪON DATA
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
    ("N", [("ン", "n"), ("", ""), ("", ""), ("", ""), ("", "")]),
]


# =============================================================================
# STROKE INFORMATION
# =============================================================================

STROKE_INFO: Dict[str, Tuple[int, str]] = {
    "あ": (3, "Short top stroke → central curve → final sweeping stroke."),
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
    "に": (3, "Short horizontal strokes → curved ending."),
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
# STUDY CONTENT
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


# =============================================================================
# QUIZ CONTENT
# =============================================================================

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


PARTICLE_QUESTIONS = [
    {
        "prompt": "Which particle marks the topic?",
        "japanese": "わたし ___ 学生です。",
        "answer": "は",
        "choices": ["は", "を", "で", "に"],
        "explanation": "は marks the topic. As a particle, it is pronounced 'wa'.",
    },
    {
        "prompt": "Which particle expresses possession or connection?",
        "japanese": "わたし ___ 本",
        "answer": "の",
        "choices": ["の", "を", "で", "が"],
        "explanation": "の connects nouns and commonly expresses possession.",
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
        "explanation": "で marks where an action takes place.",
    },
    {
        "prompt": "Which particle commonly marks the subject?",
        "japanese": "猫 ___ います。",
        "answer": "が",
        "choices": ["が", "を", "で", "の"],
        "explanation": "が commonly marks the subject or new information.",
    },
]

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
        "prompt": "Which counter is used for flat objects?",
        "japanese": "紙を四 ___ ください。",
        "answer": "枚（まい）",
        "choices": ["枚（まい）", "本（ほん）", "人（にん）", "冊（さつ）"],
        "explanation": "枚 is used for flat objects.",
    },
    {
        "prompt": "Which general counter is used for many ordinary items?",
        "japanese": "りんごを三 ___ ください。",
        "answer": "つ",
        "choices": ["つ", "台（だい）", "冊（さつ）", "人（にん）"],
        "explanation": "つ is a general-purpose counter.",
    },
    {
        "prompt": "Which counter is used for books and volumes?",
        "japanese": "本を五 ___ 読みました。",
        "answer": "冊（さつ）",
        "choices": ["冊（さつ）", "本（ほん）", "枚（まい）", "台（だい）"],
        "explanation": "冊 is used for books and volumes.",
    },
    {
        "prompt": "Which counter is used for vehicles and machines?",
        "japanese": "車が二 ___ あります。",
        "answer": "台（だい）",
        "choices": ["台（だい）", "冊（さつ）", "枚（まい）", "本（ほん）"],
        "explanation": "台 is commonly used for vehicles and machines.",
    },
]


# =============================================================================
# QUESTION MODEL
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
# QUESTION BANK
# =============================================================================

def make_kana_questions(
    rows: Sequence[Tuple[str, Sequence[Tuple[str, str]]]],
    category: str,
    prefix: str,
) -> List[Question]:
    """Generate reading and recognition questions for kana."""

    items = [
        (kana, romaji)
        for _, row in rows
        for kana, romaji in row
        if kana
    ]

    symbols = [item[0] for item in items]
    readings = [item[1] for item in items]

    result: List[Question] = []

    for index, (kana, romaji) in enumerate(items):

        wrong_readings = random.sample(
            [x for x in readings if x != romaji],
            3,
        )

        result.append(
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

        result.append(
            Question(
                question_id=f"{prefix}_recognize_{index}",
                category=category,
                prompt=f"Which kana represents '{romaji}'?",
                japanese=romaji,
                answer=kana,
                choices=[kana, *wrong_symbols],
                explanation=f"'{romaji}' is written as {kana}.",
            )
        )

    return result


def make_phrase_questions() -> List[Question]:
    """Generate phrase questions."""

    result: List[Question] = []

    english = [item[1] for item in PHRASES]
    japanese = [item[0] for item in PHRASES]

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

        wrong_japanese = random.sample(
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
                choices=[jp, *wrong_japanese],
                explanation=f"{jp} means '{en}'.",
            )
        )

    return result


def make_sentence_questions() -> List[Question]:
    """Generate sentence comprehension questions."""

    translations = [
        item[1]
        for item in SENTENCES
    ]

    result: List[Question] = []

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
    """Generate particle questions."""

    result = []

    for index, item in enumerate(
        PARTICLE_QUESTIONS
    ):

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
    """Generate counter questions."""

    result = []

    for index, item in enumerate(
        COUNTER_QUESTIONS
    ):

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
    """Build the complete question bank."""

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

    bank.extend(
        make_phrase_questions()
    )

    bank.extend(
        make_sentence_questions()
    )

    bank.extend(
        make_particle_questions()
    )

    bank.extend(
        make_counter_questions()
    )

    return bank


# =============================================================================
# SESSION STATE
# =============================================================================

def initialize_state() -> None:
    """Initialize all application state."""

    defaults = {
        "theme": "🌙 Midnight Cyber-Tokyo",

        # Current screen.
        "page": "Study",

        # Study subsection.
        "study_section": "Hiragana",

        # Quiz state.
        "quiz_questions": [],
        "quiz_index": 0,
        "quiz_score": 0,
        "quiz_answered": False,
        "quiz_selected_answer": None,
        "quiz_options": {},
        "quiz_mode": "normal",

        # Missed questions.
        "missed_questions": [],

        # Quiz configuration.
        "quiz_length": 10,
        "quiz_categories": [
            "Hiragana",
            "Katakana",
        ],

        # Question bank.
        "question_bank": build_question_bank(),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


initialize_state()


# =============================================================================
# HTML HELPER
# =============================================================================

def render_html(
    html: str,
) -> None:
    """Render custom trusted HTML."""

    st.html(html)


# =============================================================================
# AUDIO
# =============================================================================

@st.cache_data(
    show_spinner=False,
    max_entries=500,
)
def generate_audio(
    text: str,
) -> bytes:
    """
    Generate Japanese TTS audio in memory.

    No MP3 files are written to disk.
    """

    buffer = io.BytesIO()

    tts = gTTS(
        text=text,
        lang="ja",
        slow=False,
    )

    tts.write_to_fp(
        buffer
    )

    buffer.seek(0)

    return buffer.getvalue()


def render_play_button(
    japanese: str,
    key_suffix: str,
    large: bool = False,
) -> None:
    """
    Display ▶ Play.

    Once pressed:
        - Generate or retrieve cached gTTS audio.
        - Display st.audio().
        - Request autoplay.

    Browsers can still block audible autoplay.
    """

    if not japanese:
        return

    visible_key = (
        f"audio_visible_{key_suffix}"
    )

    label = (
        "▶ Play pronunciation"
        if large
        else "▶ Play"
    )

    if st.button(
        label,
        key=f"play_{key_suffix}",
        use_container_width=large,
    ):
        st.session_state[
            visible_key
        ] = True

    if st.session_state.get(
        visible_key,
        False,
    ):

        try:

            audio_bytes = generate_audio(
                japanese
            )

            st.audio(
                audio_bytes,
                format="audio/mp3",
                autoplay=True,
            )

        except Exception:

            st.warning(
                "Unable to generate Japanese pronunciation. "
                "Check your internet connection."
            )


# =============================================================================
# KANJIVG STROKE DATA
# =============================================================================

def kanjivg_url(
    character: str,
) -> str:
    """Build the KanjiVG SVG URL."""

    return (
        "https://raw.githubusercontent.com/"
        "KanjiVG/kanjivg/master/kanji/"
        f"{ord(character):05x}.svg"
    )


@st.cache_data(
    show_spinner=False,
    max_entries=200,
)
def fetch_stroke_svg(
    character: str,
) -> Optional[str]:
    """Download and cache the KanjiVG SVG."""

    if not character:
        return None

    try:

        with urllib.request.urlopen(
            kanjivg_url(character),
            timeout=10,
        ) as response:

            return response.read().decode(
                "utf-8",
                errors="replace",
            )

    except Exception:

        return None


def prepare_animated_svg(
    svg: str,
) -> Tuple[str, int]:
    """
    Add classes and stroke numbers to KanjiVG paths.
    """

    pattern = re.compile(
        r'<path\b[^>]*id="([^"]*-s(\d+))"[^>]*>',
        flags=re.IGNORECASE,
    )

    matches = list(
        pattern.finditer(svg)
    )

    matches.sort(
        key=lambda match: int(
            match.group(2)
        )
    )

    stroke_count = len(
        matches
    )

    if stroke_count == 0:
        return svg, 0

    output = svg

    for match in reversed(matches):

        original = match.group(0)

        stroke_number = int(
            match.group(2)
        )

        cleaned = re.sub(
            r'\sclass="[^"]*"',
            "",
            original,
            flags=re.IGNORECASE,
        )

        cleaned = re.sub(
            r'\sstyle="[^"]*"',
            "",
            cleaned,
            flags=re.IGNORECASE,
        )

        id_text = (
            f'id="{match.group(1)}"'
        )

        attributes = (
            f' class="kana-stroke"'
            f' data-stroke="{stroke_number}"'
        )

        replacement = cleaned.replace(
            id_text,
            id_text + attributes,
            1,
        )

        output = (
            output[:match.start()]
            + replacement
            + output[match.end():]
        )

    return output, stroke_count


def build_stroke_player(
    svg: str,
    character: str,
    stroke_count: int,
) -> str:
    """
    Build the self-contained interactive stroke player.

    The player has:
        ▶ Animate
        ⏭ Next Stroke
        ↶ Replay
    """

    prepared_svg, detected_count = (
        prepare_animated_svg(
            svg
        )
    )

    if detected_count:
        stroke_count = detected_count

    return f"""
<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta
    name="viewport"
    content="width=device-width, initial-scale=1.0"
/>

<style>

* {{
    box-sizing: border-box;
}}

body {{

    margin: 0;
    padding: 10px;

    background: transparent;

    font-family:
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;

    display: flex;
    justify-content: center;
}}

.viewer {{

    width: 100%;
    max-width: 320px;

    display: flex;
    flex-direction: column;
    align-items: center;

    gap: 9px;
}}

.title {{

    font-size: 14px;
    font-weight: 900;

    color: #d81b60;
}}

.canvas {{

    width: 235px;
    height: 235px;

    background: white;

    border:
        2px solid #f0b7c4;

    border-radius: 20px;

    display: flex;
    align-items: center;
    justify-content: center;

    box-shadow:
        0 8px 25px rgba(0,0,0,.08);
}}

.canvas svg {{
    width: 195px;
    height: 195px;
}}

.kana-stroke {{
    opacity: 0;

    transition:
        opacity .18s ease;
}}

.kana-stroke.visible {{
    opacity: 1 !important;
}}

.kana-stroke.active {{
    filter:
        drop-shadow(
            0 0 4px
            rgba(216,27,96,.45)
        );
}}

.controls {{

    display: flex;
    flex-wrap: wrap;
    justify-content: center;

    gap: 7px;
}}

button {{

    background: white;

    color: #d81b60;

    border:
        1px solid #d81b60;

    border-radius: 10px;

    padding:
        8px 12px;

    font-size: 13px;
    font-weight: 800;

    cursor: pointer;
}}

button:hover {{
    background: #fff0f4;
}}

.counter {{

    color: #d81b60;

    font-size: 14px;
    font-weight: 900;
}}

.status {{

    min-height: 18px;

    color: #666;

    font-size: 13px;

    text-align: center;
}}

.complete {{
    color: #2e8b57;
    font-weight: 900;
}}

@media (prefers-color-scheme: dark) {{

    .canvas {{
        background: #1e1e2e;
        border-color: #ff79c6;
    }}

    button {{
        background: #1e1e2e;
        border-color: #ff79c6;
        color: #ff79c6;
    }}

    button:hover {{
        background: #292941;
    }}

    .status {{
        color: #b7c1cc;
    }}
}}

</style>

</head>

<body>

<div class="viewer">

    <div class="title">
        ✍ {character} Stroke Order
    </div>

    <div class="canvas">
        {prepared_svg}
    </div>

    <div
        class="counter"
        id="counter"
    >
        Ready
    </div>

    <div
        class="status"
        id="status"
    >
        Press ▶ Animate to begin.
    </div>

    <div class="controls">

        <button onclick="animateAll()">
            ▶ Animate
        </button>

        <button onclick="nextStroke()">
            ⏭ Next Stroke
        </button>

        <button onclick="resetPlayer()">
            ↶ Replay
        </button>

    </div>

</div>

<script>

const strokes =
    Array.from(
        document.querySelectorAll(
            ".kana-stroke"
        )
    ).sort(
        (a, b) =>
            Number(a.dataset.stroke)
            -
            Number(b.dataset.stroke)
    );


const counter =
    document.getElementById(
        "counter"
    );


const status =
    document.getElementById(
        "status"
    );


let currentStroke = 0;

let animationToken = 0;


function resetPlayer() {{

    animationToken++;

    currentStroke = 0;

    strokes.forEach(
        stroke => {{
            stroke.classList.remove(
                "visible"
            );

            stroke.classList.remove(
                "active"
            );
        }}
    );

    counter.textContent =
        "Ready";

    status.textContent =
        "Press ▶ Animate to begin.";

    status.classList.remove(
        "complete"
    );
}}


function showStroke(
    index
) {{

    if (
        index < 0
        ||
        index >= strokes.length
    ) {{
        return;
    }}

    strokes.forEach(
        (stroke, i) => {{

            stroke.classList.remove(
                "active"
            );

            if (i <= index) {{
                stroke.classList.add(
                    "visible"
                );
            }} else {{
                stroke.classList.remove(
                    "visible"
                );
            }}
        }}
    );

    strokes[index].classList.add(
        "active"
    );

    currentStroke =
        index + 1;

    counter.textContent =
        "Stroke "
        +
        currentStroke
        +
        " / "
        +
        strokes.length;

    status.textContent =
        "Drawing stroke "
        +
        currentStroke;

    status.classList.remove(
        "complete"
    );
}}


function nextStroke() {{

    if (
        currentStroke >=
        strokes.length
    ) {{
        resetPlayer();
        return;
    }}

    showStroke(
        currentStroke
    );

    if (
        currentStroke >=
        strokes.length
    ) {{

        counter.textContent =
            "Complete ✓";

        status.textContent =
            "All strokes completed.";

        status.classList.add(
            "complete"
        );

        strokes.forEach(
            stroke =>
                stroke.classList.remove(
                    "active"
                )
        );
    }}
}}


async function animateAll() {{

    resetPlayer();

    const animationId =
        animationToken;

    for (
        let i = 0;
        i < strokes.length;
        i++
    ) {{

        if (
            animationId
            !==
            animationToken
        ) {{
            return;
        }}

        showStroke(i);

        await new Promise(
            resolve =>
                setTimeout(
                    resolve,
                    650
                )
        );

        if (
            animationId
            !==
            animationToken
        ) {{
            return;
        }}
    }}

    counter.textContent =
        "Complete ✓";

    status.textContent =
        "All strokes completed.";

    status.classList.add(
        "complete"
    );

    strokes.forEach(
        stroke =>
            stroke.classList.remove(
                "active"
            )
    );
}}

</script>

</body>

</html>
"""


def render_stroke_guide(
    character: str,
) -> None:
    """Render the interactive stroke guide."""

    count, note = STROKE_INFO.get(
        character,
        (
            0,
            "Stroke information unavailable.",
        ),
    )

    render_html(
        f"""
        <div class="stroke-panel">

            <div class="stroke-heading">
                ✍ Stroke Order
            </div>

            <div class="stroke-count">
                {count}
                stroke{"s" if count != 1 else ""}
            </div>

            <div class="stroke-note">
                {note}
            </div>

        </div>
        """
    )

    svg = fetch_stroke_svg(
        character
    )

    if svg is None:

        st.warning(
            "Unable to load stroke-order data."
        )

        return

    player = build_stroke_player(
        svg,
        character,
        count,
    )

    # Current st.iframe API:
    # src, width, height, tab_index
    st.iframe(
        player,
        height=360,
    )

    st.caption(
        "Stroke reference: KanjiVG • CC BY-SA 3.0"
    )


# =============================================================================
# CUSTOM CSS
# =============================================================================

def inject_css(
    theme_name: str,
) -> None:
    """Apply the application's custom visual theme."""

    theme = THEMES[
        theme_name
    ]

    css = f"""
<style>

:root {{
    --page-bg: {theme["page_bg"]};
    --card-bg: {theme["card_bg"]};
    --text: {theme["text"]};
    --muted: {theme["muted"]};
    --primary: {theme["primary"]};
    --primary-hover: {theme["primary_hover"]};
    --secondary: {theme["secondary"]};
    --border: {theme["border"]};
    --accent: {theme["accent"]};
    --code-bg: {theme["code_bg"]};
}}


/* ==============================================================
   GLOBAL
   ============================================================== */

.stApp {{

    background:
        radial-gradient(
            circle at top right,
            rgba(255,183,197,.10),
            transparent 30%
        ),
        var(--page-bg);

    color: var(--text);
}}

.main .block-container {{

    max-width: 1400px;

    padding-top: 1.4rem;
    padding-bottom: 4rem;
}}

h1, h2, h3, h4, h5, p {{
    color: var(--text) !important;
}}

[data-testid="stCaptionContainer"] {{
    color: var(--muted) !important;
}}


/* ==============================================================
   SIDEBAR
   ============================================================== */

section[data-testid="stSidebar"] {{

    background:
        var(--card-bg);

    border-right:
        1px solid var(--border);
}}


/* ==============================================================
   SIDEBAR NAV
   ============================================================== */

.sidebar-title {{

    font-size: 1.55rem;

    font-weight: 900;

    margin-bottom: .2rem;
}}

.sidebar-section {{

    font-size: .78rem;

    font-weight: 900;

    letter-spacing: .06em;

    color: var(--muted);

    margin-top: .8rem;

    margin-bottom: .35rem;

    text-transform: uppercase;
}}


/* ==============================================================
   BUTTONS
   ============================================================== */

.stButton > button {{

    border:
        1px solid var(--border);

    border-radius:
        11px;

    background:
        var(--card-bg);

    color:
        var(--text);

    font-weight:
        800;

    min-height:
        40px;

    transition:
        transform .15s ease,
        border-color .15s ease,
        color .15s ease;
}}

.stButton > button:hover {{

    border-color:
        var(--primary);

    color:
        var(--primary);

    transform:
        translateY(-1px);
}}


/* ==============================================================
   HERO
   ============================================================== */

.hero {{

    background:
        linear-gradient(
            135deg,
            rgba(255,183,197,.15),
            rgba(139,233,253,.08)
        ),
        var(--card-bg);

    border:
        1px solid var(--border);

    border-radius:
        24px;

    padding:
        1.7rem;

    margin-bottom:
        1.2rem;

    box-shadow:
        0 12px 35px
        rgba(0,0,0,.06);
}}

.hero-japanese {{

    font-family:
        "Noto Sans JP",
        "Yu Gothic",
        sans-serif;

    font-size:
        clamp(2.4rem, 6vw, 5rem);

    font-weight:
        900;

    line-height:
        1.15;

    text-align:
        center;
}}

.hero-subtitle {{

    text-align:
        center;

    color:
        var(--muted);

    margin-top:
        .5rem;
}}


/* ==============================================================
   STUDY CARD
   ============================================================== */

.kana-card {{

    background:
        var(--card-bg);

    border:
        1px solid var(--border);

    border-radius:
        16px;

    padding:
        .8rem;

    min-height:
        115px;

    display:
        flex;

    flex-direction:
        column;

    justify-content:
        center;

    align-items:
        center;

    text-align:
        center;

    box-shadow:
        0 5px 18px
        rgba(0,0,0,.04);
}}

.kana-character {{

    font-family:
        "Noto Sans JP",
        "Yu Gothic",
        "Hiragino Kaku Gothic ProN",
        sans-serif;

    font-size:
        clamp(2.2rem, 7vw, 3.5rem);

    line-height:
        1;

    font-weight:
        900;

    color:
        var(--text);
}}

.kana-romaji {{

    margin-top:
        .4rem;

    font-size:
        .88rem;

    font-weight:
        800;

    color:
        var(--muted);
}}

.row-label {{

    color:
        var(--primary);

    font-size:
        .85rem;

    font-weight:
        900;

    margin-top:
        .9rem;

    margin-bottom:
        .35rem;
}}


/* ==============================================================
   STROKE PANEL
   ============================================================== */

.stroke-panel {{

    background:
        var(--code-bg);

    border:
        1px solid var(--border);

    border-radius:
        13px;

    padding:
        .8rem;

    margin-top:
        .5rem;
}}

.stroke-heading {{

    color:
        var(--primary);

    font-weight:
        900;
}}

.stroke-count {{

    font-size:
        1.1rem;

    font-weight:
        900;

    color:
        var(--text);

    margin-top:
        .15rem;
}}

.stroke-note {{

    color:
        var(--muted);

    font-size:
        .82rem;

    line-height:
        1.45;

    margin-top:
        .3rem;
}}


/* ==============================================================
   QUIZ
   ============================================================== */

.japanese-prompt {{

    font-family:
        "Noto Sans JP",
        "Yu Gothic",
        "Hiragino Kaku Gothic ProN",
        sans-serif;

    font-size:
        clamp(2.4rem, 6vw, 4.8rem);

    font-weight:
        900;

    line-height:
        1.2;

    text-align:
        center;

    background:
        var(--card-bg);

    border:
        2px solid var(--border);

    border-radius:
        20px;

    padding:
        1.5rem .8rem;

    margin:
        1rem 0;

    color:
        var(--text);
}}


/* ==============================================================
   SCORE
   ============================================================== */

.score-card {{

    background:
        var(--card-bg);

    border:
        1px solid var(--border);

    border-radius:
        20px;

    padding:
        1.6rem;

    text-align:
        center;
}}

.score-stars {{

    font-size:
        2.8rem;
}}

.score-percent {{

    font-size:
        3.2rem;

    font-weight:
        900;

    color:
        var(--primary);

    margin:
        .3rem 0;
}}


/* ==============================================================
   MOBILE
   ============================================================== */

@media (max-width: 700px) {{

    .main .block-container {{

        padding-left:
            .65rem;

        padding-right:
            .65rem;
    }}

    .hero {{

        padding:
            1.1rem;

        border-radius:
            18px;
    }}

    .hero-japanese {{

        font-size:
            2.25rem;
    }}

    .hero-subtitle {{

        font-size:
            .88rem;
    }}

    .kana-card {{

        min-height:
            105px;

        padding:
            .55rem;

        border-radius:
            14px;
    }}

    .kana-character {{

        font-size:
            2.2rem;
    }}

    .kana-romaji {{

        font-size:
            .78rem;
    }}

    .japanese-prompt {{

        font-size:
            2rem;

        padding:
            1.1rem .5rem;
    }}

}}

</style>
"""

    st.html(
        css
    )


inject_css(
    st.session_state.theme
)


# =============================================================================
# QUIZ HELPERS
# =============================================================================

def get_quiz_questions(
    categories: Sequence[str],
) -> List[Question]:
    """Filter the question bank by selected categories."""

    selected = set(
        categories
    )

    if "Both Kana" in selected:

        selected.update(
            {
                "Hiragana",
                "Katakana",
            }
        )

    return [
        question
        for question in st.session_state.question_bank
        if question.category in selected
    ]


def start_new_quiz(
    categories: Sequence[str],
    length: int,
) -> bool:
    """
    Start a new quiz.

    Returns True when successfully started.
    """

    available = get_quiz_questions(
        categories
    )

    if not available:

        return False

    actual_length = min(
        length,
        len(available),
    )

    selected = random.sample(
        available,
        actual_length,
    )

    st.session_state.quiz_questions = (
        selected
    )

    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_selected_answer = None
    st.session_state.quiz_options = {}
    st.session_state.missed_questions = []
    st.session_state.quiz_mode = "normal"

    return True


def start_missed_quiz() -> bool:
    """Start a quiz made exclusively from missed questions."""

    missed = (
        st.session_state.missed_questions.copy()
    )

    if not missed:

        return False

    random.shuffle(
        missed
    )

    st.session_state.quiz_questions = (
        missed
    )

    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_selected_answer = None
    st.session_state.quiz_options = {}

    # Clear the current missed list.
    # Any new misses will populate it again.
    st.session_state.missed_questions = []

    st.session_state.quiz_mode = "missed"

    return True


def get_stable_options(
    question: Question,
) -> List[str]:
    """Create stable randomized options for one question."""

    key = question.question_id

    if key not in (
        st.session_state.quiz_options
    ):

        options = list(
            dict.fromkeys(
                question.choices
            )
        )

        random.shuffle(
            options
        )

        st.session_state.quiz_options[
            key
        ] = options

    return st.session_state.quiz_options[
        key
    ]


# =============================================================================
# STUDY PAGE COMPONENTS
# =============================================================================

def render_kana_card(
    kana: str,
    romaji: str,
    card_id: str,
) -> None:
    """Render one kana card."""

    if not kana:

        render_html(
            """
            <div style="
                min-height:105px;
                display:flex;
                align-items:center;
                justify-content:center;
                opacity:.1;
                font-size:1.5rem;
            ">
                ・
            </div>
            """
        )

        return

    render_html(
        f"""
        <div class="kana-card">

            <div class="kana-character">
                {kana}
            </div>

            <div class="kana-romaji">
                {romaji}
            </div>

        </div>
        """
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
    """Render a mobile-friendly kana chart."""

    for row_index, (
        label,
        row,
    ) in enumerate(rows):

        render_html(
            f"""
            <div class="row-label">
                {label}
            </div>
            """
        )

        for start in range(
            0,
            len(row),
            2,
        ):

            pair = row[
                start:start + 2
            ]

            columns = st.columns(
                2
            )

            for column_index, column in enumerate(
                columns
            ):

                if column_index >= len(
                    pair
                ):
                    continue

                kana, romaji = (
                    pair[column_index]
                )

                with column:

                    render_kana_card(
                        kana,
                        romaji,
                        (
                            f"{chart_id}_"
                            f"{row_index}_"
                            f"{start + column_index}"
                        ),
                    )


def render_hiragana_page() -> None:
    """Render Hiragana study page."""

    render_html(
        """
        <div class="hero">

            <div class="hero-japanese">
                ひらがな
            </div>

            <div class="hero-subtitle">
                Hiragana • Gojūon
            </div>

        </div>
        """
    )

    st.caption(
        "▶ Play = pronunciation • ✍ Stroke = handwriting practice"
    )

    render_kana_chart(
        HIRAGANA_ROWS,
        "hiragana",
    )


def render_katakana_page() -> None:
    """Render Katakana study page."""

    render_html(
        """
        <div class="hero">

            <div class="hero-japanese">
                カタカナ
            </div>

            <div class="hero-subtitle">
                Katakana • Gojūon
            </div>

        </div>
        """
    )

    st.caption(
        "▶ Play = pronunciation • ✍ Stroke = handwriting practice"
    )

    render_kana_chart(
        KATAKANA_ROWS,
        "katakana",
    )


def render_expressions_page() -> None:
    """Render expressions and phrases."""

    render_html(
        """
        <div class="hero">

            <div class="hero-japanese">
                日本語フレーズ
            </div>

            <div class="hero-subtitle">
                Essential Japanese Expressions
            </div>

        </div>
        """
    )

    for index, (
        japanese,
        english,
    ) in enumerate(PHRASES):

        render_html(
            f"""
            <div class="kana-card"
                 style="
                    margin-bottom:.45rem;
                    min-height:105px;
                 ">

                <div class="kana-character"
                     style="font-size:2rem;">
                    {japanese}
                </div>

                <div class="kana-romaji">
                    {english}
                </div>

            </div>
            """
        )

        render_play_button(
            japanese,
            f"expression_{index}",
        )


def render_grammar_page() -> None:
    """Render grammar and counter reference."""

    render_html(
        """
        <div class="hero">

            <div class="hero-japanese">
                文法
            </div>

            <div class="hero-subtitle">
                Grammar, particles and counters
            </div>

        </div>
        """
    )

    st.subheader(
        "🧠 Essential Particles"
    )

    st.markdown(
        """
        | Particle | Common function | Example |
        |---|---|---|
        | **は** | Topic | わたし**は**学生です。 |
        | **の** | Possession / connection | わたし**の**本 |
        | **を** | Direct object | 水**を**飲みます。 |
        | **に** | Destination / time | 学校**に**行きます。 |
        | **で** | Place of action | 学校**で**勉強します。 |
        | **が** | Subject / new information | 猫**が**います。 |
        """
    )

    st.divider()

    st.subheader(
        "🔢 Counters & Quantifiers"
    )

    st.markdown(
        """
        | Counter | Used for | Example |
        |---|---|---|
        | **人（にん）** | People | 三人 |
        | **本（ほん）** | Long objects | 三本 |
        | **枚（まい）** | Flat objects | 三枚 |
        | **つ** | General items | 三つ |
        | **冊（さつ）** | Books / volumes | 三冊 |
        | **台（だい）** | Vehicles / machines | 三台 |
        """
    )


# =============================================================================
# STUDY ROUTER
# =============================================================================

def render_study_section() -> None:
    """Render the study subsection selected in the sidebar."""

    section = (
        st.session_state.study_section
    )

    if section == "Hiragana":

        render_hiragana_page()

    elif section == "Katakana":

        render_katakana_page()

    elif section == "Expressions":

        render_expressions_page()

    elif section == "Grammar":

        render_grammar_page()

    else:

        st.session_state.study_section = (
            "Hiragana"
        )

        render_hiragana_page()


# =============================================================================
# QUIZ PAGE
# =============================================================================

def render_quiz_landing() -> None:
    """Render quiz landing page."""

    render_html(
        """
        <div class="hero">

            <div class="hero-japanese">
                クイズ
            </div>

            <div class="hero-subtitle">
                Test your Japanese knowledge
            </div>

        </div>
        """
    )

    st.markdown(
        """
        Choose your categories and question count from
        **⚙ Quiz Settings** in the sidebar.

        Your wrong answers are automatically collected so you
        can practice them again afterward.
        """
    )

    st.divider()

    col1, col2, col3 = (
        st.columns(3)
    )

    with col1:

        st.metric(
            "Round Lengths",
            "10 / 25 / 50",
        )

    with col2:

        st.metric(
            "Categories",
            "6",
        )

    with col3:

        st.metric(
            "Rating",
            "0–3 ⭐",
        )

    if st.session_state.missed_questions:

        st.divider()

        st.warning(
            f"You have "
            f"{len(st.session_state.missed_questions)} "
            f"missed question(s) ready for practice."
        )

        if st.button(
            "🎯 Practice Missed Questions",
            type="primary",
        ):

            if start_missed_quiz():

                st.rerun()


def render_quiz_active() -> None:
    """Render the current quiz question."""

    questions = (
        st.session_state.quiz_questions
    )

    if not questions:

        render_quiz_landing()

        return

    if (
        st.session_state.quiz_index
        >= len(questions)
    ):

        render_quiz_results()

        return

    index = (
        st.session_state.quiz_index
    )

    total = len(
        questions
    )

    question = questions[
        index
    ]

    # -------------------------------------------------------------------------
    # Header
    # -------------------------------------------------------------------------

    mode_text = (
        "🎯 Targeted Review"
        if st.session_state.quiz_mode == "missed"
        else "📝 Quiz"
    )

    st.subheader(
        mode_text
    )

    st.progress(
        index / total,
        text=(
            f"Question {index + 1} of {total}"
            f" • Score {st.session_state.quiz_score}"
        ),
    )

    score_col, category_col = (
        st.columns(2)
    )

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

    # -------------------------------------------------------------------------
    # Prompt
    # -------------------------------------------------------------------------

    render_html(
        f"""
        <div style="
            text-align:center;
            font-size:1.08rem;
            font-weight:800;
            color:var(--muted);
        ">
            {question.prompt}
        </div>
        """
    )

    if question.japanese:

        render_html(
            f"""
            <div class="japanese-prompt">
                {question.japanese}
            </div>
            """
        )

        render_play_button(
            question.japanese,
            f"quiz_prompt_{question.question_id}",
            large=True,
        )

    options = get_stable_options(
        question
    )

    # -------------------------------------------------------------------------
    # Answer
    # -------------------------------------------------------------------------

    if not st.session_state.quiz_answered:

        with st.form(
            key=f"quiz_{question.question_id}"
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
                    "Please choose an answer first."
                )

                st.stop()

            st.session_state.quiz_selected_answer = (
                selected
            )

            st.session_state.quiz_answered = (
                True
            )

            if selected == question.answer:

                st.session_state.quiz_score += 1

            else:

                st.session_state.missed_questions.append(
                    question
                )

            st.rerun()

    # -------------------------------------------------------------------------
    # Feedback
    # -------------------------------------------------------------------------

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
                large=True,
            )

        st.divider()

        is_last = (
            index + 1 >= total
        )

        next_label = (
            "🏁 Finish Round"
            if is_last
            else "➡️ Next Question"
        )

        if st.button(
            next_label,
            use_container_width=True,
            type="primary",
        ):

            st.session_state.quiz_index += 1

            st.session_state.quiz_answered = (
                False
            )

            st.session_state.quiz_selected_answer = (
                None
            )

            st.rerun()


def render_quiz_results() -> None:
    """Render the final quiz results."""

    questions = (
        st.session_state.quiz_questions
    )

    total = len(
        questions
    )

    score = (
        st.session_state.quiz_score
    )

    percentage = (
        score / total * 100
        if total
        else 0
    )

    if percentage >= 100:

        stars = 3

    elif percentage >= 70:

        stars = 2

    elif percentage >= 30:

        stars = 1

    else:

        stars = 0

    star_display = (
        "🌟" * stars
        if stars
        else "☆☆☆"
    )

    render_html(
        f"""
        <div class="score-card">

            <div class="score-stars">
                {star_display}
            </div>

            <div class="score-percent">
                {percentage:.0f}%
            </div>

            <div>
                {score} correct out of {total}
            </div>

        </div>
        """
    )

    st.divider()

    if stars == 3:

        st.success(
            "Perfect score! 日本語が上手ですね！ 🔥"
        )

    elif stars == 2:

        st.success(
            "Great work! You're very close to perfect."
        )

    elif stars == 1:

        st.warning(
            "Good start. Review your mistakes and try again."
        )

    else:

        st.error(
            "Let's turn your mistakes into your study list."
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

                    render_html(
                        f"""
                        <div class="japanese-prompt"
                             style="font-size:2.4rem;">
                            {question.japanese}
                        </div>
                        """
                    )

                    render_play_button(
                        question.japanese,
                        f"review_{question.question_id}",
                        large=True,
                    )

                st.markdown(
                    f"**Correct answer:** "
                    f"`{question.answer}`"
                )

                st.caption(
                    question.explanation
                )

                st.divider()


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> None:
    """Render the application sidebar."""

    with st.sidebar:

        render_html(
            """
            <div class="sidebar-title">
                🇯🇵 Japanese Lab
            </div>
            """
        )

        st.caption(
            "Study. Listen. Practice."
        )

        st.divider()

        # ---------------------------------------------------------------------
        # STUDY NAVIGATION
        # ---------------------------------------------------------------------

        st.markdown(
            '<div class="sidebar-section">📚 Study</div>',
            unsafe_allow_html=True,
        )

        study_choice = st.radio(
            "Study",
            [
                "あ Hiragana",
                "カ Katakana",
                "💬 Expressions",
                "🧠 Grammar",
            ],
            index=[
                "Hiragana",
                "Katakana",
                "Expressions",
                "Grammar",
            ].index(
                st.session_state.study_section
            ),
            label_visibility="collapsed",
        )

        study_mapping = {
            "あ Hiragana": "Hiragana",
            "カ Katakana": "Katakana",
            "💬 Expressions": "Expressions",
            "🧠 Grammar": "Grammar",
        }

        selected_study_section = (
            study_mapping[study_choice]
        )

        if (
            selected_study_section
            != st.session_state.study_section
        ):

            st.session_state.study_section = (
                selected_study_section
            )

            st.session_state.page = "Study"

            st.rerun()

        # ---------------------------------------------------------------------
        # QUIZ NAVIGATION
        # ---------------------------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="sidebar-section">📝 Quiz</div>',
            unsafe_allow_html=True,
        )

        if st.button(
            "📝 Start Quiz",
            use_container_width=True,
        ):

            st.session_state.page = "Quiz"

            st.rerun()

        if st.button(
            "🎯 Review Missed",
            use_container_width=True,
            disabled=not bool(
                st.session_state.missed_questions
            ),
        ):

            if start_missed_quiz():

                st.session_state.page = (
                    "Quiz"
                )

                st.rerun()

        # ---------------------------------------------------------------------
        # HIDDEN QUIZ SETTINGS
        # ---------------------------------------------------------------------

        with st.expander(
            "⚙ Quiz Settings",
            expanded=False,
        ):

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

            st.session_state.quiz_categories = (
                categories
            )

            length = st.selectbox(
                "Round length",
                [10, 25, 50],
                index=[
                    10,
                    25,
                    50,
                ].index(
                    st.session_state.quiz_length
                ),
            )

            st.session_state.quiz_length = (
                length
            )

            if st.button(
                "🚀 Start Configured Quiz",
                use_container_width=True,
                type="primary",
            ):

                if not categories:

                    st.warning(
                        "Select at least one category."
                    )

                elif start_new_quiz(
                    categories,
                    length,
                ):

                    st.session_state.page = (
                        "Quiz"
                    )

                    st.rerun()

        # ---------------------------------------------------------------------
        # MISSED QUESTION INDICATOR
        # ---------------------------------------------------------------------

        if st.session_state.missed_questions:

            st.divider()

            render_html(
                f"""
                <div style="
                    padding:.65rem;
                    border-radius:10px;
                    background:var(--code-bg);
                    font-size:.84rem;
                ">
                    🎯
                    <strong>
                    {len(st.session_state.missed_questions)}
                    </strong>
                    missed question(s)
                </div>
                """
            )

        # ---------------------------------------------------------------------
        # APPEARANCE
        # ---------------------------------------------------------------------

        st.divider()

        st.markdown(
            '<div class="sidebar-section">🎨 Appearance</div>',
            unsafe_allow_html=True,
        )

        selected_theme = st.selectbox(
            "Theme",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(
                st.session_state.theme
            ),
            label_visibility="collapsed",
        )

        if (
            selected_theme
            != st.session_state.theme
        ):

            st.session_state.theme = (
                selected_theme
            )

            st.rerun()


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:
    """Application entry point."""

    render_sidebar()

    if st.session_state.page == "Study":

        render_study_section()

    elif st.session_state.page == "Quiz":

        if st.session_state.quiz_questions:

            render_quiz_active()

        else:

            render_quiz_landing()


if __name__ == "__main__":
    main()
