class ConversationMemory:
    """
    Simple conversation memory.

    It has:
    - recent turn buffer
    - rolling summary when the buffer becomes too long

    This is intentionally simple because Week 3 says:
    No new framework.
    """

    def __init__(self, max_turns: int = 4):
        self.max_turns = max_turns
        self.turns = []
        self.rolling_summary = ""

    def add_turn(self, user_message: str, assistant_message: str):
        """
        Add one user/assistant turn.
        """

        self.turns.append(
            {
                "user": user_message,
                "assistant": assistant_message,
            }
        )

        self._roll_if_needed()

    def _roll_if_needed(self):
        """
        Move old turns into a simple rolling summary.

        This is not LLM summarization. It is deterministic and transparent.
        """

        while len(self.turns) > self.max_turns:
            old_turn = self.turns.pop(0)

            summary_line = (
                f"User asked: {old_turn['user']} "
                f"Assistant answered: {old_turn['assistant']}"
            )

            if self.rolling_summary:
                self.rolling_summary += "\n" + summary_line
            else:
                self.rolling_summary = summary_line

    def context(self):
        """
        Return the assembled memory context injected into the agent each turn.
        """

        parts = []

        if self.rolling_summary:
            parts.append("Rolling summary:")
            parts.append(self.rolling_summary)

        if self.turns:
            parts.append("Recent turns:")

            for index, turn in enumerate(self.turns, start=1):
                parts.append(f"Turn {index} user: {turn['user']}")
                parts.append(f"Turn {index} assistant: {turn['assistant']}")

        if not parts:
            return "No previous conversation context."

        return "\n".join(parts)

    def clear(self):
        """
        Clear memory.
        """

        self.turns = []
        self.rolling_summary = ""