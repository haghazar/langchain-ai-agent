from dataclasses import dataclass

from email_memory import EmailMemoryStore


@dataclass
class EmailMessage:
    """
    Simple email input model.
    """

    sender: str
    subject: str
    body: str


@dataclass
class TriageDecision:
    """
    Result of email triage.
    """

    action: str
    reason: str
    memory_used: str


@dataclass
class DraftResult:
    """
    Result of email reply drafting.
    """

    subject: str
    body: str
    procedural_instructions_used: list[str]


class EmailTriageRouter:
    """
    Email triage router.

    This class owns the triage behavior.

    It uses:
    - procedural memory for rules/instructions
    - episodic memory for past examples

    Important homework proof:
    One episodic example can flip the decision without changing any hard-coded rule.
    """

    def __init__(self, memory_store: EmailMemoryStore):
        self.memory_store = memory_store

    def triage(self, email: EmailMessage) -> TriageDecision:
        """
        Decide what to do with an email.
        """

        email_text = self._email_to_text(email)

        similar_episode = self.memory_store.retrieve_similar_episode(
            email_text=email_text,
        )

        if similar_episode is not None:
            return TriageDecision(
                action=similar_episode["decision"],
                reason=(
                    "Decision influenced by similar episodic memory: "
                    + similar_episode["reason"]
                ),
                memory_used="episodic",
            )

        body_lower = email.body.lower()
        subject_lower = email.subject.lower()

        risky_keywords = [
            "legal",
            "court",
            "complaint",
            "deadline",
            "payment",
            "loan",
            "urgent",
        ]

        for keyword in risky_keywords:
            if keyword in body_lower or keyword in subject_lower:
                return TriageDecision(
                    action="reply",
                    reason=f"Email contains important keyword: {keyword}",
                    memory_used="rule",
                )

        return TriageDecision(
            action="archive",
            reason="No reply-required signal found.",
            memory_used="rule",
        )

    def _email_to_text(self, email: EmailMessage) -> str:
        """
        Convert email object to searchable text.
        """

        return f"{email.sender}\n{email.subject}\n{email.body}"


class EmailResponseAgent:
    """
    Email response agent.

    This class owns reply drafting behavior.

    It uses:
    - semantic memory for user style/preferences
    - procedural memory for instructions
    """

    def __init__(self, memory_store: EmailMemoryStore):
        self.memory_store = memory_store

    def draft_reply(
        self,
        email: EmailMessage,
        decision: TriageDecision,
    ) -> DraftResult:
        """
        Draft a safe Gmail reply.

        This does not send anything.
        """

        semantic_facts = self.memory_store.recall_semantic(
            "Hayk email reply style preference tone"
        )

        procedural_instructions = self.memory_store.get_procedural_instructions()

        tone_line = self._build_tone_line(
            semantic_facts=semantic_facts,
            procedural_instructions=procedural_instructions,
        )

        subject = self._build_reply_subject(email.subject)

        if decision.action != "reply":
            body = (
                "No reply draft was created because the triage decision was "
                f"`{decision.action}`."
            )

            return DraftResult(
                subject=subject,
                body=body,
                procedural_instructions_used=procedural_instructions,
            )

        body = (
            "Dear colleague,\n\n"
            "Thank you for your email.\n\n"
            "I have reviewed your message and will follow up accordingly. "
            "If any additional information is required, I will let you know.\n\n"
            f"{tone_line}\n\n"
            "Best regards,\n"
            "Hayk"
        )

        return DraftResult(
            subject=subject,
            body=body,
            procedural_instructions_used=procedural_instructions,
        )

    def _build_reply_subject(self, subject: str) -> str:
        """
        Build reply subject.
        """

        if subject.lower().startswith("re:"):
            return subject

        return f"Re: {subject}"

    def _build_tone_line(
        self,
        semantic_facts: list[str],
        procedural_instructions: list[str],
    ) -> str:
        """
        Build a visible line proving which memory affected the draft.
        """

        memory_notes = []

        if semantic_facts:
            memory_notes.append(
                "Style memory applied: " + "; ".join(semantic_facts)
            )

        if procedural_instructions:
            memory_notes.append(
                "Procedural instructions applied: "
                + "; ".join(procedural_instructions)
            )

        if not memory_notes:
            return "No stored memory instructions were applied."

        return " ".join(memory_notes)


