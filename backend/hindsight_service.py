import os

from dotenv import load_dotenv
from hindsight_client import Hindsight


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

HINDSIGHT_BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "pulseloop"
)


# =========================================================
# HINDSIGHT CLIENT
# =========================================================

client = None

if HINDSIGHT_API_KEY:

    try:

        client = Hindsight(
            base_url=HINDSIGHT_BASE_URL,
            api_key=HINDSIGHT_API_KEY
        )

        print("Hindsight client initialized.")
        print(
            "Hindsight base URL:",
            HINDSIGHT_BASE_URL
        )
        print(
            "Hindsight bank:",
            HINDSIGHT_BANK_ID
        )

    except Exception as error:

        client = None

        print(
            "Hindsight client initialization failed:"
        )
        print(error)

else:

    print(
        "Hindsight API key is missing."
    )


# =========================================================
# AVAILABILITY
# =========================================================

def is_available():

    return client is not None


# =========================================================
# TEST CONNECTION
# =========================================================

def test_connection():

    if not client:

        return {
            "success": False,
            "connected": False,
            "bank_id": HINDSIGHT_BANK_ID,
            "message": (
                "Hindsight client is not configured. "
                "Check HINDSIGHT_API_KEY in .env."
            )
        }

    try:

        result = client.list_memories(
            bank_id=HINDSIGHT_BANK_ID,
            limit=1,
            offset=0
        )

        total = getattr(
            result,
            "total",
            0
        )

        try:
            total = int(total)
        except Exception:
            total = 0

        return {
            "success": True,
            "connected": True,
            "bank_id": HINDSIGHT_BANK_ID,
            "memory_count": total,
            "message": (
                "Hindsight connection is working "
                "and the PulseLoop memory bank is accessible."
            )
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight connection test failed:"
        )
        print(error_text)

        return {
            "success": False,
            "connected": False,
            "bank_id": HINDSIGHT_BANK_ID,
            "memory_count": 0,
            "message": error_text
        }


# =========================================================
# CREATE / CHECK MEMORY BANK
# =========================================================

def ensure_bank():

    if not client:

        return {
            "success": False,
            "message": (
                "Hindsight API key is not configured."
            ),
            "bank_id": HINDSIGHT_BANK_ID
        }

    try:

        # First check whether the bank is already usable.
        existing = client.list_memories(
            bank_id=HINDSIGHT_BANK_ID,
            limit=1,
            offset=0
        )

        total = getattr(
            existing,
            "total",
            0
        )

        try:
            total = int(total)
        except Exception:
            total = 0

        return {
            "success": True,
            "bank_id": HINDSIGHT_BANK_ID,
            "memory_count": total,
            "message": (
                "PulseLoop Hindsight bank is ready."
            )
        }

    except Exception as check_error:

        print(
            "Existing Hindsight bank check failed:"
        )
        print(check_error)

    # -----------------------------------------------------
    # BANK DOES NOT APPEAR TO EXIST
    # -----------------------------------------------------

    try:

        bank = client.create_bank(

            bank_id=HINDSIGHT_BANK_ID,

            name="PulseLoop Product Intelligence",

            background=(
                "Memory bank for PulseLoop, a product "
                "intelligence agent that learns from "
                "customer feedback, product changes, "
                "historical issues, recurring problems, "
                "sentiment, priorities, and outcomes."
            )
        )

        return {
            "success": True,
            "bank_id": getattr(
                bank,
                "bank_id",
                HINDSIGHT_BANK_ID
            ),
            "message": (
                "PulseLoop Hindsight bank created."
            )
        }

    except Exception as error:

        error_text = str(error)

        # Bank already exists.
        if (
            "already exists" in error_text.lower()
            or
            "already exist" in error_text.lower()
            or
            "409" in error_text
        ):

            return {
                "success": True,
                "bank_id": HINDSIGHT_BANK_ID,
                "message": (
                    "PulseLoop Hindsight bank already exists."
                )
            }

        return {
            "success": False,
            "bank_id": HINDSIGHT_BANK_ID,
            "message": error_text
        }


# =========================================================
# STORE CUSTOMER FEEDBACK
# =========================================================

def store_feedback(feedback):

    if not client:

        return {
            "success": False,
            "message": (
                "Hindsight API key is not configured."
            )
        }

    bank_status = ensure_bank()

    if not bank_status.get("success"):

        return bank_status

    content = f"""
PulseLoop customer feedback event.

Customer feedback:
{feedback.get("text", "")}

Topic:
{feedback.get("topic", "General Feedback")}

Sentiment:
{feedback.get("sentiment", "Neutral")}

Priority:
{feedback.get("priority", "Medium")}

Source:
{feedback.get("source", "Customer feedback")}

Timestamp:
{feedback.get("created_at", "Unknown")}

This event is part of PulseLoop's product intelligence history.

Use this information to identify:

- recurring customer problems
- emerging themes
- sentiment changes
- product impact
- affected users
- relationships with future product changes
- relationships with historical outcomes
"""

    try:

        result = client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=content,
            context="PulseLoop customer feedback"
        )

        print(
            "HINDSIGHT RETAIN SUCCESS"
        )

        print(result)

        return {
            "success": True,
            "message": (
                "Feedback stored in Hindsight memory."
            ),
            "bank_id": HINDSIGHT_BANK_ID,
            "result": str(result)
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight retain error:"
        )
        print(error_text)

        return {
            "success": False,
            "message": error_text,
            "bank_id": HINDSIGHT_BANK_ID
        }


