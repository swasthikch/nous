"""Intent Classification Engine for NOUS.

Detects user intent using low-latency heuristic analysis and keyword classification,
routing queries to appropriate tools or model pipelines.
"""

import re
from enum import Enum
from typing import Optional
from pydantic import BaseModel


class IntentType(str, Enum):
    GREETING = "greeting"
    DATETIME_QUERY = "datetime_query"
    SYSTEM_QUERY = "system_query"
    CALCULATION = "calculation"
    REMEMBER_FACT = "remember_fact"
    RECALL_MEMORY = "recall_memory"
    SCHEDULE_QUERY = "schedule_query"
    ADD_ACTIVITY = "add_activity"
    UPDATE_STATUS = "update_status"
    RESCHEDULE_ACTIVITY = "reschedule_activity"
    DAILY_REVIEW = "daily_review"
    CHECK_EMAILS = "check_emails"
    SUMMARIZE_EMAILS = "summarize_emails"
    FIND_DEADLINES = "find_deadlines"
    REPLY_NEEDED = "reply_needed"
    DRAFT_EMAIL = "draft_email"
    PROJECT_PROGRESS = "project_progress"
    PROJECT_DEADLINES = "project_deadlines"
    GITHUB_ACTIVITY = "github_activity"
    INACTIVE_PROJECTS = "inactive_projects"
    ADD_PROJECT_MILESTONE = "add_project_milestone"
    MARKET_OVERVIEW = "market_overview"
    STOCK_QUERY = "stock_query"
    MARKET_ANALYSIS = "market_analysis"
    MARKET_WATCHLIST = "market_watchlist"
    MARKET_ALERT = "market_alert"
    FII_DII_FLOWS = "fii_dii_flows"
    WEB_SEARCH = "web_search"
    DEEP_RESEARCH = "deep_research"
    RESEARCH_NOTES = "research_notes"
    LIST_FILES = "list_files"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    RUN_COMMAND = "run_command"
    SCHEDULE_TASK = "schedule_task"
    LIST_TASKS = "list_tasks"
    SECURITY_AUDIT = "security_audit"
    PRIVACY_SETTINGS = "privacy_settings"
    OFFLINE_LOCKDOWN = "offline_lockdown"
    PURGE_SECURITY = "purge_security"
    WEATHER_QUERY = "weather_query"
    DICTIONARY_LOOKUP = "dictionary_lookup"
    CURRENCY_CONVERT = "currency_convert"
    RANDOM_JOKE = "random_joke"
    DAEMON_STATUS = "daemon_status"
    COMPLEX_REASONING = "complex_reasoning"
    GENERAL_CHAT = "general_chat"


class IntentResult(BaseModel):
    intent: IntentType
    confidence: float
    suggested_tool: Optional[str] = None
    tool_parameters: Optional[dict] = None
    requires_cloud_routing: bool = False


