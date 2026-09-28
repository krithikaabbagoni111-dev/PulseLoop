import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from hindsight_service import (
    store_feedback,
    recall_memories,
    reflect_on_memory,
    get_memory_stats,
    is_available,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="PulseLoop API",
    description=(
        "Memory-driven customer feedback intelligence "
        "platform with local AI-style conversation"
    ),
    version="4.1.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DEMO FEEDBACK DATA
# =========================================================

feedback_data: List[Dict[str, Any]] = [
    {
        "id": 1,
        "avatar": "AI",
        "source": "Customer feedback",
        "text": "Checkout is taking too long on mobile.",
        "sentiment": "Negative",
        "priority": "High",
        "topic": "Checkout",
        "created_at": "2026-09-28T09:00:00",
        "time": "Today",
    },
    {
        "id": 2,
        "avatar": "AI",
        "source": "Customer feedback",
        "text": "The new dashboard looks much cleaner.",
        "sentiment": "Positive",
        "priority": "Low",
        "topic": "Dashboard",
        "created_at": "2026-09-27T14:30:00",
        "time": "Yesterday",
    },
    {
        "id": 3,
        "avatar": "AI",
        "source": "Customer feedback",
        "text": "Payment failed twice before going through.",
        "sentiment": "Negative",
        "priority": "High",
        "topic": "Payments",
        "created_at": "2026-09-27T11:15:00",
        "time": "Yesterday",
    },
]


# =========================================================
# CHAT SETTINGS
# =========================================================

MAX_CHAT_MESSAGES = 20
MAX_MEMORY_RESULTS = 8


# =========================================================
# REQUEST MODELS
# =========================================================

class FeedbackRequest(BaseModel):
    text: str = Field(..., min_length=1)


class MemoryRequest(BaseModel):
    query: str = Field(..., min_length=1)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation: List[ChatMessage] = Field(
        default_factory=list
    )


class InsightRequest(BaseModel):
    query: Optional[str] = None


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def contains_any(
    text: str,
    words: List[str]
) -> bool:

    text_lower = text.lower()

    return any(
        word.lower() in text_lower
        for word in words
    )


# =========================================================
# CONVERSATION CONTEXT
# =========================================================

def build_conversation_context(
    current_message: str,
    conversation: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """
    Understands the current message using previous chat turns.

    This fixes follow-up questions such as:

    User:
        What is the main problem?

    User:
        How do I resolve this issue?

    The second question does not contain the topic itself,
    so the previous conversation is used to understand
    what "this issue" refers to.
    """

    current_message = clean_text(
        current_message
    )

    previous_user_messages: List[str] = []
    previous_assistant_messages: List[str] = []

    if conversation:

        for item in conversation[-MAX_CHAT_MESSAGES:]:

            if isinstance(item, ChatMessage):

                role = item.role
                content = clean_text(
                    item.content
                )

            elif isinstance(item, dict):

                role = clean_text(
                    item.get("role", "")
                )

                content = clean_text(
                    item.get("content", "")
                )

            else:
                continue

            if not content:
                continue

            if role.lower() == "user":
                previous_user_messages.append(
                    content
                )

            elif role.lower() == "assistant":
                previous_assistant_messages.append(
                    content
                )

    recent_user_context = " ".join(
        previous_user_messages[-4:]
    )

    # -----------------------------------------------------
    # Detect whether this is a follow-up question
    # -----------------------------------------------------

    follow_up = contains_any(
        current_message,
        [
            "this issue",
            "that issue",
            "this problem",
            "that problem",
            "this",
            "that",
            "it",
            "the issue",
            "the problem",
            "same issue",
            "same problem",
        ]
    )

    # -----------------------------------------------------
    # Detect current intent
    # -----------------------------------------------------

    if contains_any(
        current_message,
        [
            "how to resolve",
            "how do i resolve",
            "how can i resolve",
            "how to fix",
            "how do i fix",
            "how can i fix",
            "how should we fix",
            "how should we resolve",
            "solution",
            "solutions",
            "resolve",
            "fix this",
            "fix the issue",
            "fix the problem",
        ]
    ):

        intent = "resolution"

    elif contains_any(
        current_message,
        [
            "who is affected",
            "who are affected",
            "affected users",
            "which users",
            "who faces",
            "who face",
        ]
    ):

        intent = "affected_users"

    elif contains_any(
        current_message,
        [
            "when",
            "timeline",
            "when did",
            "since when",
            "history",
            "historical",
            "date",
        ]
    ):

        intent = "timeline"

    elif contains_any(
        current_message,
        [
            "what changed",
            "what has changed",
            "changed over time",
            "improved",
            "improvement",
            "progress",
        ]
    ):

        intent = "changes"

    elif contains_any(
        current_message,
        [
            "did the redesign solve",
            "did it solve",
            "was it solved",
            "is it solved",
            "has it been solved",
            "resolved",
            "fully solved",
        ]
    ):

        intent = "resolution_status"

    elif contains_any(
        current_message,
        [
            "recommend",
            "recommendation",
            "next step",
            "next steps",
            "what should we do",
            "what should the team do",
            "action",
            "actions",
        ]
    ):

        intent = "recommendation"

    elif contains_any(
        current_message,
        [
            "sentiment",
            "positive",
            "negative",
            "satisfaction",
            "priority",
        ]
    ):

        intent = "sentiment"

    elif contains_any(
        current_message,
        [
            "summary",
            "summarize",
            "overview",
            "give me an overview",
        ]
    ):

        intent = "summary"

    elif contains_any(
        current_message,
        [
            "main problem",
            "main problems",
            "biggest problem",
            "biggest issue",
            "major problem",
            "major issue",
            "customer problem",
            "customer problems",
            "what problem",
            "what problems",
        ]
    ):

        intent = "main_problem"

    else:

        intent = "general"

    # -----------------------------------------------------
    # Build retrieval query
    # -----------------------------------------------------

    if follow_up and recent_user_context:

        retrieval_query = (
            f"Previous conversation: "
            f"{recent_user_context}\n\n"
            f"Current question: "
            f"{current_message}"
        )

    else:

        retrieval_query = current_message

    return {
        "current_message": current_message,
        "intent": intent,
        "follow_up": follow_up,
        "previous_user_messages": previous_user_messages,
        "previous_assistant_messages": previous_assistant_messages,
        "retrieval_query": retrieval_query,
    }


# =========================================================
# MEMORY HELPERS
# =========================================================

def extract_memory_text(
    memories: List[Dict[str, Any]]
) -> str:

    memory_parts = []

    for memory in memories[:MAX_MEMORY_RESULTS]:

        if not isinstance(memory, dict):
            continue

        text = clean_text(
            memory.get("text", "")
        )

        if text:
            memory_parts.append(text)

    if not memory_parts:

        return (
            "No relevant PulseLoop historical memories "
            "were found for this question."
        )

    return "\n\n".join(
        memory_parts
    )


def memory_texts(
    memories: List[Dict[str, Any]]
) -> List[str]:

    texts = []

    for memory in memories:

        if not isinstance(memory, dict):
            continue

        text = clean_text(
            memory.get("text", "")
        )

        if text:
            texts.append(text)

    return texts


def get_hindsight_memories(
    query: str
) -> Dict[str, Any]:

    if not is_available():

        return {
            "success": False,
            "memories": [],
            "message": (
                "Hindsight memory is not configured."
            ),
        }

    try:

        result = recall_memories(
            query
        )

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "memories": [],
                "message": (
                    "Hindsight returned an invalid response."
                ),
            }

        memories = result.get(
            "memories",
            []
        )

        if not isinstance(
            memories,
            list
        ):

            memories = []

        return {
            "success": bool(
                result.get(
                    "success",
                    False
                )
            ),
            "memories": memories,
            "message": result.get(
                "message",
                ""
            ),
        }

    except Exception as error:

        print(
            "Hindsight recall error:",
            error
        )

        return {
            "success": False,
            "memories": [],
            "message": str(error),
        }


def get_memory_dates(
    memories: List[Dict[str, Any]]
) -> List[str]:

    dates = []

    for memory in memories:

        text = clean_text(
            memory.get(
                "text",
                ""
            )
        )

        mentioned_at = clean_text(
            memory.get(
                "mentioned_at",
                ""
            )
        )

        if mentioned_at:

            dates.append(
                mentioned_at[:10]
            )

        elif "When:" in text:

            parts = text.split(
                "When:"
            )

            if len(parts) > 1:

                possible_date = (
                    parts[1]
                    .split("|")[0]
                    .strip()
                )

                if possible_date:

                    dates.append(
                        possible_date
                    )

    return list(
        dict.fromkeys(dates)
    )


# =========================================================
# TOPIC CLASSIFICATION
# =========================================================

def classify_memory_topics(
    memories: List[Dict[str, Any]]
) -> Dict[str, int]:

    topics = {
        "Mobile Payment": 0,
        "Checkout": 0,
        "Dashboard": 0,
        "Network Transition": 0,
        "General": 0,
    }

    for memory in memories:

        text = clean_text(
            memory.get(
                "text",
                ""
            )
        ).lower()

        if contains_any(
            text,
            [
                "wifi",
                "wi-fi",
                "5g",
                "mobile data",
                "network",
                "network transition",
            ]
        ):

            topics[
                "Network Transition"
            ] += 1

        if contains_any(
            text,
            [
                "payment",
                "mobile payment",
                "payment failure",
            ]
        ):

            topics[
                "Mobile Payment"
            ] += 1

        if contains_any(
            text,
            [
                "checkout",
                "purchase abandonment",
                "payment form",
            ]
        ):

            topics[
                "Checkout"
            ] += 1

        if contains_any(
            text,
            [
                "dashboard",
            ]
        ):

            topics[
                "Dashboard"
            ] += 1

    return topics


# =========================================================
# LOCAL PULSELOOP INTELLIGENCE
# =========================================================

def local_pulseloop_answer(
    query: str,
    memories: List[Dict[str, Any]],
    conversation: Optional[List[Any]] = None,
) -> str:

    query = clean_text(
        query
    )

    # -----------------------------------------------------
    # Conversation understanding
    # -----------------------------------------------------

    context = build_conversation_context(
        query,
        conversation
    )

    intent = context[
        "intent"
    ]

    previous_user_messages = context[
        "previous_user_messages"
    ]

    texts = memory_texts(
        memories
    )

    # -----------------------------------------------------
    # No memories
    # -----------------------------------------------------

    if not texts:

        if contains_any(
            query,
            [
                "hello",
                "hi",
                "hey",
            ]
        ):

            return (
                "Hello! I'm PulseLoop's product "
                "intelligence assistant. I can search "
                "historical customer feedback, identify "
                "recurring problems, analyze priorities, "
                "and suggest product actions."
            )

        return (
            "I searched PulseLoop's historical memory, "
            "but I could not find strongly related "
            "historical information for this question."
        )

    # =====================================================
    # ANALYZE MEMORY THEMES
    # =====================================================

    payment_count = sum(
        1
        for text in texts
        if contains_any(
            text,
            [
                "payment",
                "checkout",
                "pay",
                "transaction",
            ]
        )
    )

    network_count = sum(
        1
        for text in texts
        if contains_any(
            text,
            [
                "wi-fi",
                "wifi",
                "5g",
                "mobile data",
                "network transition",
                "network changes",
            ]
        )
    )

    mobile_count = sum(
        1
        for text in texts
        if contains_any(
            text,
            [
                "mobile",
                "android",
                "phone",
            ]
        )
    )

    checkout_count = sum(
        1
        for text in texts
        if "checkout" in text.lower()
    )

    desktop_count = sum(
        1
        for text in texts
        if "desktop" in text.lower()
        or "laptop" in text.lower()
    )

    negative_count = sum(
        1
        for text in texts
        if contains_any(
            text,
            [
                "failed",
                "failure",
                "problem",
                "issue",
                "unreliable",
                "freeze",
                "stuck",
                "slow",
                "frustrating",
                "complaint",
            ]
        )
    )

    # =====================================================
    # 1. RESOLUTION QUESTIONS
    # =====================================================
    #
    # IMPORTANT:
    # This block comes BEFORE the general problem block.
    #
    # Therefore:
    # "How to resolve this issue?"
    #
    # will NOT accidentally receive the same
    # "main problem" answer.
    # =====================================================

    if intent == "resolution":

        answer = (
            "Based on PulseLoop's historical feedback, "
            "the recommended way to resolve the main issue "
            "is to improve payment-state recovery during "
            "network transitions.\n\n"

            "**Recommended resolution:**\n"

            "1. Detect Wi-Fi-to-mobile-data and "
            "mobile-data-to-Wi-Fi transitions during an "
            "active payment.\n\n"

            "2. Preserve the payment transaction state "
            "when the network temporarily changes instead "
            "of restarting the payment flow.\n\n"

            "3. Prevent the payment screen from freezing "
            "when connectivity changes.\n\n"

            "4. Make sure payment status and alerts are "
            "restored correctly after the connection "
            "returns.\n\n"

            "5. Test the complete payment flow on Android "
            "under different network-transition scenarios.\n\n"

            "6. Monitor payment failures after deployment "
            "to confirm that the problem has actually "
            "decreased.\n\n"

            "**Priority:** High, because the issue can "
            "directly prevent customers from completing "
            "payments.\n\n"

            "**Expected result:** Customers should be able "
            "to switch networks without losing payment "
            "state, freezing the payment screen, or "
            "having to restart the app."
        )

        return answer

    # =====================================================
    # 2. AFFECTED USERS
    # =====================================================

    if intent == "affected_users":

        return (
            "The historical feedback indicates that the "
            "main issue primarily affects mobile users, "
            "with Android users specifically appearing in "
            "the reported incidents.\n\n"

            "**Most affected users:**\n"
            "• Mobile users\n"
            "• Android users\n"
            "• Customers making payments while changing "
            "between Wi-Fi and mobile data\n\n"

            "Desktop users appear to have benefited more "
            "from the checkout redesign, while mobile "
            "payment reliability remains the larger concern."
        )

    # =====================================================
    # 3. TIMELINE
    # =====================================================

    if intent == "timeline":

        dates = get_memory_dates(
            memories
        )

        if dates:

            date_text = ", ".join(
                dates[:10]
            )

        else:

            date_text = (
                "specific dates were not available "
                "in the retrieved memories"
            )

        return (
            "The retrieved PulseLoop history contains "
            f"events across {date_text}.\n\n"

            "The overall progression is that checkout "
            "improvements reduced some desktop usability "
            "problems, but mobile payment reliability "
            "continued to be reported.\n\n"

            "The history then connected several mobile "
            "payment failures with network transitions, "
            "leading the team to prioritize network-"
            "transition handling."
        )

    # =====================================================
    # 4. CHANGES
    # =====================================================

    if intent == "changes":

        return (
            "The main changes visible in the historical "
            "feedback are:\n\n"

            "• Checkout was redesigned to reduce the "
            "number of steps.\n\n"

            "• The payment form was simplified.\n\n"

            "• Unnecessary confirmation screens were "
            "removed.\n\n"

            "• Desktop checkout complaints decreased.\n\n"

            "• Customers responded positively to the "
            "shorter checkout process.\n\n"

            "However, the mobile payment reliability "
            "problem continued, especially around "
            "network transitions."
        )

    # =====================================================
    # 5. RESOLUTION STATUS
    # =====================================================

    if intent == "resolution_status":

        return (
            "The historical feedback suggests that the "
            "problem was **not completely solved**.\n\n"

            "The checkout redesign successfully improved "
            "the desktop experience and reduced some "
            "checkout complaints.\n\n"

            "However, mobile payment reliability continued "
            "to be reported as a problem, particularly "
            "during transitions between Wi-Fi and mobile "
            "data.\n\n"

            "So the evidence suggests:\n\n"

            "• Desktop checkout: improved\n"
            "• Checkout usability: improved\n"
            "• Mobile payment reliability: still unresolved\n"
            "• Network-transition handling: requires further "
            "attention"
        )

    # =====================================================
    # 6. RECOMMENDATION
    # =====================================================

    if intent == "recommendation":

        return (
            "Based on the retrieved PulseLoop history, "
            "the product team should prioritize mobile "
            "payment reliability.\n\n"

            "**Recommended actions:**\n\n"

            "1. Investigate payment-state handling when "
            "users switch between Wi-Fi and mobile data.\n\n"

            "2. Test Android payment flows across different "
            "network-transition scenarios.\n\n"

            "3. Ensure payment and alert states survive "
            "temporary network changes.\n\n"

            "4. Prevent users from needing to restart the "
            "application after a network transition.\n\n"

            "5. Continue monitoring payment failures after "
            "the fix to verify that the recurring issue "
            "has actually been resolved.\n\n"

            "6. Preserve the successful desktop checkout "
            "simplifications while improving mobile "
            "reliability separately."
        )

    # =====================================================
    # 7. MAIN PROBLEM
    # =====================================================

    if intent == "main_problem":

        answer_parts = [
            "The main customer problem in PulseLoop is "
            "**unreliable mobile payment during network "
            "transitions**."
        ]

        answer_parts.append(
            "**What customers are experiencing:**\n"
            "• Payment failures during mobile checkout\n"
            "• Payment screens freezing during network changes\n"
            "• Payment alerts disappearing\n"
            "• Some users needing to restart the app\n"
            "• Mobile checkout being slower than desktop"
        )

        answer_parts.append(
            "**Who is affected:**\n"
            "Android and mobile users are repeatedly "
            "mentioned in the historical feedback."
        )

        answer_parts.append(
            "**Priority:** High. The issue directly affects "
            "payment completion and product usability."
        )

        answer_parts.append(
            "**Important product insight:**\n"
            "The checkout redesign improved the desktop "
            "experience, but mobile payment reliability "
            "remains unresolved."
        )

        return "\n\n".join(
            answer_parts
        )

    # =====================================================
    # 8. CHECKOUT
    # =====================================================

    if contains_any(
        query,
        [
            "checkout",
            "abandon",
            "checkout experience",
        ]
    ):

        return (
            "PulseLoop's historical feedback shows that "
            "checkout usability has been an important "
            "customer problem.\n\n"

            "**Earlier problems:**\n"
            "• Too many checkout steps\n"
            "• Repeated information entry\n"
            "• Slower mobile checkout\n"
            "• More complicated checkout experience\n\n"

            "**What changed:**\n"
            "The checkout process was redesigned by reducing "
            "steps, simplifying the payment form, and "
            "removing unnecessary confirmation screens.\n\n"

            "**Result:**\n"
            "Desktop complaints decreased and customers "
            "responded positively to the shorter process.\n\n"

            "**Remaining concern:**\n"
            "Mobile payment reliability continues to be "
            "the main unresolved issue."
        )

    # =====================================================
    # 9. MOBILE
    # =====================================================

    if contains_any(
        query,
        [
            "mobile",
            "android",
            "phone",
        ]
    ):

        return (
            "The strongest mobile-related problem in "
            "PulseLoop is payment reliability.\n\n"

            "Historical feedback mentions payment failures, "
            "frozen payment screens, disappearing alerts, "
            "and transactions getting stuck when users "
            "switch between Wi-Fi and mobile data.\n\n"

            "Android users are specifically mentioned in "
            "several reported incidents.\n\n"

            "The available history strongly connects the "
            "problem with network transitions.\n\n"

            "Although the checkout redesign improved the "
            "desktop experience, mobile payment reliability "
            "remains unresolved."
        )

    # =====================================================
    # 10. DESKTOP
    # =====================================================

    if contains_any(
        query,
        [
            "desktop",
            "laptop",
        ]
    ):

        return (
            "PulseLoop's desktop checkout experience has "
            "improved significantly.\n\n"

            "The product team redesigned checkout by "
            "reducing steps, simplifying the payment form, "
            "and removing unnecessary confirmation screens.\n\n"

            "Historical feedback indicates that desktop "
            "complaints decreased after the redesign.\n\n"

            "However, the improvement did not completely "
            "solve the mobile payment reliability problem."
        )

    # =====================================================
    # 11. SENTIMENT / PRIORITY
    # =====================================================

    if intent == "sentiment":

        return (
            f"PulseLoop's available historical memory "
            f"contains {len(texts)} relevant records.\n\n"

            f"Approximately {negative_count} retrieved "
            "records contain negative or problem-related "
            "signals such as failures, issues, "
            "unreliability, freezing, slow performance, "
            "or complaints.\n\n"

            "The strongest high-priority theme is mobile "
            "payment reliability, particularly during "
            "network transitions."
        )

    # =====================================================
    # 12. SUMMARY
    # =====================================================

    if intent == "summary":

        return (
            "PulseLoop's historical feedback shows that "
            "checkout and payment reliability are the main "
            "areas requiring attention.\n\n"

            "Desktop checkout improved after the redesign "
            "and customers appreciated the shorter flow.\n\n"

            "The remaining major concern is mobile payment "
            "reliability, especially when users transition "
            "between Wi-Fi and mobile data.\n\n"

            "The recommended next step is to improve "
            "payment-state recovery during these network "
            "transitions."
        )

    # =====================================================
    # 13. GENERAL QUESTION
    # =====================================================

    selected = []

    for text in texts:

        if len(selected) >= 8:
            break

        if text not in selected:

            selected.append(
                text
            )

    answer = (
        "I analyzed PulseLoop's available historical "
        "memory.\n\n"
        f"I found {len(texts)} relevant historical "
        "records.\n\n"
    )

    if payment_count:

        answer += (
            f"Payment/checkout appears frequently in "
            f"the retrieved history "
            f"({payment_count} records).\n"
        )

    if mobile_count:

        answer += (
            f"Mobile or Android-related issues appear "
            f"in {mobile_count} records.\n"
        )

    if network_count:

        answer += (
            f"Network-transition problems appear in "
            f"{network_count} records.\n"
        )

    if desktop_count:

        answer += (
            f"Desktop/laptop experience is mentioned "
            f"in {desktop_count} records.\n"
        )

    if checkout_count:

        answer += (
            f"Checkout is mentioned in "
            f"{checkout_count} records.\n"
        )

    answer += (
        "\nThe most important evidence from the "
        "retrieved history is:\n\n"
    )

    for index, text in enumerate(
        selected,
        start=1
    ):

        answer += (
            f"{index}. {text}\n\n"
        )

    answer += (
        "You can ask a follow-up question such as "
        "\"How do we resolve this?\", "
        "\"Who is affected?\", "
        "\"When did this start?\", or "
        "\"Did the previous changes solve it?\""
    )

    return answer


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "PulseLoop API is running",
        "status": "online",
        "version": "4.1.0",
        "ai_enabled": True,
        "ai_provider": "Local PulseLoop Intelligence",
        "paid_openai_required": False,
        "hindsight_enabled": is_available(),
        "model": "local-hindsight",
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "service": "PulseLoop Backend",
        "ai": "connected",
        "ai_provider": "Local PulseLoop Intelligence",
        "paid_openai_required": False,
        "hindsight": (
            "connected"
            if is_available()
            else "not configured"
        ),
        "model": "local-hindsight",
    }