# =========================================================
# RECALL HISTORICAL MEMORIES
# =========================================================

def recall_memories(query):

    if not client:

        return {
            "success": False,
            "message": (
                "Hindsight API key is not configured."
            ),
            "memories": []
        }

    query = str(query or "").strip()

    if not query:

        return {
            "success": False,
            "message": (
                "Memory query cannot be empty."
            ),
            "memories": []
        }

    bank_status = ensure_bank()

    if not bank_status.get("success"):

        return {
            "success": False,
            "message": bank_status.get(
                "message",
                "Hindsight bank is unavailable."
            ),
            "memories": []
        }

    try:

        result = client.recall(

            bank_id=HINDSIGHT_BANK_ID,

            query=query,

            budget="mid",

            max_tokens=4096
        )

        memories = []

        results = getattr(
            result,
            "results",
            []
        )

        if results is None:
            results = []

        for memory in results:

            if isinstance(
                memory,
                dict
            ):

                memory_id = memory.get(
                    "id",
                    ""
                )

                memory_type = memory.get(
                    "type",
                    "memory"
                )

                memory_text = memory.get(
                    "text",
                    ""
                )

                relevance = memory.get(
                    "score",
                    memory.get(
                        "relevance",
                        None
                    )
                )

                mentioned_at = memory.get(
                    "mentioned_at",
                    None
                )

            else:

                memory_id = getattr(
                    memory,
                    "id",
                    ""
                )

                memory_type = getattr(
                    memory,
                    "type",
                    "memory"
                )

                memory_text = getattr(
                    memory,
                    "text",
                    ""
                )

                relevance = getattr(
                    memory,
                    "score",
                    getattr(
                        memory,
                        "relevance",
                        None
                    )
                )

                mentioned_at = getattr(
                    memory,
                    "mentioned_at",
                    None
                )

            memory_text = str(
                memory_text or ""
            ).strip()

            if not memory_text:
                continue

            memories.append({

                "id": str(
                    memory_id or ""
                ),

                "type": str(
                    memory_type or "memory"
                ),

                "text": memory_text,

                "relevance": relevance,

                "mentioned_at": (
                    str(mentioned_at)
                    if mentioned_at
                    else None
                )
            })

        print(
            "HINDSIGHT RECALL"
        )

        print(
            "Query:",
            query
        )

        print(
            "Memories found:",
            len(memories)
        )

        return {

            "success": True,

            "query": query,

            "memories": memories,

            "memory_count": len(memories),

            "bank_id": HINDSIGHT_BANK_ID
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight recall error:"
        )

        print(error_text)

        return {

            "success": False,

            "query": query,

            "memories": [],

            "memory_count": 0,

            "message": error_text,

            "bank_id": HINDSIGHT_BANK_ID
        }


# =========================================================
# RECALL ALL AVAILABLE MEMORIES
# =========================================================

def get_all_memories(
    limit=100,
    offset=0
):

    if not client:

        return {
            "success": False,
            "message": (
                "Hindsight API key is not configured."
            ),
            "memories": []
        }

    try:

        bank_status = ensure_bank()

        if not bank_status.get("success"):

            return {
                "success": False,
                "message": bank_status.get(
                    "message",
                    "Hindsight bank unavailable."
                ),
                "memories": []
            }

        result = client.list_memories(

            bank_id=HINDSIGHT_BANK_ID,

            limit=limit,

            offset=offset
        )

        items = getattr(
            result,
            "items",
            []
        )

        if items is None:
            items = []

        memories = []

        for memory in items:

            if isinstance(
                memory,
                dict
            ):

                text = memory.get(
                    "text",
                    memory.get(
                        "content",
                        ""
                    )
                )

                memory_id = memory.get(
                    "id",
                    ""
                )

                memory_type = memory.get(
                    "type",
                    "memory"
                )

            else:

                text = getattr(
                    memory,
                    "text",
                    getattr(
                        memory,
                        "content",
                        ""
                    )
                )

                memory_id = getattr(
                    memory,
                    "id",
                    ""
                )

                memory_type = getattr(
                    memory,
                    "type",
                    "memory"
                )

            text = str(
                text or ""
            ).strip()

            if not text:
                continue

            memories.append({

                "id": str(
                    memory_id or ""
                ),

                "type": str(
                    memory_type or "memory"
                ),

                "text": text
            })

        total = getattr(
            result,
            "total",
            len(memories)
        )

        try:
            total = int(total)
        except Exception:
            total = len(memories)

        return {

            "success": True,

            "bank_id": HINDSIGHT_BANK_ID,

            "memories": memories,

            "memory_count": total,

            "returned": len(memories)
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight list memories error:"
        )

        print(error_text)

        return {

            "success": False,

            "message": error_text,

            "memories": [],

            "memory_count": 0
        }