class IntentClassifier:
    """Classifies user input to identify tools and optimal routing."""

    def __init__(self):
        # Heuristic regex patterns for deterministic 0ms intent extraction
        self._datetime_pattern = re.compile(
            r"\b(what('s| is)? (the )?(current |exact )?(time|date|day|today's date)|what day is it|tell me (the )?(exact )?(time|date|datetime|date and time))\b",
            re.IGNORECASE,
        )
        self._system_pattern = re.compile(
            r"\b(specs|hardware|processor|cpu|ram|graphics|gpu|system specs|laptop specs|my hardware)\b",
            re.IGNORECASE,
        )
        self._calc_pattern = re.compile(
            r"^(calculate|compute|what is|evaluate)?\s*([\d\.\s\+\-\*\/\^\(\)]+)\s*\??$",
            re.IGNORECASE,
        )
        self._greeting_pattern = re.compile(
            r"^(hi|hello|hey|good (morning|afternoon|evening)|hey nous|hello nous)\b",
            re.IGNORECASE,
        )

    def classify(self, message: str) -> IntentResult:
        text = message.strip()

        # 1. Check Date / Time Query
        if self._datetime_pattern.search(text):
            return IntentResult(
                intent=IntentType.DATETIME_QUERY,
                confidence=0.95,
                suggested_tool="get_current_datetime",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 2. Check System / Hardware Query
        if self._system_pattern.search(text):
            return IntentResult(
                intent=IntentType.SYSTEM_QUERY,
                confidence=0.92,
                suggested_tool="get_system_specs",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 3. Check Arithmetic / Calculation
        if re.search(r"\b(calculate|compute)\b", text, re.IGNORECASE) or (
            any(op in text for op in ["+", "*", "/", "^"]) and any(c.isdigit() for c in text)
        ):
            # Extract arithmetic expression (must start with digit or parenthesis)
            calc_match = re.search(r"\(?[\d]+[\d\.\s\+\-\*\/\^\(\)]*[\d\)]", text)
            if calc_match and len(calc_match.group(0).strip()) >= 3:
                expr = calc_match.group(0).strip()
                return IntentResult(
                    intent=IntentType.CALCULATION,
                    confidence=0.90,
                    suggested_tool="calculate",
                    tool_parameters={"expression": expr},
                    requires_cloud_routing=False,
                )

        # 4. Check Remember Fact ("remember that...", "please remember...", "save memory...")
        rem_match = re.search(
            r"^(please )?(remember that|remember:|remember|save this:|save that)\s+(.*)",
            text,
            re.IGNORECASE,
        )
        if rem_match:
            fact_body = rem_match.group(3).strip()
            # Categorize memory intelligently
            category = "personal_info"
            key = "note"

            if re.search(r"\b(my name is|call me|i am|i'm called)\s+([A-Za-z]+)", fact_body, re.IGNORECASE):
                name_match = re.search(r"\b(my name is|call me|i am|i'm called)\s+([A-Za-z]+)", fact_body, re.IGNORECASE)
                user_name = name_match.group(2) if name_match else "User"
                category = "user_profile"
                key = "preferred_name"
                fact_body = f"User's preferred name is {user_name}."
            elif re.search(r"\b(goal|learn|studying|master|career)\b", fact_body, re.IGNORECASE):
                category = "user_profile"
                key = "learning_goal"
            elif re.search(r"\b(project|repository|codebase|app|build|building)\b", fact_body, re.IGNORECASE):
                category = "project"
                key = "project_note"
            elif re.search(r"\b(routine|schedule|habit|wake up|sleep|gym|workout)\b", fact_body, re.IGNORECASE):
                category = "routine"
                key = "routine_schedule"

            return IntentResult(
                intent=IntentType.REMEMBER_FACT,
                confidence=0.95,
                suggested_tool="remember_fact",
                tool_parameters={
                    "category": category,
                    "key": key,
                    "content": fact_body,
                },
                requires_cloud_routing=False,
            )

        # 5. Check Recall Memories ("what do you remember", "what are my goals", "show memories")
        if re.search(r"\b(what do you remember|show (my )?memories|list (my )?memories|recall memories|what('s| is) my name|who am i|what are my goals)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.RECALL_MEMORY,
                confidence=0.92,
                suggested_tool="recall_memories",
                tool_parameters={"query": text},
                requires_cloud_routing=False,
            )

        # 6. Check Daily Review / Debrief ("generate daily review", "daily debrief", "how was my day")
        if re.search(r"\b(daily review|review my day|daily debrief|how was my day|summarise my day|summarize my day|evening review)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.DAILY_REVIEW,
                confidence=0.95,
                suggested_tool="generate_daily_review",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 7. Check Schedule Query ("what is my schedule", "show my daily plan", "what's on my schedule")
        if re.search(r"\b(what('s| is) my schedule|show (my )?schedule|check (my )?schedule|daily plan|what are my activities|what do i have planned|schedule today|my routine today)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.SCHEDULE_QUERY,
                confidence=0.94,
                suggested_tool="get_daily_schedule",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 8. Check Reschedule Missed Activity ("reschedule activity 2", "reschedule missed activity 5")
        resched_match = re.search(r"\breschedule\s+(?:activity\s+|task\s+|missed activity\s+)?(\d+)\b", text, re.IGNORECASE)
        if resched_match:
            act_id = int(resched_match.group(1))
            return IntentResult(
                intent=IntentType.RESCHEDULE_ACTIVITY,
                confidence=0.95,
                suggested_tool="reschedule_missed_activity",
                tool_parameters={"activity_id": act_id},
                requires_cloud_routing=False,
            )

        # 9. Check Update Activity Status ("mark activity 3 as completed", "mark gym as completed", "finished walking")
        status_match = re.search(
            r"\b(mark|set)\s+(?:activity\s+|task\s+)?(\d+)\s+(?:as\s+)?(completed|finished|in progress|skipped|rescheduled|not started)\b",
            text,
            re.IGNORECASE,
        )
        if status_match:
            act_id = int(status_match.group(2))
            st_raw = status_match.group(3).lower()
            status_map = {
                "finished": "completed",
                "completed": "completed",
                "in progress": "in_progress",
                "skipped": "skipped",
                "rescheduled": "rescheduled",
                "not started": "not_started",
            }
            return IntentResult(
                intent=IntentType.UPDATE_STATUS,
                confidence=0.95,
                suggested_tool="update_activity_status",
                tool_parameters={
                    "activity_id": act_id,
                    "status": status_map.get(st_raw, "completed"),
                },
                requires_cloud_routing=False,
            )

        # 10. Check Add Activity ("add activity LeetCode Practice from 17:00 to 18:00", "schedule Walking from 07:00 to 08:00")
        add_match = re.search(
            r"\b(add|schedule|plan)\s+(?:activity\s+|task\s+)?(.+?)\s+(?:from|at)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s+(?:to|-)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\b",
            text,
            re.IGNORECASE,
        )
        if add_match:
            act_name = add_match.group(2).strip()
            raw_start = add_match.group(3).strip()
            raw_end = add_match.group(4).strip()

            def normalize_time(t: str) -> str:
                m24 = re.match(r"^(\d{1,2}):(\d{2})$", t)
                if m24:
                    return f"{int(m24.group(1)):02d}:{int(m24.group(2)):02d}"
                m12 = re.match(r"^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$", t, re.IGNORECASE)
                if m12:
                    h = int(m12.group(1))
                    m = int(m12.group(2) or 0)
                    if m12.group(3).lower() == "pm" and h != 12:
                        h += 12
                    elif m12.group(3).lower() == "am" and h == 12:
                        h = 0
                    return f"{h:02d}:{m:02d}"
                if t.isdigit():
                    return f"{int(t):02d}:00"
                return t

            start_t = normalize_time(raw_start)
            end_t = normalize_time(raw_end)

            category = "routine"
            lower_name = act_name.lower()
            if any(w in lower_name for w in ["study", "exam", "reading", "revision", "course"]):
                category = "study"
            elif any(w in lower_name for w in ["code", "coding", "leetcode", "project", "python", "dev"]):
                category = "coding"
            elif any(w in lower_name for w in ["gym", "workout", "fitness", "walk", "walking", "run", "running"]):
                category = "fitness"
            elif any(w in lower_name for w in ["college", "lecture", "class"]):
                category = "college"

            return IntentResult(
                intent=IntentType.ADD_ACTIVITY,
                confidence=0.92,
                suggested_tool="add_schedule_activity",
                tool_parameters={
                    "name": act_name,
                    "start_time": start_t,
                    "end_time": end_t,
                    "category": category,
                    "priority": "medium",
                },
                requires_cloud_routing=False,
            )

        # 11. Check Email Deadlines ("find emails containing assignment deadlines", "deadlines in my email")
        if re.search(r"\b(emails?|messages?)\s+(containing|with|about)?\s*(assignment\s+)?deadlines?\b|\bdeadlines?\s+(in\s+my\s+email|from\s+email)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.FIND_DEADLINES,
                confidence=0.94,
                suggested_tool="find_email_deadlines",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 12. Check Emails Requiring Response ("which emails require my response", "emails needing reply")
        if re.search(r"\b(which|what)?\s*emails?\s+(require|need|awaiting)\s+(my\s+)?(response|reply)\b|\bemails?\s+requiring\s+(a\s+)?response\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.REPLY_NEEDED,
                confidence=0.94,
                suggested_tool="get_emails_requiring_response",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 13. Check Summarize Emails ("summarise the important emails from today", "summarize unread emails", "daily email summary")
        if re.search(r"\b(summarise|summarize)\s+(the\s+)?(important|unread|today's)?\s*emails?\b|\bdaily email summary\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.SUMMARIZE_EMAILS,
                confidence=0.95,
                suggested_tool="summarize_emails",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 14. Check Draft Email Reply ("draft reply to email msg_001 saying I will submit by Friday")
        draft_match = re.search(r"\b(draft|write)\s+(?:a\s+)?(?:reply|response)\s+to\s+(?:email\s+)?([A-Za-z0-9_\-]+)\s*(?:saying|with|stating)?\s*(.*)", text, re.IGNORECASE)
        if draft_match:
            mid = draft_match.group(2).strip()
            intent_text = draft_match.group(3).strip() or "Acknowledged, thank you."
            return IntentResult(
                intent=IntentType.DRAFT_EMAIL,
                confidence=0.95,
                suggested_tool="draft_email_reply",
                tool_parameters={"email_id": mid, "reply_intent": intent_text},
                requires_cloud_routing=False,
            )

        # 15. Check General Email Queries ("check my emails", "check inbox", "any emails about upcoming projects")
        if re.search(r"\b(check|show|list|read)\s+(?:my\s+)?(?:emails?|inbox)\b|\bare there any emails\b", text, re.IGNORECASE):
            category = None
            if "project" in text.lower() or "work" in text.lower() or "github" in text.lower():
                category = "work"
            elif "college" in text.lower() or "assignment" in text.lower() or "exam" in text.lower():
                category = "college"
            elif "unread" in text.lower():
                pass

            params: dict = {"max_results": 5}
            if category:
                params["category"] = category
            if "unread" in text.lower():
                params["unread_only"] = True

            return IntentResult(
                intent=IntentType.CHECK_EMAILS,
                confidence=0.93,
                suggested_tool="check_emails",
                tool_parameters=params,
                requires_cloud_routing=False,
            )

        # 16. Check GitHub Activity / Commits / PRs ("summarise recent commits on repository", "check github activity", "show pull requests")
        if re.search(r"\b(github activity|recent commits?|pull requests?|commits? on (?:the )?(?:repository|repo)|check github|show github)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.GITHUB_ACTIVITY,
                confidence=0.94,
                suggested_tool="check_github_activity",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 17. Check Inactive Projects ("are there any inactive projects", "check inactive repos", "stale projects")
        if re.search(r"\b(inactive (?:projects?|repos?)|stale (?:projects?|repos?)|projects? with no recent activity)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.INACTIVE_PROJECTS,
                confidence=0.94,
                suggested_tool="find_inactive_projects",
                tool_parameters={"days_threshold": 7},
                requires_cloud_routing=False,
            )

        # 18. Check Project Deadlines ("what are my upcoming project deadlines", "project deadlines")
        if re.search(r"\b(project deadlines?|upcoming project deadlines?|milestone deadlines?)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.PROJECT_DEADLINES,
                confidence=0.95,
                suggested_tool="check_project_deadlines",
                tool_parameters={"days_ahead": 14},
                requires_cloud_routing=False,
            )

        # 19. Check Project Progress & Status ("check my project progress", "show my projects", "project status")
        if re.search(r"\b(check (?:my )?project progress|show (?:my )?projects?|list (?:my )?projects?|project status|projects overview)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.PROJECT_PROGRESS,
                confidence=0.94,
                suggested_tool="get_projects_overview",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 20. Check Add Project Milestone ("add project milestone: finish phase 9 by tonight")
        ms_match = re.search(r"\badd (?:project )?milestone:?\s*(?:to project (\d+):?\s*)?([^\.\n]+)", text, re.IGNORECASE)
        if ms_match:
            pid = int(ms_match.group(1)) if ms_match.group(1) else 1
            ms_title = ms_match.group(2).strip()
            return IntentResult(
                intent=IntentType.ADD_PROJECT_MILESTONE,
                confidence=0.92,
                suggested_tool="add_project_milestone",
                tool_parameters={"project_id": pid, "title": ms_title},
                requires_cloud_routing=False,
            )

        # 21. Check Market Causal Reasoning ("why is the market down", "why did nifty fall", "explain why nifty fell", "explain market movement", "why is reliance down")
        if re.search(
            r"\b(why (?:is|did|are) (?:the )?(?:market|nifty|sensex|bank\s*nifty|stocks?|reliance|tcs|hdfc|[a-z0-9\.\^]+) (?:down|falling|fell|up|rallying|crashing|drop|dropped|slump|slumped|surge|surged)|explain (?:why )?(?:the )?(?:market|nifty|sensex|stocks?|reliance|tcs|hdfc|[a-z0-9\.\^]+) (?:moved?|fell|dropped|rallied|is down|is up|crashed|movement)|explain market movement|what caused (?:the )?(?:drop|fall|rally|surge|crash|movement))\b",
            text,
            re.IGNORECASE,
        ):
            target_sym = "^NSEI"
            lower_text = text.lower()
            if "reliance" in lower_text:
                target_sym = "RELIANCE.NS"
            elif "tcs" in lower_text:
                target_sym = "TCS.NS"
            elif "hdfc" in lower_text:
                target_sym = "HDFCBANK.NS"
            elif "sensex" in lower_text:
                target_sym = "^BSESN"
            elif "bank" in lower_text:
                target_sym = "^NSEBANK"
            elif "nasdaq" in lower_text:
                target_sym = "^IXIC"
            return IntentResult(
                intent=IntentType.MARKET_ANALYSIS,
                confidence=0.96,
                suggested_tool="explain_market_movement",
                tool_parameters={"symbol_or_index": target_sym},
                requires_cloud_routing=False,
            )

        # 22. Check Stock Quote ("what is Reliance stock price", "TCS share price", "quote for HDFCBANK", "price of Nifty")
        quote_match = re.search(r"\b(?:what(?:'s| is) (?:the )?(?:current )?(?:price|quote|share price|stock price) (?:of|for) ([a-z0-9\.\^ ]+)|([a-z0-9\.\^]+) (?:stock price|share price|quote))\b", text, re.IGNORECASE)
        if quote_match or re.search(r"\b(stock price|share price|stock quote)\b", text, re.IGNORECASE):
            raw_sym = (quote_match.group(1) or quote_match.group(2) or "").strip().lower() if quote_match else ""
            target_sym = "^NSEI"
            if "reliance" in raw_sym or "reliance" in text.lower():
                target_sym = "RELIANCE.NS"
            elif "tcs" in raw_sym or "tcs" in text.lower():
                target_sym = "TCS.NS"
            elif "hdfc" in raw_sym or "hdfc" in text.lower():
                target_sym = "HDFCBANK.NS"
            elif "sensex" in raw_sym or "sensex" in text.lower():
                target_sym = "^BSESN"
            elif "bank" in raw_sym or "bank nifty" in text.lower():
                target_sym = "^NSEBANK"
            elif "nasdaq" in raw_sym or "nasdaq" in text.lower():
                target_sym = "^IXIC"
            elif raw_sym.upper() in ["INFY", "INFY.NS", "AAPL", "MSFT"]:
                target_sym = raw_sym.upper() if raw_sym.endswith(".NS") else f"{raw_sym.upper()}.NS"

            return IntentResult(
                intent=IntentType.STOCK_QUERY,
                confidence=0.95,
                suggested_tool="get_stock_quote",
                tool_parameters={"symbol": target_sym},
                requires_cloud_routing=False,
            )

        # 23. Check Market Overview & Indices ("how is the market performing", "show market overview", "nifty update", "stock market summary")
        if re.search(r"\b(market (?:overview|update|summary|indices|performance)|how (?:is|are) (?:the )?markets? (?:doing|performing)|stock market today|nifty update)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.MARKET_OVERVIEW,
                confidence=0.95,
                suggested_tool="get_market_indices",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 24. Check FII / DII Institutional Activity ("fii dii data", "institutional flows", "fii activity", "are fii buying or selling")
        if re.search(r"\b(fii dii|fii activity|dii activity|institutional flows?|fii data|are fii|are dii|fii buying|fii selling|fii\b|dii\b)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.FII_DII_FLOWS,
                confidence=0.95,
                suggested_tool="get_fii_dii_activity",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 25. Check Market Watchlist ("show my stock watchlist", "check watchlist")
        if re.search(r"\b(?:stock |market )?watchlist\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.MARKET_WATCHLIST,
                confidence=0.94,
                suggested_tool="manage_market_watchlist",
                tool_parameters={"action": "list"},
                requires_cloud_routing=False,
            )

        # 26. Check Research Notes ("show my research notes", "saved research", "research notebook")
        if re.search(r"\b(show (?:my )?research notes|list (?:my )?research notes|saved research|research notebook)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.RESEARCH_NOTES,
                confidence=0.94,
                suggested_tool="list_research_notes",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 27. Check Deep Research ("research Raft consensus", "conduct research on quantum computing", "investigate the history of FastAPI")
        research_match = re.search(
            r"\b(?:research (?:topic |on )?|deep research (?:on )?|investigate (?:the )?|conduct research (?:on )?|prepare research report on )([^\.\n\?]+)",
            text,
            re.IGNORECASE,
        )
        if research_match:
            r_query = research_match.group(1).strip()
            cat = "general"
            lower_q = r_query.lower()
            if any(k in lower_q for k in ["algorithm", "framework", "architecture", "fastapi", "raft", "python", "docker", "k8s"]):
                cat = "technology"
            elif any(k in lower_q for k in ["company", "inc", "ltd", "google", "apple", "microsoft", "nvidia", "reliance"]):
                cat = "company"
            elif any(k in lower_q for k in ["theory", "quantum", "physics", "proof", "math", "academic"]):
                cat = "academic"
            elif any(k in lower_q for k in ["market", "economy", "fed", "inflation", "stock"]):
                cat = "market"

            return IntentResult(
                intent=IntentType.DEEP_RESEARCH,
                confidence=0.95,
                suggested_tool="conduct_deep_research",
                tool_parameters={"query": r_query, "category": cat, "save_to_notebook": True},
                requires_cloud_routing=False,
            )

        # 28. Check Web Search ("search the web for...", "web search:...", "search online for...")
        search_match = re.search(
            r"\b(?:search (?:the )?web for |web search:?\s*|search online for |google )([^\.\n\?]+)",
            text,
            re.IGNORECASE,
        )
        if search_match:
            s_query = search_match.group(1).strip()
            return IntentResult(
                intent=IntentType.WEB_SEARCH,
                confidence=0.94,
                suggested_tool="web_search",
                tool_parameters={"query": s_query, "limit": 5},
                requires_cloud_routing=False,
            )

        # 29. Check File Operations (Phase 13)
        # 29A. List Workspace Files
        if re.search(r"\b(?:list|show|browse|view)\s+(?:workspace\s+files|files\s+in\s+workspace|my\s+workspace\s+files|workspace\s+directory)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.LIST_FILES,
                confidence=0.95,
                suggested_tool="list_workspace_files",
                tool_parameters={"subpath": ""},
                requires_cloud_routing=False,
            )

        # 29B. Read Workspace File
        read_file_match = re.search(r"\b(?:read|view|cat|display|inspect)\s+(?:file|workspace\s+file)\s+['\"]?([a-zA-Z0-9_\-\./\\]+)['\"]?", text, re.IGNORECASE)
        if read_file_match:
            f_path = read_file_match.group(1).strip()
            return IntentResult(
                intent=IntentType.READ_FILE,
                confidence=0.94,
                suggested_tool="read_workspace_file",
                tool_parameters={"file_path": f_path},
                requires_cloud_routing=False,
            )

        # 29C. Write Workspace File
        write_file_match = re.search(r"\b(?:create|write|save)\s+(?:file|to\s+file)\s+['\"]?([a-zA-Z0-9_\-\./\\]+)['\"]?\s+(?:with\s+content\s+|as\s+)?(.*)", text, re.IGNORECASE)
        if write_file_match and len(write_file_match.group(2).strip()) > 0:
            target_file = write_file_match.group(1).strip()
            file_body = write_file_match.group(2).strip()
            return IntentResult(
                intent=IntentType.WRITE_FILE,
                confidence=0.93,
                suggested_tool="write_workspace_file",
                tool_parameters={"file_path": target_file, "content": file_body, "overwrite": True},
                requires_cloud_routing=False,
            )

        # 30. Check Controlled Command Execution (Phase 13)
        cmd_match = re.search(r"\b(?:run|execute)\s+(?:command|safe\s+command|shell|terminal)\s*[:\-]?\s*['\"]?([^\n\r]+)['\"]?", text, re.IGNORECASE)
        if cmd_match:
            raw_command = cmd_match.group(1).strip(" '\"")
            return IntentResult(
                intent=IntentType.RUN_COMMAND,
                confidence=0.94,
                suggested_tool="execute_safe_command",
                tool_parameters={"command": raw_command},
                requires_cloud_routing=False,
            )

        # 31. Check Scheduled Automation Tasks (Phase 13)
        # 31A. List Scheduled Tasks
        if re.search(r"\b(?:list|show|view)\s+(?:scheduled\s+tasks|automation\s+jobs|background\s+tasks|automations)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.LIST_TASKS,
                confidence=0.95,
                suggested_tool="list_scheduled_tasks",
                tool_parameters={"status": None},
                requires_cloud_routing=False,
            )

        # 31B. Create Scheduled Task
        sched_match = re.search(r"\b(?:schedule|create\s+scheduled)\s+(?:task|job|automation)\s+['\"]?([^'\"\n]+)['\"]?\s+(?:every\s+(\d+)\s+seconds?)?", text, re.IGNORECASE)
        if sched_match:
            task_title = sched_match.group(1).strip()
            interval_val = int(sched_match.group(2)) if sched_match.group(2) else 3600
            return IntentResult(
                intent=IntentType.SCHEDULE_TASK,
                confidence=0.93,
                suggested_tool="create_scheduled_task",
                tool_parameters={"name": task_title, "action_type": "briefing", "interval_seconds": interval_val},
                requires_cloud_routing=False,
            )

        # 32. Check Security & Privacy Vault Operations (Phase 14)
        # 32A. Security Audit Logs
        if re.search(r"\b(?:show|view|inspect|get|check)\s+(?:security\s+audit|audit\s+log|security\s+logs|audit\s+trail|security\s+vault)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.SECURITY_AUDIT,
                confidence=0.95,
                suggested_tool="get_security_audit_logs",
                tool_parameters={"limit": 25},
                requires_cloud_routing=False,
            )

        # 32B. Offline Lockdown
        if re.search(r"\b(?:enable|activate|turn\s+on)\s+(?:offline\s+lockdown|offline\s+mode|lockdown\s+mode|network\s+lockdown)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.OFFLINE_LOCKDOWN,
                confidence=0.95,
                suggested_tool="set_security_privacy_mode",
                tool_parameters={"offline_lockdown": True},
                requires_cloud_routing=False,
            )

        # 32C. Purge Transient Artifacts
        if re.search(r"\b(?:purge|clear|clean\s+up)\s+(?:transient\s+data|temporary\s+data|security\s+cache|temporary\s+logs|session\s+artifacts)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.PURGE_SECURITY,
                confidence=0.95,
                suggested_tool="purge_transient_security_data",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 34. Check Weather Query (Public APIs - Open-Meteo)
        weather_match = re.search(
            r"\b(?:what(?:'s|\s+is)\s+the\s+weather\s+(?:in|for|like\s+in)|how(?:'s|\s+is)\s+the\s+weather\s+in|weather\s+(?:forecast\s+for|in|for|at)|forecast\s+for|temperature\s+in)\s+([a-zA-Z\s]+?)(?:\s+today|\s+now|\s+tomorrow|\?|$)",
            text,
            re.IGNORECASE,
        )
        if not weather_match:
            weather_match = re.search(r"\b([a-zA-Z]{3,25})\s+weather\b", text, re.IGNORECASE)

        if weather_match:
            target_city = weather_match.group(1).strip()
            # Avoid matching common keywords as city names
            if target_city.lower() not in {"the", "my", "current", "this", "today"}:
                return IntentResult(
                    intent=IntentType.WEATHER_QUERY,
                    confidence=0.94,
                    suggested_tool="get_weather_forecast",
                    tool_parameters={"location": target_city},
                    requires_cloud_routing=False,
                )

        # 35. Check Dictionary Lookup (Public APIs - Free Dictionary)
        dict_match = re.search(
            r"\b(?:what\s+does\s+['\"]?([a-zA-Z\-]{2,30})['\"]?\s+mean|meaning\s+of\s+['\"]?([a-zA-Z\-]{2,30})['\"]?|definition\s+of\s+['\"]?([a-zA-Z\-]{2,30})['\"]?|define\s+['\"]?([a-zA-Z\-]{2,30})['\"]?)\b",
            text,
            re.IGNORECASE,
        )
        if dict_match:
            lookup_word = next(w for w in dict_match.groups() if w is not None).strip()
            if lookup_word.lower() not in {"the", "a", "an", "this", "that"}:
                return IntentResult(
                    intent=IntentType.DICTIONARY_LOOKUP,
                    confidence=0.94,
                    suggested_tool="lookup_dictionary_definition",
                    tool_parameters={"word": lookup_word},
                    requires_cloud_routing=False,
                )

        # 36. Check Currency Conversion (Public APIs - Frankfurter)
        currency_match = re.search(
            r"\b(?:convert|how\s+much\s+is)\s+([\d\.]+)\s*([a-zA-Z]{3}|dollars?|euros?|pounds?|rupees?|yen|cad|aud|chf|cny|sgd)\s+(?:to|in|into)\s+([a-zA-Z]{3}|dollars?|euros?|pounds?|rupees?|yen|cad|aud|chf|cny|sgd)\b",
            text,
            re.IGNORECASE,
        )
        if currency_match:
            raw_amt = float(currency_match.group(1))
            from_c = currency_match.group(2).strip()
            to_c = currency_match.group(3).strip()
            return IntentResult(
                intent=IntentType.CURRENCY_CONVERT,
                confidence=0.95,
                suggested_tool="convert_currency",
                tool_parameters={"amount": raw_amt, "from_currency": from_c, "to_currency": to_c},
                requires_cloud_routing=False,
            )

        # 37. Check Joke / Humor (Public APIs - Official Joke API)
        if re.search(r"\b(?:tell\s+me\s+a\s+joke|random\s+joke|programming\s+joke|developer\s+joke|crack\s+a\s+joke|make\s+me\s+laugh)\b", text, re.IGNORECASE):
            joke_cat = "programming" if "programming" in text.lower() or "developer" in text.lower() else "general"
            return IntentResult(
                intent=IntentType.RANDOM_JOKE,
                confidence=0.94,
                suggested_tool="get_random_joke",
                tool_parameters={"category": joke_cat},
                requires_cloud_routing=False,
            )

        # 38. Check Autonomous Minute Daemon Status
        if re.search(r"\b(?:daemon\s+status|minute\s+daemon|background\s+daemon|autonomous\s+worker|offline\s+daemon|is\s+the\s+daemon\s+running)\b", text, re.IGNORECASE):
            return IntentResult(
                intent=IntentType.DAEMON_STATUS,
                confidence=0.95,
                suggested_tool="get_autonomous_daemon_status",
                tool_parameters={},
                requires_cloud_routing=False,
            )

        # 33. Check Greetings
        if self._greeting_pattern.search(text) and len(text.split()) <= 4:
            return IntentResult(
                intent=IntentType.GREETING,
                confidence=0.95,
                suggested_tool=None,
                requires_cloud_routing=False,
            )

        # 5. Check Complex Reasoning Indicators (e.g. detailed architectural breakdowns, deep proof)
        complex_triggers = [
            "deep reasoning", "comprehensive analysis", "step-by-step mathematical proof",
            "compare across 10 dimensions", "formal verification",
        ]
        if any(trigger in text.lower() for trigger in complex_triggers):
            return IntentResult(
                intent=IntentType.COMPLEX_REASONING,
                confidence=0.85,
                suggested_tool=None,
                requires_cloud_routing=True,
            )

        # Default: General Chat
        return IntentResult(
            intent=IntentType.GENERAL_CHAT,
            confidence=0.80,
            suggested_tool=None,
            requires_cloud_routing=False,
        )


intent_classifier = IntentClassifier()
