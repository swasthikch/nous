/**
 * NOUS Frontend Application Engine (Phase 5 - Persistent Memory Edition)
 * Manages Multi-Turn Sessions, Routing Modes, Anti-Hallucination Tools,
 * and Persistent SQLite Long-Term Memory Dashboard.
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Element References - Views & Navigation
    const navChat = document.getElementById("nav-chat");
    const navMemory = document.getElementById("nav-memory");
    const navVoice = document.getElementById("nav-voice");
    const navRoutine = document.getElementById("nav-routine");
    const navEmail = document.getElementById("nav-email");
    const navProjects = document.getElementById("nav-projects");
    const navMarket = document.getElementById("nav-market");
    const navResearch = document.getElementById("nav-research");
    const navAutomation = document.getElementById("nav-automation");
    const navSecurity = document.getElementById("nav-security");
    const viewChat = document.getElementById("view-chat");
    const viewMemory = document.getElementById("view-memory");
    const viewVoice = document.getElementById("view-voice");
    const viewRoutine = document.getElementById("view-routine");
    const viewEmail = document.getElementById("view-email");
    const viewProjects = document.getElementById("view-projects");
    const viewMarket = document.getElementById("view-market");
    const viewResearch = document.getElementById("view-research");
    const viewAutomation = document.getElementById("view-automation");
    const viewSecurity = document.getElementById("view-security");
    const memoryCountBadge = document.getElementById("memory-count-badge");
    const routineCountBadge = document.getElementById("routine-count-badge");
    const emailCountBadge = document.getElementById("email-count-badge");
    const projectsCountBadge = document.getElementById("projects-count-badge");
    const marketSessionBadge = document.getElementById("market-session-badge");
    const researchCountBadge = document.getElementById("research-count-badge");
    const automationTasksBadge = document.getElementById("automation-tasks-badge");
    const securityModeBadge = document.getElementById("security-mode-badge");
    const specMemoryStatus = document.getElementById("spec-memory-status");

    // Chat Elements
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const modelSelect = document.getElementById("model-select");
    const clearChatBtn = document.getElementById("clear-chat-btn");
    const refreshHealthBtn = document.getElementById("refresh-health-btn");
    const welcomeCard = document.getElementById("welcome-card");
    const topStatusText = document.getElementById("top-status-text");
    const topStatusIndicator = document.getElementById("top-status-indicator");
    const systemStatusIndicator = document.getElementById("system-status-indicator");
    const specCpu = document.getElementById("spec-cpu");
    const specModel = document.getElementById("spec-model");
    const responseStats = document.getElementById("response-stats");
    const sessionLabel = document.getElementById("session-label");
    const sessionsList = document.getElementById("sessions-list");
    const newChatBtn = document.getElementById("new-chat-btn");
    const modePills = document.querySelectorAll(".mode-pill");

    // Memory Dashboard Elements
    const memoryToggle = document.getElementById("memory-toggle");
    const categoryTabs = document.querySelectorAll(".cat-tab");
    const memorySearchInput = document.getElementById("memory-search-input");
    const memoryGrid = document.getElementById("memory-grid");
    const btnAddMemory = document.getElementById("btn-add-memory");
    const memoryModal = document.getElementById("memory-modal");
    const modalTitle = document.getElementById("modal-title");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnCancelModal = document.getElementById("btn-cancel-modal");
    const btnSaveMemory = document.getElementById("btn-save-memory");
    const editMemoryId = document.getElementById("edit-memory-id");
    const memCategory = document.getElementById("mem-category");
    const memKey = document.getElementById("mem-key");
    const memContent = document.getElementById("mem-content");

    // Voice Assistant Elements
    const voiceOrbWrapper = document.getElementById("voice-orb-wrapper");
    const voiceOrbCenter = document.getElementById("voice-orb-center");
    const voiceStatusLabel = document.getElementById("voice-status-label");
    const subtitleRole = document.getElementById("subtitle-role");
    const subtitleText = document.getElementById("subtitle-text");
    const btnVoiceToggle = document.getElementById("btn-voice-toggle");
    const btnVoiceToggleText = document.getElementById("btn-voice-toggle-text");
    const btnVoiceStop = document.getElementById("btn-voice-stop");
    const selectVoice = document.getElementById("select-voice");
    const sliderRate = document.getElementById("slider-rate");
    const valRate = document.getElementById("val-rate");
    const sliderPitch = document.getElementById("slider-pitch");
    const valPitch = document.getElementById("val-pitch");
    const toggleWakeWord = document.getElementById("toggle-wake-word");
    const toggleChatAutoSpeak = document.getElementById("toggle-chat-auto-speak");

    // Routine & Daily Life Elements (Phase 7)
    const routineDatePicker = document.getElementById("routine-date-picker");
    const btnRoutinePrevDay = document.getElementById("btn-routine-prev-day");
    const btnRoutineNextDay = document.getElementById("btn-routine-next-day");
    const btnRoutineToday = document.getElementById("btn-routine-today");
    const btnGenerateReview = document.getElementById("btn-generate-review");
    const btnAddActivity = document.getElementById("btn-add-activity");
    const statCompRate = document.getElementById("stat-comp-rate");
    const statCompSub = document.getElementById("stat-comp-sub");
    const statCodingHours = document.getElementById("stat-coding-hours");
    const statStudyHours = document.getElementById("stat-study-hours");
    const statTotalTasks = document.getElementById("stat-total-tasks");
    const statConflictsSub = document.getElementById("stat-conflicts-sub");
    const routineConflictBanner = document.getElementById("routine-conflict-banner");
    const conflictDetailsText = document.getElementById("conflict-details-text");
    const routineTimeline = document.getElementById("routine-timeline");
    const routineCategoryTabs = document.querySelectorAll("#routine-category-tabs .cat-tab");

    // Activity Modal Elements
    const activityModal = document.getElementById("activity-modal");
    const actModalTitle = document.getElementById("act-modal-title");
    const btnCloseActModal = document.getElementById("btn-close-act-modal");
    const btnCancelActModal = document.getElementById("btn-cancel-act-modal");
    const btnSaveActivity = document.getElementById("btn-save-activity");
    const editActId = document.getElementById("edit-act-id");
    const actName = document.getElementById("act-name");
    const actStartTime = document.getElementById("act-start-time");
    const actEndTime = document.getElementById("act-end-time");
    const actCategory = document.getElementById("act-category");
    const actPriority = document.getElementById("act-priority");
    const actNotes = document.getElementById("act-notes");
    const actFixed = document.getElementById("act-fixed");

    // Review Modal Elements
    const reviewModal = document.getElementById("review-modal");
    const btnCloseReviewModal = document.getElementById("btn-close-review-modal");
    const btnCloseReviewFooter = document.getElementById("btn-close-review-footer");
    const reviewModalBody = document.getElementById("review-modal-body");

    // Email Intelligence Elements (Phase 8)
    const emailOAuthDot = document.getElementById("email-oauth-dot");
    const emailOAuthText = document.getElementById("email-oauth-text");
    const btnEmailAuthAction = document.getElementById("btn-email-auth-action");
    const btnEmailBriefing = document.getElementById("btn-email-briefing");
    const btnEmailDeadlinesFilter = document.getElementById("btn-email-deadlines-filter");
    const statEmailUnread = document.getElementById("stat-email-unread");
    const statEmailUrgent = document.getElementById("stat-email-urgent");
    const statEmailDeadlines = document.getElementById("stat-email-deadlines");
    const statEmailReplies = document.getElementById("stat-email-replies");
    const emailCategoryTabs = document.querySelectorAll("#email-category-tabs .cat-tab");
    const emailSearchInput = document.getElementById("email-search-input");
    const emailMessagesList = document.getElementById("email-messages-list");

    // Email Modals
    const emailDetailModal = document.getElementById("email-detail-modal");
    const emailModalSubject = document.getElementById("email-modal-subject");
    const emailModalBody = document.getElementById("email-modal-body");
    const btnCloseEmailModal = document.getElementById("btn-close-email-modal");
    const btnCloseEmailFooter = document.getElementById("btn-close-email-footer");
    const btnOpenDraftFromDetail = document.getElementById("btn-open-draft-from-detail");

    const emailDraftModal = document.getElementById("email-draft-modal");
    const draftReplyToId = document.getElementById("draft-reply-to-id");
    const draftTo = document.getElementById("draft-to");
    const draftSubject = document.getElementById("draft-subject");
    const draftBody = document.getElementById("draft-body");
    const draftConfirmCheck = document.getElementById("draft-confirm-check");
    const btnCloseDraftModal = document.getElementById("btn-close-draft-modal");
    const btnCancelDraft = document.getElementById("btn-cancel-draft");
    const btnSaveDraftOnly = document.getElementById("btn-save-draft-only");
    const btnSendDraft = document.getElementById("btn-send-draft");

    const emailBriefingModal = document.getElementById("email-briefing-modal");
    const emailBriefingBody = document.getElementById("email-briefing-body");
    const btnCloseBriefingModal = document.getElementById("btn-close-briefing-modal");
    const btnCloseBriefingFooter = document.getElementById("btn-close-briefing-footer");

    // Project Intelligence Elements (Phase 9)
    const btnSyncGithub = document.getElementById("btn-sync-github");
    const btnInactivityAudit = document.getElementById("btn-inactivity-audit");
    const btnAddProject = document.getElementById("btn-add-project");
    const statProjActive = document.getElementById("stat-proj-active");
    const statProjMilestones = document.getElementById("stat-proj-milestones");
    const statProjDeadlines = document.getElementById("stat-proj-deadlines");
    const statProjInactive = document.getElementById("stat-proj-inactive");
    const projectsInactivityBanner = document.getElementById("projects-inactivity-banner");
    const inactivityBannerText = document.getElementById("inactivity-banner-text");
    const projectStatusTabs = document.querySelectorAll("#project-status-tabs .cat-tab");
    const projectsListContainer = document.getElementById("projects-list-container");

    // GitHub Telemetry Elements
    const githubRepoLabel = document.getElementById("github-repo-label");
    const githubSyncTime = document.getElementById("github-sync-time");
    const githubCommitsList = document.getElementById("github-commits-list");
    const githubPrsList = document.getElementById("github-prs-list");
    const githubIssuesList = document.getElementById("github-issues-list");

    // Project Modals
    const projectModal = document.getElementById("project-modal");
    const projectModalTitle = document.getElementById("project-modal-title");
    const btnCloseProjectModal = document.getElementById("btn-close-project-modal");
    const btnCancelProjectModal = document.getElementById("btn-cancel-project-modal");
    const btnSaveProject = document.getElementById("btn-save-project");
    const editProjId = document.getElementById("edit-proj-id");
    const projName = document.getElementById("proj-name");
    const projDescription = document.getElementById("proj-description");
    const projTechStack = document.getElementById("proj-tech-stack");
    const projRepoUrl = document.getElementById("proj-repo-url");
    const projDeadline = document.getElementById("proj-deadline");
    const projPriority = document.getElementById("proj-priority");
    const projStatus = document.getElementById("proj-status");

    const milestoneModal = document.getElementById("milestone-modal");
    const milestoneProjId = document.getElementById("milestone-proj-id");
    const milestoneTitle = document.getElementById("milestone-title");
    const milestoneDueDate = document.getElementById("milestone-due-date");
    const milestoneNotes = document.getElementById("milestone-notes");
    const btnCloseMilestoneModal = document.getElementById("btn-close-milestone-modal");
    const btnCancelMilestone = document.getElementById("btn-cancel-milestone");
    const btnSaveMilestone = document.getElementById("btn-save-milestone");

    const inactivityAuditModal = document.getElementById("inactivity-audit-modal");
    const inactivityAuditBody = document.getElementById("inactivity-audit-body");
    const btnCloseAuditModal = document.getElementById("btn-close-audit-modal");
    const btnCloseAuditFooter = document.getElementById("btn-close-audit-footer");

    // State
    let currentSessionId = null;
    let isGenerating = false;
    let activeModel = "qwen2.5:3b";
    let activeMode = "hybrid";
    let activeCategoryFilter = "";
    let memorySearchTimeout = null;

    // Routine State
    const todayISO = new Date().toISOString().split("T")[0];
    let selectedRoutineDate = todayISO;
    let activeRoutineCategory = "";

    // Email State (Phase 8)
    let activeEmailCategory = "";
    let activeEmailSearch = "";
    let emailSearchTimeout = null;
    let currentViewingEmail = null;

    // Voice State
    let isListening = false;
    let speechRecognition = null;
    let systemVoices = [];
    let selectedVoice = null;
    let speechRate = 1.0;
    let speechPitch = 1.0;
    let wakeWordEnabled = false;
    let autoSpeakInChat = true;

    // ==============================================================
    // NAVIGATION SWITCHING (Chat vs. Memory vs. Voice vs. Routine vs. Email)
    // ==============================================================
    function switchView(target) {
        [navChat, navMemory, navVoice, navRoutine, navEmail, navProjects, navMarket, navResearch, navAutomation, navSecurity].forEach(n => n && n.classList.remove("active"));
        [viewChat, viewMemory, viewVoice, viewRoutine, viewEmail, viewProjects, viewMarket, viewResearch, viewAutomation, viewSecurity].forEach(v => v && v.classList.remove("active"));

        if (target === "chat") {
            navChat.classList.add("active");
            viewChat.classList.add("active");
        } else if (target === "memory") {
            navMemory.classList.add("active");
            viewMemory.classList.add("active");
            loadMemories();
        } else if (target === "voice") {
            navVoice.classList.add("active");
            viewVoice.classList.add("active");
            initVoiceSystem();
        } else if (target === "routine") {
            navRoutine.classList.add("active");
            viewRoutine.classList.add("active");
            loadSchedule(selectedRoutineDate);
        } else if (target === "email") {
            navEmail.classList.add("active");
            viewEmail.classList.add("active");
            checkEmailAuth();
            loadEmails();
        } else if (target === "projects") {
            navProjects.classList.add("active");
            viewProjects.classList.add("active");
            loadProjects();
            loadGithubTelemetry();
        } else if (target === "market") {
            if (navMarket) navMarket.classList.add("active");
            if (viewMarket) viewMarket.classList.add("active");
            loadMarketDashboard();
        } else if (target === "research") {
            if (navResearch) navResearch.classList.add("active");
            if (viewResearch) viewResearch.classList.add("active");
            loadResearchNotes();
        } else if (target === "automation") {
            if (navAutomation) navAutomation.classList.add("active");
            if (viewAutomation) viewAutomation.classList.add("active");
            loadWorkspaceFiles();
            loadScheduledTasks();
        } else if (target === "security") {
            if (navSecurity) navSecurity.classList.add("active");
            if (viewSecurity) viewSecurity.classList.add("active");
            loadPrivacySettings();
            loadAuditTrail();
        }

        // Close mobile drawer if open on smartphone screens
        closeMobileDrawer();
    }

    // ==============================================================
    // MOBILE RESPONSIVE DRAWER & TOUCH INTERACTION
    // ==============================================================
    const sidebar = document.querySelector(".sidebar");
    const mobileBackdrop = document.getElementById("mobile-backdrop");
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
    const mobileNewChatBtn = document.getElementById("mobile-new-chat-btn");
    const sidebarCloseBtn = document.getElementById("sidebar-close-btn");

    function openMobileDrawer() {
        if (sidebar) sidebar.classList.add("mobile-open");
        if (mobileBackdrop) mobileBackdrop.classList.add("active");
    }

    function closeMobileDrawer() {
        if (sidebar) sidebar.classList.remove("mobile-open");
        if (mobileBackdrop) mobileBackdrop.classList.remove("active");
    }

    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener("click", () => {
            if (sidebar && sidebar.classList.contains("mobile-open")) {
                closeMobileDrawer();
            } else {
                openMobileDrawer();
            }
        });
    }

    if (mobileBackdrop) {
        mobileBackdrop.addEventListener("click", closeMobileDrawer);
    }

    if (sidebarCloseBtn) {
        sidebarCloseBtn.addEventListener("click", closeMobileDrawer);
    }

    if (mobileNewChatBtn) {
        mobileNewChatBtn.addEventListener("click", () => {
            if (newChatBtn) newChatBtn.click();
            closeMobileDrawer();
        });
    }

    navChat.addEventListener("click", (e) => { e.preventDefault(); switchView("chat"); });
    navMemory.addEventListener("click", (e) => { e.preventDefault(); switchView("memory"); });
    navVoice.addEventListener("click", (e) => { e.preventDefault(); switchView("voice"); });
    if (navRoutine) navRoutine.addEventListener("click", (e) => { e.preventDefault(); switchView("routine"); });
    if (navEmail) navEmail.addEventListener("click", (e) => { e.preventDefault(); switchView("email"); });
    if (navProjects) navProjects.addEventListener("click", (e) => { e.preventDefault(); switchView("projects"); });
    if (navMarket) navMarket.addEventListener("click", (e) => { e.preventDefault(); switchView("market"); });
    if (navResearch) navResearch.addEventListener("click", (e) => { e.preventDefault(); switchView("research"); });
    if (navAutomation) navAutomation.addEventListener("click", (e) => { e.preventDefault(); switchView("automation"); });
    if (navSecurity) navSecurity.addEventListener("click", (e) => { e.preventDefault(); switchView("security"); });

    // ==============================================================
    // CHAT & CONVERSATION SESSIONS
    // ==============================================================
    chatInput.addEventListener("input", () => {
        chatInput.style.height = "auto";
        chatInput.style.height = Math.min(chatInput.scrollHeight, 160) + "px";
        sendBtn.disabled = !chatInput.value.trim() || isGenerating;
    });

    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled && !isGenerating) {
                sendMessage();
            }
        }
    });

    sendBtn.addEventListener("click", () => {
        if (!isGenerating && chatInput.value.trim()) {
            sendMessage();
        }
    });

    newChatBtn.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/sessions", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: "New Conversation" }),
            });
            const data = await res.json();
            currentSessionId = data.id;
            sessionLabel.textContent = `Session: ${currentSessionId}`;
            renderChatHistory([]);
            await loadSessions();
            chatInput.focus();
        } catch (e) {
            console.error("Error creating session:", e);
        }
    });

    clearChatBtn.addEventListener("click", async () => {
        if (!currentSessionId) return;
        try {
            await fetch(`/api/sessions/${currentSessionId}/clear`, { method: "POST" });
            renderChatHistory([]);
            responseStats.textContent = "";
            chatInput.focus();
        } catch (e) {
            console.error("Error clearing session:", e);
        }
    });

    document.addEventListener("click", (e) => {
        const promptBtn = e.target.closest(".quick-prompt-btn");
        if (promptBtn) {
            const prompt = promptBtn.dataset.prompt;
            if (prompt && !isGenerating) {
                // If in memory view, switch to chat
                navChat.click();
                chatInput.value = prompt;
                chatInput.dispatchEvent(new Event("input"));
                sendMessage();
            }
        }
    });

    refreshHealthBtn.addEventListener("click", checkHealth);

    modelSelect.addEventListener("change", (e) => {
        activeModel = e.target.value;
        specModel.textContent = activeModel;
    });

    modePills.forEach((pill) => {
        pill.addEventListener("click", async () => {
            const mode = pill.dataset.mode;
            try {
                const res = await fetch("/api/routing/mode", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ mode }),
                });
                if (res.ok) {
                    modePills.forEach((p) => p.classList.remove("active"));
                    pill.classList.add("active");
                    activeMode = mode;
                }
            } catch (e) {
                console.error("Error setting routing mode:", e);
            }
        });
    });

    async function loadSessions() {
        try {
            const res = await fetch("/api/sessions");
            if (!res.ok) return;
            const data = await res.json();
            const sessions = data.sessions || [];

            sessionsList.innerHTML = "";

            if (sessions.length === 0) {
                const newRes = await fetch("/api/sessions", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ title: "Main Conversation" }),
                });
                const newSession = await newRes.json();
                currentSessionId = newSession.id;
                sessions.push(newSession);
            } else if (!currentSessionId) {
                currentSessionId = sessions[0].id;
            }

            sessionLabel.textContent = `Session: ${currentSessionId}`;

            sessions.forEach((s) => {
                const item = document.createElement("div");
                item.className = `session-item ${s.id === currentSessionId ? "active" : ""}`;
                item.dataset.id = s.id;

                const titleSpan = document.createElement("span");
                titleSpan.className = "session-title";
                titleSpan.textContent = s.title || "Conversation";

                const delBtn = document.createElement("button");
                delBtn.className = "session-del-btn";
                delBtn.title = "Delete conversation";
                delBtn.innerHTML = "✕";
                delBtn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    await deleteSession(s.id);
                });

                item.appendChild(titleSpan);
                item.appendChild(delBtn);

                item.addEventListener("click", () => switchSession(s.id));
                sessionsList.appendChild(item);
            });
        } catch (e) {
            console.error("Error loading sessions:", e);
        }
    }

    async function switchSession(sessionId) {
        if (sessionId === currentSessionId || isGenerating) return;
        currentSessionId = sessionId;
        sessionLabel.textContent = `Session: ${currentSessionId}`;

        document.querySelectorAll(".session-item").forEach((el) => {
            el.classList.toggle("active", el.dataset.id === sessionId);
        });

        try {
            const res = await fetch(`/api/sessions/${sessionId}`);
            if (res.ok) {
                const data = await res.json();
                renderChatHistory(data.messages || []);
            }
        } catch (e) {
            console.error("Error switching session:", e);
        }
    }

    async function deleteSession(sessionId) {
        try {
            await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
            if (sessionId === currentSessionId) {
                currentSessionId = null;
            }
            await loadSessions();
            if (currentSessionId) {
                await switchSession(currentSessionId);
            }
        } catch (e) {
            console.error("Error deleting session:", e);
        }
    }

    function renderChatHistory(messages) {
        chatMessages.innerHTML = "";
        if (messages.length === 0) {
            if (welcomeCard) chatMessages.appendChild(welcomeCard);
            return;
        }

        messages.forEach((m) => {
            if (m.role === "user") {
                appendUserMessage(m.content);
            } else if (m.role === "assistant") {
                const tools = m.metadata && m.metadata.tools ? m.metadata.tools.map(t => ({ tool_name: t, is_verified: true })) : [];
                appendAssistantMessage(m.content, {
                    toolsExecuted: tools,
                    model: (m.metadata && m.metadata.model) || activeModel,
                    intent: m.metadata && m.metadata.intent,
                });
            }
        });
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    async function checkHealth() {
        systemStatusIndicator.className = "status-dot dot-checking";
        topStatusIndicator.className = "status-indicator";
        topStatusText.textContent = "Checking system health...";

        try {
            const response = await fetch("/api/health");
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            if (data.system) {
                specCpu.textContent = data.system.cpu_model || "Intel Core i5-1334U";
            }

            if (data.ai_engine) {
                const isConnected = data.ai_engine.connection_status === "connected";
                if (isConnected) {
                    systemStatusIndicator.className = "status-dot dot-online";
                    topStatusIndicator.className = "status-indicator connected";
                    topStatusText.textContent = `Online · ${data.ai_engine.configured_model}`;
                    specModel.textContent = data.ai_engine.configured_model;
                    activeModel = data.ai_engine.configured_model;
                } else {
                    systemStatusIndicator.className = "status-dot dot-offline";
                    topStatusIndicator.className = "status-indicator error";
                    topStatusText.textContent = "Ollama Disconnected";
                    specModel.textContent = "Offline";
                }
            }

            await loadModels();
            await checkMemorySettings();
        } catch (error) {
            console.error("Health check error:", error);
            systemStatusIndicator.className = "status-dot dot-offline";
            topStatusIndicator.className = "status-indicator error";
            topStatusText.textContent = "Backend Unreachable";
        }
    }

    async function loadModels() {
        try {
            const response = await fetch("/api/models");
            if (!response.ok) return;
            const data = await response.json();

            modelSelect.innerHTML = "";
            const localModels = data.available_local_models || [];

            if (localModels.length === 0) {
                const opt = document.createElement("option");
                opt.value = "";
                opt.textContent = "No models installed";
                modelSelect.appendChild(opt);
            } else {
                localModels.forEach((modelName) => {
                    const opt = document.createElement("option");
                    opt.value = modelName;
                    opt.textContent = `[Local] ${modelName}`;
                    if (modelName === data.active_model || modelName.startsWith("qwen2.5:3b")) {
                        opt.selected = true;
                        activeModel = modelName;
                        specModel.textContent = modelName;
                    }
                    modelSelect.appendChild(opt);
                });
            }

            if (data.cloud_provider && data.cloud_provider.configured) {
                const cloudOpt = document.createElement("option");
                cloudOpt.value = `cloud:${data.cloud_provider.model}`;
                cloudOpt.textContent = `[Cloud] ${data.cloud_provider.model}`;
                modelSelect.appendChild(cloudOpt);
            }
        } catch (e) {
            console.warn("Could not fetch models:", e);
        }
    }

    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text || isGenerating) return;

        if (welcomeCard && welcomeCard.parentNode) {
            welcomeCard.remove();
        }

        appendUserMessage(text);
        chatInput.value = "";
        chatInput.style.height = "auto";
        sendBtn.disabled = true;
        isGenerating = true;

        const { metaElement, bubbleElement, bodyElement } = createAssistantMessageBubble();
        bubbleElement.classList.add("typing-cursor");

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    session_id: currentSessionId,
                    model: activeModel,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }

            const data = await response.json();
            currentSessionId = data.session_id;

            bubbleElement.classList.remove("typing-cursor");
            bubbleElement.innerHTML = formatMarkdown(data.response);

            if (data.tools_executed && data.tools_executed.length > 0) {
                const banner = document.createElement("div");
                banner.className = "tools-executed-banner";

                data.tools_executed.forEach((tool) => {
                    const badge = document.createElement("span");
                    badge.className = "tool-badge";
                    badge.innerHTML = `⚡ <strong>Verified Tool:</strong> ${tool.tool_name}`;
                    banner.appendChild(badge);
                });

                if (data.intent) {
                    const intentBadge = document.createElement("span");
                    intentBadge.className = "intent-badge";
                    intentBadge.textContent = `🎯 Intent: ${data.intent}`;
                    banner.appendChild(intentBadge);
                }

                bodyElement.insertBefore(banner, bubbleElement);
            }

            const targetInfo = data.routing ? `${data.routing.selected_target.toUpperCase()} (${data.routing.selected_model})` : activeModel;
            const tps = data.tokens_per_second ? ` · ${data.tokens_per_second} t/s` : "";
            metaElement.textContent = `${targetInfo} · ${data.elapsed_seconds}s${tps}`;
            responseStats.textContent = `Last response: ${data.elapsed_seconds}s (${targetInfo})`;

            await loadSessions();
            await checkMemorySettings();

        } catch (error) {
            console.error("Chat error:", error);
            bubbleElement.classList.remove("typing-cursor");
            bubbleElement.innerHTML = `<span style="color: #ef4444;">⚠️ AI Brain Error: ${error.message}</span>`;
            metaElement.textContent = "Request failed";
        } finally {
            isGenerating = false;
            sendBtn.disabled = !chatInput.value.trim();
            chatInput.focus();
        }
    }

    function appendUserMessage(text) {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper user";

        const body = document.createElement("div");
        body.className = "message-body";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";
        bubble.textContent = text;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "YOU";

        body.appendChild(bubble);
        wrapper.appendChild(body);
        wrapper.appendChild(avatar);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function createAssistantMessageBubble() {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper assistant";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = "N";

        const body = document.createElement("div");
        body.className = "message-body";

        const bubble = document.createElement("div");
        bubble.className = "message-bubble";

        const meta = document.createElement("div");
        meta.className = "message-meta";
        meta.textContent = `Analyzing intent & reasoning...`;

        body.appendChild(bubble);
        body.appendChild(meta);
        wrapper.appendChild(avatar);
        wrapper.appendChild(body);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        return { bodyElement: body, metaElement: meta, bubbleElement: bubble };
    }

    function appendAssistantMessage(content, options = {}) {
        const { bodyElement, metaElement, bubbleElement } = createAssistantMessageBubble();
        bubbleElement.innerHTML = formatMarkdown(content);

        if (options.toolsExecuted && options.toolsExecuted.length > 0) {
            const banner = document.createElement("div");
            banner.className = "tools-executed-banner";
            options.toolsExecuted.forEach((tool) => {
                const badge = document.createElement("span");
                badge.className = "tool-badge";
                badge.innerHTML = `⚡ <strong>Verified Tool:</strong> ${tool.tool_name}`;
                banner.appendChild(badge);
            });
            bodyElement.insertBefore(banner, bubbleElement);
        }

        metaElement.textContent = options.model || "NOUS";
    }

    function formatMarkdown(text) {
        if (!text) return "";

        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        escaped = escaped.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
        });

        escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        escaped = escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");

        const parts = escaped.split(/(<pre>[\s\S]*?<\/pre>)/g);
        for (let i = 0; i < parts.length; i++) {
            if (!parts[i].startsWith("<pre>")) {
                parts[i] = parts[i].replace(/\n/g, "<br>");
            }
        }
        return parts.join("");
    }

    // ==============================================================
    // PERSISTENT MEMORY MANAGEMENT CONTROLS
    // ==============================================================
    async function checkMemorySettings() {
        try {
            const res = await fetch("/api/memory/settings");
            if (!res.ok) return;
            const data = await res.json();
            memoryToggle.checked = data.memory_enabled;
            specMemoryStatus.textContent = data.memory_enabled ? "Active (SQLite)" : "Disabled (Off)";
            specMemoryStatus.style.color = data.memory_enabled ? "var(--accent-cyan)" : "var(--status-offline)";

            const catRes = await fetch("/api/memory/categories");
            if (catRes.ok) {
                const catData = await catRes.json();
                memoryCountBadge.textContent = catData.total_active_memories || 0;
            }
        } catch (e) {
            console.error("Error checking memory settings:", e);
        }
    }

    memoryToggle.addEventListener("change", async () => {
        try {
            const enabled = memoryToggle.checked;
            await fetch("/api/memory/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ enabled }),
            });
            specMemoryStatus.textContent = enabled ? "Active (SQLite)" : "Disabled (Off)";
            specMemoryStatus.style.color = enabled ? "var(--accent-cyan)" : "var(--status-offline)";
        } catch (e) {
            console.error("Error toggling memory:", e);
        }
    });

    categoryTabs.forEach((tab) => {
        tab.addEventListener("click", () => {
            categoryTabs.forEach((t) => t.classList.remove("active"));
            tab.classList.add("active");
            activeCategoryFilter = tab.dataset.cat || "";
            loadMemories();
        });
    });

    memorySearchInput.addEventListener("input", () => {
        clearTimeout(memorySearchTimeout);
        memorySearchTimeout = setTimeout(() => {
            loadMemories();
        }, 300);
    });

    async function loadMemories() {
        const query = memorySearchInput.value.trim();
        let url = `/api/memory?limit=100`;
        if (activeCategoryFilter) url += `&category=${encodeURIComponent(activeCategoryFilter)}`;
        if (query) url += `&search=${encodeURIComponent(query)}`;

        try {
            const res = await fetch(url);
            if (!res.ok) return;
            const data = await res.json();
            renderMemoryCards(data.memories || []);
            memoryCountBadge.textContent = data.count || 0;
        } catch (e) {
            console.error("Error loading memories:", e);
        }
    }

    function renderMemoryCards(memories) {
        memoryGrid.innerHTML = "";
        if (memories.length === 0) {
            memoryGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
                    <p style="font-size: 1rem;">No memories found in this category.</p>
                    <small>Tell NOUS "Remember that..." in chat or click "+ Add Memory" above.</small>
                </div>
            `;
            return;
        }

        memories.forEach((m) => {
            const card = document.createElement("div");
            card.className = "memory-card";

            const header = document.createElement("div");
            header.className = "memory-card-header";

            const tag = document.createElement("span");
            tag.className = `category-tag cat-${m.category}`;
            tag.textContent = m.category.replace("_", " ");

            const actions = document.createElement("div");
            actions.className = "memory-card-actions";

            const editBtn = document.createElement("button");
            editBtn.innerHTML = "Edit";
            editBtn.addEventListener("click", () => openEditMemoryModal(m));

            const delBtn = document.createElement("button");
            delBtn.className = "btn-del";
            delBtn.innerHTML = "Delete";
            delBtn.addEventListener("click", () => deleteMemoryItem(m.id));

            actions.appendChild(editBtn);
            actions.appendChild(delBtn);
            header.appendChild(tag);
            header.appendChild(actions);

            const keyEl = document.createElement("div");
            keyEl.className = "memory-card-key";
            keyEl.textContent = m.key;

            const contentEl = document.createElement("div");
            contentEl.className = "memory-card-content";
            contentEl.textContent = m.content;

            const footer = document.createElement("div");
            footer.className = "memory-card-footer";
            const dateStr = new Date(m.updated_at * 1000).toLocaleDateString();
            footer.textContent = `Updated: ${dateStr}`;

            card.appendChild(header);
            card.appendChild(keyEl);
            card.appendChild(contentEl);
            card.appendChild(footer);

            memoryGrid.appendChild(card);
        });
    }

    // Modal Handling
    btnAddMemory.addEventListener("click", () => {
        modalTitle.textContent = "Add New Memory";
        editMemoryId.value = "";
        memKey.value = "";
        memContent.value = "";
        memCategory.value = activeCategoryFilter || "user_profile";
        memoryModal.classList.add("active");
    });

    btnCloseModal.addEventListener("click", () => memoryModal.classList.remove("active"));
    btnCancelModal.addEventListener("click", () => memoryModal.classList.remove("active"));

    function openEditMemoryModal(memory) {
        modalTitle.textContent = "Edit Memory";
        editMemoryId.value = memory.id;
        memCategory.value = memory.category;
        memKey.value = memory.key;
        memContent.value = memory.content;
        memoryModal.classList.add("active");
    }

    btnSaveMemory.addEventListener("click", async () => {
        const id = editMemoryId.value;
        const category = memCategory.value;
        const key = memKey.value.trim();
        const content = memContent.value.trim();

        if (!key || !content) {
            alert("Please provide both a Key and Content for the memory.");
            return;
        }

        try {
            if (id) {
                // Update existing
                await fetch(`/api/memory/${id}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ category, key, content }),
                });
            } else {
                // Create new
                await fetch("/api/memory", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ category, key, content }),
                });
            }
            memoryModal.classList.remove("active");
            await loadMemories();
            await checkMemorySettings();
        } catch (e) {
            console.error("Error saving memory:", e);
        }
    });

    async function deleteMemoryItem(id) {
        if (!confirm("Are you sure you want to delete this memory?")) return;
        try {
            await fetch(`/api/memory/${id}`, { method: "DELETE" });
            await loadMemories();
            await checkMemorySettings();
        } catch (e) {
            console.error("Error deleting memory:", e);
        }
    }

    // ==============================================================
    // VOICE ASSISTANT ENGINE (PHASE 6)
    // ==============================================================
    function initVoiceSystem() {
        // 1. Initialize Speech Synthesis Voices
        if ("speechSynthesis" in window) {
            function populateVoices() {
                systemVoices = window.speechSynthesis.getVoices();
                selectVoice.innerHTML = "";
                
                // Prioritize English natural voices
                systemVoices.forEach((v, idx) => {
                    const opt = document.createElement("option");
                    opt.value = idx;
                    opt.textContent = `${v.name} (${v.lang})`;
                    if (v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("David") || v.name.includes("Google"))) {
                        opt.selected = true;
                        selectedVoice = v;
                    }
                    selectVoice.appendChild(opt);
                });

                if (!selectedVoice && systemVoices.length > 0) {
                    selectedVoice = systemVoices[0];
                }
            }

            populateVoices();
            if (window.speechSynthesis.onvoiceschanged !== undefined) {
                window.speechSynthesis.onvoiceschanged = populateVoices;
            }
        }

        // 2. Initialize Speech Recognition
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (SpeechRec) {
            speechRecognition = new SpeechRec();
            speechRecognition.continuous = false;
            speechRecognition.interimResults = true;
            speechRecognition.lang = "en-US";

            speechRecognition.onstart = () => {
                isListening = true;
                voiceOrbWrapper.className = "voice-orb-wrapper listening";
                voiceStatusLabel.textContent = "Listening... Speak your command now.";
                btnVoiceToggleText.textContent = "Stop Listening";
                subtitleRole.textContent = "Listening (You):";
                subtitleText.textContent = "...";
            };

            speechRecognition.onresult = (event) => {
                let transcript = "";
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    transcript += event.results[i][0].transcript;
                }
                subtitleText.textContent = `"${transcript}"`;

                if (event.results[0].isFinal) {
                    handleSpokenInput(transcript);
                }
            };

            speechRecognition.onerror = (event) => {
                console.warn("Speech recognition error:", event.error);
                resetVoiceOrb();
                voiceStatusLabel.textContent = `Mic status: ${event.error}. Click to retry.`;
            };

            speechRecognition.onend = () => {
                isListening = false;
                btnVoiceToggleText.textContent = "Start Listening";
                if (!voiceOrbWrapper.classList.contains("thinking") && !voiceOrbWrapper.classList.contains("speaking")) {
                    resetVoiceOrb();
                }
            };
        } else {
            voiceStatusLabel.textContent = "Speech recognition is not supported in this browser. (Use Chrome or Edge).";
            btnVoiceToggle.disabled = true;
        }
    }

    // Voice UI Event Listeners
    voiceOrbWrapper.addEventListener("click", () => {
        if (window.speechSynthesis.speaking) {
            interruptSpeech();
        } else {
            toggleListening();
        }
    });

    btnVoiceToggle.addEventListener("click", toggleListening);
    btnVoiceStop.addEventListener("click", interruptSpeech);

    selectVoice.addEventListener("change", (e) => {
        const idx = parseInt(e.target.value, 10);
        if (!isNaN(idx) && systemVoices[idx]) {
            selectedVoice = systemVoices[idx];
        }
    });

    sliderRate.addEventListener("input", (e) => {
        speechRate = parseFloat(e.target.value);
        valRate.textContent = `${speechRate.toFixed(1)}x`;
    });

    sliderPitch.addEventListener("input", (e) => {
        speechPitch = parseFloat(e.target.value);
        valPitch.textContent = speechPitch.toFixed(1);
    });

    toggleWakeWord.addEventListener("change", (e) => {
        wakeWordEnabled = e.target.checked;
        fetch("/api/voice/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ wake_word_enabled: wakeWordEnabled }),
        });
    });

    toggleChatAutoSpeak.addEventListener("change", (e) => {
        autoSpeakInChat = e.target.checked;
    });

    function toggleListening() {
        if (!speechRecognition) {
            initVoiceSystem();
        }
        if (isListening) {
            speechRecognition.stop();
        } else {
            interruptSpeech();
            try {
                speechRecognition.start();
            } catch (err) {
                console.warn("Could not start speech recognition:", err);
            }
        }
    }

    async function handleSpokenInput(spokenText) {
        if (!spokenText.trim()) return;

        voiceOrbWrapper.className = "voice-orb-wrapper thinking";
        voiceStatusLabel.textContent = "Processing speech & querying AI Brain...";

        try {
            const res = await fetch("/api/voice/process-speech", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    speech_text: spokenText,
                    session_id: currentSessionId,
                }),
            });

            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (!data.processed) {
                voiceStatusLabel.textContent = data.message || "Wake-word required.";
                resetVoiceOrb();
                return;
            }

            const reply = data.spoken_text || data.response || "Task complete.";
            subtitleRole.textContent = "NOUS Spoke:";
            subtitleText.textContent = `"${reply}"`;
            voiceStatusLabel.textContent = "Speaking response...";

            speakText(reply);

        } catch (err) {
            console.error("Spoken input processing error:", err);
            voiceStatusLabel.textContent = `Error: ${err.message}`;
            resetVoiceOrb();
        }
    }

    function speakText(text) {
        if (!("speechSynthesis" in window) || !text) return;

        interruptSpeech();

        // Strip markdown stars, hashes, and backticks for clean speech
        const cleanSpeech = text
            .replace(/[#*`_~]/g, "")
            .replace(/\[VERIFIED.*?\]/gi, "")
            .trim();

        const utterance = new SpeechSynthesisUtterance(cleanSpeech);
        if (selectedVoice) utterance.voice = selectedVoice;
        utterance.rate = speechRate;
        utterance.pitch = speechPitch;

        voiceOrbWrapper.className = "voice-orb-wrapper speaking";

        utterance.onend = () => {
            resetVoiceOrb();
            voiceStatusLabel.textContent = "Speech completed. Click to speak again.";
        };

        utterance.onerror = (e) => {
            console.warn("Speech synthesis error:", e);
            resetVoiceOrb();
        };

        window.speechSynthesis.speak(utterance);
    }

    function interruptSpeech() {
        if ("speechSynthesis" in window) {
            window.speechSynthesis.cancel();
        }
        resetVoiceOrb();
    }

    function resetVoiceOrb() {
        voiceOrbWrapper.className = "voice-orb-wrapper";
        btnVoiceToggleText.textContent = "Start Listening";
        isListening = false;
    }

    // ==============================================================
    // ROUTINE & DAILY LIFE MANAGER (PHASE 7)
    // ==============================================================
    if (routineDatePicker) {
        routineDatePicker.value = selectedRoutineDate;
        routineDatePicker.addEventListener("change", (e) => {
            selectedRoutineDate = e.target.value;
            loadSchedule(selectedRoutineDate);
        });
    }

    if (btnRoutinePrevDay) {
        btnRoutinePrevDay.addEventListener("click", () => {
            const d = new Date(selectedRoutineDate);
            d.setDate(d.getDate() - 1);
            selectedRoutineDate = d.toISOString().split("T")[0];
            if (routineDatePicker) routineDatePicker.value = selectedRoutineDate;
            loadSchedule(selectedRoutineDate);
        });
    }

    if (btnRoutineNextDay) {
        btnRoutineNextDay.addEventListener("click", () => {
            const d = new Date(selectedRoutineDate);
            d.setDate(d.getDate() + 1);
            selectedRoutineDate = d.toISOString().split("T")[0];
            if (routineDatePicker) routineDatePicker.value = selectedRoutineDate;
            loadSchedule(selectedRoutineDate);
        });
    }

    if (btnRoutineToday) {
        btnRoutineToday.addEventListener("click", () => {
            selectedRoutineDate = new Date().toISOString().split("T")[0];
            if (routineDatePicker) routineDatePicker.value = selectedRoutineDate;
            loadSchedule(selectedRoutineDate);
        });
    }

    routineCategoryTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            routineCategoryTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeRoutineCategory = tab.dataset.cat || "";
            loadSchedule(selectedRoutineDate);
        });
    });

    async function loadSchedule(dateStr) {
        try {
            let url = `/api/routine/schedule?date=${dateStr}`;
            if (activeRoutineCategory) {
                url += `&category=${activeRoutineCategory}`;
            }

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const activities = data.activities || [];
            const conflicts = data.conflicts || [];

            // Update badge
            if (routineCountBadge) {
                routineCountBadge.textContent = activities.length;
            }

            // Update stats ribbon
            const total = activities.length;
            const completed = activities.filter(a => a.status === "completed").length;
            const compRate = total > 0 ? Math.round((completed / total) * 100) : 0;

            if (statCompRate) statCompRate.textContent = `${compRate}%`;
            if (statCompSub) statCompSub.textContent = `${completed} of ${total} completed`;
            if (statTotalTasks) statTotalTasks.textContent = total;

            // Calculate coding & study hours
            function timeToMins(t) {
                const parts = t.split(":");
                return parseInt(parts[0], 10) * 60 + parseInt(parts[1], 10);
            }

            let codingMins = 0;
            let studyMins = 0;
            activities.forEach(a => {
                if (a.status === "completed") {
                    const dur = Math.max(0, timeToMins(a.end_time) - timeToMins(a.start_time));
                    if (a.category === "coding") codingMins += dur;
                    else if (a.category === "study" || a.category === "college") studyMins += dur;
                }
            });

            if (statCodingHours) statCodingHours.textContent = `${(codingMins / 60).toFixed(1)}h`;
            if (statStudyHours) statStudyHours.textContent = `${(studyMins / 60).toFixed(1)}h`;

            // Conflicts handling
            if (routineConflictBanner && conflictDetailsText) {
                if (data.has_conflicts && conflicts.length > 0) {
                    routineConflictBanner.style.display = "flex";
                    conflictDetailsText.textContent = `Schedule overlap: ${conflicts.map(c => `${c.activity_1.name} & ${c.activity_2.name}`).join("; ")}`;
                    if (statConflictsSub) statConflictsSub.textContent = `⚠️ ${conflicts.length} overlap(s)`;
                } else {
                    routineConflictBanner.style.display = "none";
                    if (statConflictsSub) statConflictsSub.textContent = "No conflicts";
                }
            }

            renderTimeline(activities);
        } catch (err) {
            console.error("Error loading daily schedule:", err);
            if (routineTimeline) {
                routineTimeline.innerHTML = `<div class="empty-state">Failed to load schedule: ${err.message}</div>`;
            }
        }
    }

    function renderTimeline(activities) {
        if (!routineTimeline) return;

        if (activities.length === 0) {
            routineTimeline.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 8px;">📅</div>
                    <p>No activities scheduled for this date.</p>
                    <button class="btn-sm btn-outline" style="margin-top: 12px;" onclick="document.getElementById('btn-add-activity').click()">+ Add First Activity</button>
                </div>
            `;
            return;
        }

        routineTimeline.innerHTML = activities.map(act => {
            const startH = act.start_time;
            const endH = act.end_time;
            const dur = calculateDurationStr(startH, endH);
            const isMissedOrSkipped = act.status === "skipped" || act.status === "not_started" || act.status === "rescheduled";

            return `
                <div class="timeline-card status-${act.status}" id="act-card-${act.id}">
                    <div class="timeline-left">
                        <div class="timeline-time-box">
                            <div class="time-primary">${act.start_time} - ${act.end_time}</div>
                            <div class="time-duration">${dur}</div>
                        </div>
                        <div class="timeline-info">
                            <div class="timeline-title-row">
                                <span class="timeline-title">${escapeHtml(act.name)}</span>
                                ${act.is_fixed ? '<span class="fixed-pin" title="Fixed Commitment (Cannot be auto-rescheduled)">📌 Fixed</span>' : ''}
                            </div>
                            <div class="timeline-meta">
                                <span class="category-tag category-${act.category}">${act.category}</span>
                                <span class="priority-tag priority-${act.priority}">${act.priority}</span>
                                ${act.notes ? `<span class="timeline-notes">${escapeHtml(act.notes)}</span>` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="timeline-right">
                        <select class="status-dropdown" data-id="${act.id}" title="Update completion status">
                            <option value="not_started" ${act.status === 'not_started' ? 'selected' : ''}>Not Started</option>
                            <option value="in_progress" ${act.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                            <option value="completed" ${act.status === 'completed' ? 'selected' : ''}>Completed</option>
                            <option value="skipped" ${act.status === 'skipped' ? 'selected' : ''}>Skipped</option>
                            <option value="rescheduled" ${act.status === 'rescheduled' ? 'selected' : ''}>Rescheduled</option>
                        </select>
                        <div class="timeline-btn-group">
                            ${!act.is_fixed && isMissedOrSkipped ? `
                                <button class="btn-sm btn-ghost btn-resched" data-id="${act.id}" title="Reschedule to next available slot">
                                    🔄 Reschedule
                                </button>
                            ` : ''}
                            <button class="btn-sm btn-ghost btn-act-edit" data-id="${act.id}" title="Edit activity">✏️</button>
                            <button class="btn-sm btn-ghost btn-act-delete" data-id="${act.id}" title="Delete activity">🗑️</button>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        // Attach event listeners to status dropdowns
        routineTimeline.querySelectorAll(".status-dropdown").forEach(sel => {
            sel.addEventListener("change", (e) => {
                const actId = parseInt(e.target.dataset.id, 10);
                const newStatus = e.target.value;
                updateActivityStatus(actId, newStatus);
            });
        });

        // Attach edit buttons
        routineTimeline.querySelectorAll(".btn-act-edit").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const actId = parseInt(e.currentTarget.dataset.id, 10);
                const act = activities.find(a => a.id === actId);
                if (act) openActivityModal(act);
            });
        });

        // Attach delete buttons
        routineTimeline.querySelectorAll(".btn-act-delete").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const actId = parseInt(e.currentTarget.dataset.id, 10);
                deleteActivity(actId);
            });
        });

        // Attach reschedule buttons
        routineTimeline.querySelectorAll(".btn-resched").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const actId = parseInt(e.currentTarget.dataset.id, 10);
                rescheduleActivity(actId);
            });
        });
    }

    function calculateDurationStr(s, e) {
        try {
            const p1 = s.split(":");
            const p2 = e.split(":");
            const mins = (parseInt(p2[0], 10) * 60 + parseInt(p2[1], 10)) - (parseInt(p1[0], 10) * 60 + parseInt(p1[1], 10));
            if (mins >= 60) {
                const h = Math.floor(mins / 60);
                const m = mins % 60;
                return m > 0 ? `${h}h ${m}m` : `${h}h`;
            }
            return `${mins}m`;
        } catch (_) {
            return "";
        }
    }

    async function updateActivityStatus(activityId, status) {
        try {
            const res = await fetch(`/api/routine/activity/${activityId}/status`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: status }),
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            loadSchedule(selectedRoutineDate);
        } catch (err) {
            console.error("Failed to update activity status:", err);
            alert(`Could not update status: ${err.message}`);
        }
    }

    async function rescheduleActivity(activityId) {
        try {
            const res = await fetch(`/api/routine/reschedule/${activityId}`, {
                method: "POST",
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);

            const newAct = data.new_activity;
            alert(`Activity rescheduled to ${newAct.date} from ${newAct.start_time} to ${newAct.end_time}.`);
            loadSchedule(selectedRoutineDate);
        } catch (err) {
            console.error("Reschedule failed:", err);
            alert(`Reschedule failed: ${err.message}`);
        }
    }

    async function deleteActivity(activityId) {
        if (!confirm("Are you sure you want to remove this activity from the schedule?")) return;
        try {
            const res = await fetch(`/api/routine/activity/${activityId}`, {
                method: "DELETE",
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            loadSchedule(selectedRoutineDate);
        } catch (err) {
            console.error("Delete failed:", err);
            alert(`Delete failed: ${err.message}`);
        }
    }

    // Modal Operations
    function openActivityModal(act = null) {
        if (!activityModal) return;
        if (act) {
            actModalTitle.textContent = "Edit Scheduled Activity";
            editActId.value = act.id;
            actName.value = act.name;
            actStartTime.value = act.start_time;
            actEndTime.value = act.end_time;
            actCategory.value = act.category;
            actPriority.value = act.priority;
            actNotes.value = act.notes || "";
            actFixed.checked = !!act.is_fixed;
        } else {
            actModalTitle.textContent = "Add New Scheduled Activity";
            editActId.value = "";
            actName.value = "";
            actStartTime.value = "09:00";
            actEndTime.value = "10:00";
            actCategory.value = "routine";
            actPriority.value = "medium";
            actNotes.value = "";
            actFixed.checked = false;
        }
        activityModal.classList.add("active");
    }

    function closeActivityModal() {
        if (activityModal) activityModal.classList.remove("active");
    }

    if (btnAddActivity) btnAddActivity.addEventListener("click", () => openActivityModal());
    if (btnCloseActModal) btnCloseActModal.addEventListener("click", closeActivityModal);
    if (btnCancelActModal) btnCancelActModal.addEventListener("click", closeActivityModal);

    if (btnSaveActivity) {
        btnSaveActivity.addEventListener("click", async () => {
            const name = actName.value.trim();
            const start = actStartTime.value.trim();
            const end = actEndTime.value.trim();
            if (!name || !start || !end) {
                alert("Please provide activity name, start time, and end time.");
                return;
            }

            const id = editActId.value;
            const payload = {
                name: name,
                start_time: start,
                end_time: end,
                target_date: selectedRoutineDate,
                category: actCategory.value,
                priority: actPriority.value,
                notes: actNotes.value.trim(),
                is_fixed: actFixed.checked,
            };

            try {
                let res;
                if (id) {
                    res = await fetch(`/api/routine/activity/${id}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                } else {
                    res = await fetch("/api/routine/activity", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                }

                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.detail || `HTTP ${res.status}`);
                }

                closeActivityModal();
                loadSchedule(selectedRoutineDate);
            } catch (err) {
                console.error("Save activity failed:", err);
                alert(`Failed to save activity: ${err.message}`);
            }
        });
    }

    // Evening Daily Review Debrief Modal
    if (btnGenerateReview) {
        btnGenerateReview.addEventListener("click", () => openDailyReviewModal(selectedRoutineDate));
    }
    if (btnCloseReviewModal) btnCloseReviewModal.addEventListener("click", () => reviewModal.classList.remove("active"));
    if (btnCloseReviewFooter) btnCloseReviewFooter.addEventListener("click", () => reviewModal.classList.remove("active"));

    async function openDailyReviewModal(dateStr) {
        if (!reviewModal || !reviewModalBody) return;
        reviewModalBody.innerHTML = `<div style="text-align: center; padding: 20px;">Generating comprehensive debrief...</div>`;
        reviewModal.classList.add("active");

        try {
            const res = await fetch(`/api/routine/review?date=${dateStr}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const completedPills = (data.completed_activities || []).map(name =>
                `<span class="review-pill completed">✓ ${escapeHtml(name)}</span>`
            ).join("") || '<span style="color: var(--text-muted); font-size: 0.8rem;">None recorded yet</span>';

            const outstandingPills = (data.outstanding_tasks || []).map(t =>
                `<span class="review-pill outstanding">⏳ ${escapeHtml(t.name)} (${t.time})</span>`
            ).join("") || '<span style="color: var(--text-muted); font-size: 0.8rem;">All tasks completed!</span>';

            const suggestionsItems = (data.suggestions || []).map(s =>
                `<li>${escapeHtml(s)}</li>`
            ).join("") || '<li>Maintain your established rhythm tomorrow.</li>';

            reviewModalBody.innerHTML = `
                <div class="review-summary-box">
                    <div>
                        <div class="review-comp-badge">${data.completion_rate_percent}%</div>
                        <div class="review-meta-item">${data.completed_count} of ${data.total_planned} activities completed</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.95rem; font-weight: 600; color: #60a5fa;">Coding: ${data.coding_hours}h</div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #c084fc;">Study: ${data.study_hours}h</div>
                        <div class="review-meta-item">Date: ${data.date}</div>
                    </div>
                </div>

                <div class="review-block">
                    <h4>Completed Activities</h4>
                    <div class="review-pill-list">${completedPills}</div>
                </div>

                <div class="review-block">
                    <h4>Outstanding / Unfinished Tasks</h4>
                    <div class="review-pill-list">${outstandingPills}</div>
                </div>

                <div class="review-block">
                    <h4>NOUS Strategic Suggestions for Tomorrow</h4>
                    <ul class="review-suggestions-list">${suggestionsItems}</ul>
                </div>
            `;
        } catch (err) {
            reviewModalBody.innerHTML = `<div class="empty-state">Error generating review: ${err.message}</div>`;
        }
    }

    // Hook auto-speak into text chat sendMessage if enabled
    const originalSendMessage = sendMessage;

    // ==============================================================
    // EMAIL INTELLIGENCE & COMMUNICATIONS (PHASE 8)
    // ==============================================================
    async function checkEmailAuth() {
        if (!emailOAuthDot || !emailOAuthText) return;
        try {
            const res = await fetch("/api/email/auth/status");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (data.is_authenticated && data.connected_account) {
                emailOAuthDot.className = "status-dot dot-online";
                emailOAuthText.textContent = `Connected: ${data.connected_account}`;
                if (btnEmailAuthAction) {
                    btnEmailAuthAction.textContent = "Disconnect";
                    btnEmailAuthAction.onclick = disconnectEmailAuth;
                }
            } else {
                emailOAuthDot.className = "status-dot dot-checking";
                emailOAuthText.textContent = "Demo Mailbox (Offline Mode)";
                if (btnEmailAuthAction) {
                    btnEmailAuthAction.textContent = "Connect Gmail";
                    btnEmailAuthAction.onclick = initiateEmailOAuth;
                }
            }
        } catch (err) {
            console.warn("Could not check email auth status:", err);
            if (emailOAuthText) emailOAuthText.textContent = "Mailbox Offline";
        }
    }

    async function initiateEmailOAuth() {
        try {
            const res = await fetch("/api/email/auth/url");
            const data = await res.json();
            if (data.configured && data.url) {
                window.location.href = data.url;
            } else {
                alert(
                    "Google OAuth setup notice:\n\n" +
                    "To connect your live Gmail mailbox, configure GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env.\n\n" +
                    "For now, NOUS is running in fully-functional Demonstration Mailbox mode with academic and project emails!"
                );
            }
        } catch (err) {
            alert(`OAuth error: ${err.message}`);
        }
    }

    async function disconnectEmailAuth() {
        if (!confirm("Are you sure you want to unlink your Google account?")) return;
        try {
            await fetch("/api/email/auth/disconnect", { method: "POST" });
            checkEmailAuth();
            loadEmails();
        } catch (err) {
            console.error("Disconnect error:", err);
        }
    }

    // Category Tabs
    emailCategoryTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            emailCategoryTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeEmailCategory = tab.dataset.cat || "";
            loadEmails();
        });
    });

    // Search input debouncer
    if (emailSearchInput) {
        emailSearchInput.addEventListener("input", (e) => {
            clearTimeout(emailSearchTimeout);
            emailSearchTimeout = setTimeout(() => {
                activeEmailSearch = e.target.value.trim();
                loadEmails();
            }, 300);
        });
    }

    if (btnEmailDeadlinesFilter) {
        btnEmailDeadlinesFilter.addEventListener("click", () => {
            loadEmails(true);
        });
    }

    if (btnEmailBriefing) {
        btnEmailBriefing.addEventListener("click", openEmailBriefingModal);
    }

    async function loadEmails(filterDeadlinesOnly = false) {
        try {
            let url = `/api/email/messages?limit=25`;
            if (activeEmailCategory) {
                url += `&category=${activeEmailCategory}`;
            }
            if (activeEmailSearch) {
                url += `&search=${encodeURIComponent(activeEmailSearch)}`;
            }

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            let emails = data.messages || [];

            if (filterDeadlinesOnly) {
                emails = emails.filter(e => e.detected_deadlines && e.detected_deadlines.length > 0);
            }

            // Update badge
            if (emailCountBadge) {
                emailCountBadge.textContent = emails.length;
            }

            updateEmailRibbonStats();
            renderEmails(emails);
        } catch (err) {
            console.error("Error loading emails:", err);
            if (emailMessagesList) {
                emailMessagesList.innerHTML = `<div class="empty-state">Failed to load emails: ${err.message}</div>`;
            }
        }
    }

    async function updateEmailRibbonStats() {
        try {
            const res = await fetch("/api/email/summary");
            if (!res.ok) return;
            const summary = await res.json();

            if (statEmailUnread) statEmailUnread.textContent = summary.unread_count || 0;
            if (statEmailUrgent) statEmailUrgent.textContent = summary.urgent_count || 0;
            if (statEmailDeadlines) statEmailDeadlines.textContent = (summary.deadlines_detected || []).length;
            if (statEmailReplies) statEmailReplies.textContent = summary.requires_response_count || 0;
        } catch (_) {}
    }

    function renderEmails(emails) {
        if (!emailMessagesList) return;

        if (emails.length === 0) {
            emailMessagesList.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 8px;">📬</div>
                    <p>No emails match the selected filter.</p>
                </div>
            `;
            return;
        }

        emailMessagesList.innerHTML = emails.map(e => {
            const initial = (e.sender_name || e.sender || "?")[0].toUpperCase();
            const unreadClass = e.is_unread ? "unread" : "";
            const urgentClass = e.is_urgent ? "urgent" : "";
            const injectionClass = e.is_suspicious_injection ? "suspicious-injection" : "";

            const deadlinesBadges = (e.detected_deadlines || []).map(d =>
                `<span class="badge-pill badge-deadline">⏳ Deadline: ${escapeHtml(d)}</span>`
            ).join("");

            const meetingBadge = e.has_meeting_invite ? `<span class="badge-pill badge-meeting">📅 Meeting Invite</span>` : "";
            const replyBadge = e.requires_response ? `<span class="badge-pill badge-reply-needed">💬 Reply Needed</span>` : "";
            const injectionBadge = e.is_suspicious_injection ? `<span class="badge-pill badge-injection-warning">⚠️ PROMPT INJECTION DETECTED</span>` : "";

            return `
                <div class="email-card ${unreadClass} ${urgentClass} ${injectionClass}" data-id="${e.id}">
                    <div class="email-card-header">
                        <div class="email-sender-info">
                            <div class="email-sender-avatar">${initial}</div>
                            <div>
                                <div class="email-sender-name">${escapeHtml(e.sender_name)}</div>
                                <div style="font-size: 0.72rem; color: var(--text-muted);">${escapeHtml(e.sender)}</div>
                            </div>
                        </div>
                        <div class="email-date">${escapeHtml(e.date)}</div>
                    </div>
                    <div class="email-subject-line">${escapeHtml(e.subject)}</div>
                    <div class="email-snippet-text">${escapeHtml(e.snippet)}</div>
                    <div class="email-badges-row">
                        <span class="category-tag category-${e.category}">${e.category}</span>
                        ${deadlinesBadges}
                        ${meetingBadge}
                        ${replyBadge}
                        ${injectionBadge}
                    </div>
                    <div class="email-card-actions">
                        <button class="btn-sm btn-ghost btn-view-email" data-id="${e.id}">View Details</button>
                        <button class="btn-sm btn-outline btn-draft-email" data-id="${e.id}">Draft Reply</button>
                    </div>
                </div>
            `;
        }).join("");

        emailMessagesList.querySelectorAll(".btn-view-email").forEach(btn => {
            btn.addEventListener("click", () => {
                const eid = btn.dataset.id;
                const email = emails.find(x => x.id === eid);
                if (email) openEmailDetailModal(email);
            });
        });

        emailMessagesList.querySelectorAll(".btn-draft-email").forEach(btn => {
            btn.addEventListener("click", () => {
                const eid = btn.dataset.id;
                const email = emails.find(x => x.id === eid);
                if (email) openEmailDraftModal(email);
            });
        });
    }

    function openEmailDetailModal(email) {
        if (!emailDetailModal || !emailModalBody) return;
        currentViewingEmail = email;

        emailModalSubject.textContent = email.subject;

        const warningBox = email.is_suspicious_injection ? `
            <div style="background: rgba(239, 68, 68, 0.15); border: 1px solid #ef4444; border-radius: var(--radius-sm); padding: 12px; margin-bottom: 14px; color: #fca5a5; font-size: 0.82rem;">
                <strong>⚠️ Prompt Injection Warning:</strong> The email body contained suspicious instructions:
                <ul style="margin: 4px 0 0 16px;">
                    ${(email.suspicious_reasons || []).map(r => `<li>${escapeHtml(r)}</li>`).join("")}
                </ul>
                NOUS isolated and sanitized this text to protect your memories and system policies.
            </div>
        ` : "";

        const deadlinesSection = (email.detected_deadlines || []).length > 0 ? `
            <div style="margin-bottom: 12px; padding: 8px 12px; background: rgba(245, 158, 11, 0.1); border-radius: var(--radius-sm); border-left: 3px solid #f59e0b;">
                <strong style="color: #fbbf24; font-size: 0.82rem;">Detected Deadlines:</strong>
                <span style="font-size: 0.82rem; color: var(--text-primary); margin-left: 6px;">
                    ${email.detected_deadlines.map(d => escapeHtml(d)).join(", ")}
                </span>
            </div>
        ` : "";

        const actionsSection = (email.action_items || []).length > 0 ? `
            <div style="margin-bottom: 12px;">
                <strong style="font-size: 0.82rem; color: var(--text-muted);">Extracted Action Items:</strong>
                <ul style="margin: 4px 0 0 18px; font-size: 0.82rem; color: var(--text-primary);">
                    ${email.action_items.map(a => `<li>${escapeHtml(a)}</li>`).join("")}
                </ul>
            </div>
        ` : "";

        emailModalBody.innerHTML = `
            ${warningBox}
            <div style="display: flex; justify-content: space-between; margin-bottom: 12px; font-size: 0.82rem; color: var(--text-muted); border-bottom: 1px solid var(--border-color); padding-bottom: 8px;">
                <div><strong>From:</strong> ${escapeHtml(email.sender)}</div>
                <div>${escapeHtml(email.date)}</div>
            </div>
            ${deadlinesSection}
            ${actionsSection}
            <div style="margin-top: 14px;">
                <strong style="font-size: 0.84rem; color: var(--text-muted);">Sanitized Email Body:</strong>
                <pre style="white-space: pre-wrap; font-family: var(--font-main); font-size: 0.84rem; line-height: 1.6; color: var(--text-primary); background: var(--bg-secondary); padding: 14px; border-radius: var(--radius-sm); border: 1px solid var(--border-color); margin-top: 6px;">${escapeHtml(email.body)}</pre>
            </div>
        `;

        emailDetailModal.classList.add("active");
    }

    if (btnCloseEmailModal) btnCloseEmailModal.addEventListener("click", () => emailDetailModal.classList.remove("active"));
    if (btnCloseEmailFooter) btnCloseEmailFooter.addEventListener("click", () => emailDetailModal.classList.remove("active"));
    if (btnOpenDraftFromDetail) {
        btnOpenDraftFromDetail.addEventListener("click", () => {
            emailDetailModal.classList.remove("active");
            if (currentViewingEmail) openEmailDraftModal(currentViewingEmail);
        });
    }

    // Draft Modal Operations
    function openEmailDraftModal(replyToEmail = null) {
        if (!emailDraftModal) return;
        if (replyToEmail) {
            draftReplyToId.value = replyToEmail.id;
            draftTo.value = replyToEmail.sender;
            draftSubject.value = replyToEmail.subject.startsWith("Re:") ? replyToEmail.subject : `Re: ${replyToEmail.subject}`;
            draftBody.value = `Hi ${replyToEmail.sender_name},\n\nThank you for your email.\n\n\nBest regards,\n`;
        } else {
            draftReplyToId.value = "";
            draftTo.value = "";
            draftSubject.value = "";
            draftBody.value = "";
        }
        draftConfirmCheck.checked = false;
        emailDraftModal.classList.add("active");
    }

    if (btnCloseDraftModal) btnCloseDraftModal.addEventListener("click", () => emailDraftModal.classList.remove("active"));
    if (btnCancelDraft) btnCancelDraft.addEventListener("click", () => emailDraftModal.classList.remove("active"));

    if (btnSaveDraftOnly) {
        btnSaveDraftOnly.addEventListener("click", async () => {
            const to = draftTo.value.trim();
            const subj = draftSubject.value.trim();
            const body = draftBody.value.trim();
            if (!to || !subj || !body) {
                alert("Please fill in recipient, subject, and body.");
                return;
            }

            try {
                const res = await fetch("/api/email/draft", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        to_email: to,
                        subject: subj,
                        body: body,
                        reply_to_id: draftReplyToId.value || null,
                    }),
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                alert("Draft saved in 'pending_approval' state.");
                emailDraftModal.classList.remove("active");
                updateEmailRibbonStats();
            } catch (err) {
                alert(`Error saving draft: ${err.message}`);
            }
        });
    }

    if (btnSendDraft) {
        btnSendDraft.addEventListener("click", async () => {
            if (!draftConfirmCheck.checked) {
                alert("Security Requirement: You must check 'Strict Approval: I confirm and authorize NOUS to send this email' before dispatching.");
                return;
            }

            const to = draftTo.value.trim();
            const subj = draftSubject.value.trim();
            const body = draftBody.value.trim();
            if (!to || !subj || !body) {
                alert("Please fill in recipient, subject, and body.");
                return;
            }

            try {
                const draftRes = await fetch("/api/email/draft", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        to_email: to,
                        subject: subj,
                        body: body,
                        reply_to_id: draftReplyToId.value || null,
                    }),
                });
                const draftData = await draftRes.json();
                const draftId = draftData.draft.id;

                const sendRes = await fetch(`/api/email/send/${draftId}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ user_confirmed: true }),
                });

                if (!sendRes.ok) {
                    const err = await sendRes.json();
                    throw new Error(err.detail || `HTTP ${sendRes.status}`);
                }

                alert(`Email successfully dispatched to ${to}!`);
                emailDraftModal.classList.remove("active");
                updateEmailRibbonStats();
            } catch (err) {
                console.error("Send email error:", err);
                alert(`Failed to send email: ${err.message}`);
            }
        });
    }

    // Inbox Briefing Modal Operations
    async function openEmailBriefingModal() {
        if (!emailBriefingModal || !emailBriefingBody) return;
        emailBriefingBody.innerHTML = `<div style="text-align: center; padding: 20px;">Generating Executive Inbox Briefing...</div>`;
        emailBriefingModal.classList.add("active");

        try {
            const res = await fetch("/api/email/summary");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const prioritiesHtml = (data.top_priorities || []).map(p => `
                <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 10px 14px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="font-size: 0.88rem; color: var(--text-primary);">${escapeHtml(p.subject)}</strong>
                        <span class="category-tag category-${p.category}">${p.category}</span>
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 2px;">From: ${escapeHtml(p.sender)}</div>
                    ${(p.action_items || []).length > 0 ? `
                        <div style="font-size: 0.78rem; color: #38bdf8; margin-top: 4px;">Action: ${escapeHtml(p.action_items[0])}</div>
                    ` : ''}
                </div>
            `).join("") || '<p style="font-size: 0.82rem; color: var(--text-muted);">No critical priorities today.</p>';

            const deadlinesHtml = (data.deadlines_detected || []).map(d => `
                <div style="font-size: 0.82rem; color: #fbbf24; margin-bottom: 4px;">
                    ⏳ <strong>${escapeHtml(d.subject)}</strong>: ${d.deadlines.map(x => escapeHtml(x)).join(", ")}
                </div>
            `).join("") || '<p style="font-size: 0.82rem; color: var(--text-muted);">No impending deadlines detected.</p>';

            emailBriefingBody.innerHTML = `
                <div class="review-summary-box" style="margin-bottom: 16px;">
                    <div>
                        <div class="review-comp-badge">${data.unread_count}</div>
                        <div class="review-meta-item">Unread messages in inbox (${data.total_emails} total)</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.95rem; font-weight: 600; color: #f87171;">Urgent: ${data.urgent_count}</div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #c084fc;">Replies Needed: ${data.requires_response_count}</div>
                    </div>
                </div>

                <div class="review-block">
                    <h4>Top Priority Attention Items</h4>
                    ${prioritiesHtml}
                </div>

                <div class="review-block">
                    <h4>Impending Deadlines Extracted from Mail</h4>
                    ${deadlinesHtml}
                </div>
            `;
        } catch (err) {
            emailBriefingBody.innerHTML = `<div class="empty-state">Error generating briefing: ${err.message}</div>`;
        }
    }

    if (btnCloseBriefingModal) btnCloseBriefingModal.addEventListener("click", () => emailBriefingModal.classList.remove("active"));
    if (btnCloseBriefingFooter) btnCloseBriefingFooter.addEventListener("click", () => emailBriefingModal.classList.remove("active"));

    // ==============================================================
    // PROJECT INTELLIGENCE & GITHUB TELEMETRY (PHASE 9)
    // ==============================================================
    let activeProjectStatus = "";

    projectStatusTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            projectStatusTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeProjectStatus = tab.dataset.status || "";
            loadProjects();
        });
    });

    if (btnSyncGithub) {
        btnSyncGithub.addEventListener("click", () => {
            loadGithubTelemetry();
            loadProjects();
        });
    }

    if (btnInactivityAudit) {
        btnInactivityAudit.addEventListener("click", openInactivityAuditModal);
    }

    async function loadProjects() {
        try {
            let url = `/api/projects`;
            if (activeProjectStatus) {
                url += `?status=${activeProjectStatus}`;
            }

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const projects = data.projects || [];

            if (projectsCountBadge) {
                projectsCountBadge.textContent = projects.length;
            }

            updateProjectsRibbonStats();
            renderProjects(projects);
        } catch (err) {
            console.error("Error loading projects:", err);
            if (projectsListContainer) {
                projectsListContainer.innerHTML = `<div class="empty-state">Failed to load projects: ${err.message}</div>`;
            }
        }
    }

    async function updateProjectsRibbonStats() {
        try {
            const res = await fetch("/api/projects/health");
            if (!res.ok) return;
            const health = await res.json();

            if (statProjActive) statProjActive.textContent = health.active_projects || 0;
            if (statProjDeadlines) statProjDeadlines.textContent = health.upcoming_deadlines_count || 0;
            if (statProjInactive) statProjInactive.textContent = health.inactive_projects_count || 0;

            let totalM = 0;
            let compM = 0;
            (health.projects || []).forEach(p => {
                totalM += p.milestones_count || 0;
                compM += Math.round((p.milestones_count || 0) * (p.progress_percent / 100));
            });
            const overallPct = totalM > 0 ? Math.round((compM / totalM) * 100) : 0;
            if (statProjMilestones) statProjMilestones.textContent = `${overallPct}%`;

            if (projectsInactivityBanner && inactivityBannerText) {
                if (health.inactive_projects_count > 0 && health.inactive_projects.length > 0) {
                    projectsInactivityBanner.style.display = "flex";
                    const idleNames = health.inactive_projects.map(p => p.name).join(", ");
                    inactivityBannerText.textContent = `Stale repository notice: ${idleNames} (no commits in > 7 days).`;
                } else {
                    projectsInactivityBanner.style.display = "none";
                }
            }
        } catch (_) {}
    }

    function renderProjects(projects) {
        if (!projectsListContainer) return;

        if (projects.length === 0) {
            projectsListContainer.innerHTML = `
                <div class="empty-state" style="text-align: center; padding: 40px 20px; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 8px;">🚀</div>
                    <p>No projects match the selected filter.</p>
                    <button class="btn-sm btn-outline" style="margin-top: 10px;" onclick="document.getElementById('btn-add-project').click()">+ Track New Project</button>
                </div>
            `;
            return;
        }

        projectsListContainer.innerHTML = projects.map(p => {
            const techBadges = (p.tech_stack || "").split(",")
                .map(t => t.trim())
                .filter(t => t)
                .map(t => `<span class="tech-tag">${escapeHtml(t)}</span>`)
                .join("");

            const milestonesHtml = (p.milestones || []).map(m => `
                <div class="milestone-row" data-mid="${m.id}">
                    <label class="milestone-left">
                        <input type="checkbox" class="milestone-check" data-pid="${p.id}" data-mid="${m.id}" ${m.is_completed ? 'checked' : ''}>
                        <span class="milestone-title-text ${m.is_completed ? 'milestone-completed' : ''}">${escapeHtml(m.title)}</span>
                    </label>
                    ${m.due_date ? `<span class="milestone-due-tag">Due ${escapeHtml(m.due_date)}</span>` : ''}
                </div>
            `).join("") || '<p style="font-size: 0.74rem; color: var(--text-muted);">No milestones configured yet.</p>';

            return `
                <div class="project-card" data-id="${p.id}">
                    <div class="project-card-header">
                        <div>
                            <div class="project-name">${escapeHtml(p.name)}</div>
                            <div class="project-desc">${escapeHtml(p.description)}</div>
                        </div>
                        <span class="priority-tag priority-${p.priority}">${p.priority}</span>
                    </div>

                    <div class="project-progress-wrapper">
                        <div class="progress-header">
                            <span>Delivery Progress</span>
                            <span class="progress-pct">${p.progress_percent}%</span>
                        </div>
                        <div class="progress-bar-bg">
                            <div class="progress-bar-fill" style="width: ${p.progress_percent}%;"></div>
                        </div>
                    </div>

                    ${techBadges ? `<div class="tech-stack-row">${techBadges}</div>` : ''}

                    <div class="milestones-box">
                        <div class="milestones-box-title">
                            <span>Milestones (${(p.milestones || []).filter(m => m.is_completed).length} / ${(p.milestones || []).length})</span>
                            <button class="btn-sm btn-ghost btn-add-ms" data-pid="${p.id}" title="Add deliverable milestone" style="padding: 2px 6px; font-size: 0.72rem;">+ Milestone</button>
                        </div>
                        <div class="milestones-list">${milestonesHtml}</div>
                    </div>

                    <div class="project-card-footer">
                        <span>Status: <strong style="color: var(--text-primary);">${p.status}</strong></span>
                        <span>Deadline: <strong style="color: #fbbf24;">${p.deadline || 'Flexible'}</strong></span>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn-sm btn-ghost btn-edit-proj" data-id="${p.id}">Edit</button>
                            <button class="btn-sm btn-ghost btn-del-proj" data-id="${p.id}">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }).join("");

        projectsListContainer.querySelectorAll(".milestone-check").forEach(chk => {
            chk.addEventListener("change", async (e) => {
                const pid = e.target.dataset.pid;
                const mid = e.target.dataset.mid;
                await toggleMilestone(pid, mid);
            });
        });

        projectsListContainer.querySelectorAll(".btn-add-ms").forEach(btn => {
            btn.addEventListener("click", () => {
                const pid = btn.dataset.pid;
                openMilestoneModal(pid);
            });
        });

        projectsListContainer.querySelectorAll(".btn-edit-proj").forEach(btn => {
            btn.addEventListener("click", () => {
                const pid = parseInt(btn.dataset.id, 10);
                const proj = projects.find(p => p.id === pid);
                if (proj) openProjectModal(proj);
            });
        });

        projectsListContainer.querySelectorAll(".btn-del-proj").forEach(btn => {
            btn.addEventListener("click", () => {
                const pid = parseInt(btn.dataset.id, 10);
                deleteProject(pid);
            });
        });
    }

    async function toggleMilestone(projectId, milestoneId) {
        try {
            const res = await fetch(`/api/projects/${projectId}/milestones/${milestoneId}/toggle`, {
                method: "PATCH",
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            loadProjects();
        } catch (err) {
            console.error("Milestone toggle error:", err);
            alert(`Could not toggle milestone: ${err.message}`);
        }
    }

    async function loadGithubTelemetry() {
        if (!githubCommitsList || !githubPrsList || !githubIssuesList) return;

        try {
            const res = await fetch("/api/projects/github/activity");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (githubRepoLabel) githubRepoLabel.textContent = data.repository;
            if (githubSyncTime) githubSyncTime.textContent = data.is_live ? "Live Sync" : "Local Telemetry";

            githubCommitsList.innerHTML = (data.recent_commits || []).map(c => `
                <div class="telemetry-item">
                    <div class="telemetry-commit-top">
                        <span class="sha-badge">${escapeHtml(c.sha)}</span>
                        <span class="commit-author">${escapeHtml(c.author)}</span>
                    </div>
                    <div class="commit-msg">${escapeHtml(c.message)}</div>
                </div>
            `).join("") || '<p style="font-size: 0.76rem; color: var(--text-muted);">No commits found.</p>';

            githubPrsList.innerHTML = (data.open_pull_requests || []).map(p => `
                <div class="telemetry-item">
                    <div class="pr-item-title">#${p.number} ${escapeHtml(p.title)}</div>
                    <div class="pr-item-meta">
                        <span>by ${escapeHtml(p.author)}</span>
                        <span style="color: #38bdf8;">${escapeHtml(p.state)}</span>
                    </div>
                </div>
            `).join("") || '<p style="font-size: 0.76rem; color: var(--text-muted);">No open PRs.</p>';

            githubIssuesList.innerHTML = (data.open_issues || []).map(i => `
                <div class="telemetry-item">
                    <div class="pr-item-title">#${i.number} ${escapeHtml(i.title)}</div>
                    <div class="pr-item-meta">
                        ${(i.labels || []).map(l => `<span class="category-tag category-coding">${escapeHtml(l)}</span>`).join("")}
                    </div>
                </div>
            `).join("") || '<p style="font-size: 0.76rem; color: var(--text-muted);">No open issues.</p>';

        } catch (err) {
            console.warn("Could not load GitHub telemetry:", err);
        }
    }

    function openProjectModal(proj = null) {
        if (!projectModal) return;
        if (proj) {
            projectModalTitle.textContent = "Edit Project";
            editProjId.value = proj.id;
            projName.value = proj.name;
            projDescription.value = proj.description || "";
            projTechStack.value = proj.tech_stack || "";
            projRepoUrl.value = proj.repo_url || "";
            projDeadline.value = proj.deadline || "";
            projPriority.value = proj.priority || "medium";
            projStatus.value = proj.status || "active";
        } else {
            projectModalTitle.textContent = "Add New Project";
            editProjId.value = "";
            projName.value = "";
            projDescription.value = "";
            projTechStack.value = "";
            projRepoUrl.value = "";
            projDeadline.value = "";
            projPriority.value = "medium";
            projStatus.value = "active";
        }
        projectModal.classList.add("active");
    }

    function closeProjectModal() {
        if (projectModal) projectModal.classList.remove("active");
    }

    if (btnAddProject) btnAddProject.addEventListener("click", () => openProjectModal());
    if (btnCloseProjectModal) btnCloseProjectModal.addEventListener("click", closeProjectModal);
    if (btnCancelProjectModal) btnCancelProjectModal.addEventListener("click", closeProjectModal);

    if (btnSaveProject) {
        btnSaveProject.addEventListener("click", async () => {
            const name = projName.value.trim();
            if (!name) {
                alert("Please enter a project name.");
                return;
            }

            const id = editProjId.value;
            const payload = {
                name: name,
                description: projDescription.value.trim(),
                tech_stack: projTechStack.value.trim(),
                repo_url: projRepoUrl.value.trim(),
                deadline: projDeadline.value,
                priority: projPriority.value,
                status: projStatus.value,
            };

            try {
                let res;
                if (id) {
                    res = await fetch(`/api/projects/${id}`, {
                        method: "PUT",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                } else {
                    res = await fetch("/api/projects", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                }

                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                closeProjectModal();
                loadProjects();
            } catch (err) {
                alert(`Error saving project: ${err.message}`);
            }
        });
    }

    async function deleteProject(id) {
        if (!confirm("Are you sure you want to delete this project and all its milestones?")) return;
        try {
            const res = await fetch(`/api/projects/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            loadProjects();
        } catch (err) {
            alert(`Error deleting project: ${err.message}`);
        }
    }

    function openMilestoneModal(projectId) {
        if (!milestoneModal) return;
        milestoneProjId.value = projectId;
        milestoneTitle.value = "";
        milestoneDueDate.value = "";
        milestoneNotes.value = "";
        milestoneModal.classList.add("active");
    }

    function closeMilestoneModal() {
        if (milestoneModal) milestoneModal.classList.remove("active");
    }

    if (btnCloseMilestoneModal) btnCloseMilestoneModal.addEventListener("click", closeMilestoneModal);
    if (btnCancelMilestone) btnCancelMilestone.addEventListener("click", closeMilestoneModal);

    if (btnSaveMilestone) {
        btnSaveMilestone.addEventListener("click", async () => {
            const pid = milestoneProjId.value;
            const title = milestoneTitle.value.trim();
            if (!title) {
                alert("Please enter a milestone title.");
                return;
            }

            try {
                const res = await fetch(`/api/projects/${pid}/milestones`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: title,
                        due_date: milestoneDueDate.value || "",
                        notes: milestoneNotes.value.trim(),
                    }),
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                closeMilestoneModal();
                loadProjects();
            } catch (err) {
                alert(`Error adding milestone: ${err.message}`);
            }
        });
    }

    async function openInactivityAuditModal() {
        if (!inactivityAuditModal || !inactivityAuditBody) return;
        inactivityAuditBody.innerHTML = `<div style="text-align: center; padding: 20px;">Auditing repository velocity...</div>`;
        inactivityAuditModal.classList.add("active");

        try {
            const res = await fetch("/api/projects/health");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            const inactiveList = (data.inactive_projects || []).map(p => `
                <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 12px 14px; margin-bottom: 10px; border-left: 3px solid #f59e0b;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: var(--text-primary); font-size: 0.9rem;">${escapeHtml(p.name)}</strong>
                        <span style="font-size: 0.72rem; color: #fbbf24; font-weight: 600;">Idle for ${p.days_inactive} days</span>
                    </div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 4px;">Last Updated: ${escapeHtml(p.last_updated)}</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-top: 6px; font-style: italic;">
                        💡 ${escapeHtml(p.suggestion)}
                    </div>
                </div>
            `).join("") || '<p style="color: #34d399; font-size: 0.85rem;">✓ All tracked projects have active commits within the last 7 days.</p>';

            const deadlinesList = (data.upcoming_deadlines || []).map(d => `
                <div style="font-size: 0.82rem; color: #38bdf8; margin-bottom: 6px;">
                    🎯 <strong>${escapeHtml(d.due_date)}</strong>: ${escapeHtml(d.title)} (${escapeHtml(d.project_name)})
                </div>
            `).join("") || '<p style="color: var(--text-muted); font-size: 0.82rem;">No impending deadlines in the next 14 days.</p>';

            inactivityAuditBody.innerHTML = `
                <div class="review-summary-box" style="margin-bottom: 16px;">
                    <div>
                        <div class="review-comp-badge">${data.inactive_projects_count}</div>
                        <div class="review-meta-item">Stale or idle repositories detected (&gt; 7 days)</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.95rem; font-weight: 600; color: #38bdf8;">Active Projects: ${data.active_projects}</div>
                        <div style="font-size: 0.95rem; font-weight: 600; color: #fbbf24;">Upcoming Deadlines: ${data.upcoming_deadlines_count}</div>
                    </div>
                </div>

                <div class="review-block">
                    <h4>Stale & Inactive Codebases</h4>
                    ${inactiveList}
                </div>

                <div class="review-block">
                    <h4>Upcoming 14-Day Delivery Deadlines</h4>
                    ${deadlinesList}
                </div>
            `;
        } catch (err) {
            inactivityAuditBody.innerHTML = `<div class="empty-state">Error running audit: ${err.message}</div>`;
        }
    }

    if (btnCloseAuditModal) btnCloseAuditModal.addEventListener("click", () => inactivityAuditModal.classList.remove("active"));
    if (btnCloseAuditFooter) btnCloseAuditFooter.addEventListener("click", () => inactivityAuditModal.classList.remove("active"));

    // ==============================================================
    // PHASE 10 & 11: FINANCIAL MARKET INTELLIGENCE & CAUSAL REASONING
    // ==============================================================
    const tickerContent = document.getElementById("ticker-content");
    const btnRefreshMarket = document.getElementById("btn-refresh-market");
    const btnQuickAnalyzeNifty = document.getElementById("btn-quick-analyze-nifty");
    const btnOpenAlertModal = document.getElementById("btn-open-alert-modal");
    const btnNewAlertSide = document.getElementById("btn-new-alert-side");
    const marketIndicesGrid = document.getElementById("market-indices-grid");
    const watchlistTbody = document.getElementById("watchlist-tbody");
    const btnAddWatchlistInline = document.getElementById("btn-add-watchlist-inline");
    const watchlistNewSym = document.getElementById("watchlist-new-sym");
    const watchlistNewName = document.getElementById("watchlist-new-name");
    const watchlistNewMarket = document.getElementById("watchlist-new-market");
    const selectReasoningSymbol = document.getElementById("select-reasoning-symbol");
    const btnTriggerReasoning = document.getElementById("btn-trigger-reasoning");
    const marketAlertsList = document.getElementById("market-alerts-list");
    const marketReasoningModal = document.getElementById("market-reasoning-modal");
    const marketReasoningBody = document.getElementById("market-reasoning-body");
    const reasoningModalTitle = document.getElementById("reasoning-modal-title");
    const btnCloseReasoningModal = document.getElementById("btn-close-reasoning-modal");
    const btnCloseReasoningFooter = document.getElementById("btn-close-reasoning-footer");
    const marketAlertModal = document.getElementById("market-alert-modal");
    const btnCloseAlertModal = document.getElementById("btn-close-alert-modal");
    const btnCancelAlert = document.getElementById("btn-cancel-alert");
    const btnSaveAlert = document.getElementById("btn-save-alert");
    const alertSymbol = document.getElementById("alert-symbol");
    const alertCondition = document.getElementById("alert-condition");
    const alertTargetValue = document.getElementById("alert-target-value");
    const alertNotes = document.getElementById("alert-notes");
    const sessionPillNse = document.getElementById("session-pill-nse");
    const sessionPillUs = document.getElementById("session-pill-us");
    const sessionPillProvider = document.getElementById("session-pill-provider");
    const fiiNetVal = document.getElementById("fii-net-val");
    const diiNetVal = document.getElementById("dii-net-val");
    const netInstVal = document.getElementById("net-inst-val");
    const instSentimentBadge = document.getElementById("inst-sentiment-badge");

    // Helper: generate inline SVG sparkline polyline
    function generateSparklineSvg(sparkline, isUp, width = 100, height = 30) {
        if (!sparkline || sparkline.length < 2) {
            return `<svg viewBox="0 0 ${width} ${height}" class="sparkline-svg"><line x1="0" y1="${height/2}" x2="${width}" y2="${height/2}" stroke="#64748b" stroke-width="1.5"/></svg>`;
        }
        const prices = sparkline.map(p => p.price);
        const min = Math.min(...prices);
        const max = Math.max(...prices);
        const range = (max - min) || 1;
        const pad = 3;

        const points = sparkline.map((p, idx) => {
            const x = (idx / (sparkline.length - 1)) * width;
            const y = height - pad - (((p.price - min) / range) * (height - pad * 2));
            return `${x.toFixed(1)},${y.toFixed(1)}`;
        }).join(" ");

        const strokeColor = isUp ? "#34d399" : "#f87171";
        return `<svg viewBox="0 0 ${width} ${height}" class="sparkline-svg">
            <polyline points="${points}" fill="none" stroke="${strokeColor}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>`;
    }

    // 1. Ticker Tape Polling
    async function loadTickerTape() {
        if (!tickerContent) return;
        try {
            const resp = await fetch("/api/market/indices");
            if (!resp.ok) return;
            const data = await resp.json();
            const allQuotes = [...(data.indian_indices || []), ...(data.global_indices || [])];

            if (allQuotes.length === 0) return;

            tickerContent.innerHTML = allQuotes.map(q => {
                const isUp = q.change >= 0;
                const sign = isUp ? "+" : "";
                const chgClass = isUp ? "up" : "down";
                const displaySym = q.symbol.replace("^", "").replace(".NS", "");
                return `
                    <span class="ticker-item" title="${escapeHtml(q.name)}">
                        <strong class="ticker-sym">${displaySym}</strong>
                        <span class="ticker-price">${q.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                        <span class="ticker-chg ${chgClass}">${sign}${q.pct_change.toFixed(2)}%</span>
                    </span>
                `;
            }).join("");

            // Update sidebar session status badge
            if (marketSessionBadge && data.session && data.session.nse) {
                const nseState = data.session.nse.state;
                marketSessionBadge.textContent = nseState === "REGULAR" ? "OPEN" : nseState;
                marketSessionBadge.style.background = nseState === "REGULAR" ? "rgba(16, 185, 129, 0.2)" : "rgba(239, 68, 68, 0.2)";
                marketSessionBadge.style.color = nseState === "REGULAR" ? "#34d399" : "#f87171";
            }
        } catch (err) {
            console.warn("Ticker tape poll error:", err);
        }
    }

    // 2. Full Market Dashboard Loader
    async function loadMarketDashboard() {
        await Promise.allSettled([
            loadMarketIndices(),
            loadFiiDiiData(),
            loadWatchlist(),
            loadAlerts()
        ]);
    }

    // 3. Benchmark Indices Grid & Session Status
    async function loadMarketIndices() {
        if (!marketIndicesGrid) return;
        try {
            const resp = await fetch("/api/market/indices");
            if (!resp.ok) throw new Error("Failed to fetch market indices");
            const data = await resp.json();

            // Update session pills
            if (data.session) {
                if (sessionPillNse && data.session.nse) {
                    sessionPillNse.textContent = `NSE: ${data.session.nse.label}`;
                    sessionPillNse.className = `session-pill ${data.session.nse.state === "REGULAR" ? "session-open" : "session-closed"}`;
                }
                if (sessionPillUs && data.session.us) {
                    sessionPillUs.textContent = `US: ${data.session.us.label}`;
                    sessionPillUs.className = `session-pill ${data.session.us.state === "REGULAR" ? "session-open" : "session-closed"}`;
                }
            }

            const indian = data.indian_indices || [];
            const global = data.global_indices || [];
            const all = [...indian, ...global];

            // Primary Hero card is NIFTY 50
            const hero = indian.find(i => i.symbol === "^NSEI") || indian[0] || all[0];
            const otherIndices = all.filter(i => i.symbol !== hero.symbol);

            let heroHtml = "";
            if (hero) {
                const isUp = hero.change >= 0;
                const sign = isUp ? "+" : "";
                const chgClass = isUp ? "up" : "down";
                const dayRange = (hero.day_high - hero.day_low) || 1;
                const posInRange = Math.max(0, Math.min(100, ((hero.price - hero.day_low) / dayRange) * 100));

                heroHtml = `
                    <div class="market-hero-card">
                        <div>
                            <div class="hero-card-top">
                                <div>
                                    <span class="hero-sym-title">${escapeHtml(hero.name)}</span>
                                    <span class="hero-market-tag">${hero.market} · ${hero.data_status.toUpperCase()}</span>
                                </div>
                                <button class="btn-sm btn-outline btn-hero-explain" data-symbol="${hero.symbol}">
                                    Explain Movement
                                </button>
                            </div>
                            <div class="hero-price-row">
                                <span class="hero-price-val">${hero.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
                                <span class="hero-chg-pill ${chgClass}">${sign}${hero.change.toFixed(2)} (${sign}${hero.pct_change.toFixed(2)}%)</span>
                            </div>
                            <div class="hero-range-bar-wrapper">
                                <div class="range-labels">
                                    <span>Low: ${hero.day_low ? hero.day_low.toFixed(2) : "--"}</span>
                                    <span>High: ${hero.day_high ? hero.day_high.toFixed(2) : "--"}</span>
                                </div>
                                <div class="range-bar">
                                    <div class="range-bar-fill" style="width: ${posInRange.toFixed(0)}%;"></div>
                                </div>
                            </div>
                            <div class="hero-sparkline-svg">
                                ${generateSparklineSvg(hero.sparkline, isUp, 280, 42)}
                            </div>
                        </div>
                        <div class="hero-card-bottom">
                            <span style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono);">
                                Prev Close: ${hero.prev_close ? hero.prev_close.toFixed(2) : "--"} · Vol: ${hero.volume ? (hero.volume/1000000).toFixed(1) + "M" : "--"}
                            </span>
                            <span style="font-size: 0.72rem; color: #38bdf8;">
                                Session: ${hero.market_session_label || "Active"}
                            </span>
                        </div>
                    </div>
                `;
            }

            const cardsHtml = otherIndices.map(item => {
                const isUp = item.change >= 0;
                const sign = isUp ? "+" : "";
                const chgClass = isUp ? "up" : "down";
                const displaySym = item.symbol.replace("^", "").replace(".NS", "");
                return `
                    <div class="index-card">
                        <div>
                            <div class="index-card-header">
                                <span class="index-card-title">${escapeHtml(item.name)}</span>
                                <span style="font-size: 0.68rem; font-family: var(--font-mono); color: var(--text-muted);">${item.market}</span>
                            </div>
                            <div class="index-card-price">${item.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</div>
                            <div class="index-card-chg text-${chgClass === 'up' ? 'success' : 'danger'}">
                                ${sign}${item.change.toFixed(2)} (${sign}${item.pct_change.toFixed(2)}%)
                            </div>
                            <div class="index-sparkline">
                                ${generateSparklineSvg(item.sparkline, isUp, 180, 26)}
                            </div>
                        </div>
                        <div style="display: flex; justify-content: flex-end; margin-top: 8px;">
                            <button class="btn-icon-xs btn-hero-explain" data-symbol="${item.symbol}" title="Investigate causal reason">
                                🔍 Why?
                            </button>
                        </div>
                    </div>
                `;
            }).join("");

            marketIndicesGrid.innerHTML = heroHtml + cardsHtml;

            // Wire explain buttons
            marketIndicesGrid.querySelectorAll(".btn-hero-explain").forEach(btn => {
                btn.addEventListener("click", () => {
                    const sym = btn.getAttribute("data-symbol");
                    if (sym) investigateMovement(sym);
                });
            });

        } catch (err) {
            marketIndicesGrid.innerHTML = `<div class="empty-state">Error loading indices: ${err.message}</div>`;
        }
    }

    // 4. Institutional Flows Telemetry
    async function loadFiiDiiData() {
        try {
            const resp = await fetch("/api/market/fii-dii");
            if (!resp.ok) return;
            const data = await resp.json();

            if (fiiNetVal) {
                fiiNetVal.textContent = `${data.fii_net_flow_cr > 0 ? "+" : ""}${data.fii_net_flow_cr.toLocaleString()} Cr`;
                fiiNetVal.className = `fii-dii-val ${data.fii_net_flow_cr >= 0 ? "text-success" : "text-danger"}`;
            }
            if (diiNetVal) {
                diiNetVal.textContent = `${data.dii_net_flow_cr > 0 ? "+" : ""}${data.dii_net_flow_cr.toLocaleString()} Cr`;
                diiNetVal.className = `fii-dii-val ${data.dii_net_flow_cr >= 0 ? "text-success" : "text-danger"}`;
            }
            if (netInstVal) {
                netInstVal.textContent = `${data.net_institutional_flow_cr > 0 ? "+" : ""}${data.net_institutional_flow_cr.toLocaleString()} Cr`;
                netInstVal.className = `fii-dii-val ${data.net_institutional_flow_cr >= 0 ? "text-success" : "text-danger"}`;
            }
            if (instSentimentBadge) {
                instSentimentBadge.textContent = data.sentiment || "Neutral";
            }
        } catch (err) {
            console.warn("FII/DII fetch error:", err);
        }
    }

    // 5. Watchlist Management
    async function loadWatchlist() {
        if (!watchlistTbody) return;
        try {
            const resp = await fetch("/api/market/watchlist");
            if (!resp.ok) throw new Error("Failed to fetch watchlist");
            const data = await resp.json();
            const items = data.watchlist || [];

            if (items.length === 0) {
                watchlistTbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 20px; color: var(--text-muted);">Watchlist is empty. Add a symbol above.</td></tr>`;
                return;
            }

            watchlistTbody.innerHTML = items.map(item => {
                const q = item.quote || {};
                const price = q.price ? q.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) : "--";
                const isUp = (q.change || 0) >= 0;
                const sign = isUp ? "+" : "";
                const chgText = q.pct_change !== undefined ? `${sign}${q.pct_change.toFixed(2)}%` : "--";
                const chgColor = isUp ? "text-success" : "text-danger";
                const highLow = (q.day_high && q.day_low) ? `${q.day_low.toFixed(1)} / ${q.day_high.toFixed(1)}` : "--";
                const volText = q.volume ? (q.volume > 1000000 ? (q.volume/1000000).toFixed(1) + "M" : (q.volume/1000).toFixed(0) + "k") : "--";

                return `
                    <tr>
                        <td>
                            <div class="watchlist-sym-col">
                                <span class="watchlist-sym-name">${escapeHtml(item.symbol)}</span>
                                <span class="watchlist-company-name">${escapeHtml(item.name || item.symbol)}</span>
                            </div>
                        </td>
                        <td class="mono-num">${price} ${q.currency || ""}</td>
                        <td class="mono-num ${chgColor}">${chgText}</td>
                        <td class="mono-num" style="font-size: 0.74rem; color: var(--text-muted);">${highLow}</td>
                        <td class="mono-num" style="font-size: 0.74rem; color: var(--text-muted);">${volText}</td>
                        <td>
                            <button class="btn-icon-xs btn-analyze-wl" data-symbol="${item.symbol}" title="Investigate why it moved">🔍 Why?</button>
                            <button class="btn-icon-xs btn-remove-wl" data-symbol="${item.symbol}" title="Remove from watchlist" style="color: #f87171;">✕</button>
                        </td>
                    </tr>
                `;
            }).join("");

            // Wire actions
            watchlistTbody.querySelectorAll(".btn-analyze-wl").forEach(btn => {
                btn.addEventListener("click", () => {
                    const sym = btn.getAttribute("data-symbol");
                    if (sym) investigateMovement(sym);
                });
            });

            watchlistTbody.querySelectorAll(".btn-remove-wl").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const sym = btn.getAttribute("data-symbol");
                    if (!sym) return;
                    if (confirm(`Remove ${sym} from your watchlist?`)) {
                        await fetch(`/api/market/watchlist/${encodeURIComponent(sym)}`, { method: "DELETE" });
                        loadWatchlist();
                    }
                });
            });

        } catch (err) {
            watchlistTbody.innerHTML = `<tr><td colspan="6" style="color: #f87171; text-align: center;">Error loading watchlist: ${err.message}</td></tr>`;
        }
    }

    if (btnAddWatchlistInline) {
        btnAddWatchlistInline.addEventListener("click", async () => {
            const sym = (watchlistNewSym.value || "").trim().toUpperCase();
            const name = (watchlistNewName.value || "").trim() || sym;
            const market = watchlistNewMarket.value || "NSE";
            if (!sym) {
                alert("Please specify a ticker symbol (e.g. INFY.NS, ^BSESN)");
                return;
            }

            try {
                const resp = await fetch("/api/market/watchlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ symbol: sym, name: name, market: market })
                });
                if (resp.ok) {
                    watchlistNewSym.value = "";
                    watchlistNewName.value = "";
                    loadWatchlist();
                    loadMarketIndices();
                } else {
                    const err = await resp.json();
                    alert(`Failed to add: ${err.detail || 'Unknown error'}`);
                }
            } catch (e) {
                alert(`Error: ${e.message}`);
            }
        });
    }

    // 6. Market Alerts Management
    async function loadAlerts() {
        if (!marketAlertsList) return;
        try {
            const resp = await fetch("/api/market/alerts");
            if (!resp.ok) return;
            const data = await resp.json();
            const alerts = data.alerts || [];

            if (alerts.length === 0) {
                marketAlertsList.innerHTML = `<div style="font-size: 0.8rem; color: var(--text-muted); padding: 8px;">No active alerts. Click '+ Alert' to configure.</div>`;
                return;
            }

            marketAlertsList.innerHTML = alerts.map(a => `
                <div class="alert-item-card">
                    <div class="alert-item-info">
                        <span class="alert-item-sym">${escapeHtml(a.symbol)}</span>
                        <span class="alert-item-cond">
                            Trigger: <strong>${a.condition}</strong> ${a.target_value.toLocaleString()}
                            ${a.notes ? ` · <em>${escapeHtml(a.notes)}</em>` : ""}
                        </span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="${a.is_active ? 'alert-badge-active' : 'alert-badge-triggered'}">
                            ${a.is_active ? 'Active' : 'Triggered'}
                        </span>
                        <button class="btn-icon-xs btn-delete-alert" data-id="${a.id}" title="Delete alert">✕</button>
                    </div>
                </div>
            `).join("");

            marketAlertsList.querySelectorAll(".btn-delete-alert").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const id = btn.getAttribute("data-id");
                    if (!id) return;
                    await fetch(`/api/market/alerts/${id}`, { method: "DELETE" });
                    loadAlerts();
                });
            });

        } catch (err) {
            marketAlertsList.innerHTML = `<div style="color: #f87171; font-size: 0.8rem;">Error loading alerts.</div>`;
        }
    }

    // Modal Alert Creation
    if (btnOpenAlertModal) btnOpenAlertModal.addEventListener("click", () => marketAlertModal.classList.add("active"));
    if (btnNewAlertSide) btnNewAlertSide.addEventListener("click", () => marketAlertModal.classList.add("active"));
    if (btnCloseAlertModal) btnCloseAlertModal.addEventListener("click", () => marketAlertModal.classList.remove("active"));
    if (btnCancelAlert) btnCancelAlert.addEventListener("click", () => marketAlertModal.classList.remove("active"));

    if (btnSaveAlert) {
        btnSaveAlert.addEventListener("click", async () => {
            const sym = (alertSymbol.value || "").trim().toUpperCase();
            const cond = alertCondition.value;
            const val = parseFloat(alertTargetValue.value);
            const notes = (alertNotes.value || "").trim();

            if (!sym || isNaN(val)) {
                alert("Please provide both a valid ticker symbol and numerical target threshold.");
                return;
            }

            try {
                const resp = await fetch("/api/market/alerts", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        symbol: sym,
                        condition: cond,
                        target_value: val,
                        notes: notes
                    })
                });
                if (resp.ok) {
                    marketAlertModal.classList.remove("active");
                    alertSymbol.value = "";
                    alertTargetValue.value = "";
                    alertNotes.value = "";
                    loadAlerts();
                } else {
                    const err = await resp.json();
                    alert(`Error: ${err.detail || 'Could not save alert'}`);
                }
            } catch (e) {
                alert(`Error: ${e.message}`);
            }
        });
    }

    // 7. Phase 11 Causal Reasoning Engine Execution & Modal
    async function investigateMovement(symbol) {
        if (!marketReasoningModal || !marketReasoningBody) return;
        marketReasoningModal.classList.add("active");
        if (reasoningModalTitle) reasoningModalTitle.textContent = `Market Investigation: ${symbol}`;

        marketReasoningBody.innerHTML = `
            <div style="text-align: center; padding: 40px 20px;">
                <div class="welcome-orb" style="width: 46px; height: 46px; margin: 0 auto 16px auto; animation: pulse 1.5s infinite;"></div>
                <h4 style="color: var(--text-primary); margin-bottom: 6px;">Synthesizing Multi-Factor Evidence...</h4>
                <p style="color: var(--text-secondary); font-size: 0.84rem;">
                    Correlating global benchmarks, macro statements, institutional FII/DII liquidity, and news publication timestamps for <strong>${escapeHtml(symbol)}</strong>.
                </p>
            </div>
        `;

        try {
            const resp = await fetch("/api/market/analyze", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ symbol: symbol })
            });

            if (!resp.ok) {
                const err = await resp.json();
                throw new Error(err.detail || "Analysis request failed");
            }

            const data = await resp.json();
            const a = data.analysis || {};
            const isUp = (a.change || 0) >= 0;
            const sign = isUp ? "+" : "";
            const confClass = (a.confidence || "Medium").toLowerCase();

            const sourcesHtml = (a.sources || []).map(s => {
                // If contains url inside parens
                const match = s.match(/(.+?)\s*\((https?:\/\/[^\)]+)\)/);
                if (match) {
                    return `<li><a href="${match[2]}" target="_blank" rel="noopener noreferrer">↗ ${escapeHtml(match[1])}</a></li>`;
                }
                return `<li>${escapeHtml(s)}</li>`;
            }).join("");

            marketReasoningBody.innerHTML = `
                <!-- Modal Hero Header -->
                <div class="reasoning-modal-hero">
                    <div>
                        <div class="reasoning-modal-sym">${escapeHtml(a.name || a.symbol)} (${escapeHtml(a.symbol)})</div>
                        <div class="reasoning-modal-name">
                            ${a.price ? a.price.toFixed(2) : "--"} · <span class="${isUp ? 'text-success' : 'text-danger'}">${sign}${a.change ? a.change.toFixed(2) : "--"} (${sign}${a.pct_change ? a.pct_change.toFixed(2) : "--"}%)</span>
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <span class="hero-chg-pill ${isUp ? 'up' : 'down'}">${escapeHtml(a.magnitude || '')} ${escapeHtml(a.direction || '')}</span>
                        <span class="confidence-pill confidence-${confClass}">${escapeHtml(a.confidence || 'Medium')} Confidence</span>
                    </div>
                </div>

                <!-- 1. Market Movement -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">1. Market Movement (What Changed?)</div>
                    <div class="reasoning-section-text">${escapeHtml(a.market_movement || "")}</div>
                </div>

                <!-- 2. Possible Reason -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">2. Possible Reason (Evidence-Based Causal Analysis)</div>
                    <div class="reasoning-section-text" style="border-left: 3px solid #38bdf8;">${escapeHtml(a.possible_reason || "")}</div>
                </div>

                <!-- 3. Evidence & Data Points -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">3. Supporting Evidence & Macro Telemetry</div>
                    <div class="reasoning-section-text">${escapeHtml(a.evidence || "")}</div>
                </div>

                <!-- 4. Timing -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">4. Timestamp Alignment</div>
                    <div class="reasoning-section-text">${escapeHtml(a.timing || "")}</div>
                </div>

                <!-- 5. Sector & Asset Impact -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">5. Affected Sectors & Market Breadth</div>
                    <div class="reasoning-section-text">${escapeHtml(a.impact || "")}</div>
                </div>

                <!-- 6. Verified Sources -->
                <div class="reasoning-section-block">
                    <div class="reasoning-section-title">6. Verified Sources & Publications</div>
                    <ul class="reasoning-sources-list">
                        ${sourcesHtml}
                    </ul>
                </div>

                <!-- 7. Anti-Hallucination Disclaimer -->
                <div class="reasoning-disclaimer-box">
                    <strong>Notice:</strong> ${escapeHtml(a.disclaimer || "")}
                </div>
            `;
        } catch (err) {
            marketReasoningBody.innerHTML = `
                <div class="empty-state" style="color: #f87171;">
                    Failed to generate causal reasoning report: ${escapeHtml(err.message)}
                </div>
            `;
        }
    }

    if (btnCloseReasoningModal) btnCloseReasoningModal.addEventListener("click", () => marketReasoningModal.classList.remove("active"));
    if (btnCloseReasoningFooter) btnCloseReasoningFooter.addEventListener("click", () => marketReasoningModal.classList.remove("active"));

    // Quick Trigger Buttons
    if (btnQuickAnalyzeNifty) {
        btnQuickAnalyzeNifty.addEventListener("click", () => investigateMovement("^NSEI"));
    }

    if (btnTriggerReasoning && selectReasoningSymbol) {
        btnTriggerReasoning.addEventListener("click", () => {
            const sym = selectReasoningSymbol.value || "^NSEI";
            investigateMovement(sym);
        });
    }

    if (btnRefreshMarket) {
        btnRefreshMarket.addEventListener("click", () => {
            loadMarketDashboard();
            loadTickerTape();
        });
    }

    // Set recurring 30s ticker tape poll
    setInterval(loadTickerTape, 30000);

    // ==============================================================
    // WEB RESEARCH ENGINE & KNOWLEDGE NOTEBOOK (Phase 12)
    // ==============================================================
    const btnOpenNewNoteModal = document.getElementById("btn-open-new-note-modal");
    const btnClearResearchView = document.getElementById("btn-clear-research-view");
    const researchQueryInput = document.getElementById("research-query-input");
    const researchCategorySelect = document.getElementById("research-category-select");
    const btnRunDeepResearch = document.getElementById("btn-run-deep-research");
    const btnRunFastSearch = document.getElementById("btn-run-fast-search");
    const checkAutosaveReport = document.getElementById("check-autosave-report");

    const researchViewerTitle = document.getElementById("research-viewer-title");
    const researchViewerSubtitle = document.getElementById("research-viewer-subtitle");
    const btnSaveCurrentReport = document.getElementById("btn-save-current-report");
    const researchReportContent = document.getElementById("research-report-content");

    const notebookSearchInput = document.getElementById("notebook-search-input");
    const notebookCategoryTabs = document.getElementById("notebook-category-tabs");
    const researchNotesList = document.getElementById("research-notes-list");

    const researchNoteModal = document.getElementById("research-note-modal");
    const researchNoteModalTitle = document.getElementById("research-note-modal-title");
    const btnCloseNoteModal = document.getElementById("btn-close-note-modal");
    const btnCancelNote = document.getElementById("btn-cancel-note");
    const btnSaveNote = document.getElementById("btn-save-note");
    const noteTitle = document.getElementById("note-title");
    const noteQuery = document.getElementById("note-query");
    const noteCategory = document.getElementById("note-category");
    const noteSummary = document.getElementById("note-summary");
    const noteMarkdown = document.getElementById("note-markdown");
    const noteTags = document.getElementById("note-tags");

    let currentActiveReport = null;
    let selectedNotebookCat = "";
    let notebookSearchTerm = "";

    // 1. Load Saved Research Notes
    async function loadResearchNotes(category = selectedNotebookCat, search = notebookSearchTerm) {
        if (!researchNotesList) return;
        try {
            let url = "/api/research/notes?";
            if (category) url += `category=${encodeURIComponent(category)}&`;
            if (search) url += `search=${encodeURIComponent(search)}&`;

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            const data = await res.json();
            const notes = data.notes || [];

            if (researchCountBadge) {
                researchCountBadge.textContent = notes.length;
            }

            if (notes.length === 0) {
                researchNotesList.innerHTML = `
                    <div class="empty-state" style="padding: 24px 10px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                        No research notes found in notebook.
                    </div>
                `;
                return;
            }

            researchNotesList.innerHTML = notes.map(note => {
                const catClass = `cat-${note.category || 'general'}`;
                const createdDate = note.created_at ? new Date(note.created_at).toLocaleDateString(undefined, {
                    month: 'short', day: 'numeric', year: 'numeric'
                }) : "";
                return `
                    <div class="research-note-item" data-id="${escapeHtml(note.id)}">
                        <div class="note-item-top">
                            <span class="note-item-title" title="Click to view report">${escapeHtml(note.title || note.query)}</span>
                            <span class="note-cat-badge ${catClass}">${escapeHtml(note.category || 'general')}</span>
                        </div>
                        <div class="note-item-snippet">${escapeHtml(note.summary || "")}</div>
                        <div class="note-item-footer">
                            <span class="note-item-date">${createdDate}</span>
                            <div class="note-item-actions">
                                <button class="btn-xs btn-outline btn-view-note" data-id="${escapeHtml(note.id)}">View</button>
                                <button class="btn-xs btn-ghost btn-delete-note" data-id="${escapeHtml(note.id)}" style="color: #f87171;">✕</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join("");

            // Wire view & delete handlers on note cards
            researchNotesList.querySelectorAll(".btn-view-note, .note-item-title").forEach(el => {
                el.addEventListener("click", () => {
                    const card = el.closest(".research-note-item");
                    const noteId = card ? card.dataset.id : null;
                    if (noteId) viewSavedNote(noteId);
                });
            });

            researchNotesList.querySelectorAll(".btn-delete-note").forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    const noteId = btn.dataset.id;
                    if (!confirm("Are you sure you want to delete this research note?")) return;
                    try {
                        const delRes = await fetch(`/api/research/notes/${noteId}`, { method: "DELETE" });
                        if (!delRes.ok) throw new Error("Delete failed");
                        loadResearchNotes();
                    } catch (err) {
                        alert(`Failed to delete note: ${err.message}`);
                    }
                });
            });
        } catch (err) {
            console.error("Failed to load research notes:", err);
            researchNotesList.innerHTML = `<div class="empty-state" style="color: #f87171;">Error loading notes: ${escapeHtml(err.message)}</div>`;
        }
    }

    // 2. View a Saved Note in the Active Viewer
    async function viewSavedNote(noteId) {
        try {
            const res = await fetch(`/api/research/notes/${noteId}`);
            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            const data = await res.json();
            const note = data.note;
            if (!note) return;

            currentActiveReport = {
                title: note.title,
                research_question: note.query,
                category: note.category,
                summary: note.summary,
                key_findings: note.key_findings || [],
                sources: note.sources || [],
                full_report_markdown: note.full_report_markdown,
                saved_id: note.id
            };

            if (researchViewerTitle) researchViewerTitle.textContent = note.title;
            if (researchViewerSubtitle) {
                const dateStr = note.created_at ? new Date(note.created_at).toLocaleDateString() : "";
                researchViewerSubtitle.textContent = `Saved Note • Category: ${note.category} • Created: ${dateStr}`;
            }
            if (btnSaveCurrentReport) btnSaveCurrentReport.style.display = "none";

            renderNoteReport(note);
        } catch (err) {
            alert(`Failed to open note: ${err.message}`);
        }
    }

    // 3. Render 8-Part Research Report
    function renderResearchReport(report) {
        currentActiveReport = report;

        if (researchViewerTitle) {
            researchViewerTitle.textContent = report.research_question || report.query || "Research Investigation";
        }
        if (researchViewerSubtitle) {
            const srcCount = (report.sources || []).length;
            const cat = report.category || "technology";
            researchViewerSubtitle.textContent = `Synthesized across ${srcCount} verified sources • Category: ${cat.toUpperCase()}`;
        }
        if (btnSaveCurrentReport) {
            btnSaveCurrentReport.style.display = "inline-flex";
        }

        const findingsHtml = (report.key_findings || []).map((f, i) => `
            <li class="report-finding-item">
                <span class="finding-num">${i + 1}</span>
                <span>${escapeHtml(f)}</span>
            </li>
        `).join("");

        const viewpointsHtml = (report.different_viewpoints || []).map(v => `
            <div style="margin-bottom: 6px;">• ${escapeHtml(v)}</div>
        `).join("");

        const timelineHtml = (report.important_dates || []).map(d => `
            <li class="report-timeline-item">⏱ ${escapeHtml(d)}</li>
        `).join("");

        const sourcesHtml = (report.sources || []).map(s => {
            const url = s.url || "#";
            const isHttp = url.startsWith("http");
            return `
                <a href="${escapeHtml(url)}" ${isHttp ? 'target="_blank" rel="noopener noreferrer"' : ''} class="source-card-pill">
                    <span class="source-card-title">${escapeHtml(s.title || "Source")}</span>
                    <span class="source-card-pub">${escapeHtml(s.publisher || s.source || "Web")}</span>
                </a>
            `;
        }).join("");

        researchReportContent.innerHTML = `
            <!-- 1. Research Question -->
            <div class="report-section-block">
                <div class="report-section-heading">❓ 1. Research Question</div>
                <div class="report-question-box">"${escapeHtml(report.research_question || "")}"</div>
            </div>

            <!-- 2. Key Findings -->
            <div class="report-section-block">
                <div class="report-section-heading">🔍 2. Key Findings</div>
                <ul class="report-findings-list">
                    ${findingsHtml || '<li class="report-finding-item">No specific findings extracted.</li>'}
                </ul>
            </div>

            <!-- 3. Supporting Evidence -->
            <div class="report-section-block">
                <div class="report-section-heading">📊 3. Supporting Evidence</div>
                <div class="report-evidence-box">${escapeHtml(report.supporting_evidence || "")}</div>
            </div>

            <!-- 4. Different Viewpoints & Trade-Offs -->
            <div class="report-section-block">
                <div class="report-section-heading">⚖️ 4. Different Viewpoints & Trade-Offs</div>
                <div class="report-viewpoints-box">
                    ${viewpointsHtml || '<div>No conflicting trade-offs identified for this subject.</div>'}
                </div>
            </div>

            <!-- 5. Important Dates & Milestones -->
            <div class="report-section-block">
                <div class="report-section-heading">📅 5. Important Dates & Milestones</div>
                <ul class="report-timeline-list">
                    ${timelineHtml || '<li class="report-timeline-item">No explicit calendar dates recorded.</li>'}
                </ul>
            </div>

            <!-- 6. Source Links -->
            <div class="report-section-block">
                <div class="report-section-heading">🔗 6. Source Links (${(report.sources || []).length})</div>
                <div class="report-sources-grid">
                    ${sourcesHtml || '<div>No external sources retrieved.</div>'}
                </div>
            </div>

            <!-- 7. Uncertainties & Limitations -->
            <div class="report-section-block">
                <div class="report-section-heading">⚠️ 7. Uncertainties & Limitations</div>
                <div class="report-limits-box">${escapeHtml(report.uncertainties_and_limitations || "Information based on retrieved public datasets.")}</div>
            </div>

            <!-- 8. Final Summary -->
            <div class="report-section-block">
                <div class="report-section-heading">💡 8. Final Summary</div>
                <div class="report-summary-box">${escapeHtml(report.final_summary || "")}</div>
            </div>
        `;
    }

    // 4. Render Saved Note
    function renderNoteReport(note) {
        const findingsHtml = (note.key_findings || []).map((f, i) => `
            <li class="report-finding-item">
                <span class="finding-num">${i + 1}</span>
                <span>${escapeHtml(f)}</span>
            </li>
        `).join("");

        const sourcesHtml = (note.sources || []).map(s => {
            const url = s.url || "#";
            const isHttp = url.startsWith("http");
            return `
                <a href="${escapeHtml(url)}" ${isHttp ? 'target="_blank" rel="noopener noreferrer"' : ''} class="source-card-pill">
                    <span class="source-card-title">${escapeHtml(s.title || "Source")}</span>
                    <span class="source-card-pub">${escapeHtml(s.publisher || s.source || "Archive")}</span>
                </a>
            `;
        }).join("");

        researchReportContent.innerHTML = `
            <div class="report-section-block">
                <div class="report-section-heading">📌 Topic / Query</div>
                <div class="report-question-box">"${escapeHtml(note.query || note.title)}"</div>
            </div>

            <div class="report-section-block">
                <div class="report-section-heading">💡 Takeaway Summary</div>
                <div class="report-summary-box">${escapeHtml(note.summary || "")}</div>
            </div>

            ${findingsHtml ? `
            <div class="report-section-block">
                <div class="report-section-heading">🔍 Key Takeaways</div>
                <ul class="report-findings-list">${findingsHtml}</ul>
            </div>` : ''}

            <div class="report-section-block">
                <div class="report-section-heading">📝 Full Markdown Content</div>
                <div class="report-evidence-box">${escapeHtml(note.full_report_markdown || "")}</div>
            </div>

            ${sourcesHtml ? `
            <div class="report-section-block">
                <div class="report-section-heading">🔗 Verified Sources</div>
                <div class="report-sources-grid">${sourcesHtml}</div>
            </div>` : ''}
        `;
    }

    // 5. Render Fast Web Search Results
    function renderSearchResults(data) {
        if (researchViewerTitle) researchViewerTitle.textContent = `Search Results: "${data.query}"`;
        if (researchViewerSubtitle) researchViewerSubtitle.textContent = `Found ${data.count || 0} multi-provider sources`;
        if (btnSaveCurrentReport) btnSaveCurrentReport.style.display = "none";

        const sources = data.sources || [];
        if (sources.length === 0) {
            researchReportContent.innerHTML = `
                <div class="empty-state" style="padding: 40px; text-align: center;">
                    <h4>No search results found</h4>
                    <p style="color: var(--text-muted);">Try a broader query or run a Deep Research investigation.</p>
                </div>
            `;
            return;
        }

        const cards = sources.map(s => {
            const isHttp = (s.url || "").startsWith("http");
            return `
                <div class="card-panel" style="padding: 14px; margin-bottom: 12px; background: var(--bg-secondary);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <a href="${escapeHtml(s.url || '#')}" ${isHttp ? 'target="_blank" rel="noopener noreferrer"' : ''} style="font-weight: 700; color: #38bdf8; text-decoration: none; font-size: 0.95rem;">
                            ${escapeHtml(s.title || "Result")} ↗
                        </a>
                        <span class="note-cat-badge cat-technology">${escapeHtml(s.publisher || s.source || "Web")}</span>
                    </div>
                    <p style="font-size: 0.84rem; color: var(--text-primary); line-height: 1.5; margin-bottom: 6px;">
                        ${escapeHtml(s.snippet || "")}
                    </p>
                    <div style="font-size: 0.72rem; color: var(--text-muted); font-family: var(--font-mono); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${escapeHtml(s.url || "")}
                    </div>
                </div>
            `;
        }).join("");

        researchReportContent.innerHTML = `
            <div style="margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.85rem; color: var(--text-secondary);">Direct Web & Encyclopedia Extracts</span>
                <button id="btn-deep-investigate-search" class="btn-sm btn-primary">🔬 Deep Investigate "${escapeHtml(data.query)}"</button>
            </div>
            ${cards}
        `;

        const btnDeepInv = document.getElementById("btn-deep-investigate-search");
        if (btnDeepInv) {
            btnDeepInv.addEventListener("click", () => {
                if (researchQueryInput) researchQueryInput.value = data.query;
                runDeepResearch(data.query, researchCategorySelect ? researchCategorySelect.value : "technology", checkAutosaveReport ? checkAutosaveReport.checked : false);
            });
        }
    }

    // 6. Execute Deep Research
    async function runDeepResearch(query, category = "technology", autoSave = false) {
        if (!query || !query.trim()) {
            alert("Please enter a research topic or question.");
            return;
        }
        const q = query.trim();

        if (btnRunDeepResearch) {
            btnRunDeepResearch.disabled = true;
            btnRunDeepResearch.innerHTML = "⏳ Synthesizing...";
        }

        researchReportContent.innerHTML = `
            <div class="empty-state" style="padding: 60px 20px; text-align: center;">
                <div class="loading-spinner" style="width: 36px; height: 36px; margin: 0 auto 16px; border: 3px solid rgba(56, 189, 248, 0.2); border-top-color: #38bdf8; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <h4 style="color: var(--text-primary);">Synthesizing Multi-Source Intelligence</h4>
                <p style="color: var(--text-muted); font-size: 0.85rem; max-width: 460px; margin: 0 auto;">
                    Aggregating DuckDuckGo, Wikipedia API, and Google News RSS... Building 8-part evidence matrix for "${escapeHtml(q)}".
                </p>
            </div>
        `;

        try {
            const res = await fetch("/api/research/investigate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: q,
                    category: category,
                    auto_save: autoSave,
                    tags: category
                })
            });

            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            const data = await res.json();
            if (data.status === "success" && data.report) {
                renderResearchReport(data.report);
                if (autoSave) {
                    loadResearchNotes();
                }
            } else {
                throw new Error("Invalid response from research engine");
            }
        } catch (err) {
            console.error("Investigation failed:", err);
            researchReportContent.innerHTML = `
                <div class="empty-state" style="color: #f87171; padding: 40px; text-align: center;">
                    <h4>Research Investigation Failed</h4>
                    <p style="font-size: 0.85rem;">${escapeHtml(err.message)}</p>
                </div>
            `;
        } finally {
            if (btnRunDeepResearch) {
                btnRunDeepResearch.disabled = false;
                btnRunDeepResearch.innerHTML = "🔬 Deep Research (8-Part Report)";
            }
        }
    }

    // 7. Execute Fast Web Search
    async function runFastSearch(query) {
        if (!query || !query.trim()) {
            alert("Please enter a search query.");
            return;
        }
        const q = query.trim();

        if (btnRunFastSearch) {
            btnRunFastSearch.disabled = true;
            btnRunFastSearch.innerHTML = "🔍 Searching...";
        }

        researchReportContent.innerHTML = `
            <div class="empty-state" style="padding: 50px 20px; text-align: center;">
                <div class="loading-spinner" style="width: 30px; height: 30px; margin: 0 auto 12px; border: 3px solid rgba(56, 189, 248, 0.2); border-top-color: #38bdf8; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <p style="color: var(--text-muted); font-size: 0.85rem;">Retrieving real-time web results...</p>
            </div>
        `;

        try {
            const res = await fetch("/api/research/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: q, limit: 8 })
            });

            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            const data = await res.json();
            renderSearchResults(data);
        } catch (err) {
            console.error("Search failed:", err);
            researchReportContent.innerHTML = `
                <div class="empty-state" style="color: #f87171; padding: 40px; text-align: center;">
                    <h4>Web Search Failed</h4>
                    <p style="font-size: 0.85rem;">${escapeHtml(err.message)}</p>
                </div>
            `;
        } finally {
            if (btnRunFastSearch) {
                btnRunFastSearch.disabled = false;
                btnRunFastSearch.innerHTML = "🔍 Fast Web Search";
            }
        }
    }

    // 8. Save Current Active Report to Notebook
    async function saveCurrentReport() {
        if (!currentActiveReport) {
            alert("No active research report to save.");
            return;
        }

        const r = currentActiveReport;
        const title = r.title || r.research_question || r.query || "Research Note";
        const cat = r.category || "technology";

        try {
            const res = await fetch("/api/research/notes", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    title: title,
                    query: r.research_question || r.query || title,
                    category: cat,
                    summary: r.final_summary || r.summary || "",
                    full_report_markdown: r.supporting_evidence || r.full_report_markdown || "",
                    key_findings: r.key_findings || [],
                    sources: r.sources || [],
                    tags: cat
                })
            });

            if (!res.ok) throw new Error(`HTTP error ${res.status}`);
            if (btnSaveCurrentReport) {
                btnSaveCurrentReport.textContent = "✓ Saved!";
                setTimeout(() => {
                    if (btnSaveCurrentReport) btnSaveCurrentReport.textContent = "Save to Notebook";
                }, 2000);
            }
            loadResearchNotes();
        } catch (err) {
            alert(`Failed to save report: ${err.message}`);
        }
    }

    // 9. Wire Research Buttons & Inputs
    if (btnRunDeepResearch) {
        btnRunDeepResearch.addEventListener("click", () => {
            const query = researchQueryInput ? researchQueryInput.value : "";
            const cat = researchCategorySelect ? researchCategorySelect.value : "technology";
            const autoSave = checkAutosaveReport ? checkAutosaveReport.checked : false;
            runDeepResearch(query, cat, autoSave);
        });
    }

    if (btnRunFastSearch) {
        btnRunFastSearch.addEventListener("click", () => {
            const query = researchQueryInput ? researchQueryInput.value : "";
            runFastSearch(query);
        });
    }

    if (researchQueryInput) {
        researchQueryInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const query = researchQueryInput.value;
                const cat = researchCategorySelect ? researchCategorySelect.value : "technology";
                const autoSave = checkAutosaveReport ? checkAutosaveReport.checked : false;
                runDeepResearch(query, cat, autoSave);
            }
        });
    }

    if (btnSaveCurrentReport) {
        btnSaveCurrentReport.addEventListener("click", saveCurrentReport);
    }

    if (btnClearResearchView) {
        btnClearResearchView.addEventListener("click", () => {
            currentActiveReport = null;
            if (researchQueryInput) researchQueryInput.value = "";
            if (researchViewerTitle) researchViewerTitle.textContent = "Research Debrief & Investigation";
            if (researchViewerSubtitle) researchViewerSubtitle.textContent = "Ready to investigate topics with primary sources";
            if (btnSaveCurrentReport) btnSaveCurrentReport.style.display = "none";
            if (researchReportContent) {
                researchReportContent.innerHTML = `
                    <div class="research-empty-state">
                        <div class="empty-icon">🌐</div>
                        <h4>Explore & Synthesize Knowledge</h4>
                        <p>Enter any research topic above to generate a comprehensive 8-section evidence-backed report with verified references, opposing viewpoints, and dates.</p>
                        <div class="research-suggested-prompts">
                            <button class="suggested-tag-btn" data-query="Raft consensus algorithm safety proofs" data-cat="technology">Raft Consensus Algorithm</button>
                            <button class="suggested-tag-btn" data-query="FastAPI asynchronous architecture benchmarks" data-cat="technology">FastAPI Performance</button>
                            <button class="suggested-tag-btn" data-query="Quantum computing advantage and surface codes" data-cat="academic">Quantum Advantage</button>
                            <button class="suggested-tag-btn" data-query="Transformer self-attention mechanisms" data-cat="technology">Transformer Architecture</button>
                        </div>
                    </div>
                `;
                wireSuggestedPrompts();
            }
        });
    }

    // Suggested prompts
    function wireSuggestedPrompts() {
        document.querySelectorAll(".suggested-tag-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                const q = btn.dataset.query;
                const cat = btn.dataset.cat || "technology";
                if (researchQueryInput) researchQueryInput.value = q;
                if (researchCategorySelect) researchCategorySelect.value = cat;
                const autoSave = checkAutosaveReport ? checkAutosaveReport.checked : false;
                runDeepResearch(q, cat, autoSave);
            });
        });
    }
    wireSuggestedPrompts();

    // Notebook category filter
    if (notebookCategoryTabs) {
        notebookCategoryTabs.querySelectorAll(".cat-tab").forEach(tab => {
            tab.addEventListener("click", () => {
                notebookCategoryTabs.querySelectorAll(".cat-tab").forEach(t => t.classList.remove("active"));
                tab.classList.add("active");
                selectedNotebookCat = tab.dataset.cat || "";
                loadResearchNotes(selectedNotebookCat, notebookSearchTerm);
            });
        });
    }

    // Notebook search input with debounce
    let searchDebounceTimer = null;
    if (notebookSearchInput) {
        notebookSearchInput.addEventListener("input", (e) => {
            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                notebookSearchTerm = e.target.value.trim();
                loadResearchNotes(selectedNotebookCat, notebookSearchTerm);
            }, 300);
        });
    }

    // 10. Manual Note Modal
    if (btnOpenNewNoteModal && researchNoteModal) {
        btnOpenNewNoteModal.addEventListener("click", () => {
            if (noteTitle) noteTitle.value = "";
            if (noteQuery) noteQuery.value = researchQueryInput ? researchQueryInput.value : "";
            if (noteCategory) noteCategory.value = researchCategorySelect ? researchCategorySelect.value : "technology";
            if (noteSummary) noteSummary.value = "";
            if (noteMarkdown) noteMarkdown.value = "";
            if (noteTags) noteTags.value = "";
            researchNoteModal.classList.add("active");
        });
    }

    if (btnCloseNoteModal && researchNoteModal) {
        btnCloseNoteModal.addEventListener("click", () => researchNoteModal.classList.remove("active"));
    }
    if (btnCancelNote && researchNoteModal) {
        btnCancelNote.addEventListener("click", () => researchNoteModal.classList.remove("active"));
    }

    if (btnSaveNote) {
        btnSaveNote.addEventListener("click", async () => {
            const titleVal = noteTitle ? noteTitle.value.trim() : "";
            const summaryVal = noteSummary ? noteSummary.value.trim() : "";
            const markdownVal = noteMarkdown ? noteMarkdown.value.trim() : "";
            const queryVal = noteQuery ? noteQuery.value.trim() : (titleVal || "Manual Note");
            const catVal = noteCategory ? noteCategory.value : "general";
            const tagsVal = noteTags ? noteTags.value.trim() : "";

            if (!titleVal) {
                alert("Please provide a note title.");
                return;
            }
            if (!summaryVal && !markdownVal) {
                alert("Please provide either a summary or markdown content.");
                return;
            }

            try {
                const res = await fetch("/api/research/notes", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        title: titleVal,
                        query: queryVal,
                        category: catVal,
                        summary: summaryVal || markdownVal.slice(0, 150),
                        full_report_markdown: markdownVal || summaryVal,
                        key_findings: [],
                        sources: [],
                        tags: tagsVal
                    })
                });

                if (!res.ok) throw new Error(`HTTP error ${res.status}`);
                researchNoteModal.classList.remove("active");
                loadResearchNotes();
            } catch (err) {
                alert(`Failed to save manual note: ${err.message}`);
            }
        });
    }

    // ==============================================================
    // COMPUTER & TASK AUTOMATION (Phase 13)
    // ==============================================================
    const btnOpenNewFileModal = document.getElementById("btn-open-new-file-modal");
    const btnOpenNewTaskModal = document.getElementById("btn-open-new-task-modal");
    const btnRefreshAutomation = document.getElementById("btn-refresh-automation");
    const btnReloadFiles = document.getElementById("btn-reload-files");
    const workspaceFilesList = document.getElementById("workspace-files-list");
    const workspaceRootLabel = document.getElementById("workspace-root-label");

    const terminalScreen = document.getElementById("terminal-screen");
    const consoleCommandInput = document.getElementById("console-command-input");
    const btnRunConsoleCommand = document.getElementById("btn-run-console-command");
    const approvalBox = document.getElementById("approval-box");
    const approvalTokenLabel = document.getElementById("approval-token-label");
    const approvalReasonText = document.getElementById("approval-reason-text");
    const approvalCmdPreview = document.getElementById("approval-cmd-preview");
    const btnConfirmApproval = document.getElementById("btn-confirm-approval");
    const btnCancelApproval = document.getElementById("btn-cancel-approval");

    const tabBtnScheduled = document.getElementById("tab-btn-scheduled");
    const tabBtnHistory = document.getElementById("tab-btn-history");
    const scheduledTasksList = document.getElementById("scheduled-tasks-list");
    const executionHistoryList = document.getElementById("execution-history-list");

    const automationTaskModal = document.getElementById("automation-task-modal");
    const btnCloseTaskModal = document.getElementById("btn-close-task-modal");
    const btnCancelTask = document.getElementById("btn-cancel-task");
    const btnSaveTask = document.getElementById("btn-save-task");
    const taskNameInput = document.getElementById("task-name");
    const taskActionTypeSelect = document.getElementById("task-action-type");
    const taskIntervalInput = document.getElementById("task-interval");
    const taskCommandGroup = document.getElementById("task-command-group");
    const taskCommandInput = document.getElementById("task-command");

    const automationFileModal = document.getElementById("automation-file-modal");
    const btnCloseFileModal = document.getElementById("btn-close-file-modal");
    const btnCancelFile = document.getElementById("btn-cancel-file");
    const btnSaveFile = document.getElementById("btn-save-file");
    const workspaceFilePath = document.getElementById("workspace-file-path");
    const workspaceFileContent = document.getElementById("workspace-file-content");
    const checkOverwriteFile = document.getElementById("check-overwrite-file");
    const automationFileModalTitle = document.getElementById("automation-file-modal-title");

    let pendingCommandApproval = null;

    // 1. Load Workspace Files
    async function loadWorkspaceFiles(path = "") {
        if (!workspaceFilesList) return;
        try {
            const res = await fetch(`/api/automation/files?path=${encodeURIComponent(path)}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const files = data.files || [];

            if (workspaceRootLabel && data.workspace_root) {
                workspaceRootLabel.textContent = `Root: ${data.workspace_root}`;
            }

            if (files.length === 0) {
                workspaceFilesList.innerHTML = `
                    <div class="empty-state" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                        Workspace folder is empty. Click '+ New File' to create.
                    </div>
                `;
                return;
            }

            workspaceFilesList.innerHTML = files.map(f => {
                const icon = f.is_dir ? "📁" : (f.extension === ".py" ? "🐍" : (f.extension === ".md" ? "📝" : (f.extension === ".json" ? "⚙️" : "📄")));
                const sizeText = f.is_dir ? "folder" : `${(f.size_bytes / 1024).toFixed(1)} KB`;
                return `
                    <div class="workspace-file-row" data-path="${escapeHtml(f.relative_path)}" data-isdir="${f.is_dir}">
                        <div class="file-info-group">
                            <span class="file-icon">${icon}</span>
                            <span class="file-name" title="${escapeHtml(f.relative_path)}">${escapeHtml(f.name)}</span>
                        </div>
                        <div class="file-actions">
                            <span class="file-size-badge">${sizeText}</span>
                            ${!f.is_dir ? `<button class="btn-xs btn-outline btn-open-file" data-path="${escapeHtml(f.relative_path)}">Edit</button>` : ''}
                            <button class="btn-xs btn-ghost btn-del-file" data-path="${escapeHtml(f.relative_path)}" style="color: #f87171;">✕</button>
                        </div>
                    </div>
                `;
            }).join("");

            // Wire row actions
            workspaceFilesList.querySelectorAll(".btn-open-file").forEach(btn => {
                btn.addEventListener("click", (e) => {
                    e.stopPropagation();
                    const p = btn.dataset.path;
                    openFileInModal(p);
                });
            });

            workspaceFilesList.querySelectorAll(".btn-del-file").forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    e.stopPropagation();
                    const p = btn.dataset.path;
                    if (!confirm(`Are you sure you want to delete '${p}'?`)) return;
                    try {
                        const delRes = await fetch("/api/automation/files", {
                            method: "DELETE",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ file_path: p })
                        });
                        if (!delRes.ok) throw new Error("Delete failed");
                        loadWorkspaceFiles();
                    } catch (err) {
                        alert(`Failed to delete file: ${err.message}`);
                    }
                });
            });
        } catch (err) {
            console.error("Failed to load workspace files:", err);
            workspaceFilesList.innerHTML = `<div class="empty-state" style="color: #f87171;">Error loading files: ${escapeHtml(err.message)}</div>`;
        }
    }

    // 2. Open File in Editor Modal
    async function openFileInModal(filePath) {
        try {
            const res = await fetch("/api/automation/files/read", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ file_path: filePath })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (automationFileModalTitle) automationFileModalTitle.textContent = `Edit File: ${filePath}`;
            if (workspaceFilePath) {
                workspaceFilePath.value = data.relative_path;
                workspaceFilePath.readOnly = true;
            }
            if (workspaceFileContent) workspaceFileContent.value = data.content;
            if (automationFileModal) automationFileModal.classList.add("active");
        } catch (err) {
            alert(`Failed to open file: ${err.message}`);
        }
    }

    // 3. Save File
    async function saveFile() {
        const pathVal = workspaceFilePath ? workspaceFilePath.value.trim() : "";
        const contentVal = workspaceFileContent ? workspaceFileContent.value : "";
        const overwriteVal = checkOverwriteFile ? checkOverwriteFile.checked : true;

        if (!pathVal) {
            alert("Please specify a file path.");
            return;
        }

        try {
            const res = await fetch("/api/automation/files/write", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    file_path: pathVal,
                    content: contentVal,
                    overwrite: overwriteVal
                })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            if (automationFileModal) automationFileModal.classList.remove("active");
            loadWorkspaceFiles();
            appendTerminalOutput(`[FILE SAVED] Successfully wrote ${pathVal}`);
        } catch (err) {
            alert(`Failed to save file: ${err.message}`);
        }
    }

    // 4. Terminal Helpers & Command Execution
    function appendTerminalOutput(line, cssClass = "terminal-system") {
        if (!terminalScreen) return;
        const lineEl = document.createElement("div");
        lineEl.className = `terminal-line ${cssClass}`;
        lineEl.textContent = line;
        terminalScreen.appendChild(lineEl);
        terminalScreen.scrollTop = terminalScreen.scrollHeight;
    }

    async function executeConsoleCommand(command, token = null) {
        if (!command || !command.trim()) return;
        const cmd = command.trim();

        appendTerminalOutput(`C:\\workspace> ${cmd}`, "terminal-prompt");
        if (btnRunConsoleCommand) btnRunConsoleCommand.disabled = true;

        try {
            const res = await fetch("/api/automation/execute", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd, approval_token: token })
            });
            const data = await res.json();

            if (data.status === "requires_approval") {
                pendingCommandApproval = {
                    command: cmd,
                    token: data.approval_token
                };
                if (approvalBox) {
                    approvalBox.style.display = "block";
                    if (approvalTokenLabel) approvalTokenLabel.textContent = `Token: ${data.approval_token}`;
                    if (approvalReasonText) approvalReasonText.textContent = data.reason || "Confirmation required.";
                    if (approvalCmdPreview) approvalCmdPreview.textContent = cmd;
                }
                appendTerminalOutput(`[SECURITY GATE] Action requires confirmation. Token: ${data.approval_token}`, "terminal-error");
            } else if (data.status === "blocked") {
                if (approvalBox) approvalBox.style.display = "none";
                appendTerminalOutput(`[BLOCKED] ${data.error || 'Dangerous command blocked by policy.'}`, "terminal-error");
            } else {
                if (approvalBox) approvalBox.style.display = "none";
                pendingCommandApproval = null;
                const output = data.output || "(Command completed without console output)";
                const isErr = data.exit_code !== 0 && data.status !== "success";
                appendTerminalOutput(output, isErr ? "terminal-error" : "terminal-success");
                loadExecutionHistory();
            }
        } catch (err) {
            appendTerminalOutput(`[EXECUTION FAILED] ${err.message}`, "terminal-error");
        } finally {
            if (btnRunConsoleCommand) btnRunConsoleCommand.disabled = false;
            if (consoleCommandInput) consoleCommandInput.value = "";
        }
    }

    // 5. Load Scheduled Tasks
    async function loadScheduledTasks() {
        if (!scheduledTasksList) return;
        try {
            const res = await fetch("/api/automation/tasks");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const tasks = data.tasks || [];

            if (automationTasksBadge) {
                automationTasksBadge.textContent = tasks.length;
            }

            if (tasks.length === 0) {
                scheduledTasksList.innerHTML = `
                    <div class="empty-state" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                        No scheduled background automations configured.
                    </div>
                `;
                return;
            }

            scheduledTasksList.innerHTML = tasks.map(t => {
                const intervalText = t.interval_seconds ? `Every ${t.interval_seconds}s` : (t.cron_expression || "Scheduled");
                const lastRunText = t.last_run_at ? new Date(t.last_run_at).toLocaleTimeString() : "Never run";
                return `
                    <div class="scheduled-task-card" data-id="${escapeHtml(t.id)}">
                        <div class="scheduled-task-top">
                            <span class="scheduled-task-title">${escapeHtml(t.name)}</span>
                            <span class="note-cat-badge cat-technology">${escapeHtml(t.action_type)}</span>
                        </div>
                        <div class="scheduled-task-meta">
                            ⏱ ${escapeHtml(intervalText)} • Last: ${escapeHtml(lastRunText)}
                        </div>
                        <div style="display: flex; justify-content: flex-end; gap: 6px; margin-top: 4px;">
                            <button class="btn-xs btn-primary btn-run-task" data-id="${escapeHtml(t.id)}">Run Now</button>
                            <button class="btn-xs btn-ghost btn-del-task" data-id="${escapeHtml(t.id)}" style="color: #f87171;">✕</button>
                        </div>
                    </div>
                `;
            }).join("");

            // Wire task buttons
            scheduledTasksList.querySelectorAll(".btn-run-task").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const tid = btn.dataset.id;
                    btn.disabled = true;
                    btn.textContent = "Running...";
                    try {
                        const runRes = await fetch(`/api/automation/tasks/${tid}/run`, { method: "POST" });
                        const rdata = await runRes.json();
                        appendTerminalOutput(`[SCHEDULED JOB EXECUTED] ${rdata.name}: ${rdata.output || 'OK'}`, "terminal-success");
                        loadScheduledTasks();
                    } catch (err) {
                        alert(`Failed to run task: ${err.message}`);
                    } finally {
                        btn.disabled = false;
                        btn.textContent = "Run Now";
                    }
                });
            });

            scheduledTasksList.querySelectorAll(".btn-del-task").forEach(btn => {
                btn.addEventListener("click", async () => {
                    const tid = btn.dataset.id;
                    if (!confirm("Are you sure you want to delete this scheduled task?")) return;
                    try {
                        await fetch(`/api/automation/tasks/${tid}`, { method: "DELETE" });
                        loadScheduledTasks();
                    } catch (err) {
                        alert(`Failed to delete task: ${err.message}`);
                    }
                });
            });
        } catch (err) {
            console.error("Failed to load tasks:", err);
        }
    }

    // 6. Load Execution History
    async function loadExecutionHistory() {
        if (!executionHistoryList) return;
        try {
            const res = await fetch("/api/automation/history?limit=30");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const history = data.history || [];

            if (history.length === 0) {
                executionHistoryList.innerHTML = `
                    <div class="empty-state" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                        No command audit records available.
                    </div>
                `;
                return;
            }

            executionHistoryList.innerHTML = history.map(h => {
                const dateStr = h.timestamp ? new Date(h.timestamp).toLocaleTimeString() : "";
                const isOk = h.status === "success";
                const badgeColor = isOk ? "#34d399" : (h.status === "blocked" ? "#f87171" : "#fbbf24");
                return `
                    <div class="history-item-row">
                        <div class="history-top-line">
                            <span style="color: #38bdf8; font-weight: 600;">${escapeHtml(h.command)}</span>
                            <span style="color: ${badgeColor}; font-size: 0.68rem; font-weight: 700;">${escapeHtml(h.status.toUpperCase())} (${h.execution_time_ms}ms)</span>
                        </div>
                        <div style="font-size: 0.68rem; color: var(--text-muted); font-family: var(--font-mono);">
                            ⏱ ${dateStr} • Exit: ${h.exit_code}
                        </div>
                    </div>
                `;
            }).join("");
        } catch (err) {
            console.error("Failed to load execution history:", err);
        }
    }

    // 7. Wire UI Events & Modals
    if (btnRunConsoleCommand && consoleCommandInput) {
        btnRunConsoleCommand.addEventListener("click", () => {
            executeConsoleCommand(consoleCommandInput.value);
        });

        consoleCommandInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                executeConsoleCommand(consoleCommandInput.value);
            }
        });
    }

    if (btnConfirmApproval) {
        btnConfirmApproval.addEventListener("click", () => {
            if (pendingCommandApproval) {
                executeConsoleCommand(pendingCommandApproval.command, pendingCommandApproval.token);
            }
        });
    }

    if (btnCancelApproval) {
        btnCancelApproval.addEventListener("click", () => {
            if (approvalBox) approvalBox.style.display = "none";
            pendingCommandApproval = null;
            appendTerminalOutput("[CANCELLED] Command confirmation was cancelled by user.", "terminal-system");
        });
    }

    if (btnRefreshAutomation) {
        btnRefreshAutomation.addEventListener("click", () => {
            loadWorkspaceFiles();
            loadScheduledTasks();
            loadExecutionHistory();
        });
    }

    if (btnReloadFiles) {
        btnReloadFiles.addEventListener("click", () => loadWorkspaceFiles());
    }

    // Task subtabs
    if (tabBtnScheduled && tabBtnHistory) {
        tabBtnScheduled.addEventListener("click", () => {
            tabBtnScheduled.classList.add("active");
            tabBtnHistory.classList.remove("active");
            if (scheduledTasksList) scheduledTasksList.style.display = "flex";
            if (executionHistoryList) executionHistoryList.style.display = "none";
            loadScheduledTasks();
        });

        tabBtnHistory.addEventListener("click", () => {
            tabBtnHistory.classList.add("active");
            tabBtnScheduled.classList.remove("active");
            if (scheduledTasksList) scheduledTasksList.style.display = "none";
            if (executionHistoryList) executionHistoryList.style.display = "flex";
            loadExecutionHistory();
        });
    }

    // Task Modal
    if (btnOpenNewTaskModal && automationTaskModal) {
        btnOpenNewTaskModal.addEventListener("click", () => {
            if (taskNameInput) taskNameInput.value = "";
            if (taskIntervalInput) taskIntervalInput.value = "3600";
            if (taskCommandInput) taskCommandInput.value = "";
            automationTaskModal.classList.add("active");
        });
    }

    if (btnCloseTaskModal && automationTaskModal) {
        btnCloseTaskModal.addEventListener("click", () => automationTaskModal.classList.remove("active"));
    }
    if (btnCancelTask && automationTaskModal) {
        btnCancelTask.addEventListener("click", () => automationTaskModal.classList.remove("active"));
    }

    if (taskActionTypeSelect && taskCommandGroup) {
        taskActionTypeSelect.addEventListener("change", () => {
            taskCommandGroup.style.display = taskActionTypeSelect.value === "command" ? "block" : "none";
        });
    }

    if (btnSaveTask) {
        btnSaveTask.addEventListener("click", async () => {
            const name = taskNameInput ? taskNameInput.value.trim() : "";
            const actionType = taskActionTypeSelect ? taskActionTypeSelect.value : "briefing";
            const interval = taskIntervalInput ? parseInt(taskIntervalInput.value, 10) : 3600;
            const command = taskCommandInput ? taskCommandInput.value.trim() : "";

            if (!name) {
                alert("Please enter a task name.");
                return;
            }

            try {
                const res = await fetch("/api/automation/tasks", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name: name,
                        action_type: actionType,
                        interval_seconds: interval,
                        command: actionType === "command" ? command : null
                    })
                });
                if (!res.ok) throw new Error("Task creation failed");
                if (automationTaskModal) automationTaskModal.classList.remove("active");
                loadScheduledTasks();
                appendTerminalOutput(`[TASK SCHEDULED] '${name}' configured.`);
            } catch (err) {
                alert(`Failed to create task: ${err.message}`);
            }
        });
    }

    // File Modal
    if (btnOpenNewFileModal && automationFileModal) {
        btnOpenNewFileModal.addEventListener("click", () => {
            if (automationFileModalTitle) automationFileModalTitle.textContent = "New Workspace File";
            if (workspaceFilePath) {
                workspaceFilePath.value = "";
                workspaceFilePath.readOnly = false;
            }
            if (workspaceFileContent) workspaceFileContent.value = "";
            automationFileModal.classList.add("active");
        });
    }

    if (btnCloseFileModal && automationFileModal) {
        btnCloseFileModal.addEventListener("click", () => automationFileModal.classList.remove("active"));
    }
    if (btnCancelFile && automationFileModal) {
        btnCancelFile.addEventListener("click", () => automationFileModal.classList.remove("active"));
    }

    if (btnSaveFile) {
        btnSaveFile.addEventListener("click", saveFile);
    }

    // ==============================================================
    // PHASE 14: SECURITY VAULT, PRIVACY CONTROLS & AUDIT TRAIL
    // ==============================================================
    const toggleOfflineLockdown = document.getElementById("toggle-offline-lockdown");
    const pillLockdownStatus = document.getElementById("pill-lockdown-status");
    const cardLockdownStatus = document.getElementById("card-lockdown-status");
    const togglePauseMemory = document.getElementById("toggle-pause-memory");
    const pillMemoryRetentionStatus = document.getElementById("pill-memory-retention-status");
    const toggleStrictRedaction = document.getElementById("toggle-strict-redaction");
    const pillRedactionStatus = document.getElementById("pill-redaction-status");
    const toggleAutoMedium = document.getElementById("toggle-auto-medium");
    const vaultModeLabel = document.getElementById("vault-mode-label");

    const redactorTestInput = document.getElementById("redactor-test-input");
    const btnRunSanitizeTest = document.getElementById("btn-run-sanitize-test");
    const btnInsertSampleSecrets = document.getElementById("btn-insert-sample-secrets");
    const redactorBadgeResult = document.getElementById("redactor-badge-result");
    const redactorOutputDisplay = document.getElementById("redactor-output-display");

    const auditSearchInput = document.getElementById("audit-search-input");
    const auditFilterType = document.getElementById("audit-filter-type");
    const auditEventsList = document.getElementById("audit-events-list");
    const auditTrailCount = document.getElementById("audit-trail-count");
    const btnRefreshAuditTrail = document.getElementById("btn-refresh-audit-trail");
    const btnExportSecurityData = document.getElementById("btn-export-security-data");
    const btnPurgeSecurityData = document.getElementById("btn-purge-security-data");

    let auditSearchDebounceTimer = null;

    async function loadPrivacySettings() {
        try {
            const res = await fetch("/api/security/privacy");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const priv = data.privacy_settings || {};

            // Offline Lockdown
            if (toggleOfflineLockdown) {
                toggleOfflineLockdown.checked = !!priv.offline_lockdown;
            }
            if (pillLockdownStatus) {
                if (priv.offline_lockdown) {
                    pillLockdownStatus.textContent = "LOCKED";
                    pillLockdownStatus.className = "status-pill pill-danger";
                    if (cardLockdownStatus) cardLockdownStatus.classList.add("lockdown-active");
                } else {
                    pillLockdownStatus.textContent = "INACTIVE";
                    pillLockdownStatus.className = "status-pill pill-neutral";
                    if (cardLockdownStatus) cardLockdownStatus.classList.remove("lockdown-active");
                }
            }
            if (securityModeBadge) {
                if (priv.offline_lockdown) {
                    securityModeBadge.textContent = "LOCKDOWN";
                    securityModeBadge.style.color = "#ef4444";
                } else {
                    securityModeBadge.textContent = "SECURE";
                    securityModeBadge.style.color = "#34d399";
                }
            }
            if (vaultModeLabel) {
                vaultModeLabel.textContent = priv.offline_lockdown ? "Offline Lockdown" : "Hybrid Guarded";
            }

            // Pause Memory
            if (togglePauseMemory) {
                togglePauseMemory.checked = !!priv.pause_memory_retention;
            }
            if (pillMemoryRetentionStatus) {
                if (priv.pause_memory_retention) {
                    pillMemoryRetentionStatus.textContent = "PAUSED";
                    pillMemoryRetentionStatus.className = "status-pill pill-danger";
                } else {
                    pillMemoryRetentionStatus.textContent = "RECORDING";
                    pillMemoryRetentionStatus.className = "status-pill pill-green";
                }
            }

            // Strict Redaction
            if (toggleStrictRedaction) {
                toggleStrictRedaction.checked = priv.strict_redaction !== false;
            }
            if (pillRedactionStatus) {
                if (priv.strict_redaction !== false) {
                    pillRedactionStatus.textContent = "ACTIVE";
                    pillRedactionStatus.className = "status-pill pill-cyan";
                } else {
                    pillRedactionStatus.textContent = "DISABLED";
                    pillRedactionStatus.className = "status-pill pill-neutral";
                }
            }

            // Auto-Approve Medium
            if (toggleAutoMedium) {
                toggleAutoMedium.checked = !!priv.auto_approve_medium;
            }
        } catch (err) {
            console.error("Failed to load privacy settings:", err);
        }
    }

    async function updatePrivacySetting(key, val) {
        try {
            const body = {};
            body[key] = val;
            const res = await fetch("/api/security/privacy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            await loadPrivacySettings();
            await loadAuditTrail();
        } catch (err) {
            alert(`Failed to update privacy setting: ${err.message}`);
        }
    }

    if (toggleOfflineLockdown) {
        toggleOfflineLockdown.addEventListener("change", (e) => {
            updatePrivacySetting("offline_lockdown", e.target.checked);
        });
    }

    if (togglePauseMemory) {
        togglePauseMemory.addEventListener("change", (e) => {
            updatePrivacySetting("pause_memory_retention", e.target.checked);
        });
    }

    if (toggleStrictRedaction) {
        toggleStrictRedaction.addEventListener("change", (e) => {
            updatePrivacySetting("strict_redaction", e.target.checked);
        });
    }

    if (toggleAutoMedium) {
        toggleAutoMedium.addEventListener("change", (e) => {
            updatePrivacySetting("auto_approve_medium", e.target.checked);
        });
    }

    async function loadAuditTrail(search = "", eventType = "") {
        if (!auditEventsList) return;
        try {
            let url = `/api/security/audit?limit=60`;
            if (search) url += `&search=${encodeURIComponent(search)}`;
            if (eventType) url += `&event_type=${encodeURIComponent(eventType)}`;

            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            const events = data.events || [];

            if (auditTrailCount) {
                auditTrailCount.textContent = `${events.length} events recorded`;
            }

            if (events.length === 0) {
                auditEventsList.innerHTML = `
                    <div class="empty-state" style="padding: 24px; text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                        No audit events match your search or filters.
                    </div>
                `;
                return;
            }

            auditEventsList.innerHTML = events.map(e => {
                const dateStr = e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : "";
                const dec = (e.decision || "ALLOWED").toUpperCase();
                let badgeClass = "decision-allowed";
                if (dec === "CONFIRMED") badgeClass = "decision-confirmed";
                else if (dec === "DENIED") badgeClass = "decision-denied";
                else if (dec === "BLOCKED") badgeClass = "decision-blocked";

                const resourceText = e.resource || e.action || e.event_type || "system_action";
                const detailsText = e.details ? JSON.stringify(e.details) : "";

                return `
                    <div class="audit-event-card">
                        <div class="audit-event-top">
                            <span class="audit-event-time">🕒 ${escapeHtml(dateStr)}</span>
                            <span class="audit-event-actor">@${escapeHtml(e.actor || 'system')}</span>
                        </div>
                        <div class="audit-event-main">
                            <span class="audit-event-resource">${escapeHtml(resourceText)}</span>
                            <span class="decision-badge ${badgeClass}">${escapeHtml(dec)}</span>
                        </div>
                        ${detailsText ? `<div class="audit-event-details" title="${escapeHtml(detailsText)}">${escapeHtml(detailsText)}</div>` : ''}
                    </div>
                `;
            }).join("");
        } catch (err) {
            console.error("Failed to load audit trail:", err);
        }
    }

    if (auditSearchInput) {
        auditSearchInput.addEventListener("input", () => {
            clearTimeout(auditSearchDebounceTimer);
            auditSearchDebounceTimer = setTimeout(() => {
                loadAuditTrail(auditSearchInput.value.trim(), auditFilterType ? auditFilterType.value : "");
            }, 300);
        });
    }

    if (auditFilterType) {
        auditFilterType.addEventListener("change", () => {
            loadAuditTrail(auditSearchInput ? auditSearchInput.value.trim() : "", auditFilterType.value);
        });
    }

    if (btnRefreshAuditTrail) {
        btnRefreshAuditTrail.addEventListener("click", () => {
            loadAuditTrail(auditSearchInput ? auditSearchInput.value.trim() : "", auditFilterType ? auditFilterType.value : "");
            loadPrivacySettings();
        });
    }

    // Redactor Live Sandbox
    if (btnRunSanitizeTest) {
        btnRunSanitizeTest.addEventListener("click", async () => {
            const text = redactorTestInput ? redactorTestInput.value.trim() : "";
            if (!text) {
                alert("Please enter text or credentials to test sanitization.");
                return;
            }

            btnRunSanitizeTest.disabled = true;
            btnRunSanitizeTest.textContent = "Sanitizing...";

            try {
                const res = await fetch("/api/security/sanitize", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: text })
                });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();

                if (redactorOutputDisplay) {
                    redactorOutputDisplay.textContent = data.sanitized_text || "[Empty string]";
                }
                if (redactorBadgeResult) {
                    if (data.contains_secrets) {
                        redactorBadgeResult.textContent = "SECRETS MASKED";
                        redactorBadgeResult.className = "badge-secrets-redacted";
                    } else {
                        redactorBadgeResult.textContent = "CLEAN (NO SECRETS)";
                        redactorBadgeResult.className = "badge-secrets-clean";
                    }
                }
            } catch (err) {
                alert(`Sanitization failed: ${err.message}`);
            } finally {
                btnRunSanitizeTest.disabled = false;
                btnRunSanitizeTest.textContent = "⚡ Sanitize & Redact";
            }
        });
    }

    if (btnInsertSampleSecrets && redactorTestInput) {
        btnInsertSampleSecrets.addEventListener("click", () => {
            redactorTestInput.value = `Connecting to external services:
- OpenAI API Key: sk-abcdef123456789012345678901234567890
- Google Gemini API Key: AIzaSyD9876543210123456789012345678901
- GitHub Token: ghp_1234567890abcdefghijklmnopqrstuvwxyz
- Header: Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test
- Database URL: postgresql://admin:p@ssw0rd123@db.nous.local:5432/main`;
            if (btnRunSanitizeTest) btnRunSanitizeTest.click();
        });
    }

    // Export Data Package
    if (btnExportSecurityData) {
        btnExportSecurityData.addEventListener("click", async () => {
            try {
                const res = await fetch("/api/security/export");
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                const jsonStr = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonStr], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `nous_security_privacy_export_${new Date().toISOString().split("T")[0]}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            } catch (err) {
                alert(`Export failed: ${err.message}`);
            }
        });
    }

    // Purge Data
    if (btnPurgeSecurityData) {
        btnPurgeSecurityData.addEventListener("click", async () => {
            if (!confirm("Are you sure you want to purge transient security caches and temp artifacts? This action cannot be undone.")) return;
            try {
                const res = await fetch("/api/security/purge", { method: "POST" });
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                const data = await res.json();
                alert(`Security Purge Complete: Purged ${data.purged_files_count || 0} temporary files and cleaned up vault artifacts.`);
                loadAuditTrail();
            } catch (err) {
                alert(`Purge failed: ${err.message}`);
            }
        });
    }

    // ==============================================================
    // PHASE 15: SYSTEM HEALTH, DIAGNOSTICS & SMOKE TESTING
    // ==============================================================
    const diagnosticsModal = document.getElementById("diagnostics-modal");
    const btnCloseDiagModal = document.getElementById("btn-close-diag-modal");
    const btnCloseDiagFooter = document.getElementById("btn-close-diag-footer");
    const btnRefreshDiag = document.getElementById("btn-refresh-diag");
    const btnRunSmokeTest = document.getElementById("btn-run-smoke-test");
    const diagHeaderDot = document.getElementById("diag-header-dot");
    const diagStatusBanner = document.getElementById("diag-status-banner");
    const diagOverallTitle = document.getElementById("diag-overall-title");
    const diagOverallDesc = document.getElementById("diag-overall-desc");
    const diagDbsSummaryBadge = document.getElementById("diag-dbs-summary-badge");
    const diagDbGrid = document.getElementById("diag-db-grid");
    const diagCpuVal = document.getElementById("diag-cpu-val");
    const diagRamVal = document.getElementById("diag-ram-val");
    const diagDiskVal = document.getElementById("diag-disk-val");
    const diagOllamaVal = document.getElementById("diag-ollama-val");
    const diagSmokeSection = document.getElementById("diag-smoke-section");
    const diagSmokeBadge = document.getElementById("diag-smoke-badge");
    const diagSmokeList = document.getElementById("diag-smoke-list");

    async function openDiagnosticsModal() {
        if (!diagnosticsModal) return;
        diagnosticsModal.classList.add("active");
        await loadDiagnosticsReport();
    }

    async function loadDiagnosticsReport() {
        if (!diagDbGrid) return;
        try {
            const res = await fetch("/api/diagnostics/report");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            // Overall banner
            if (diagOverallTitle) diagOverallTitle.textContent = `SYSTEM STATUS: ${data.overall_status}`;
            if (diagOverallDesc) diagOverallDesc.textContent = `Timestamp: ${data.iso_time} • Version: ${data.project.name} v${data.project.version}`;
            if (diagStatusBanner) {
                if (data.overall_status === "OPTIMAL") {
                    diagStatusBanner.className = "diag-banner";
                    if (diagHeaderDot) diagHeaderDot.className = "status-dot dot-online";
                } else {
                    diagStatusBanner.className = "diag-banner banner-warning";
                    if (diagHeaderDot) diagHeaderDot.className = "status-dot dot-checking";
                }
            }

            // Databases
            const dbs = data.databases ? data.databases.databases || [] : [];
            if (diagDbsSummaryBadge && data.databases) {
                diagDbsSummaryBadge.textContent = `${data.databases.healthy_count}/${data.databases.databases_count} HEALTHY`;
                diagDbsSummaryBadge.className = data.databases.all_healthy ? "status-pill pill-green" : "status-pill pill-danger";
            }

            diagDbGrid.innerHTML = dbs.map(d => {
                const isHealthy = d.status === "HEALTHY";
                const pillClass = isHealthy ? "pill-green" : "pill-danger";
                const tableCount = Object.keys(d.tables || {}).length;
                const totalRows = Object.values(d.tables || {}).reduce((a, b) => a + b, 0);
                return `
                    <div class="diag-db-card">
                        <div class="diag-db-top">
                            <span class="diag-db-name">${escapeHtml(d.id.toUpperCase())}</span>
                            <span class="status-pill ${pillClass}">${escapeHtml(d.journal_mode.toUpperCase())}</span>
                        </div>
                        <div class="diag-db-meta">
                            ${d.size_kb} KB • ${tableCount} tables (${totalRows} rows)
                        </div>
                        <div style="font-size: 0.65rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                            ${escapeHtml(d.name)}
                        </div>
                    </div>
                `;
            }).join("");

            // Hardware
            if (data.hardware) {
                const hw = data.hardware;
                if (diagCpuVal && hw.cpu) {
                    diagCpuVal.textContent = `${hw.cpu.name} (${hw.cpu.cores_logical} cores)`;
                    if (specCpu) specCpu.textContent = hw.cpu.name;
                }
                if (diagRamVal && hw.ram) {
                    diagRamVal.textContent = `${hw.ram.used_gb} / ${hw.ram.total_gb} GB (${hw.ram.percent_used}% load)`;
                }
                if (diagDiskVal && hw.disk) {
                    diagDiskVal.textContent = `${hw.disk.free_gb} GB free / ${hw.disk.total_gb} GB (${hw.disk.percent_used}% used)`;
                }
            }

            // Ollama
            if (data.ollama && diagOllamaVal) {
                const o = data.ollama;
                const lat = o.latency_ms ? ` (${o.latency_ms}ms)` : '';
                diagOllamaVal.textContent = `${o.status} • ${o.default_model}${lat}`;
            }
        } catch (err) {
            console.error("Failed to load diagnostic report:", err);
        }
    }

    async function runDiagnosticsSmokeTest() {
        if (!diagSmokeSection || !btnRunSmokeTest) return;
        diagSmokeSection.style.display = "block";
        if (diagSmokeBadge) {
            diagSmokeBadge.textContent = "RUNNING...";
            diagSmokeBadge.className = "status-pill pill-cyan";
        }
        btnRunSmokeTest.disabled = true;
        btnRunSmokeTest.textContent = "Testing...";

        try {
            const res = await fetch("/api/diagnostics/smoke-test", { method: "POST" });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();

            if (diagSmokeBadge) {
                diagSmokeBadge.textContent = data.status === "PASSED" ? "ALL PASSED" : "FAILED";
                diagSmokeBadge.className = data.status === "PASSED" ? "status-pill pill-green" : "status-pill pill-danger";
            }

            if (diagSmokeList) {
                diagSmokeList.innerHTML = (data.results || []).map(r => {
                    const icon = r.passed ? "✓" : "✗";
                    const color = r.passed ? "#10b981" : "#ef4444";
                    return `
                        <div class="diag-smoke-item">
                            <span class="smoke-comp"><span style="color: ${color}; font-weight: 800; margin-right: 6px;">${icon}</span>${escapeHtml(r.component)}</span>
                            <span class="smoke-detail">${escapeHtml(r.detail)}</span>
                        </div>
                    `;
                }).join("");
            }
        } catch (err) {
            alert(`Smoke test execution failed: ${err.message}`);
        } finally {
            btnRunSmokeTest.disabled = false;
            btnRunSmokeTest.textContent = "⚡ Run In-Process Smoke Test";
        }
    }

    if (btnCloseDiagModal && diagnosticsModal) {
        btnCloseDiagModal.addEventListener("click", () => diagnosticsModal.classList.remove("active"));
    }
    if (btnCloseDiagFooter && diagnosticsModal) {
        btnCloseDiagFooter.addEventListener("click", () => diagnosticsModal.classList.remove("active"));
    }
    if (btnRefreshDiag) {
        btnRefreshDiag.addEventListener("click", () => loadDiagnosticsReport());
    }
    if (btnRunSmokeTest) {
        btnRunSmokeTest.addEventListener("click", () => runDiagnosticsSmokeTest());
    }

    if (systemStatusIndicator) {
        systemStatusIndicator.style.cursor = "pointer";
        systemStatusIndicator.addEventListener("click", openDiagnosticsModal);
    }
    if (refreshHealthBtn) {
        refreshHealthBtn.addEventListener("click", openDiagnosticsModal);
    }

    // Initialize on page load
    checkHealth();
    loadSessions();
    loadMemories();
    loadSchedule(selectedRoutineDate);
    checkEmailAuth();
    loadEmails();
    loadProjects();
    loadGithubTelemetry();
    initVoiceSystem();
    loadTickerTape();
    loadResearchNotes();
    loadWorkspaceFiles();
    loadScheduledTasks();
    loadPrivacySettings();
});
