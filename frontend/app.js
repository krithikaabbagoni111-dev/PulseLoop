/* =====================================================
   PULSELOOP
   FRONTEND APPLICATION

   FastAPI + Hindsight + Local AI
   ===================================================== */


/* =====================================================
   CONFIGURATION
   ===================================================== */

const CONFIG = {
    API_BASE:
        window.PULSELOOP_API_BASE ||
        "https://pulseloop-backend.onrender.com",

    DEMO_MODE: false
};


/* =====================================================
   DEMO FEEDBACK
   ===================================================== */

const demoFeedback = [
    {
        id: 1,
        avatar: "AR",
        source: "Customer feedback",
        text: "Checkout is really confusing on my phone. I couldn't find where to enter my coupon.",
        topic: "Checkout",
        sentiment: "Negative",
        priority: "High",
        time: "8 min ago"
    },
    {
        id: 2,
        avatar: "SM",
        source: "Support ticket",
        text: "The new checkout is much faster than before. Payment was easy this time.",
        topic: "Checkout",
        sentiment: "Positive",
        priority: "Medium",
        time: "21 min ago"
    },
    {
        id: 3,
        avatar: "RK",
        source: "Customer feedback",
        text: "I still don't understand the search filters. It takes too long to find what I need.",
        topic: "Search",
        sentiment: "Negative",
        priority: "Medium",
        time: "36 min ago"
    },
    {
        id: 4,
        avatar: "NV",
        source: "Survey",
        text: "The redesigned checkout looks much cleaner now.",
        topic: "Checkout",
        sentiment: "Positive",
        priority: "Low",
        time: "1 hr ago"
    },
    {
        id: 5,
        avatar: "PK",
        source: "Customer feedback",
        text: "Payment keeps failing when I try to complete the order from my phone.",
        topic: "Mobile Payment",
        sentiment: "Negative",
        priority: "High",
        time: "2 hrs ago"
    },
    {
        id: 6,
        avatar: "AS",
        source: "Support ticket",
        text: "I receive too many notifications during the day.",
        topic: "Notifications",
        sentiment: "Negative",
        priority: "Medium",
        time: "3 hrs ago"
    },
    {
        id: 7,
        avatar: "JM",
        source: "Survey",
        text: "Search suggestions are much better after the latest update.",
        topic: "Search",
        sentiment: "Positive",
        priority: "Low",
        time: "4 hrs ago"
    },
    {
        id: 8,
        avatar: "TS",
        source: "Customer feedback",
        text: "I couldn't find where to apply my discount during mobile checkout.",
        topic: "Mobile Payment",
        sentiment: "Negative",
        priority: "High",
        time: "5 hrs ago"
    }
];

let feedbackData = [...demoFeedback];


/* =====================================================
   CHAT STATE
   ===================================================== */

let pulseLoopConversation = [];
let pulseLoopChatBusy = false;
let toastTimer = null;


/* =====================================================
   DOM HELPERS
   ===================================================== */

const $ = (selector) => document.querySelector(selector);

const $$ = (selector) => document.querySelectorAll(selector);


/* =====================================================
   INITIALIZATION
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    initializeNavigation();
    initializeMobileMenu();
    initializeModal();
    initializeFeedback();
    initializeMemory();
    initializeInsights();
    initializeSearch();
    initializeNotifications();
    initializePulseLoopChat();
    initializeMemorySuggestions();

    renderFeedback();
    renderOverviewFeedback();
    updateFeedbackCounts();
    updateSentimentStats();

    loadMemoryStats();
});


/* =====================================================
   NAVIGATION
   ===================================================== */

function initializeNavigation() {

    $$("[data-page]").forEach((button) => {

        button.addEventListener("click", () => {

            const page = button.dataset.page;

            if (!page) {
                return;
            }

            navigateTo(page);

            closeMobileSidebar();
        });
    });
}


function navigateTo(page) {

    $$(".page").forEach((section) => {
        section.classList.remove("active-page");
    });

    const target = $(`#page-${page}`);

    if (!target) {
        return;
    }

    target.classList.add("active-page");

    $$(".nav-item").forEach((item) => {
        item.classList.remove("active");
    });

    const activeNav =
        document.querySelector(
            `.nav-item[data-page="${page}"]`
        );

    activeNav?.classList.add("active");

    const breadcrumb = $("#breadcrumbCurrent");

    if (breadcrumb) {

        breadcrumb.textContent =
            page.charAt(0).toUpperCase() +
            page.slice(1).replace("-", " ");
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });

    if (page === "memory") {
        loadMemoryStats();
    }

    if (page === "feedback") {
        updateFeedbackCounts();
    }

    if (page === "chat") {

        setTimeout(() => {
            $("#chatInput")?.focus();
        }, 200);
    }
}


/* =====================================================
   MOBILE MENU
   ===================================================== */

