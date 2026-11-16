"""Sensitive Data Redaction & Sanitization Engine for NOUS (Phase 14).

Detects and masks API keys, secrets, private keys, passwords, and PII
before text is sent to LLMs, written to audit logs, or rendered in UI.
"""

from __future__ import annotations

import re
from typing import Any

# Regular expression patterns for sensitive data detection
REDACTION_PATTERNS: list[tuple[str, str]] = [
    # 1. Private Keys
    (
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "[REDACTED_PRIVATE_KEY]",
    ),
    # 2. OpenAI / Anthropic / Generic AI API Keys
    (r"\b(?:sk|anthropic)-[a-zA-Z0-9_-]{20,}\b", "[REDACTED_AI_API_KEY]"),
    # 3. Google API Keys (AIzaSy...)
    (r"\bAIza[0-9A-Za-z\-_]{30,45}\b", "[REDACTED_GOOGLE_API_KEY]"),
    # 4. GitHub Personal Access Tokens (ghp_..., github_pat_...)
    (r"\bgh[pousr]_[A-Za-z0-9_]{25,}\b", "[REDACTED_GITHUB_TOKEN]"),
    (r"\bgithub_pat_[A-Za-z0-9_]{30,}\b", "[REDACTED_GITHUB_TOKEN]"),
    # 5. Bearer tokens in Authorization headers / text
    (r"(?i)\bBearer\s+[a-zA-Z0-9\-\._~+/]+=*", "Bearer [REDACTED_BEARER_TOKEN]"),
    # 6. Passwords in URLs (e.g. postgresql://user:pass@host:5432)
    (r"://([^:]+):([^@]+)@", r"://\1:[REDACTED_URL_PASSWORD]@"),
    # 7. Credit Card numbers (13 to 16 digits, with optional spaces or dashes)
    (r"\b(?:\d{4}[ -]?){3}\d{4}\b", "[REDACTED_CREDIT_CARD]"),
    # 8. Key-Value and JSON Secrets (password, secret, client_secret, api_key)
    (
        r'(?i)(["\']?(?:password|client_secret|secret_key|api_key|auth_token|access_token|private_key)["\']?\s*[:=]\s*["\'])([^"\'\s]{3,})(["\'])',
        r"\g<1>[REDACTED_SECRET]\g<3>",
    ),
]


class SensitiveDataRedactor:
    """Detects and scrubs sensitive secrets, credentials, and PII."""

    def __init__(self) -> None:
        self._compiled_patterns = [
            (re.compile(pat, re.MULTILINE), repl) for pat, repl in REDACTION_PATTERNS
        ]

    def redact(self, text: str | None) -> str:
        """Scrub all sensitive patterns from text."""
        if not text:
            return ""

        redacted = str(text)
        for pattern, replacement in self._compiled_patterns:
            redacted = pattern.sub(replacement, redacted)

        return redacted

    def contains_sensitive(self, text: str | None) -> bool:
        """Check whether text contains any known secret or credential pattern."""
        if not text:
            return False

        for pattern, _ in self._compiled_patterns:
            if pattern.search(str(text)):
                return True

        return False

    def redact_data_structure(self, data: Any) -> Any:
        """Recursively redact strings in dictionaries, lists, and primitives."""
        if isinstance(data, str):
            return self.redact(data)
        elif isinstance(data, dict):
            new_dict = {}
            for k, v in data.items():
                redacted_v = self.redact_data_structure(v)
                if isinstance(redacted_v, str) and "[REDACTED_" in redacted_v:
                    new_dict[k] = redacted_v
                elif re.search(r"(?i)(password|secret|token|key|credential)", str(k)):
                    new_dict[k] = "[REDACTED_SECRET]"
                else:
                    new_dict[k] = redacted_v
            return new_dict
        elif isinstance(data, list):
            return [self.redact_data_structure(item) for item in data]
        return data


# Global singleton redactor
sensitive_redactor = SensitiveDataRedactor()
