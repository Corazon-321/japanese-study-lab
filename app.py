"""
Japanese Study Lab
==================

A feature-rich Japanese learning application built with:

    - Streamlit
    - gTTS
    - KanjiVG SVG stroke-order references
    - Python standard library

Main features
--------------
1. Study tab
   - Hiragana Gojūon chart
   - Katakana Gojūon chart
   - Japanese pronunciation audio
   - Stroke-order SVG viewer
   - Stroke count / handwriting notes
   - Phrase and grammar references

2. Quiz tab
   - Hiragana
   - Katakana
   - Both Kana
   - Phrases & Sentences
   - Grammar & Particles
   - Counters & Quantifiers

3. Quiz engine
   - 10 / 25 / 50 questions
   - Randomized questions
   - Randomized distractors
   - Live score
   - Progress bar
   - 0-3 star rating

4. Mistake review
   - Missed-question tracker
   - Expandable review drawer
   - Japanese audio
   - Targeted re-quiz

5. Themes
   - Sakura
   - Midnight Cyber-Tokyo

Run locally
-----------
pip install -r requirements.txt
streamlit run app.py

Deployment
----------
Works with Streamlit Community Cloud and other Streamlit-compatible
deployments.

Notes
-----
gTTS requires internet access because speech generation is performed
through Google's Text-to-Speech service.

KanjiVG stroke-order SVGs are referenced remotely from the official
KanjiVG GitHub repository. KanjiVG is licensed CC BY-SA 3.0.
"""

from __future__ import annotations

import io
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import streamlit as st
from gtts import gTTS


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="Japanese Study Lab",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =============================================================================
# THEME DEFINITIONS
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
        "tab_active": "#D81B60",
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
        "tab_active": "#FF79C6",
        "code_bg": "#181825",
    },
}


# =============================================================================
# GOJŪON DATA
# =============================================================================

# 46 modern basic kana.
#
# The traditional "Gojūon" chart is usually represented by this standard
# layout, even though the modern language does not use all 50 historical cells.

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
# KANA STROKE INFORMATION
# =============================================================================

# Basic stroke counts for the modern gojūon characters.
#
# These are intended as beginner handwriting guidance rather than a
# substitute for a formal Japanese handwriting reference.

