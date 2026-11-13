"""NOUS Email Intelligence & Communications Package."""

from backend.app.email.sanitizer import email_sanitizer, SanitizedEmail
from backend.app.email.oauth import google_oauth
from backend.app.email.analyzer import email_analyzer, EmailMessage, EmailCategory
from backend.app.email.client import gmail_client

__all__ = [
    "email_sanitizer",
    "SanitizedEmail",
    "google_oauth",
    "email_analyzer",
    "EmailMessage",
    "EmailCategory",
    "gmail_client",
]