function initializeMobileMenu() {

    $("#openSidebar")?.addEventListener("click", () => {

        $("#sidebar")?.classList.add("open");

        $("#mobileOverlay")?.classList.add("open");
    });


    $("#closeSidebar")?.addEventListener(
        "click",
        closeMobileSidebar
    );


    $("#mobileOverlay")?.addEventListener(
        "click",
        closeMobileSidebar
    );
}


function closeMobileSidebar() {

    $("#sidebar")?.classList.remove("open");

    $("#mobileOverlay")?.classList.remove("open");
}


/* =====================================================
   MODAL
   ===================================================== */

function initializeModal() {

    $("#analyzeButton")?.addEventListener(
        "click",
        openModal
    );


    $("#addFeedbackButton")?.addEventListener(
        "click",
        openModal
    );


    $$("[data-close-modal]").forEach((button) => {

        button.addEventListener(
            "click",
            closeModal
        );
    });


    $("#analyzeModal")?.addEventListener(
        "click",
        (event) => {

            if (event.target === $("#analyzeModal")) {
                closeModal();
            }
        }
    );


    $("#submitFeedback")?.addEventListener(
        "click",
        submitFeedback
    );


    $$(".source-option").forEach((option) => {

        option.addEventListener("click", () => {

            $$(".source-option").forEach((item) => {
                item.classList.remove("active");
            });

            option.classList.add("active");
        });
    });
}


function openModal() {

    $("#analyzeModal")?.classList.add("open");

    setTimeout(() => {
        $("#feedbackInput")?.focus();
    }, 100);
}


function closeModal() {

    $("#analyzeModal")?.classList.remove("open");
}


/* =====================================================
   FEEDBACK INITIALIZATION
   ===================================================== */

function initializeFeedback() {

    $("#feedbackSearch")?.addEventListener(
        "input",
        (event) => {

            const query =
                event.target.value
                    .toLowerCase()
                    .trim();

            const filtered =
                feedbackData.filter((item) => {

                    return (
                        String(item.text || "")
                            .toLowerCase()
                            .includes(query)

                        ||

                        String(item.topic || "")
                            .toLowerCase()
                            .includes(query)

                        ||

                        String(item.sentiment || "")
                            .toLowerCase()
                            .includes(query)
                    );
                });

            renderFeedback(filtered);
        }
    );


    $$(".filter-button").forEach((button) => {

        button.addEventListener("click", () => {

            $$(".filter-button").forEach((item) => {
                item.classList.remove("active");
            });

            button.classList.add("active");

            const filter =
                button.textContent.trim();


            if (filter === "All") {

                renderFeedback(feedbackData);

                return;
            }


            if (filter === "Negative") {

                renderFeedback(
                    feedbackData.filter(
                        (item) =>
                            item.sentiment === "Negative"
                    )
                );

                return;
            }


            if (filter === "Positive") {

                renderFeedback(
                    feedbackData.filter(
                        (item) =>
                            item.sentiment === "Positive"
                    )
                );

                return;
            }


            if (filter === "High priority") {

                renderFeedback(
                    feedbackData.filter(
                        (item) =>
                            item.priority === "High"
                    )
                );
            }
        });
    });
}


/* =====================================================
   RENDER FEEDBACK
   ===================================================== */

function renderFeedback(data = feedbackData) {

    const container = $("#feedbackList");

    if (!container) {
        return;
    }


    if (!data.length) {

        container.innerHTML = `
            <div class="panel empty-state">

                <div class="empty-icon">
                    ⌁
                </div>

                <h3>
                    No feedback found
                </h3>

                <p>
                    Try another search or add a new
                    customer signal.
                </p>

            </div>
        `;

        return;
    }


    container.innerHTML =
        data
            .map((item) => {

                const sentiment =
                    item.sentiment === "Positive"
                        ? "positive"
                        : "negative";

                return `
                    <article class="feedback-item">

                        <div class="feedback-avatar">
                            ${escapeHTML(item.avatar || "AI")}
                        </div>

                        <div class="feedback-content">

                            <strong>
                                ${escapeHTML(
                                    item.source ||
                                    "Customer feedback"
                                )}
                            </strong>

                            <p>
                                ${escapeHTML(
                                    item.text || ""
                                )}
                            </p>

                            <div class="feedback-meta">

                                <span>
                                    ${escapeHTML(
                                        item.topic ||
                                        "General Feedback"
                                    )}
                                </span>

                                <span>
                                    ${escapeHTML(
                                        item.priority ||
                                        "Medium"
                                    )}
                                    priority
                                </span>

                            </div>

                        </div>

                        <div class="feedback-side">

                            <span class="sentiment ${sentiment}">
                                ${escapeHTML(
                                    item.sentiment ||
                                    "Neutral"
                                )}
                            </span>

                            <time>
                                ${escapeHTML(
                                    item.time ||
                                    "Just now"
                                )}
                            </time>

                        </div>

                    </article>
                `;
            })
            .join("");
}


/* =====================================================
   OVERVIEW FEEDBACK
   ===================================================== */