STROKE_INFO: Dict[str, Tuple[int, str]] = {
    # Hiragana
    "あ": (3, "Start with the short horizontal stroke, then the curved middle, then the final sweeping stroke."),
    "い": (2, "Write the left stroke first, then the right stroke."),
    "う": (2, "Short mark first, followed by the larger curved stroke."),
    "え": (2, "Short top stroke, then the longer lower stroke."),
    "お": (3, "Write the left component first, then the upper crossing stroke, then the final curve."),
    "か": (3, "Left vertical component, upper diagonal, then the final curved stroke."),
    "き": (4, "Two horizontal strokes first, then the crossing vertical/diagonal, then the lower curve."),
    "く": (1, "Single curved stroke from upper-left toward lower-right."),
    "け": (3, "Left component first, then the central vertical, then the right crossing stroke."),
    "こ": (2, "Upper horizontal first, then lower horizontal."),
    "さ": (3, "Upper mark, central horizontal/vertical component, then final curved stroke."),
    "し": (1, "One long curved stroke."),
    "す": (2, "Short top stroke, then the long descending curve."),
    "せ": (3, "Vertical component, upper horizontal, then final curved stroke."),
    "そ": (1, "Single flowing stroke."),
    "た": (4, "Top-left component first, then horizontal/diagonal elements, finishing with the lower curve."),
    "ち": (2, "Short top stroke followed by the larger curved stroke."),
    "つ": (1, "One curved stroke."),
    "て": (1, "Single stroke, beginning at the upper left."),
    "と": (2, "Short diagonal stroke, then long curved stroke."),
    "な": (4, "Left component first, then crossing structure and lower curve."),
    "に": (3, "Two short horizontals followed by a vertical/curved ending."),
    "ぬ": (2, "Long flowing loop with a final crossing tail."),
    "ね": (4, "Left component first, then upper/right structure, finishing with the loop."),
    "の": (1, "One continuous rounded stroke."),
    "は": (3, "Left vertical, central structure, then right curved stroke."),
    "ひ": (1, "One flowing stroke with a loop-like finish."),
    "ふ": (4, "Short upper marks, then the central flowing stroke."),
    "へ": (1, "One angular descending stroke."),
    "ほ": (4, "Vertical/horizontal structure first, then right-side stroke and final vertical."),
    "ま": (3, "Upper component first, then lower horizontal, then looped stroke."),
    "み": (2, "Two connected flowing strokes."),
    "む": (3, "Upper strokes first, then large looping finish."),
    "め": (2, "First curved stroke, then crossing loop."),
    "も": (3, "Two horizontals followed by the final descending curve."),
    "や": (3, "Two upper strokes followed by the large lower curve."),
    "ゆ": (2, "Vertical/curved left stroke followed by the enclosing loop."),
    "よ": (2, "Upper horizontal then the lower vertical/curve."),
    "ら": (2, "Short upper stroke followed by lower curve."),
    "り": (2, "Two separate flowing strokes."),
    "る": (1, "One looping stroke."),
    "れ": (2, "Left vertical/curve followed by the larger right loop."),
    "ろ": (1, "One looping stroke."),
    "わ": (2, "Vertical/curved stroke followed by the looped ending."),
    "を": (3, "Top component followed by the main crossing and sweeping stroke."),
    "ん": (1, "One continuous curved stroke."),

    # Katakana
    "ア": (2, "Horizontal stroke first, then the descending diagonal stroke."),
    "イ": (2, "Left diagonal stroke first, then right diagonal."),
    "ウ": (3, "Top mark, then upper horizontal/curve, then descending stroke."),
    "エ": (3, "Top horizontal, center vertical, bottom horizontal."),
    "オ": (3, "Horizontal stroke, vertical/diagonal crossing, then right diagonal."),
    "カ": (2, "Left descending stroke first, then right angled stroke."),
    "キ": (3, "Two horizontals followed by the central diagonal."),
    "ク": (2, "Top angled stroke, then larger descending stroke."),
    "ケ": (3, "Left diagonal, upper horizontal, then long right descending stroke."),
    "コ": (2, "Top horizontal followed by descending and lower horizontal."),
    "サ": (3, "Upper strokes, followed by long diagonal."),
    "シ": (3, "Three short strokes, written from upper to lower."),
    "ス": (2, "Short upper stroke followed by long curved stroke."),
    "セ": (2, "Horizontal stroke then vertical/diagonal stroke."),
    "ソ": (2, "Two flowing diagonal strokes."),
    "タ": (3, "Short upper stroke, angled middle stroke, then long lower diagonal."),
    "チ": (3, "Top horizontal, central diagonal, then lower horizontal."),
    "ツ": (3, "Three short strokes, descending from upper to lower."),
    "テ": (3, "Two horizontals followed by descending stroke."),
    "ト": (2, "Vertical stroke followed by short diagonal."),
    "ナ": (2, "Horizontal first, then large descending diagonal."),
    "ニ": (2, "Two horizontal strokes."),
    "ヌ": (2, "Diagonal stroke then crossing curved stroke."),
    "ネ": (4, "Top strokes first, then lower cross and final diagonal."),
    "ノ": (1, "Single diagonal stroke."),
    "ハ": (2, "Two diagonal strokes."),
    "ヒ": (2, "Horizontal stroke followed by vertical/curve."),
    "フ": (1, "One descending curved stroke."),
    "ヘ": (1, "One angular stroke."),
    "ホ": (4, "Horizontal and vertical structure, then side diagonals."),
    "マ": (2, "Upper horizontal, then descending diagonal."),
    "ミ": (3, "Three horizontal strokes."),
    "ム": (2, "Descending stroke followed by the angled base."),
    "メ": (2, "Two crossing diagonal strokes."),
    "モ": (3, "Two horizontals and a descending stroke."),
    "ヤ": (2, "Short left diagonal followed by larger right structure."),
    "ユ": (2, "Vertical curve followed by lower horizontal."),
    "ヨ": (3, "Three horizontal/vertical segments."),
    "ラ": (2, "Top horizontal followed by curved lower stroke."),
    "リ": (2, "Two descending strokes."),
    "ル": (2, "Left vertical followed by right curved stroke."),
    "レ": (1, "One long angled stroke."),
    "ロ": (3, "Top, side, and bottom strokes form the box."),
    "ワ": (2, "Top/left component followed by right descending stroke."),
    "ヲ": (3, "Top horizontal, middle structure, then descending curve."),
    "ン": (2, "Two short diagonal strokes."),
}


# =============================================================================
# PHRASES
# =============================================================================

