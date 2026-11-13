"""Email Intelligence & Analysis Engine for NOUS.

Categorizes emails, identifies urgency, detects assignment & project deadlines,
extracts actionable items, detects meeting invitations, and generates daily inbox briefings.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

from backend.app.email.sanitizer import email_sanitizer


class EmailCategory(str, Enum):
    IMPORTANT = "important"
    WORK = "work"
    COLLEGE = "college"
    PERSONAL = "personal"
    PROMOTIONS = "promotions"
    NOTIFICATIONS = "notifications"
    URGENT = "urgent"
    REQUIRES_RESPONSE = "requires_response"


class EmailMessage(BaseModel):
    id: str
    thread_id: str = ""
    sender: str
    sender_name: str = ""
    recipient: str = "me"
    subject: str
    snippet: str
    body: str
    date: str
    timestamp: float
    is_unread: bool = True
    category: EmailCategory = EmailCategory.IMPORTANT
    is_urgent: bool = False
    requires_response: bool = False
    detected_deadlines: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    has_meeting_invite: bool = False
    is_suspicious_injection: bool = False
    suspicious_reasons: list[str] = Field(default_factory=list)


class EmailIntelligenceAnalyzer:
    """Core analysis engine extracting semantic intelligence from email contents."""

    # Heuristic patterns for category classification
    COLLEGE_KEYWORDS = [
        "assignment", "lecture", "professor", "exam", "syllabus", "course",
        "university", "campus", "department", "lab report", "submission", "grade"
    ]
    WORK_KEYWORDS = [
        "pull request", "jira", "sprint", "deployment", "production", "client",
        "repository", "commit", "standup", "code review", "milestone"
    ]
    PROMO_KEYWORDS = [
        "discount", "offer", "sale", "% off", "coupon", "limited time",
        "promo", "deal", "subscribe", "newsletter", "unsubscribe"
    ]
    NOTIFICATION_KEYWORDS = [
        "security alert", "sign-in from", "password reset", "notification",
        "verify your email", "two-factor", "automated message", "do-not-reply"
    ]

    # Deadline extraction patterns
    DEADLINE_PATTERNS = [
        re.compile(r"\b(due (?:date|by|on)|deadline(?:\s+is)?|submit by|submission deadline)\s*:?\s*([A-Za-z0-9\s,\/\-]+(?:am|pm|\d{4})?)", re.I),
        re.compile(r"\bby\s+(tomorrow|tonight|(?:next\s+)?(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b(?:\s+at\s+[\d:]+\s*(?:am|pm)?)?", re.I),
        re.compile(r"\bby\s+(\d{1,2}(?:st|nd|rd|th)?\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*)\b", re.I),
    ]

    # Action item patterns
    ACTION_PATTERNS = [
        re.compile(r"(?:please|kindly|could you|make sure to)\s+([^\.\n\?]+)", re.I),
        re.compile(r"(?:action required|todo|to-do):\s*([^\.\n]+)", re.I),
        re.compile(r"\[ \]\s*([^\.\n]+)", re.I),
    ]

    # Meeting detection
    MEETING_PATTERNS = [
        re.compile(r"(https?://(?:meet\.google\.com|zoom\.us|teams\.microsoft\.com)/[^\s]+)", re.I),
        re.compile(r"\b(google meet|zoom meeting|video call|calendar invitation|join with google meet)\b", re.I),
    ]

    # Response required patterns
    RESPONSE_PATTERNS = [
        re.compile(r"\b(please let (?:me|us) know|awaiting your (?:reply|response)|could you confirm|please confirm|rsvp)\b", re.I),
        re.compile(r"\b(what are your thoughts|let me know if|can you do this)\b", re.I),
    ]

    # Urgent keywords
    URGENT_KEYWORDS = ["urgent", "asap", "immediate attention", "critical", "action needed today", "emergency"]

    def analyze(
        self,
        email_id: str,
        sender: str,
        subject: str,
        body: str,
        date_str: str,
        timestamp: float,
        is_unread: bool = True,
        thread_id: str = "",
    ) -> EmailMessage:
        """Run full intelligence analysis on an email message."""
        # 1. Sanitize & check for prompt injection
        sanitized = email_sanitizer.sanitize(body)
        clean_body = sanitized.clean_text

        combined_text = f"{subject} {clean_body}".lower()

        # 2. Urgent check
        is_urgent = any(w in combined_text for w in self.URGENT_KEYWORDS)

        # 3. Meeting check
        has_meeting = any(p.search(clean_body) or p.search(subject) for p in self.MEETING_PATTERNS)

        # 4. Response required check
        req_response = (
            any(p.search(clean_body) for p in self.RESPONSE_PATTERNS) or
            ("?" in clean_body and not any(p in combined_text for p in self.PROMO_KEYWORDS))
        )

        # 5. Extract deadlines
        deadlines = []
        for p in self.DEADLINE_PATTERNS:
            matches = p.findall(clean_body)
            for m in matches:
                if isinstance(m, tuple):
                    val = " ".join([x for x in m if x]).strip()
                else:
                    val = str(m).strip()
                if val and len(val) <= 60 and val not in deadlines:
                    deadlines.append(val)

        # 6. Extract action items
        action_items = []
        for p in self.ACTION_PATTERNS:
            matches = p.findall(clean_body)
            for m in matches:
                item_text = m.strip()
                if item_text and 10 <= len(item_text) <= 120 and item_text not in action_items:
                    action_items.append(item_text)

        # 7. Categorize
        sender_lower = sender.lower()
        if is_urgent:
            category = EmailCategory.URGENT
        elif req_response and not any(w in combined_text for w in self.PROMO_KEYWORDS):
            category = EmailCategory.REQUIRES_RESPONSE
        elif any(w in combined_text or w in sender_lower for w in self.COLLEGE_KEYWORDS):
            category = EmailCategory.COLLEGE
        elif any(w in combined_text or w in sender_lower for w in self.WORK_KEYWORDS):
            category = EmailCategory.WORK
        elif any(w in combined_text for w in self.PROMO_KEYWORDS):
            category = EmailCategory.PROMOTIONS
        elif any(w in combined_text or w in sender_lower for w in self.NOTIFICATION_KEYWORDS):
            category = EmailCategory.NOTIFICATIONS
        else:
            category = EmailCategory.IMPORTANT

        # Extract sender name
        sender_name = sender.split("<")[0].replace('"', '').strip()
        if not sender_name:
            sender_name = sender

        snippet = clean_body[:180] + ("..." if len(clean_body) > 180 else "")

        return EmailMessage(
            id=email_id,
            thread_id=thread_id or email_id,
            sender=sender,
            sender_name=sender_name,
            subject=subject,
            snippet=snippet,
            body=clean_body,
            date=date_str,
            timestamp=timestamp,
            is_unread=is_unread,
            category=category,
            is_urgent=is_urgent,
            requires_response=req_response,
            detected_deadlines=deadlines,
            action_items=action_items[:5],
            has_meeting_invite=has_meeting,
            is_suspicious_injection=sanitized.is_suspicious,
            suspicious_reasons=sanitized.suspicious_patterns_detected,
        )

    def generate_daily_summary(self, emails: list[EmailMessage]) -> dict:
        """Create executive summary briefing across inbox."""
        total = len(emails)
        unread = [e for e in emails if e.is_unread]
        urgent = [e for e in emails if e.is_urgent]
        req_reply = [e for e in emails if e.requires_response]
        deadlines_found = [
            {"subject": e.subject, "sender": e.sender_name, "deadlines": e.detected_deadlines}
            for e in emails if e.detected_deadlines
        ]
        meetings = [
            {"subject": e.subject, "sender": e.sender_name, "date": e.date}
            for e in emails if e.has_meeting_invite
        ]

        # Category counts
        cat_counts = {}
        for c in EmailCategory:
            cat_counts[c.value] = sum(1 for e in emails if e.category == c)

        # Highlight top 3 most important
        top_items = []
        for e in urgent + req_reply + [x for x in emails if x.category in [EmailCategory.COLLEGE, EmailCategory.WORK]]:
            if e not in top_items:
                top_items.append({
                    "id": e.id,
                    "sender": e.sender_name,
                    "subject": e.subject,
                    "category": e.category.value,
                    "is_urgent": e.is_urgent,
                    "action_items": e.action_items,
                })
            if len(top_items) >= 4:
                break

        return {
            "total_emails": total,
            "unread_count": len(unread),
            "urgent_count": len(urgent),
            "requires_response_count": len(req_reply),
            "category_distribution": cat_counts,
            "deadlines_detected": deadlines_found,
            "meeting_invitations": meetings,
            "top_priorities": top_items,
        }


email_analyzer = EmailIntelligenceAnalyzer()