function renderOverviewFeedback() {

    const container =
        $("#overviewFeedbackList");

    if (!container) {
        return;
    }


    container.innerHTML =
        feedbackData
            .slice(0, 3)
            .map((item) => {

                const sentiment =
                    item.sentiment === "Positive"
                        ? "positive"
                        : "negative";

                return `
                    <div class="mini-feedback">

                        <div class="mini-feedback-top">

                            <div class="mini-feedback-avatar">
                                ${escapeHTML(
                                    item.avatar || "AI"
                                )}
                            </div>

                            <span class="sentiment ${sentiment}">
                                ${escapeHTML(
                                    item.sentiment ||
                                    "Neutral"
                                )}
                            </span>

                        </div>

                        <p>
                            ${escapeHTML(item.text || "")}
                        </p>

                    </div>
                `;
            })
            .join("");
}


/* =====================================================
   FEEDBACK COUNTS
   ===================================================== */

function updateFeedbackCounts() {

    const total =
        feedbackData.length;


    $("#totalFeedback")?.replaceChildren(
        document.createTextNode(
            total.toLocaleString()
        )
    );


    $("#feedbackMemoryCount")?.replaceChildren(
        document.createTextNode(
            total.toLocaleString()
        )
    );


    $("#feedbackNavCount")?.replaceChildren(
        document.createTextNode(
            total.toLocaleString()
        )
    );


    updateSentimentStats();
}


/* =====================================================
   SENTIMENT STATS
   ===================================================== */

function updateSentimentStats() {

    const positive =
        feedbackData.filter(
            (item) =>
                item.sentiment === "Positive"
        ).length;


    const high =
        feedbackData.filter(
            (item) =>
                item.priority === "High"
        ).length;


    $("#positiveCount")?.replaceChildren(
        document.createTextNode(
            positive.toLocaleString()
        )
    );


    $("#highPriorityCount")?.replaceChildren(
        document.createTextNode(
            high.toLocaleString()
        )
    );
}


/* =====================================================
   SUBMIT FEEDBACK
   ===================================================== */

async function submitFeedback() {

    const input =
        $("#feedbackInput");

    if (!input) {
        return;
    }


    const text =
        input.value.trim();


    if (!text) {

        showToast(
            "Add some feedback",
            "Enter a customer comment before analyzing."
        );

        input.focus();

        return;
    }


    const button =
        $("#submitFeedback");

    if (!button) {
        return;
    }


    const originalHTML =
        button.innerHTML;


    button.disabled = true;

    button.innerHTML =
        "◌ Remembering...";


    try {

        let result = null;


        if (
            !CONFIG.DEMO_MODE &&
            CONFIG.API_BASE
        ) {

            result =
                await apiRequest(
                    "/feedback",
                    {
                        method: "POST",

                        body: JSON.stringify({
                            text: text
                        })
                    }
                );
        }


        const backendFeedback =
            result?.feedback ||
            result?.data ||
            result;


        const newFeedback = {

            id:
                backendFeedback?.id ||
                Date.now(),

            avatar:
                backendFeedback?.avatar ||
                "AI",

            source:
                backendFeedback?.source ||
                "New customer feedback",

            text:
                backendFeedback?.text ||
                text,

            topic:
                backendFeedback?.topic ||
                detectTopic(text),

            sentiment:
                backendFeedback?.sentiment ||
                detectSentiment(text),

            priority:
                backendFeedback?.priority ||
                detectPriority(text),

            time:
                backendFeedback?.time ||
                "Just now"
        };


        feedbackData.unshift(
            newFeedback
        );


        renderFeedback();

        renderOverviewFeedback();

        updateFeedbackCounts();


        closeModal();

        input.value = "";


        await loadMemoryStats();


        showToast(
            "Feedback remembered",
            "PulseLoop stored the new customer signal in the backend."
        );


        navigateTo("feedback");


    } catch (error) {

        console.error(
            "Feedback submission error:",
            error
        );


        showToast(
            "Analysis failed",
            error.message ||
            "Check that FastAPI is running."
        );


    } finally {

        button.disabled = false;

        button.innerHTML =
            originalHTML;
    }
}


/* =====================================================
   MEMORY INITIALIZATION
   ===================================================== */

function initializeMemory() {

    $("#recallButton")?.addEventListener(
        "click",
        recallMemory
    );


    $("#memoryQuery")?.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                recallMemory();
            }
        }
    );
}


/* =====================================================
   MEMORY SUGGESTIONS
   ===================================================== */

function initializeMemorySuggestions() {

    $$(".memory-suggestion").forEach((button) => {

        button.addEventListener("click", () => {

            const input =
                $("#memoryQuery");

            if (!input) {
                return;
            }


            input.value =
                button.dataset.query ||
                button.textContent.trim();


            input.focus();
        });
    });
}


/* =====================================================
   RECALL MEMORY
   ===================================================== */

