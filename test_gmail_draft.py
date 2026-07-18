from week5_gmail_client import GmailClient


def main():
    """
    Create one safe Gmail draft.

    This test proves:
    - Gmail authentication works
    - the agent can create a real Gmail draft
    - no email is sent
    """

    client = GmailClient()
    client.authenticate()

    draft = client.create_draft_reply(
        to="haykghazaryan84x@gmail.com",
        subject="Week 5 Gmail Draft Test",
        body=(
            "Dear Hayk,\n\n"
            "This is a test draft created by the Week 5 Gmail agent.\n\n"
            "This email was NOT sent automatically. "
            "It was only saved as a Gmail draft for human review.\n\n"
            "Best regards,\n"
            "Hayk Gmail Agent"
        ),
    )

    print("=" * 100)
    print("GMAIL DRAFT CREATED")
    print("=" * 100)
    print(f"Draft ID: {draft.draft_id}")
    print(f"Message ID: {draft.message_id}")
    print("The email was saved as a draft only. It was not sent.")
    print("=" * 100)


if __name__ == "__main__":
    main()