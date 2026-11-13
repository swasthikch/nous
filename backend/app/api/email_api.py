"""FastAPI Router for NOUS Email Intelligence & Communications.

Provides endpoints for:
- Google OAuth status, consent URL, callback, and disconnect.
- Semantic email querying, unread filters, and search.
- Deadline detection and action-item extraction.
- Daily inbox summary briefings.
- Human-In-The-Loop Draft Generation and Approval-Gated Sending.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.app.email.oauth import google_oauth
from backend.app.email.client import gmail_client
from backend.app.email.analyzer import email_analyzer, EmailCategory

router = APIRouter(prefix="/api/email", tags=["Email Intelligence"])


class CreateDraftRequest(BaseModel):
    to_email: str
    subject: str
    body: str
    reply_to_id: Optional[str] = None


class SendDraftRequest(BaseModel):
    user_confirmed: bool = Field(
        ...,
        description="Explicit human confirmation required before any email can be sent.",
    )


# ==============================================================
# OAUTH 2.0 AUTHENTICATION
# ==============================================================

@router.get("/auth/status")
async def get_auth_status():
    """Retrieve Google OAuth status, connected email identity, and configuration status."""
    is_configured = google_oauth.is_configured()
    is_authenticated = google_oauth.is_authenticated()
    tokens = google_oauth.load_tokens() or {}
    user_email = tokens.get("email", "Not connected")

    return {
        "is_configured": is_configured,
        "is_authenticated": is_authenticated,
        "connected_account": user_email if is_authenticated else None,
        "mode": "live_gmail" if is_authenticated else "offline_demo",
        "scopes": [
            "gmail.readonly",
            "gmail.compose",
            "userinfo.email",
        ],
    }


@router.get("/auth/url")
async def get_auth_url():
    """Generate official Google OAuth 2.0 authorization URL."""
    if not google_oauth.is_configured():
        return {
            "configured": False,
            "url": None,
            "message": "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env to connect live Gmail.",
        }
    url = google_oauth.get_authorization_url()
    return {"configured": True, "url": url}


@router.get("/auth/callback")
async def oauth_callback(code: Optional[str] = None, error: Optional[str] = None):
    """Handle Google OAuth redirect callback."""
    if error:
        raise HTTPException(status_code=400, detail=f"Google OAuth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    try:
        await google_oauth.exchange_code_for_token(code)
        # Redirect to frontend with query flag
        return RedirectResponse(url="/?oauth=success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token exchange failed: {str(e)}")


@router.post("/auth/disconnect")
async def disconnect_account():
    """Disconnect and revoke Google OAuth tokens."""
    await google_oauth.disconnect()
    return {"status": "disconnected", "message": "Google account unlinked successfully."}


# ==============================================================
# EMAIL INTELLIGENCE & RETRIEVAL
# ==============================================================

@router.get("/messages")
async def get_messages(
    category: Optional[EmailCategory] = Query(None),
    unread_only: bool = Query(False),
    limit: int = Query(15, ge=1, le=50),
    search: Optional[str] = Query(None),
):
    """Retrieve emails with semantic intelligence categorization and security scanning."""
    emails = await gmail_client.get_messages(
        category=category,
        unread_only=unread_only,
        limit=limit,
        search_query=search,
    )
    return {
        "count": len(emails),
        "messages": [e.model_dump() for e in emails],
    }


@router.get("/messages/{message_id}")
async def get_message_detail(message_id: str):
    """Fetch single email with extracted intelligence (deadlines, action items, prompt injection warnings)."""
    emails = await gmail_client.get_messages(limit=50)
    target = next((e for e in emails if e.id == message_id), None)
    if not target:
        raise HTTPException(status_code=404, detail="Email not found.")
    return target.model_dump()


@router.get("/summary")
async def get_inbox_summary():
    """Generate executive daily email briefing."""
    emails = await gmail_client.get_messages(limit=30)
    summary = email_analyzer.generate_daily_summary(emails)
    return summary


@router.get("/deadlines")
async def get_email_deadlines():
    """Extract all emails with detected submission, assignment, or project deadlines."""
    emails = await gmail_client.get_messages(limit=30)
    deadline_emails = [e.model_dump() for e in emails if e.detected_deadlines]
    return {
        "count": len(deadline_emails),
        "deadline_emails": deadline_emails,
    }


@router.get("/action-required")
async def get_action_required_emails():
    """Extract emails requiring a reply, decision, or action."""
    emails = await gmail_client.get_messages(limit=30)
    action_emails = [
        e.model_dump() for e in emails
        if e.requires_response or e.is_urgent or e.action_items
    ]
    return {
        "count": len(action_emails),
        "action_emails": action_emails,
    }


# ==============================================================
# HUMAN-IN-THE-LOOP REPLY DRAFTING & SENDING
# ==============================================================

@router.post("/draft")
async def create_reply_draft(req: CreateDraftRequest):
    """Create a reply draft awaiting human confirmation. Never sends automatically."""
    draft = gmail_client.create_draft(
        to_email=req.to_email,
        subject=req.subject,
        body=req.body,
        reply_to_id=req.reply_to_id,
    )
    return {"status": "draft_created", "draft": draft}


@router.get("/drafts")
async def list_drafts():
    """List pending drafts awaiting user approval."""
    drafts = gmail_client.load_drafts()
    return {"count": len(drafts), "drafts": drafts}


@router.post("/send/{draft_id}")
async def send_draft(draft_id: str, req: SendDraftRequest):
    """Send an email draft. Strictly blocked without user_confirmed=True."""
    if not req.user_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Security Block: Human confirmation is mandatory before any email can be sent.",
        )
    result = await gmail_client.send_draft(draft_id, user_confirmed=True)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to send draft."))
    return result


@router.post("/demo-seed")
async def reseed_demo_emails():
    """Reset the local mailbox cache with realistic academic, coding, and security-test emails."""
    gmail_client._seed_default_emails()
    return {"status": "reseeded", "message": "Demo emails restored successfully."}