async function recallMemory() {

    const input =
        $("#memoryQuery");

    const result =
        $("#recallResult");

    const button =
        $("#recallButton");


    if (!input || !result) {
        return;
    }


    const query =
        input.value.trim();


    if (!query) {

        showToast(
            "Ask something",
            "Enter a question for PulseLoop memory."
        );

        input.focus();

        return;
    }


    const originalHTML =
        button
            ? button.innerHTML
            : "";


    if (button) {

        button.disabled = true;

        button.innerHTML =
            "◌ Searching memory...";
    }


    result.innerHTML = `
        <div class="recall-placeholder">

            <div class="placeholder-orb">
                ✦
            </div>

            <h3>
                Searching Hindsight...
            </h3>

            <p>
                PulseLoop is retrieving historical
                memories and asking the AI layer
                to reason over them.
            </p>

        </div>
    `;


    try {

        const memory =
            await apiRequest(
                "/memory",
                {
                    method: "POST",

                    body: JSON.stringify({
                        query: query
                    })
                }
            );


        console.log(
            "Hindsight memory response:",
            memory
        );


        if (memory.success === false) {

            throw new Error(
                memory.message ||
                "Memory search failed."
            );
        }


        const answer =
            memory.answer ||
            memory.message ||
            "Historical context found.";


        /*
         * IMPORTANT:
         *
         * memory_count = TOTAL memories stored
         *
         * memories = RELEVANT memories returned
         *
         * Therefore, do NOT use memory_count
         * as the number of relevant memories.
         */

        const memories =
            Array.isArray(memory.memories)
                ? memory.memories
                : [];


        const totalMemoryCount =
            Number(memory.memory_count);


        let memoryCards = "";


        if (memories.length) {

            memoryCards = `
                <div class="memory-results">

                    ${memories
                        .slice(0, 8)
                        .map((item, index) => {

                            return `
                                <div class="memory-result-item">

                                    <span class="memory-result-index">
                                        ${String(
                                            index + 1
                                        ).padStart(2, "0")}
                                    </span>

                                    <div>

                                        <strong>
                                            ${escapeHTML(
                                                item.type ||
                                                "Historical memory"
                                            )}
                                        </strong>

                                        <p>
                                            ${escapeHTML(
                                                item.text ||
                                                item.content ||
                                                item.memory ||
                                                "Historical context found."
                                            )}
                                        </p>

                                    </div>

                                </div>
                            `;
                        })
                        .join("")}

                </div>
            `;
        }


        const relevantCount =
            memories.length;


        result.innerHTML = `
            <div class="recall-answer">

                <div class="recall-answer-icon">
                    ✦
                </div>

                <div class="recall-answer-content">

                    <strong>
                        PulseLoop AI found
                        ${relevantCount}
                        relevant
                        ${
                            relevantCount === 1
                                ? "memory"
                                : "memories"
                        }
                    </strong>

                    <p class="recall-summary">
                        ${formatAIText(answer)}
                    </p>

                    ${
                        Number.isFinite(totalMemoryCount)
                            ? `
                                <div class="memory-total-info">
                                    Hindsight memory store:
                                    <strong>
                                        ${totalMemoryCount.toLocaleString()}
                                    </strong>
                                    total memories
                                </div>
                            `
                            : ""
                    }

                    ${memoryCards}

                </div>

            </div>
        `;


        showToast(
            "Memory recalled",
            memories.length
                ? `AI analyzed ${memories.length} relevant historical memories.`
                : "No strongly related historical memories were found."
        );


        await loadMemoryStats();


    } catch (error) {

        console.error(
            "Memory recall error:",
            error
        );


        result.innerHTML = `
            <div class="recall-placeholder">

                <div class="placeholder-orb">
                    !
                </div>

                <h3>
                    Memory search failed
                </h3>

                <p>
                    ${escapeHTML(
                        error.message ||
                        "Check that FastAPI and Hindsight are running."
                    )}
                </p>

            </div>
        `;


        showToast(
            "Memory search failed",
            error.message ||
            "Check your backend."
        );


    } finally {

        if (button) {

            button.disabled = false;

            button.innerHTML =
                originalHTML;
        }
    }
}


/* =====================================================
   HINDSIGHT MEMORY COUNT
   ===================================================== */

async function loadMemoryStats() {

    const counters = [

        $("#hindsightMemoryCount"),

        $("#overviewMemoryCount")

    ].filter(Boolean);


    if (!counters.length) {
        return;
    }


    counters.forEach((element) => {
        element.textContent = "…";
    });


    try {

        const stats =
            await apiRequest(
                "/memory/stats",
                {
                    method: "GET"
                }
            );


        console.log(
            "Hindsight stats:",
            stats
        );


        if (
            !stats ||
            stats.success !== true
        ) {

            throw new Error(
                stats?.message ||
                "Could not retrieve memory statistics."
            );
        }


        const count =
            Number(stats.memory_count);


        if (!Number.isFinite(count)) {

            throw new Error(
                "Invalid memory count."
            );
        }


        counters.forEach((element) => {

            element.textContent =
                count.toLocaleString();
        });


        window.PulseLoopMemoryCount =
            count;


    } catch (error) {

        console.error(
            "Memory stats error:",
            error
        );


        counters.forEach((element) => {
            element.textContent = "—";
        });
    }
}