# =========================================================
# GET FEEDBACK
# =========================================================

@app.get("/feedback")
def get_feedback():

    return {
        "feedback": feedback_data,
        "total": len(
            feedback_data
        ),
    }


# =========================================================
# CREATE FEEDBACK
# =========================================================

@app.post("/feedback")
def create_feedback(
    data: FeedbackRequest
):

    text = clean_text(
        data.text
    )

    if not text:

        return {
            "success": False,
            "message": "Feedback cannot be empty.",
        }

    text_lower = text.lower()

    # -----------------------------------------------------
    # SENTIMENT
    # -----------------------------------------------------

    negative_words = [
        "bad",
        "failed",
        "fail",
        "slow",
        "problem",
        "issue",
        "error",
        "broken",
        "confusing",
        "difficult",
        "hate",
        "friction",
    ]

    positive_words = [
        "good",
        "great",
        "easy",
        "fast",
        "love",
        "better",
        "excellent",
        "clean",
        "improved",
    ]

    if any(
        word in text_lower
        for word in negative_words
    ):

        sentiment = "Negative"

    elif any(
        word in text_lower
        for word in positive_words
    ):

        sentiment = "Positive"

    else:

        sentiment = "Neutral"

    # -----------------------------------------------------
    # TOPIC
    # -----------------------------------------------------

    if any(
        word in text_lower
        for word in [
            "mobile",
            "phone",
            "payment",
        ]
    ):

        topic = "Mobile Payment"

    elif any(
        word in text_lower
        for word in [
            "checkout",
            "coupon",
            "cart",
        ]
    ):

        topic = "Checkout"

    elif any(
        word in text_lower
        for word in [
            "search",
            "filter",
        ]
    ):

        topic = "Search"

    elif any(
        word in text_lower
        for word in [
            "notification",
            "alert",
        ]
    ):

        topic = "Notifications"

    else:

        topic = "General Feedback"

    # -----------------------------------------------------
    # PRIORITY
    # -----------------------------------------------------

    high_priority_words = [
        "failed",
        "fail",
        "payment",
        "broken",
        "error",
    ]

    if (
        sentiment == "Negative"
        and any(
            word in text_lower
            for word in high_priority_words
        )
    ):

        priority = "High"

    elif sentiment == "Negative":

        priority = "Medium"

    else:

        priority = "Low"

    # -----------------------------------------------------
    # NEW FEEDBACK
    # -----------------------------------------------------

    new_feedback = {
        "id": len(
            feedback_data
        ) + 1,
        "avatar": "AI",
        "source": "New customer feedback",
        "text": text,
        "topic": topic,
        "sentiment": sentiment,
        "priority": priority,
        "time": "Just now",
        "created_at": datetime.now().isoformat(),
    }

    feedback_data.insert(
        0,
        new_feedback
    )

    # -----------------------------------------------------
    # STORE IN HINDSIGHT
    # -----------------------------------------------------

    memory_stored = False

    try:

        hindsight_result = store_feedback(
            new_feedback
        )

        if isinstance(
            hindsight_result,
            dict
        ):

            memory_stored = bool(
                hindsight_result.get(
                    "success",
                    False
                )
            )

    except Exception as error:

        print(
            "Hindsight storage error:",
            error
        )

    return {
        **new_feedback,
        "memory_stored": memory_stored,
    }


