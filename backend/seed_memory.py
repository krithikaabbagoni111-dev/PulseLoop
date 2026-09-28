from hindsight_service import (
    ensure_bank,
    store_feedback,
    client,
    HINDSIGHT_BANK_ID
)


# ============================================================
# PULSELOOP DEMO MEMORY DATASET
# ============================================================
#
# This is a synthetic product-history dataset created
# specifically for the PulseLoop hackathon demonstration.
#
# IMPORTANT:
# Run this script only ONCE.
# Running it repeatedly will create duplicate memories.
# ============================================================


feedback_history = [

    {
        "text": (
            "Customers are reporting that checkout takes too many steps "
            "and some users abandon the purchase before payment."
        ),
        "topic": "Checkout",
        "sentiment": "Negative",
        "priority": "High",
        "source": "Support Ticket",
        "created_at": "2026-09-02"
    },

    {
        "text": (
            "I tried checking out three times today. The payment page "
            "keeps making me go back and enter the same information."
        ),
        "topic": "Checkout",
        "sentiment": "Negative",
        "priority": "High",
        "source": "App Review",
        "created_at": "2026-09-03"
    },

    {
        "text": (
            "Our customers like the new products, but checkout feels "
            "unnecessarily complicated compared with other apps."
        ),
        "topic": "Checkout",
        "sentiment": "Negative",
        "priority": "Medium",
        "source": "NPS Survey",
        "created_at": "2026-09-04"
    },

    {
        "text": (
            "Payment succeeds most of the time on desktop, but the "
            "mobile checkout experience is noticeably slower."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "Customer Interview",
        "created_at": "2026-09-05"
    },

    {
        "text": (
            "Android users are saying that the payment screen sometimes "
            "freezes after they switch between Wi-Fi and mobile data."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "Support Ticket",
        "created_at": "2026-09-10"
    },

    {
        "text": (
            "Checkout is much easier now, but I still had a payment "
            "failure when leaving Wi-Fi and moving to 5G."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "App Review",
        "created_at": "2026-09-16"
    },

    {
        "text": (
            "The new checkout flow is definitely faster on my laptop. "
            "I have not noticed the same improvement on Android."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "Medium",
        "source": "Customer Interview",
        "created_at": "2026-09-18"
    },

    {
        "text": (
            "I love the shorter checkout, but payment failed again when "
            "my phone changed from office Wi-Fi to mobile data."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "App Review",
        "created_at": "2026-09-20"
    },

    {
        "text": (
            "The checkout redesign solved most of my desktop problems. "
            "Mobile payment still feels unreliable."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "NPS Survey",
        "created_at": "2026-09-21"
    },

    {
        "text": (
            "Android alert disappeared again after moving from Wi-Fi "
            "to 5G. Payment eventually worked after reopening the app."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "Support Ticket",
        "created_at": "2026-09-23"
    },

    {
        "text": (
            "The redesigned checkout is much better overall. The only "
            "thing still frustrating me is payment reliability on mobile."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "Customer Interview",
        "created_at": "2026-09-24"
    },

    {
        "text": (
            "Desktop checkout feels excellent now. On Android, payment "
            "sometimes gets stuck when the network changes."
        ),
        "topic": "Mobile Payment",
        "sentiment": "Negative",
        "priority": "High",
        "source": "App Review",
        "created_at": "2026-09-25"
    },

]


# ============================================================
# PRODUCT HISTORY
# ============================================================

product_events = [

    {
        "date": "2026-09-08",
        "title": "Checkout redesign",
        "description": (
            "The product team reduced the number of checkout steps, "
            "simplified the payment form, and removed unnecessary "
            "confirmation screens."
        ),
        "outcome": (
            "Desktop checkout complaints decreased significantly "
            "after the redesign."
        )
    },

    {
        "date": "2026-09-15",
        "title": "Checkout outcome detected",
        "description": (
            "Historical feedback indicates that the checkout redesign "
            "successfully addressed the original desktop usability problem."
        ),
        "outcome": (
            "Desktop users reported a noticeably smoother checkout "
            "experience, while mobile payment complaints remained."
        )
    },

    {
        "date": "2026-09-19",
        "title": "Mobile payment investigation",
        "description": (
            "The product team began investigating payment failures "
            "reported by Android users."
        ),
        "outcome": (
            "The issue remained intermittent and appeared strongly "
            "connected to network transitions."
        )
    },

    {
        "date": "2026-09-25",
        "title": "New opportunity detected",
        "description": (
            "Recent customer feedback continues to mention mobile "
            "payment failures during Wi-Fi-to-mobile-data transitions."
        ),
        "outcome": (
            "PulseLoop should prioritize investigation of mobile "
            "network-transition handling in the payment flow."
        )
    },

]


def store_product_event(event):

    content = f"""
PulseLoop product history event.

Date:
{event["date"]}

Product action:
{event["title"]}

Description:
{event["description"]}

Observed outcome:
{event["outcome"]}

This event is part of the historical product journey used by
PulseLoop to connect customer feedback with product decisions
and measurable outcomes.
"""

    try:

        result = client.retain(
            bank_id=HINDSIGHT_BANK_ID,
            content=content,
            context="PulseLoop product action and outcome"
        )

        print(
            f"✓ Product event stored: {event['title']}"
        )

        return result

    except Exception as error:

        print(
            f"✗ Product event failed: {event['title']}"
        )

        print(error)


def main():

    print()
    print("=" * 60)
    print("       PULSELOOP MEMORY SEED")
    print("=" * 60)
    print()

    # Make sure the Hindsight bank exists.

    bank = ensure_bank()

    if not bank["success"]:

        print("✗ Could not prepare Hindsight memory bank.")
        print(bank["message"])
        return

    print("✓ Hindsight memory bank ready")
    print()

    # Store customer feedback.

    print("Storing customer feedback...")
    print()

    for feedback in feedback_history:

        result = store_feedback(feedback)

        if result.get("success"):

            print(
                f"✓ {feedback['created_at']} | "
                f"{feedback['topic']} | "
                f"{feedback['source']}"
            )

        else:

            print(
                f"✗ Failed: {feedback['created_at']}"
            )

            print(
                result.get(
                    "message",
                    "Unknown error"
                )
            )

    print()
    print("Storing product history...")
    print()

    # Store product actions and outcomes.

    for event in product_events:

        store_product_event(event)

    print()
    print("=" * 60)
    print("        MEMORY SEED COMPLETE")
    print("=" * 60)
    print()
    print(
        f"Customer feedback records: "
        f"{len(feedback_history)}"
    )
    print(
        f"Product history records: "
        f"{len(product_events)}"
    )
    print()
    print(
        "Wait a few seconds before running Recall or Reflect."
    )
    print()


if __name__ == "__main__":
    main()