/* =====================================================
   INSIGHTS
   ===================================================== */

function initializeInsights() {

    $("#insightButton")?.addEventListener(
        "click",
        async () => {

            navigateTo("insights");

            await generateRealInsight();
        }
    );


    $("#refreshInsights")?.addEventListener(
        "click",
        async (event) => {

            await generateRealInsight(
                event.currentTarget
            );
        }
    );


    $("#insightPageButton")?.addEventListener(
        "click",
        async (event) => {

            await generateRealInsight(
                event.currentTarget
            );
        }
    );
}


/* =====================================================
   GENERATE REAL INSIGHT
   ===================================================== */

async function generateRealInsight(button = null) {

    const refreshButton =
        button ||
        $("#refreshInsights");


    const insightButton =
        $("#insightButton");


    const originalRefresh =
        refreshButton
            ? refreshButton.innerHTML
            : "";


    const originalInsight =
        insightButton
            ? insightButton.innerHTML
            : "";


    if (refreshButton) {

        refreshButton.disabled = true;

        refreshButton.innerHTML =
            "◌ Thinking...";
    }


    if (insightButton) {

        insightButton.disabled = true;

        insightButton.innerHTML =
            "◌ Analyzing...";
    }


    try {

        const result =
            await apiRequest(
                "/insights",
                {
                    method: "POST",

                    body: JSON.stringify({

                        query:
                            "Analyze the history of checkout and mobile payment complaints. What problem was solved, what problem remains unresolved, what evidence supports this, and what should the product team do next?"
                    })
                }
            );


        console.log(
            "PulseLoop insight response:",
            result
        );


        if (
            !result ||
            result.success === false
        ) {

            throw new Error(
                result?.message ||
                "Insight generation failed."
            );
        }


        updateInsightDashboard(result);


        showToast(
            "Insights refreshed",
            "PulseLoop used Hindsight memory to generate product intelligence."
        );


    } catch (error) {

        console.error(
            "Insight error:",
            error
        );


        showToast(
            "Insight generation failed",
            error.message ||
            "Check FastAPI and Hindsight."
        );


    } finally {

        if (refreshButton) {

            refreshButton.disabled = false;

            refreshButton.innerHTML =
                originalRefresh;
        }


        if (insightButton) {

            insightButton.disabled = false;

            insightButton.innerHTML =
                originalInsight;
        }
    }
}


/* =====================================================
   UPDATE INSIGHTS
   ===================================================== */

function updateInsightDashboard(data) {

    const answer =
        data.answer ||
        data.message ||
        "No insight was generated.";


    const mainText =
        $("#insightMainText");


    if (mainText) {

        mainText.innerHTML =
            formatAIText(answer);
    }


    const overviewRecommendation =
        $("#overviewRecommendation");


    if (overviewRecommendation) {

        overviewRecommendation.innerHTML =
            formatAIText(answer);
    }


    const sources =
        Array.isArray(data.sources)
            ? data.sources
            : [];


    const confidence =
        $("#insightConfidence");


    const confidenceBar =
        $("#confidenceBar");


    if (
        confidence &&
        confidenceBar
    ) {

        const percentage =
            sources.length
                ? Math.min(
                    99,
                    Math.max(
                        70,
                        70 + sources.length * 5
                    )
                )
                : 75;


        confidence.textContent =
            `${percentage}%`;


        confidenceBar.style.width =
            `${percentage}%`;
    }


    const answerLower =
        answer.toLowerCase();


    const problemInsight =
        $("#problemInsight");


    if (problemInsight) {

        problemInsight.textContent =
            answerLower.includes("problem")
                ? answer
                : "AI identified recurring customer signals in historical memory.";
    }


    const progressInsight =
        $("#progressInsight");


    if (progressInsight) {

        progressInsight.textContent =
            "Historical customer context was used to identify what improved and what remains unresolved.";
    }


    const nextStepInsight =
        $("#nextStepInsight");


    if (nextStepInsight) {

        nextStepInsight.textContent =
            answer;
    }
}


/* =====================================================
   CHATBOT INITIALIZATION
   ===================================================== */

function initializePulseLoopChat() {

    const input =
        $("#chatInput");


    const sendButton =
        $("#sendChatButton");


    if (
        !input ||
        !sendButton
    ) {
        return;
    }


    sendButton.addEventListener(
        "click",
        sendPulseLoopMessage
    );


    input.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendPulseLoopMessage();
            }
        }
    );


    renderChatWelcome();
}


/* =====================================================
   CHAT WELCOME
   ===================================================== */

