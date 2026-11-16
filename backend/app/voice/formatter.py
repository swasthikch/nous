"""Speech Text Formatter and Conversational Pipeline for NOUS (Phase 5).

Transforms verbose LLM markdown and technical responses into natural,
concise spoken phrases suitable for Text-to-Speech (TTS) engines.
Supports English, Indian English, and Hindi.
"""

from __future__ import annotations

import re
from typing import Optional


class SpeechTextFormatter:
    """Sanitizes and condenses text for natural speech synthesis."""

    # Common currency symbols to spoken words
    CURRENCY_MAP = {
        "₹": "rupees",
        "$": "dollars",
        "€": "euros",
        "£": "pounds",
    }

    # Hindi / Hinglish greeting cues
    HINDI_PATTERNS = [
        r"[\u0900-\u097F]",  # Devanagari Unicode block
        r"\b(namaste|kaise|kya|shukriya|dhanyawad|aapka|samay|aaj)\b",  # Hinglish words
    ]

    @classmethod
    def detect_language(cls, text: str) -> str:
        """Detect whether text is English or Hindi/Hinglish."""
        if re.search(r"[\u0900-\u097F]", text):
            return "hi-IN"
        if re.search(r"\b(namaste|kaise ho|kya chal raha|dhanyawad|aaj ka)\b", text, re.IGNORECASE):
            return "hi-IN"
        return "en-US"

    @classmethod
    def clean_for_speech(cls, text: str, max_words: int = 55) -> str:
        """Convert markdown, tables, and code into concise, fluent spoken text."""
        if not text:
            return ""

        s = text.strip()

        # 1. Replace code blocks with natural audio placeholder
        s = re.sub(r"```[\w]*\n[\s\S]*?```", " I have displayed the code on your screen. ", s)
        s = re.sub(r"`[^`]+`", " ", s)  # Inline code snippets

        # 2. Strip Markdown tables (| col | col |)
        lines = []
        for line in s.splitlines():
            line_str = line.strip()
            if line_str.startswith("|") and line_str.endswith("|"):
                continue  # skip table rows
            if re.match(r"^[-|:\s]{3,}$", line_str):
                continue  # skip table divider
            lines.append(line)
        s = " ".join(lines)

        # 3. Strip citations and verification tags first
        s = re.sub(r"\[VERIFIED[^\]]*\]", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\[Source[^\]]*\]", "", s, flags=re.IGNORECASE)
        s = re.sub(r"\[\d+\]", "", s)  # Numeric citations [1], [2]

        # 4. Strip Markdown images and links: [Text](url) -> Text
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)

        # 5. Expand currencies
        for sym, word in cls.CURRENCY_MAP.items():
            escaped_sym = re.escape(sym)
            s = re.sub(rf"{escaped_sym}\s*([\d,\.]+)", rf"\1 {word}", s)

        # 6. Expand symbols: % -> percent, & -> and, + -> plus
        s = re.sub(r"\b%\b|(?<=\d)%", " percent", s)
        s = s.replace("&", " and ")

        # 7. Strip markdown formatting characters (#, *, _, ~, >, =)
        s = re.sub(r"[#*_~>]+", "", s)

        # 8. Collapse whitespace and repeated punctuation
        s = re.sub(r"\s+", " ", s).strip()
        s = re.sub(r"[\.!\?]{2,}", ".", s)

        # 9. Condense to concise spoken summary if response is excessively long
        words = s.split()
        if len(words) > max_words:
            # Pick first 2 complete sentences or truncate cleanly
            sentences = re.split(r"(?<=[.!?])\s+", s)
            condensed = ""
            for sentence in sentences:
                if len((condensed + " " + sentence).split()) <= max_words:
                    condensed = (condensed + " " + sentence).strip()
                else:
                    break
            if condensed:
                s = condensed
            else:
                s = " ".join(words[:max_words]) + "..."

        return s


speech_formatter = SpeechTextFormatter()
