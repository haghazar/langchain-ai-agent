import base64
from dataclasses import dataclass
from email.message import EmailMessage as MimeEmailMessage
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


@dataclass
class GmailMessageSummary:
    """
    Small readable Gmail message summary.
    """

    message_id: str
    thread_id: str
    sender: str
    subject: str
    snippet: str


@dataclass
class GmailDraftResult:
    """
    Result returned after creating a Gmail draft.
    """

    draft_id: str
    message_id: str


class GmailClient:
    """
    Gmail adapter for Week 5.

    This class owns:
    - OAuth credentials path
    - token path
    - Gmail API service
    - Gmail scopes

    Safety:
    - This client can read recent emails.
    - This client can create drafts.
    - This client does NOT send emails.
    """

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
    ):
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.scopes = [
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
        ]
        self.service = None

    def authenticate(self):
        """
        Authenticate with Gmail API and create the Gmail service.
        """

        if not self.credentials_path.exists():
            raise FileNotFoundError(
                "credentials.json was not found. "
                "Download OAuth Desktop credentials from Google Cloud Console "
                "and place the file in the project root."
            )

        credentials = None

        if self.token_path.exists():
            credentials = Credentials.from_authorized_user_file(
                str(self.token_path),
                self.scopes,
            )

        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path),
                    self.scopes,
                )
                credentials = flow.run_local_server(port=0)

            self.token_path.write_text(
                credentials.to_json(),
                encoding="utf-8",
            )

        self.service = build(
            "gmail",
            "v1",
            credentials=credentials,
        )

        return self

    def list_recent_messages(self, max_results: int = 5) -> list[GmailMessageSummary]:
        """
        Read recent Gmail messages.

        This only returns summaries. It does not modify Gmail.
        """

        self._ensure_authenticated()

        response = (
            self.service.users()
            .messages()
            .list(
                userId="me",
                maxResults=max_results,
            )
            .execute()
        )

        raw_messages = response.get("messages", [])

        summaries = []

        for raw_message in raw_messages:
            message = (
                self.service.users()
                .messages()
                .get(
                    userId="me",
                    id=raw_message["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject"],
                )
                .execute()
            )

            headers = message.get("payload", {}).get("headers", [])

            sender = self._get_header(headers, "From")
            subject = self._get_header(headers, "Subject")
            snippet = message.get("snippet", "")

            summaries.append(
                GmailMessageSummary(
                    message_id=message["id"],
                    thread_id=message.get("threadId", ""),
                    sender=sender,
                    subject=subject,
                    snippet=snippet,
                )
            )

        return summaries

    def create_draft_reply(
        self,
        to: str,
        subject: str,
        body: str,
        thread_id: str | None = None,
    ) -> GmailDraftResult:
        """
        Create a Gmail draft.

        This does not send the email.
        """

        self._ensure_authenticated()

        mime_message = MimeEmailMessage()
        mime_message["To"] = to
        mime_message["Subject"] = subject
        mime_message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(
            mime_message.as_bytes()
        ).decode("utf-8")

        draft_body: dict[str, Any] = {
            "message": {
                "raw": encoded_message,
            }
        }

        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        draft = (
            self.service.users()
            .drafts()
            .create(
                userId="me",
                body=draft_body,
            )
            .execute()
        )

        return GmailDraftResult(
            draft_id=draft["id"],
            message_id=draft["message"]["id"],
        )

    def _ensure_authenticated(self):
        """
        Ensure service is ready.
        """

        if self.service is None:
            self.authenticate()

    def _get_header(
        self,
        headers: list[dict],
        name: str,
    ) -> str:
        """
        Get one email header by name.
        """

        for header in headers:
            if header.get("name", "").lower() == name.lower():
                return header.get("value", "")

        return ""


if __name__ == "__main__":
    client = GmailClient()

    print("=" * 100)
    print("WEEK 5 GMAIL CLIENT CHECK")
    print("=" * 100)

    try:
        client.authenticate()

        print("Gmail authentication works.")

        messages = client.list_recent_messages(max_results=3)

        print("\nRecent Gmail messages:")
        for index, message in enumerate(messages, start=1):
            print("-" * 100)
            print(f"{index}. From: {message.sender}")
            print(f"Subject: {message.subject}")
            print(f"Snippet: {message.snippet}")
            print(f"Message ID: {message.message_id}")
            print(f"Thread ID: {message.thread_id}")

        print("=" * 100)

    except FileNotFoundError as error:
        print("Gmail credentials are not ready yet.")
        print(error)
        print("=" * 100)