function renderChatWelcome() {

    const container =
        $("#chatMessages");


    if (!container) {
        return;
    }


    if (pulseLoopConversation.length) {
        return;
    }


    container.innerHTML = `
        <div class="chat-welcome">

            <div class="chat-ai-orb">
                ✦
            </div>

            <h2>
                Ask PulseLoop anything
            </h2>

            <p>
                Your AI product intelligence assistant can
                reason over customer feedback, historical
                memory and product signals.
            </p>

            <div class="chat-suggestions">

                <button
                    class="chat-suggestion"
                    data-question="What are customers complaining about most?"
                >
                    <span>◈</span>
                    What are customers complaining about most?
                </button>


                <button
                    class="chat-suggestion"
                    data-question="What should our product team fix first?"
                >
                    <span>✦</span>
                    What should our product team fix first?
                </button>


                <button
                    class="chat-suggestion"
                    data-question="What recurring problems do you see in customer feedback?"
                >
                    <span>⌁</span>
                    Show recurring problems
                </button>


                <button
                    class="chat-suggestion"
                    data-question="Give me the strongest evidence from customer history."
                >
                    <span>◎</span>
                    Show historical evidence
                </button>

            </div>

        </div>
    `;


    $$(".chat-suggestion").forEach((button) => {

        button.addEventListener("click", () => {

            const question =
                button.dataset.question;


            const input =
                $("#chatInput");


            if (input) {

                input.value =
                    question;
            }


            sendPulseLoopMessage();
        });
    });
}


/* =====================================================
   SEND CHAT MESSAGE
   ===================================================== */

async function sendPulseLoopMessage() {

    if (pulseLoopChatBusy) {
        return;
    }


    const input =
        $("#chatInput");


    const container =
        $("#chatMessages");


    if (
        !input ||
        !container
    ) {
        return;
    }


    const message =
        input.value.trim();


    if (!message) {

        input.focus();

        return;
    }


    pulseLoopChatBusy = true;


    const sendButton =
        $("#sendChatButton");


    if (sendButton) {

        sendButton.disabled = true;
    }


    if (!pulseLoopConversation.length) {

        container.innerHTML = "";
    }


    appendChatMessage(
        "user",
        message
    );


    input.value = "";


    const typingId =
        showChatTyping();


    try {

        const response =
            await apiRequest(
                "/chat",
                {
                    method: "POST",

                    body: JSON.stringify({

                        message: message,

                        conversation:
                            pulseLoopConversation
                    })
                }
            );


        removeChatTyping(typingId);


        console.log(
            "PulseLoop chat response:",
            response
        );


        if (
            !response ||
            response.success === false
        ) {

            throw new Error(
                response?.message ||
                "PulseLoop AI could not answer."
            );
        }


        const answer =
            response.answer ||
            "I couldn't generate an answer.";


        pulseLoopConversation.push({

            role: "user",

            content: message
        });


        pulseLoopConversation.push({

            role: "assistant",

            content: answer
        });


        if (
            pulseLoopConversation.length > 20
        ) {

            pulseLoopConversation =
                pulseLoopConversation.slice(-20);
        }


        appendChatMessage(
            "assistant",
            answer,
            response.memories || []
        );


    } catch (error) {

        console.error(
            "Chatbot error:",
            error
        );


        removeChatTyping(typingId);


        appendChatMessage(
            "error",
            "I couldn't connect to PulseLoop AI."
        );


        showToast(
            "AI connection failed",
            error.message ||
            "Check your FastAPI backend."
        );


    } finally {

        pulseLoopChatBusy = false;


        if (sendButton) {

            sendButton.disabled = false;
        }


        input.focus();
    }
}


/* =====================================================
   APPEND CHAT MESSAGE
   ===================================================== */

function appendChatMessage(
    role,
    text,
    memories = []
) {

    const container =
        $("#chatMessages");


    if (!container) {
        return;
    }


    const messageElement =
        document.createElement("div");


    messageElement.className =
        `chat-message ${role}`;


    if (role === "user") {

        messageElement.innerHTML = `

            <div class="chat-message-inner">

                <div class="chat-avatar user-avatar">
                    You
                </div>

                <div class="chat-bubble">

                    <div class="chat-message-label">
                        You
                    </div>

                    <div class="chat-message-text">
                        ${escapeHTML(text)}
                    </div>

                </div>

            </div>
        `;
    }


    else if (role === "assistant") {

        const memoryCount =
            Array.isArray(memories)
                ? memories.length
                : 0;


        let memoryEvidence = "";


        if (memoryCount) {

            memoryEvidence = `

                <div class="chat-memory-evidence">

                    <div class="chat-memory-header">

                        <span>
                            ✦
                        </span>

                        <strong>
                            Hindsight Memory
                        </strong>

                        <small>
                            ${memoryCount}
                            relevant
                            ${
                                memoryCount === 1
                                    ? "memory"
                                    : "memories"
                            }
                        </small>

                    </div>

                </div>
            `;
        }


        messageElement.innerHTML = `

            <div class="chat-message-inner">

                <div class="chat-avatar ai-avatar">
                    ✦
                </div>

                <div class="chat-bubble ai-bubble">

                    <div class="chat-message-label">
                        PulseLoop AI
                    </div>

                    <div class="chat-message-text chat-ai-text">
                        ${formatAIText(text)}
                    </div>

                    ${memoryEvidence}

                </div>

            </div>
        `;
    }


    else {

        messageElement.innerHTML = `

            <div class="chat-message-inner">

                <div class="chat-avatar ai-avatar">
                    !
                </div>

                <div class="chat-bubble">

                    <div class="chat-message-label">
                        PulseLoop
                    </div>

                    <div class="chat-message-text">
                        ${escapeHTML(text)}
                    </div>

                </div>

            </div>
        `;
    }


    container.appendChild(
        messageElement
    );


    requestAnimationFrame(() => {

        container.scrollTo({

            top:
                container.scrollHeight,

            behavior:
                "smooth"
        });
    });
}