# =========================================================
# REFLECT ON HISTORICAL MEMORY
# =========================================================

def reflect_on_memory(query):

    if not client:

        return {

            "success": False,

            "message": (
                "Hindsight API key is not configured."
            ),

            "answer": "",

            "sources": []
        }

    query = str(query or "").strip()

    if not query:

        return {

            "success": False,

            "message": (
                "Reflection query cannot be empty."
            ),

            "answer": "",

            "sources": []
        }

    bank_status = ensure_bank()

    if not bank_status.get("success"):

        return {

            "success": False,

            "message": bank_status.get(
                "message",
                "Hindsight bank unavailable."
            ),

            "answer": "",

            "sources": []
        }

    try:

        result = client.reflect(

            bank_id=HINDSIGHT_BANK_ID,

            query=query,

            budget="mid"
        )

        answer = getattr(
            result,
            "text",
            ""
        )

        if not answer:

            answer = getattr(
                result,
                "answer",
                ""
            )

        if not answer:

            answer = str(
                result
            )

        sources = []

        # Newer Hindsight SDK responses use
        # "based_on" for source memories.
        based_on = getattr(
            result,
            "based_on",
            []
        )

        if based_on:

            for source in based_on:

                if isinstance(
                    source,
                    dict
                ):

                    source_text = source.get(
                        "text",
                        source.get(
                            "content",
                            str(source)
                        )
                    )

                    relevance = source.get(
                        "relevance",
                        source.get(
                            "score",
                            None
                        )
                    )

                else:

                    source_text = getattr(
                        source,
                        "text",
                        getattr(
                            source,
                            "content",
                            str(source)
                        )
                    )

                    relevance = getattr(
                        source,
                        "relevance",
                        getattr(
                            source,
                            "score",
                            None
                        )
                    )

                sources.append({

                    "text": str(
                        source_text or ""
                    ),

                    "relevance": relevance
                })

        # Compatibility with older SDK responses.
        if not sources:

            old_sources = getattr(
                result,
                "sources",
                []
            )

            if old_sources:

                for source in old_sources:

                    if isinstance(
                        source,
                        dict
                    ):

                        source_text = source.get(
                            "text",
                            source.get(
                                "content",
                                str(source)
                            )
                        )

                        relevance = source.get(
                            "relevance",
                            source.get(
                                "score",
                                None
                            )
                        )

                    else:

                        source_text = getattr(
                            source,
                            "content",
                            getattr(
                                source,
                                "text",
                                str(source)
                            )
                        )

                        relevance = getattr(
                            source,
                            "relevance",
                            getattr(
                                source,
                                "score",
                                None
                            )
                        )

                    sources.append({

                        "text": str(
                            source_text or ""
                        ),

                        "relevance": relevance
                    })

        return {

            "success": True,

            "query": query,

            "answer": str(
                answer
            ).strip(),

            "sources": sources,

            "bank_id": HINDSIGHT_BANK_ID
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight reflection error:"
        )

        print(error_text)

        return {

            "success": False,

            "query": query,

            "answer": "",

            "sources": [],

            "message": error_text
        }


# =========================================================
# MEMORY STATISTICS
# =========================================================

def get_memory_stats():

    if not client:

        return {

            "success": False,

            "message": (
                "Hindsight API key is not configured."
            ),

            "memory_count": 0
        }

    try:

        bank_status = ensure_bank()

        if not bank_status.get("success"):

            return {

                "success": False,

                "message": bank_status.get(
                    "message",
                    "Hindsight bank unavailable."
                ),

                "memory_count": 0
            }

        result = client.list_memories(

            bank_id=HINDSIGHT_BANK_ID,

            limit=1,

            offset=0
        )

        total = getattr(
            result,
            "total",
            0
        )

        try:
            total = int(total)
        except Exception:
            total = 0

        return {

            "success": True,

            "bank_id": HINDSIGHT_BANK_ID,

            "memory_count": total,

            "message": (
                "Live Hindsight memory count retrieved."
            )
        }

    except Exception as error:

        error_text = str(error)

        print(
            "Hindsight memory statistics error:"
        )

        print(error_text)

        return {

            "success": False,

            "message": error_text,

            "memory_count": 0
        }