PHRASES: List[Tuple[str, str]] = [
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

SENTENCES: List[Tuple[str, str]] = [
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
        "explanation": "は marks the topic of a sentence. It is pronounced 'wa' when used as a particle.",
    },
    {
        "prompt": "Which particle expresses possession or connection?",
        "japanese": "わたし ___ 本",
        "answer": "の",
        "choices": ["の", "を", "で", "が"],
        "explanation": "の links nouns and often expresses possession or relationship.",
    },
    {
        "prompt": "Which particle marks the direct object?",
        "japanese": "水 ___ 飲みます。",
        "answer": "を",
        "choices": ["を", "は", "に", "で"],
        "explanation": "を marks the direct object of the verb.",
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
        "explanation": "で marks the location where an action happens.",
    },
    {
        "prompt": "Which particle commonly marks the grammatical subject?",
        "japanese": "猫 ___ います。",
        "answer": "が",
        "choices": ["が", "を", "で", "の"],
        "explanation": "が often marks the grammatical subject, especially with existence and new information.",
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
        "explanation": "本 is used for long cylindrical objects such as pens, bottles and umbrellas.",
    },
    {
        "prompt": "Which counter is commonly used for flat objects?",
        "japanese": "紙を四 ___ ください。",
        "answer": "枚（まい）",
        "choices": ["枚（まい）", "本（ほん）", "人（にん）", "冊（さつ）"],
        "explanation": "枚 is used for flat, thin objects such as paper and shirts.",
    },
    {
        "prompt": "Which general counter is used for many ordinary items?",
        "japanese": "りんごを三 ___ ください。",
        "answer": "つ",
        "choices": ["つ", "台（だい）", "冊（さつ）", "人（にん）"],
        "explanation": "つ is a general counter used for many objects.",
    },
    {
        "prompt": "Which counter is used for books and volumes?",
        "japanese": "本を五 ___ 読みました。",
        "answer": "冊（さつ）",
        "choices": ["冊（さつ）", "本（ほん）", "枚（まい）", "台（だい）"],
        "explanation": "冊 is used for bound books and volumes.",
    },
    {
        "prompt": "Which counter is used for vehicles and many machines?",
        "japanese": "車が二 ___ あります。",
        "answer": "台（だい）",
        "choices": ["台（だい）", "冊（さつ）", "枚（まい）", "本（ほん）"],
        "explanation": "台 is commonly used for vehicles, machines and many electronic devices.",
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
# QUESTION BANK BUILDERS
# =============================================================================

def make_kana_questions(
    rows: Sequence[Tuple[str, Sequence[Tuple[str, str]]]],
    category: str,
    prefix: str,
) -> List[Question]:
    """Generate both reading-direction variants for kana."""

    items: List[Tuple[str, str]] = []

    for _, row_items in rows:
        for kana, romaji in row_items:
            if kana:
                items.append((kana, romaji))

    questions: List[Question] = []

    symbols = [kana for kana, _ in items]
    readings = [romaji for _, romaji in items]

    for index, (kana, romaji) in enumerate(items):

        # Kana -> Romaji
        distractors = random.sample(
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
                choices=[romaji, *distractors],
                explanation=f"{kana} is read as '{romaji}'.",
            )
        )

        # Romaji -> Kana
        distractors = random.sample(
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
                choices=[kana, *distractors],
                explanation=f"'{romaji}' is written as {kana}.",
            )
        )

    return questions


def make_phrase_questions() -> List[Question]:
    """Create vocabulary questions."""

    questions: List[Question] = []

    english = [x[1] for x in PHRASES]
    japanese = [x[0] for x in PHRASES]

    for i, (jp, en) in enumerate(PHRASES):

        wrong_answers = random.sample(
            [x for x in english if x != en],
            3,
        )

        questions.append(
            Question(
                question_id=f"phrase_meaning_{i}",
                category="Phrases & Sentences",
                prompt="What does this expression mean?",
                japanese=jp,
                answer=en,
                choices=[en, *wrong_answers],
                explanation=f"{jp} means '{en}'.",
            )
        )

        wrong_answers_jp = random.sample(
            [x for x in japanese if x != jp],
            3,
        )

        questions.append(
            Question(
                question_id=f"phrase_reverse_{i}",
                category="Phrases & Sentences",
                prompt=f"Which Japanese expression means '{en}'?",
                japanese="",
                answer=jp,
                choices=[jp, *wrong_answers_jp],
                explanation=f"{jp} means '{en}'.",
            )
        )

    return questions


def make_sentence_questions() -> List[Question]:
    """Create simple sentence comprehension questions."""

    questions: List[Question] = []

    translations = [x[1] for x in SENTENCES]

    for i, (jp, en) in enumerate(SENTENCES):

        wrong_answers = random.sample(
            [x for x in translations if x != en],
            3,
        )

        questions.append(
            Question(
                question_id=f"sentence_{i}",
                category="Phrases & Sentences",
                prompt="What does this sentence mean?",
                japanese=jp,
                answer=en,
                choices=[en, *wrong_answers],
                explanation=en,
            )
        )

    return questions