/* =====================================================
   AI TEXT FORMATTER
   ===================================================== */

function formatAIText(text) {

    let safe =
        escapeHTML(text);


    safe = safe.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );


    safe = safe.replace(
        /^### (.*)$/gm,
        "<h4>$1</h4>"
    );


    safe = safe.replace(
        /^## (.*)$/gm,
        "<h3>$1</h3>"
    );


    safe = safe.replace(
        /^# (.*)$/gm,
        "<h2>$1</h2>"
    );


    safe = safe.replace(
        /^[-•] (.*)$/gm,
        '<div class="ai-bullet">• $1</div>'
    );


    safe = safe.replace(
        /\n\n/g,
        "<br><br>"
    );


    safe = safe.replace(
        /\n/g,
        "<br>"
    );


    return safe;
}


/* =====================================================
   CHAT TYPING
   ===================================================== */

function showChatTyping() {

    const container =
        $("#chatMessages");


    if (!container) {
        return null;
    }


    const id =
        `typing-${Date.now()}`;


    const typing =
        document.createElement("div");


    typing.id = id;


    typing.className =
        "chat-message assistant";


    typing.innerHTML = `

        <div class="chat-message-inner">

            <div class="chat-avatar ai-avatar">
                ✦
            </div>

            <div class="chat-bubble ai-bubble">

                <div class="chat-message-label">
                    PulseLoop AI
                </div>

                <div class="typing-dots">

                    <span></span>

                    <span></span>

                    <span></span>

                    <em>
                        Thinking...
                    </em>

                </div>

            </div>

        </div>
    `;


    container.appendChild(typing);


    container.scrollTo({

        top:
            container.scrollHeight,

        behavior:
            "smooth"
    });


    return id;
}


function removeChatTyping(id) {

    if (!id) {
        return;
    }


    document
        .getElementById(id)
        ?.remove();
}


/* =====================================================
   SEARCH
   ===================================================== */

function initializeSearch() {

    $("#searchButton")?.addEventListener(
        "click",
        openSearch
    );


    $("#closeSearch")?.addEventListener(
        "click",
        closeSearch
    );


    $("#searchOverlay")?.addEventListener(
        "click",
        (event) => {

            if (
                event.target ===
                $("#searchOverlay")
            ) {

                closeSearch();
            }
        }
    );


    $("#globalSearchInput")?.addEventListener(
        "input",
        (event) => {

            performGlobalSearch(
                event.target.value
            );
        }
    );
}


function openSearch() {

    $("#searchOverlay")?.classList.add("open");


    setTimeout(() => {

        $("#globalSearchInput")?.focus();

    }, 100);
}


function closeSearch() {

    $("#searchOverlay")?.classList.remove("open");
}


function performGlobalSearch(value) {

    const query =
        value
            .toLowerCase()
            .trim();


    const result =
        $("#globalSearchResults");


    if (!result) {
        return;
    }


    if (!query) {

        result.innerHTML = `

            <p>
                Start typing to search the workspace.
            </p>
        `;

        return;
    }


    const matches =
        feedbackData.filter((item) => {

            return (

                String(item.text || "")
                    .toLowerCase()
                    .includes(query)

                ||

                String(item.topic || "")
                    .toLowerCase()
                    .includes(query)

                ||

                String(item.source || "")
                    .toLowerCase()
                    .includes(query)
            );
        });


    if (!matches.length) {

        result.innerHTML = `

            <div class="search-no-results">

                <strong>
                    No feedback found
                </strong>

                <p>
                    Try another keyword.
                </p>

            </div>
        `;

        return;
    }


    result.innerHTML =
        matches
            .slice(0, 6)
            .map((item) => {

                return `

                    <button
                        class="search-result"
                    >

                        <strong>
                            ${escapeHTML(
                                item.topic ||
                                "Feedback"
                            )}
                        </strong>

                        <span>
                            ${escapeHTML(
                                item.text ||
                                ""
                            )}
                        </span>

                    </button>
                `;
            })
            .join("");


    $$(".search-result").forEach((button) => {

        button.addEventListener(
            "click",
            () => {

                closeSearch();

                navigateTo("feedback");
            }
        );
    });
}


/* =====================================================
   NOTIFICATIONS
   ===================================================== */