class EmailAssistant:
    """
    Email assistant orchestrator.

    This demonstrates composition:

    EmailAssistant has-a memory_store.
    EmailAssistant has-a triage_router.
    EmailAssistant has-a response_agent.

    It does not inherit from those classes.
    """

    def __init__(
        self,
        memory_store: EmailMemoryStore,
        triage_router: EmailTriageRouter,
        response_agent: EmailResponseAgent,
    ):
        self.memory_store = memory_store
        self.triage_router = triage_router
        self.response_agent = response_agent
        self.processed_emails = []

    def remember_fact(self, fact: str):
        """
        Store semantic memory.
        """

        self.memory_store.add_semantic_fact(fact)

    def learn_from_example(
        self,
        email_text: str,
        decision: str,
        reason: str,
    ):
        """
        Store episodic memory.
        """

        self.memory_store.add_episode(
            email_text=email_text,
            decision=decision,
            reason=reason,
        )

    def apply_feedback(self, feedback: str):
        """
        Store procedural memory update.
        """

        self.memory_store.rewrite_procedural_instructions(feedback)

    def process_email(self, email: EmailMessage) -> dict:
        """
        Process one email end-to-end.
        """

        decision = self.triage_router.triage(email)
        draft = self.response_agent.draft_reply(email, decision)

        result = {
            "email": email,
            "decision": decision,
            "draft": draft,
            "memory_context": self.memory_store.context(),
        }

        self.processed_emails.append(result)

        return result

    def recall_style_without_email(self) -> list[str]:
        """
        Prove semantic memory can be recalled with no email in sight.
        """

        return self.memory_store.recall_semantic(
            "What style should be used for Hayk's replies?"
        )


def print_result(title: str, result: dict):
    """
    Print email assistant result.
    """

    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)

    decision = result["decision"]
    draft = result["draft"]

    print("Decision:")
    print(f"- Action: {decision.action}")
    print(f"- Reason: {decision.reason}")
    print(f"- Memory used: {decision.memory_used}")

    print("\nDraft:")
    print(f"Subject: {draft.subject}")
    print(draft.body)

    print("=" * 100)


def run_demo():
    """
    Demo semantic, episodic, and procedural memory end-to-end.
    """

    memory_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    triage_router = EmailTriageRouter(
        memory_store=memory_store,
    )

    response_agent = EmailResponseAgent(
        memory_store=memory_store,
    )

    assistant = EmailAssistant(
        memory_store=memory_store,
        triage_router=triage_router,
        response_agent=response_agent,
    )

    print("=" * 100)
    print("WEEK 5 EMAIL AGENT DEMO")
    print("=" * 100)

    print("\n1. Semantic memory: store and recall a fact with no email")
    assistant.remember_fact(
        "Hayk prefers concise, warm, professional email replies."
    )

    semantic_recall = assistant.recall_style_without_email()

    print("Semantic recall:")
    for fact in semantic_recall:
        print(f"- {fact}")

    print("\n2. Episodic memory: before adding example")

    follow_up_email = EmailMessage(
        sender="important.client@example.com",
        subject="Checking updates",
        body="Just checking if there are any updates on this.",
    )

    before_episode = assistant.process_email(follow_up_email)
    print_result(
        title="Before episodic example",
        result=before_episode,
    )

    print("\n3. Add ONE episodic example")

    assistant.learn_from_example(
        email_text="Just checking if there are any updates.",
        decision="reply",
        reason="A follow-up from an important client should receive an acknowledgment.",
    )

    print("Stored one episodic example.")

    print("\n4. Episodic memory: after adding example")

    after_episode = assistant.process_email(follow_up_email)
    print_result(
        title="After episodic example",
        result=after_episode,
    )

    print("\n5. Procedural memory: rewrite instructions permanently")

    print("Procedural instructions before feedback:")
    for instruction in memory_store.get_procedural_instructions():
        print(f"- {instruction}")

    assistant.apply_feedback(
        "Use a formal banking tone and avoid casual phrases."
    )

    print("\nProcedural instructions after feedback:")
    for instruction in memory_store.get_procedural_instructions():
        print(f"- {instruction}")

    procedural_email = EmailMessage(
        sender="client@example.com",
        subject="Loan payment question",
        body="Please clarify the payment deadline for the loan.",
    )

    after_procedural_feedback = assistant.process_email(procedural_email)
    print_result(
        title="After procedural feedback",
        result=after_procedural_feedback,
    )

    print("\n6. Reload JSON store to prove procedural persistence")

    reloaded_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=False,
    )

    print("Reloaded procedural instructions:")
    for instruction in reloaded_store.get_procedural_instructions():
        print(f"- {instruction}")

    print("=" * 100)


if __name__ == "__main__":
    run_demo()