# =========================================================
# MEMORY RECALL
# =========================================================

@app.post("/memory")
def recall_memory(
    data: MemoryRequest
):

    query = clean_text(
        data.query
    )

    if not query:

        return {
            "success": False,
            "answer": (
                "Please enter a question for "
                "PulseLoop's memory."
            ),
            "memories": [],
        }

    result = get_hindsight_memories(
        query
    )

    if not result.get(
        "success"
    ):

        return {
            "success": False,
            "query": query,
            "answer": result.get(
                "message",
                "PulseLoop could not access "
                "Hindsight memory."
            ),
            "memories": [],
        }

    memories = result.get(
        "memories",
        []
    )

    if not memories:

        return {
            "success": True,
            "query": query,
            "answer": (
                "PulseLoop searched its historical "
                "memory but could not find a strongly "
                "related previous event."
            ),
            "memories": [],
            "memory_count": 0,
        }

    memory_text = extract_memory_text(
        memories
    )

    answer = (
        "PulseLoop found "
        f"{len(memories)} relevant historical "
        "memories.\n\n"
        f"{memory_text}"
    )

    return {
        "success": True,
        "query": query,
        "answer": answer,
        "memories": memories,
        "memory_count": len(
            memories
        ),
    }


# =========================================================
# CHATBOT
# =========================================================