function initializeNotifications() {

    $("#notificationButton")?.addEventListener(
        "click",
        () => {

            $("#notificationPanel")
                ?.classList.toggle("open");
        }
    );


    $("#closeNotifications")?.addEventListener(
        "click",
        () => {

            $("#notificationPanel")
                ?.classList.remove("open");
        }
    );
}


/* =====================================================
   API REQUEST
   ===================================================== */

async function apiRequest(
    endpoint,
    options = {}
) {

    const url =
        `${CONFIG.API_BASE}${endpoint}`;


    const headers = {

        "Content-Type":
            "application/json",

        ...(options.headers || {})
    };


    let response;


    try {

        response =
            await fetch(
                url,
                {
                    ...options,
                    headers
                }
            );

    } catch (error) {

        throw new Error(
            `Unable to connect to PulseLoop backend at ${CONFIG.API_BASE}. Make sure FastAPI is running and CORS is enabled.`
        );
    }


    if (!response.ok) {

        let message =
            `API request failed with status ${response.status}.`;


        try {

            const errorBody =
                await response.json();


            message =
                errorBody.detail ||
                errorBody.message ||
                message;

        } catch {

            // Keep default error message.
        }


        throw new Error(message);
    }


    try {

        return await response.json();

    } catch {

        throw new Error(
            "The backend returned an invalid JSON response."
        );
    }
}


/* =====================================================
   TOPIC DETECTION
   ===================================================== */

function detectTopic(text) {

    const lower =
        text.toLowerCase();


    if (
        lower.includes("mobile") ||
        lower.includes("phone") ||
        lower.includes("payment")
    ) {

        return "Mobile Payment";
    }


    if (
        lower.includes("checkout") ||
        lower.includes("coupon") ||
        lower.includes("cart")
    ) {

        return "Checkout";
    }


    if (
        lower.includes("search") ||
        lower.includes("filter")
    ) {

        return "Search";
    }


    if (
        lower.includes("notification") ||
        lower.includes("alert")
    ) {

        return "Notifications";
    }


    if (
        lower.includes("login") ||
        lower.includes("password")
    ) {

        return "Login";
    }


    return "General Feedback";
}


/* =====================================================
   SENTIMENT
   ===================================================== */

function detectSentiment(text) {

    const lower =
        text.toLowerCase();


    const negativeWords = [

        "confusing",
        "bad",
        "failed",
        "fail",
        "difficult",
        "problem",
        "issue",
        "hate",
        "slow",
        "can't",
        "cannot",
        "error",
        "broken",
        "friction"
    ];


    const positiveWords = [

        "good",
        "great",
        "easy",
        "fast",
        "love",
        "better",
        "excellent",
        "clean",
        "improved"
    ];


    const negativeScore =
        negativeWords.filter(
            (word) =>
                lower.includes(word)
        ).length;


    const positiveScore =
        positiveWords.filter(
            (word) =>
                lower.includes(word)
        ).length;


    if (
        negativeScore === 0 &&
        positiveScore === 0
    ) {

        return "Neutral";
    }


    return negativeScore > positiveScore
        ? "Negative"
        : "Positive";
}


/* =====================================================
   PRIORITY
   ===================================================== */

function detectPriority(text) {

    const lower =
        text.toLowerCase();


    const highWords = [

        "failed",
        "failure",
        "payment",
        "cannot",
        "can't",
        "broken",
        "error",
        "blocked",
        "crash"
    ];


    return highWords.some(
        (word) =>
            lower.includes(word)
    )
        ? "High"
        : "Medium";
}


/* =====================================================
   TOAST
   ===================================================== */

function showToast(
    title,
    message
) {

    const toast =
        $("#toast");


    const titleElement =
        $("#toastTitle");


    const messageElement =
        $("#toastMessage");


    if (
        !toast ||
        !titleElement ||
        !messageElement
    ) {

        return;
    }


    titleElement.textContent =
        title;


    messageElement.textContent =
        message;


    toast.classList.add("show");


    clearTimeout(toastTimer);


    toastTimer =
        setTimeout(() => {

            toast.classList.remove("show");

        }, 4200);
}


/* =====================================================
   HELPERS
   ===================================================== */

function wait(ms) {

    return new Promise(
        (resolve) =>
            setTimeout(
                resolve,
                ms
            )
    );
}


function escapeHTML(value) {

    return String(value ?? "")

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );
}


/* =====================================================
   KEYBOARD SHORTCUTS
   ===================================================== */

document.addEventListener(
    "keydown",
    (event) => {

        const activeElement =
            document.activeElement;


        const isTyping =
            activeElement &&
            [
                "INPUT",
                "TEXTAREA"
            ].includes(
                activeElement.tagName
            );


        if (
            event.key.toLowerCase() === "a" &&
            !isTyping
        ) {

            openModal();
        }


        if (event.key === "Escape") {

            closeModal();

            closeSearch();

            $("#notificationPanel")
                ?.classList.remove("open");

            closeMobileSidebar();
        }
    }
);