def make_particle_questions() -> List[Question]:
    """Convert particle dictionaries to Question objects."""

    result: List[Question] = []

    for i, item in enumerate(PARTICLE_QUESTIONS):
        choices = item["choices"].copy()
        random.shuffle(choices)

        result.append(
            Question(
                question_id=f"particle_{i}",
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
    """Convert counter dictionaries to Question objects."""

    result: List[Question] = []

    for i, item in enumerate(COUNTER_QUESTIONS):
        choices = item["choices"].copy()
        random.shuffle(choices)

        result.append(
            Question(
                question_id=f"counter_{i}",
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
    """Build the complete quiz database."""

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
    """Create state only once."""

    if "theme" not in st.session_state:
        st.session_state.theme = "🌸 Sakura"

    if "question_bank" not in st.session_state:
        st.session_state.question_bank = build_question_bank()

    if "quiz_questions" not in st.session_state:
        st.session_state.quiz_questions = []

    if "quiz_index" not in st.session_state:
        st.session_state.quiz_index = 0

    if "quiz_score" not in st.session_state:
        st.session_state.quiz_score = 0

    if "quiz_answered" not in st.session_state:
        st.session_state.quiz_answered = False

    if "quiz_selected_answer" not in st.session_state:
        st.session_state.quiz_selected_answer = None

    if "quiz_options" not in st.session_state:
        st.session_state.quiz_options = {}

    if "missed_questions" not in st.session_state:
        st.session_state.missed_questions = []

    if "quiz_mode" not in st.session_state:
        st.session_state.quiz_mode = "normal"

    if "quiz_length" not in st.session_state:
        st.session_state.quiz_length = 10

    if "quiz_categories" not in st.session_state:
        st.session_state.quiz_categories = [
            "Hiragana",
            "Katakana",
            "Both Kana",
            "Phrases & Sentences",
            "Grammar & Particles",
            "Counters & Quantifiers",
        ]

    if "page" not in st.session_state:
        st.session_state.page = "Study"


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
    Generate Japanese gTTS audio entirely in memory.

    No temporary mp3 is written to disk.
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


def audio_player(
    japanese: str,
    key_suffix: str,
    label: str = "🔊",
) -> None:
    """
    Show an audio generation control.

    The user explicitly triggers generation, preventing the Study tab
    from making dozens of network requests on initial page load.
    """

    button_key = f"audio_button_{key_suffix}"

    if st.button(
        label,
        key=button_key,
        help="Generate Japanese pronunciation",
    ):
        st.session_state[f"show_audio_{key_suffix}"] = True

    if st.session_state.get(
        f"show_audio_{key_suffix}",
        False,
    ):
        try:
            audio = generate_audio(japanese)

            st.audio(
                audio,
                format="audio/mp3",
            )

        except Exception:
            st.warning(
                "Unable to generate audio. "
                "Please check your internet connection."
            )


# =============================================================================
# KANJIVG STROKE VIEW
# =============================================================================

def kanjivg_url(character: str) -> str:
    """
    Return the KanjiVG raw SVG URL for a character.

    KanjiVG filenames use padded lowercase hexadecimal Unicode values.
    """

    codepoint = ord(character)

    return (
        "https://raw.githubusercontent.com/"
        "KanjiVG/kanjivg/master/kanji/"
        f"{codepoint:05x}.svg"
    )


def stroke_view(character: str) -> None:
    """
    Show stroke-order SVG plus beginner-oriented stroke information.

    The SVG itself is hosted remotely by the KanjiVG project.
    """

    if not character:
        return

    info = STROKE_INFO.get(
        character,
        (0, "Stroke guidance unavailable."),
    )

    stroke_count, note = info

    st.markdown(
        f"""
        <div class="stroke-panel">
            <div class="stroke-title">✍ Stroke Order</div>
            <div class="stroke-count">{stroke_count} strokes</div>
            <div class="stroke-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.image(
        kanjivg_url(character),
        width=180,
    )

    st.caption(
        "Stroke diagram: KanjiVG • CC BY-SA 3.0"
    )


# =============================================================================
# CUSTOM CSS
# =============================================================================

def inject_theme_css(theme_name: str) -> None:
    """Inject the complete visual theme."""

    theme = THEMES[theme_name]

    css = f"""
    <style>

    /* ============================================================
       GLOBAL
       ============================================================ */

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

    .stApp {{
        background:
            radial-gradient(
                circle at top right,
                rgba(255,183,197,0.10),
                transparent 30%
            ),
            var(--page-bg);
        color: var(--text);
    }}

    .main .block-container {{
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 4rem;
    }}

    /* ============================================================
       HEADINGS
       ============================================================ */

    h1, h2, h3, h4 {{
        color: var(--text) !important;
    }}

    h1 {{
        font-weight: 800 !important;
        letter-spacing: -0.03em;
    }}

    /* ============================================================
       STREAMLIT TEXT
       ============================================================ */

    p, label, .stMarkdown {{
        color: var(--text);
    }}

    [data-testid="stCaptionContainer"] {{
        color: var(--muted) !important;
    }}

    /* ============================================================
       BUTTONS
       ============================================================ */

    .stButton > button {{
        border: 1px solid var(--border);
        border-radius: 12px;
        background: var(--card-bg);
        color: var(--text);
        font-weight: 700;
        min-height: 42px;
        transition: all 0.18s ease;
    }}

    .stButton > button:hover {{
        border-color: var(--primary);
        color: var(--primary);
        transform: translateY(-1px);
    }}

    /* ============================================================
       TABS
       ============================================================ */

    button[data-baseweb="tab"] {{
        font-size: 1.08rem;
        font-weight: 800;
        color: var(--muted);
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: var(--primary) !important;
    }}

    /* ============================================================
       CARDS
       ============================================================ */

    .study-card {{
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 8px 25px rgba(0,0,0,0.05);
        text-align: center;
    }}

    .kana-character {{
        font-family:
            "Noto Sans JP",
            "Yu Gothic",
            "Hiragino Kaku Gothic ProN",
            sans-serif;

        font-size: 3.3rem;
        line-height: 1;
        font-weight: 900;
        color: var(--text);
        margin: 0.6rem 0;
    }}

    .kana-romaji {{
        font-size: 1rem;
        font-weight: 700;
        color: var(--muted);
        margin-bottom: 0.5rem;
    }}

    .kana-row-label {{
        font-size: 1.05rem;
        font-weight: 900;
        color: var(--primary);
        padding-top: 1.5rem;
    }}

    /* ============================================================
       LARGE JAPANESE QUIZ PROMPT
       ============================================================ */

    .japanese-prompt {{
        font-family:
            "Noto Sans JP",
            "Yu Gothic",
            "Hiragino Kaku Gothic ProN",
            sans-serif;

        font-size: clamp(2.4rem, 5vw, 4.6rem);
        line-height: 1.25;
        font-weight: 900;
        text-align: center;

        background: var(--card-bg);
        border: 2px solid var(--border);
        border-radius: 20px;

        padding: 1.8rem 1rem;
        margin: 1rem 0 1.5rem;

        color: var(--text);

        box-shadow:
            0 10px 35px rgba(0,0,0,0.06);
    }}

    /* ============================================================
       STROKE PANEL
       ============================================================ */

    .stroke-panel {{
        background: var(--code-bg);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 0.9rem;
        margin-top: 0.6rem;
        margin-bottom: 0.8rem;
    }}

    .stroke-title {{
        font-size: 1rem;
        font-weight: 900;
        color: var(--primary);
    }}

    .stroke-count {{
        font-size: 1.3rem;
        font-weight: 900;
        color: var(--text);
        margin-top: 0.2rem;
    }}

    .stroke-note {{
        font-size: 0.86rem;
        line-height: 1.5;
        color: var(--muted);
        margin-top: 0.35rem;
    }}

    /* ============================================================
       HERO
       ============================================================ */

    .hero {{
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 2rem;
        background:
            linear-gradient(
                135deg,
                rgba(255,183,197,0.16),
                rgba(139,233,253,0.08)
            ),
            var(--card-bg);

        box-shadow:
            0 15px 50px rgba(0,0,0,0.07);
        margin-bottom: 1.5rem;
    }}

    .hero-japanese {{
        font-size: clamp(2.5rem, 6vw, 5rem);
        font-weight: 900;
        text-align: center;
        margin-bottom: 0.5rem;
    }}

    .hero-subtitle {{
        text-align: center;
        font-size: 1.05rem;
        color: var(--muted);
    }}

    /* ============================================================
       SCORE
       ============================================================ */

    .score-card {{
        text-align: center;
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 1.5rem;
    }}

    .score-number {{
        font-size: 3rem;
        font-weight: 900;
        color: var(--primary);
    }}

    .stars {{
        font-size: 2.8rem;
        letter-spacing: 0.08em;
        margin-top: 0.3rem;
    }}

    /* ============================================================
       SIDEBAR
       ============================================================ */

    section[data-testid="stSidebar"] {{
        background: var(--card-bg);
        border-right: 1px solid var(--border);
    }}

    /* ============================================================
       MOBILE
       ============================================================ */

    @media (max-width: 700px) {{
        .kana-character {{
            font-size: 2.4rem;
        }}

        .study-card {{
            padding: 0.75rem;
        }}

        .japanese-prompt {{
            font-size: 2.2rem;
            padding: 1.3rem 0.8rem;
        }}
    }}

    </style>
    """

    st.markdown(
        css,
        unsafe_allow_html=True,
    )


inject_theme_css(st.session_state.theme)


# =============================================================================
# SIDEBAR
# =============================================================================

def render_sidebar() -> None:
    """Render global application controls."""

    with st.sidebar:

        st.markdown(
            """
            <div style="
                font-size: 1.8rem;
                font-weight: 900;
                margin-bottom: .5rem;
            ">
                🇯🇵 Japanese Lab
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Study kana. Listen. Practice. Repeat."
        )

        st.divider()

        # ---------------------------------------------------------------------
        # Theme
        # ---------------------------------------------------------------------

        selected_theme = st.selectbox(
            "🎨 Appearance",
            list(THEMES.keys()),
            index=list(THEMES.keys()).index(
                st.session_state.theme
            ),
        )

        if selected_theme != st.session_state.theme:
            st.session_state.theme = selected_theme
            st.rerun()

        st.divider()

        # ---------------------------------------------------------------------
        # Navigation
        # ---------------------------------------------------------------------

        page = st.radio(
            "Mode",
            ["Study", "Quiz"],
            index=0 if st.session_state.page == "Study" else 1,
        )

        if page != st.session_state.page:
            st.session_state.page = page
            st.rerun()

        st.divider()

        # ---------------------------------------------------------------------
        # Quiz settings
        # ---------------------------------------------------------------------

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

            if st.button(
                "🎯 Practice Missed Questions",
                use_container_width=True,
            ):
                start_missed_quiz()
                st.session_state.page = "Quiz"
                st.rerun()


# =============================================================================
# STUDY TAB HELPERS
# =============================================================================

def render_kana_cell(
    kana: str,
    romaji: str,
    cell_id: str,
) -> None:
    """Render one kana study card."""

    if not kana:
        st.markdown(
            """
            <div class="study-card" style="opacity: .25;">
                <div style="font-size:2rem;">・</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="study-card">
            <div class="kana-character">{kana}</div>
            <div class="kana-romaji">{romaji}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    audio_player(
        kana,
        f"{cell_id}_audio",
    )

    with st.expander(
        "✍ Stroke guide",
        expanded=False,
    ):
        stroke_view(kana)


def render_kana_chart(
    rows: Sequence[Tuple[str, Sequence[Tuple[str, str]]]],
    prefix: str,
) -> None:
    """Render a complete five-column gojūon chart."""

    for row_index, (row_label, row_items) in enumerate(rows):

        columns = st.columns(5)

        for index, column in enumerate(columns):

            kana, romaji = row_items[index]

            with column:

                st.markdown(
                    f"""
                    <div class="kana-row-label">
                        {row_label}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                render_kana_cell(
                    kana,
                    romaji,
                    f"{prefix}_{row_index}_{index}",
                )


def render_phrase_reference() -> None:
    """Render a useful beginner phrase reference."""

    st.subheader("💬 Essential Expressions")

    cols = st.columns(2)

    for index, (japanese, english) in enumerate(PHRASES):

        with cols[index % 2]:

            st.markdown(
                f"""
                <div class="study-card">
                    <div class="kana-character"
                         style="font-size:2.2rem;">
                        {japanese}
                    </div>
                    <div class="kana-romaji">
                        {english}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            audio_player(
                japanese,
                f"phrase_{index}",
            )


def render_grammar_reference() -> None:
    """Render particle and counter cheat sheets."""

    st.subheader("🧠 Grammar Reference")

    particle_col, counter_col = st.columns(2)

    with particle_col:

        st.markdown(
            """
            ### Particles

            | Particle | Function | Example |
            |---|---|---|
            | **は** | Topic | わたし**は**学生です。 |
            | **の** | Possession / connection | わたし**の**本 |
            | **を** | Direct object | 水**を**飲みます。 |
            | **に** | Destination / time | 学校**に**行きます。 |
            | **で** | Place of action | 学校**で**勉強します。 |
            | **が** | Subject / new info | 猫**が**います。 |
            """
        )

    with counter_col:

        st.markdown(
            """
            ### Counters

            | Counter | Common use | Example |
            |---|---|---|
            | **人（にん）** | People | 三人 |
            | **本（ほん）** | Long objects | 三本 |
            | **枚（まい）** | Flat objects | 三枚 |
            | **つ** | General items | 三つ |
            | **冊（さつ）** | Books | 三冊 |
            | **台（だい）** | Vehicles / machines | 三台 |
            """
        )


# =============================================================================
# STUDY PAGE
# =============================================================================

def render_study_page() -> None:
    """Render the Study tab."""

    st.markdown(
        """
        <div class="hero">
            <div class="hero-japanese">日本語を勉強しましょう！</div>
            <div class="hero-subtitle">
                Study the kana, hear native pronunciation,
                and practice proper stroke order.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    study_tabs = st.tabs(
        [
            "ひらがな Hiragana",
            "カタカナ Katakana",
            "💬 Expressions",
            "🧠 Grammar",
        ]
    )

    with study_tabs[0]:

        st.markdown(
            """
            ### Hiragana Gojūon

            Tap **🔊** to generate pronunciation.
            Open **✍ Stroke guide** to see the stroke-order reference.
            """
        )

        render_kana_chart(
            HIRAGANA_ROWS,
            "hiragana_chart",
        )

    with study_tabs[1]:

        st.markdown(
            """
            ### Katakana Gojūon

            Katakana is commonly used for loanwords,
            foreign names, emphasis and technical terms.
            """
        )

        render_kana_chart(
            KATAKANA_ROWS,
            "katakana_chart",
        )

    with study_tabs[2]:

        render_phrase_reference()

    with study_tabs[3]:

        render_grammar_reference()


# =============================================================================
# QUIZ ENGINE
# =============================================================================

def get_questions_for_categories(
    categories: Sequence[str],
) -> List[Question]:
    """Map special 'Both Kana' selection to both kana datasets."""

    effective_categories = set(categories)

    if "Both Kana" in effective_categories:
        effective_categories.update(
            {"Hiragana", "Katakana"}
        )

    return [
        question
        for question in st.session_state.question_bank
        if question.category in effective_categories
    ]


def start_new_quiz(
    categories: Sequence[str],
    length: int,
) -> None:
    """Start a regular quiz round."""

    available = get_questions_for_categories(
        categories
    )

    if not available:
        st.warning(
            "Please select at least one quiz topic."
        )
        return

    actual_length = min(
        length,
        len(available),
    )

    selected = random.sample(
        available,
        actual_length,
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
    """Start a targeted quiz containing only missed questions."""

    missed = st.session_state.missed_questions.copy()

    if not missed:
        return

    random.shuffle(missed)

    st.session_state.quiz_questions = missed
    st.session_state.quiz_index = 0
    st.session_state.quiz_score = 0
    st.session_state.quiz_answered = False
    st.session_state.quiz_selected_answer = None
    st.session_state.quiz_options = {}
    st.session_state.quiz_mode = "missed"

    # The missed list is replaced after this quiz starts.
    st.session_state.missed_questions = []


def current_question() -> Optional[Question]:
    """Return current question or None if quiz is complete."""

    questions = st.session_state.quiz_questions
    index = st.session_state.quiz_index

    if not questions:
        return None

    if index >= len(questions):
        return None

    return questions[index]


def get_stable_options(
    question: Question,
) -> List[str]:
    """
    Generate options only once per question.

    This is important for Streamlit because reruns can happen after
    widget interactions.
    """

    key = question.question_id

    if key not in st.session_state.quiz_options:

        choices = question.choices.copy()

        # Remove accidental duplicates.
        choices = list(dict.fromkeys(choices))

        random.shuffle(choices)

        st.session_state.quiz_options[key] = choices

    return st.session_state.quiz_options[key]


def calculate_score_percentage() -> float:
    """Return current final percentage."""

    questions = st.session_state.quiz_questions

    if not questions:
        return 0.0

    return (
        st.session_state.quiz_score
        / len(questions)
    ) * 100


def star_rating(percentage: float) -> int:
    """Return the requested 0-3 star rating."""

    if percentage >= 100:
        return 3

    if percentage >= 70:
        return 2

    if percentage >= 30:
        return 1

    return 0


def render_quiz_page() -> None:
    """Render the Quiz tab/page."""

    questions = st.session_state.quiz_questions

    if not questions:
        render_quiz_landing()
        return

    # Quiz complete
    if st.session_state.quiz_index >= len(questions):
        render_quiz_results()
        return

    question = current_question()

    if question is None:
        render_quiz_results()
        return

    total = len(questions)
    index = st.session_state.quiz_index

    # -------------------------------------------------------------------------
    # Quiz header
    # -------------------------------------------------------------------------

    mode_label = (
        "🎯 Targeted Missed-Question Review"
        if st.session_state.quiz_mode == "missed"
        else "📝 Quiz Round"
    )

    st.subheader(mode_label)

    progress = (
        index / total
        if total
        else 0
    )

    st.progress(
        progress,
        text=f"Question {index + 1} of {total}",
    )

    score_col, category_col = st.columns(2)

    with score_col:
        st.metric(
            "Current Score",
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

    st.markdown(
        f"""
        <div style="
            font-size: 1.2rem;
            font-weight: 800;
            color: var(--muted);
            text-align: center;
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

        # Japanese audio for the displayed prompt.
        audio_player(
            question.japanese,
            f"quiz_prompt_{question.question_id}",
        )

    # -------------------------------------------------------------------------
    # Answer form
    # -------------------------------------------------------------------------

    options = get_stable_options(
        question
    )

    if not st.session_state.quiz_answered:

        with st.form(
            key=f"quiz_form_{question.question_id}"
        ):

            selected = st.radio(
                "Select your answer:",
                options,
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

            st.session_state.quiz_selected_answer = selected
            st.session_state.quiz_answered = True

            if selected == question.answer:

                st.session_state.quiz_score += 1

            else:

                st.session_state.missed_questions.append(
                    question
                )

            st.rerun()

    # -------------------------------------------------------------------------
    # Feedback state
    # -------------------------------------------------------------------------

    else:

        selected = (
            st.session_state.quiz_selected_answer
        )

        if selected == question.answer:

            st.success(
                "🎉 Correct! Excellent."
            )

        else:

            st.error(
                f"❌ Incorrect. Correct answer: "
                f"**{question.answer}**"
            )

        st.info(
            f"💡 {question.explanation}"
        )

        # Repeat audio after answering.
        if question.japanese:
            audio_player(
                question.japanese,
                f"quiz_review_{question.question_id}",
                "🔊 Hear it again",
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
            st.session_state.quiz_answered = False
            st.session_state.quiz_selected_answer = None

            st.rerun()


# =============================================================================
# QUIZ LANDING
# =============================================================================

def render_quiz_landing() -> None:
    """Render quiz setup / empty state."""

    st.title("📝 Japanese Quiz")

    st.markdown(
        """
        Test your Japanese knowledge across kana, everyday expressions,
        grammar, particles and counters.

        Configure the round from the sidebar.
        """
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Question Sizes",
            "10 / 25 / 50",
        )

    with col2:
        st.metric(
            "Quiz Categories",
            "6",
        )

    with col3:
        st.metric(
            "Rating",
            "0–3 ⭐",
        )

    st.divider()

    st.info(
        "Choose your topics and question count in the sidebar, "
        "then press 'Start New Quiz'."
    )

    if st.session_state.missed_questions:

        st.warning(
            f"You have "
            f"{len(st.session_state.missed_questions)} "
            f"missed questions ready for targeted review."
        )

        if st.button(
            "🎯 Practice Missed Questions",
            type="primary",
        ):
            start_missed_quiz()
            st.rerun()


# =============================================================================
# RESULTS
# =============================================================================

def render_quiz_results() -> None:
    """Render final quiz results."""

    total = len(
        st.session_state.quiz_questions
    )

    score = st.session_state.quiz_score

    percentage = (
        score / total * 100
        if total
        else 0
    )

    stars = star_rating(
        percentage
    )

    star_display = (
        "🌟" * stars
        if stars > 0
        else "☆☆☆"
    )

    st.title("🏆 Round Complete")

    st.markdown(
        f"""
        <div class="score-card">

            <div class="stars">
                {star_display}
            </div>

            <div class="score-number">
                {percentage:.0f}%
            </div>

            <div style="
                font-size: 1.2rem;
                color: var(--muted);
            ">
                {score} correct out of {total}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    if stars == 3:
        st.success(
            "Perfect score. 日本語が上手ですね！ 🔥"
        )
    elif stars == 2:
        st.success(
            "Great work. You're getting really close to perfect."
        )
    elif stars == 1:
        st.warning(
            "Solid start. Review the mistakes and go again."
        )
    else:
        st.error(
            "Time for another round. The good news: "
            "the app already knows what to review."
        )

    # -------------------------------------------------------------------------
    # Missed question review
    # -------------------------------------------------------------------------

    missed = st.session_state.missed_questions

    with st.expander(
        f"📖 Review Missed Questions ({len(missed)})",
        expanded=bool(missed),
    ):

        if not missed:

            st.success(
                "🎉 No mistakes this round!"
            )

        else:

            for index, question in enumerate(
                missed,
                start=1,
            ):

                st.markdown(
                    f"### {index}. {question.prompt}"
                )

                if question.japanese:

                    st.markdown(
                        f"""
                        <div class="japanese-prompt"
                             style="font-size:2.5rem;">
                            {question.japanese}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    audio_player(
                        question.japanese,
                        f"missed_{question.question_id}",
                        "🔊 Pronunciation",
                    )

                st.markdown(
                    f"**Correct answer:** "
                    f"`{question.answer}`"
                )

                st.caption(
                    question.explanation
                )

                st.divider()

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        if missed:

            if st.button(
                "🎯 Practice Missed Questions",
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

            categories = (
                st.session_state.quiz_categories
            )

            start_new_quiz(
                categories,
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
# MAIN
# =============================================================================

def main() -> None:
    """Application entry point."""

    render_sidebar()

    if st.session_state.page == "Study":
        render_study_page()

    elif st.session_state.page == "Quiz":
        render_quiz_page()


if __name__ == "__main__":
    main()