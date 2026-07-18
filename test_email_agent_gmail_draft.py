from email_agent import (
    EmailAssistant,
    EmailMessage,
    EmailResponseAgent,
    EmailTriageRouter,
)
from email_memory import EmailMemoryStore
from week5_gmail_client import GmailClient


def main():
    """
    End-to-end Gmail draft test.

    This proves:
    - EmailAssistant uses semantic/procedural memory
    - EmailTriageRouter decides whether reply is needed
    - EmailResponseAgent creates a draft body
    - GmailClient saves the result as a real Gmail draft
    - Nothing is sent automatically
    """

    memory_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    assistant = EmailAssistant(
        memory_store=memory_store,
        triage_router=EmailTriageRouter(memory_store),
        response_agent=EmailResponseAgent(memory_store),
    )

    assistant.remember_fact(
        "Hayk prefers concise, warm, professional email replies."
    )

    assistant.apply_feedback(
        "Use a formal banking tone and avoid casual phrases."
    )

    incoming_email = EmailMessage(
        sender="client@example.com",
        subject="Loan payment deadline",
        body="Please clarify the payment deadline for the loan.",
    )

    result = assistant.process_email(incoming_email)

    decision = result["decision"]
    draft = result["draft"]

    print("=" * 100)
    print("EMAIL ASSISTANT RESULT")
    print("=" * 100)
    print(f"Decision action: {decision.action}")
    print(f"Decision reason: {decision.reason}")
    print(f"Memory used: {decision.memory_used}")
    print("-" * 100)
    print("Generated draft:")
    print(f"Subject: {draft.subject}")
    print(draft.body)
    print("=" * 100)

    if decision.action != "reply":
        print("No Gmail draft created because triage decision was not reply.")
        return

    gmail_client = GmailClient()
    gmail_client.authenticate()

    gmail_draft = gmail_client.create_draft_reply(
        to="haykghazaryan84x@gmail.com",
        subject=draft.subject,
        body=(
            draft.body
            + "\n\n---\n"
            "Safety note: This draft was created by the Week 5 Email Agent. "
            "It was NOT sent automatically."
        ),
    )

    print("\n" + "=" * 100)
    print("REAL GMAIL DRAFT CREATED BY EMAIL ASSISTANT")
    print("=" * 100)
    print(f"Draft ID: {gmail_draft.draft_id}")
    print(f"Message ID: {gmail_draft.message_id}")
    print("The email was saved as a Gmail draft only. It was not sent.")
    print("=" * 100)


if __name__ == "__main__":
    main()