@app.post("/chat")
def chat_with_pulseloop(
    data: ChatRequest
):

    message = clean_text(
        data.message
    )

    conversation = data.conversation

    if not message:

        return {
            "success": False,
            "answer": "",
            "memories": [],
            "memory_count": 0,
            "message": "Please enter a message.",
        }

    # =====================================================
    # UNDERSTAND CONVERSATION
    # =====================================================

    context = build_conversation_context(
        message,
        conversation
    )

    retrieval_query = context[
        "retrieval_query"
    ]

    intent = context[
        "intent"
    ]

    # =====================================================
    # HINDSIGHT RECALL
    # =====================================================

    memories: List[Dict[str, Any]] = []

    try:

        memory_result = get_hindsight_memories(
            retrieval_query
        )

        if isinstance(
            memory_result,
            dict
        ):

            if memory_result.get(
                "success",
                False
            ):

                memories = memory_result.get(
                    "memories",
                    []
                )

                if not isinstance(
                    memories,
                    list
                ):

                    memories = []

            else:

                print(
                    "Hindsight chat recall failed:",
                    memory_result.get(
                        "message",
                        "Unknown error"
                    )
                )

    except Exception as error:

        print(
            "Hindsight chat recall error:",
            error
        )

        memories = []

    # =====================================================
    # LOCAL ANSWER GENERATION
    # =====================================================

    answer = local_pulseloop_answer(
        message,
        memories,
        conversation
    )

    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "success": True,

        "answer": answer,

        "memories": memories,

        "memory_count": len(
            memories
        ),

        "model": "Local PulseLoop Intelligence",

        "query": message,

        "retrieval_query": retrieval_query,

        "intent": intent,

        "ai_mode": "local_hindsight",

        "paid_openai_required": False,

        "memory_available": bool(
            memories
        ),
    }


# =========================================================
# STATS
# =========================================================

@app.get("/stats")
def get_stats():

    return {

        "total_feedback": len(
            feedback_data
        ),

        "high_priority": sum(
            1
            for item in feedback_data
            if item["priority"] == "High"
        ),

        "positive": sum(
            1
            for item in feedback_data
            if item["sentiment"] == "Positive"
        ),

        "negative": sum(
            1
            for item in feedback_data
            if item["sentiment"] == "Negative"
        ),

        "neutral": sum(
            1
            for item in feedback_data
            if item["sentiment"] == "Neutral"
        ),
    }


# =========================================================
# AI INSIGHTS
# =========================================================

@app.post("/insights")
def generate_insight(
    data: InsightRequest
):

    query = data.query

    if not query:

        query = (
            "Analyze the historical customer feedback "
            "in PulseLoop. Identify the most important "
            "recurring product problem, how it changed "
            "over time, which users are affected, "
            "whether previous product changes solved it, "
            "and what the product team should do next."
        )

    try:

        result = reflect_on_memory(
            query
        )

        if not isinstance(
            result,
            dict
        ):

            return {
                "success": False,
                "message": (
                    "Invalid response from "
                    "Hindsight reflection."
                ),
                "answer": "",
                "sources": [],
            }

        if not result.get(
            "success"
        ):

            return {
                "success": False,
                "message": result.get(
                    "message",
                    "Unable to generate "
                    "product insight."
                ),
                "answer": "",
                "sources": [],
            }

        return {

            "success": True,

            "query": query,

            "answer": result.get(
                "answer",
                ""
            ),

            "sources": result.get(
                "sources",
                []
            ),

            "ai_mode": "hindsight",

            "paid_openai_required": False,
        }

    except Exception as error:

        print(
            "Insight generation error:",
            error
        )

        return {

            "success": False,

            "message": str(
                error
            ),

            "answer": "",

            "sources": [],
        }


# =========================================================
# MEMORY STATISTICS
# =========================================================

@app.get("/memory/stats")
def memory_stats():

    try:

        result = get_memory_stats()

        if isinstance(
            result,
            dict
        ):

            return result

        return {
            "success": False,
            "message": (
                "Invalid memory statistics response."
            ),
        }

    except Exception as error:

        print(
            "Memory statistics error:",
            error
        )

        return {
            "success": False,
            "message": str(error),
        }