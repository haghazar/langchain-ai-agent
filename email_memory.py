import json
from pathlib import Path
from typing import Any


class EmailMemoryStore:
    """
    Persistent email memory store.

    This class owns three memory types:

    1. Semantic memory:
       Stable facts about the user or preferences.

    2. Episodic memory:
       Concrete past examples that can influence future decisions.

    3. Procedural memory:
       Instructions that define how the email agent should behave.

    The store is persisted to a JSON file so procedural feedback permanently
    rewrites the agent's instructions.
    """

    def __init__(
        self,
        path: str = "email_memory_store.json",
        reset: bool = False,
    ):
        self.path = Path(path)

        if reset or not self.path.exists():
            self.data = self._default_data()
            self.save()
        else:
            self.data = self.load()

    def _default_data(self) -> dict[str, Any]:
        """
        Create default memory structure.
        """

        return {
            "semantic_facts": [],
            "episodic_examples": [],
            "procedural_instructions": [
                "Never send emails automatically.",
                "Always create a Gmail draft and require human review before sending.",
                "Use a concise, professional tone.",
            ],
        }

    def load(self) -> dict[str, Any]:
        """
        Load memory from JSON file.
        """

        with self.path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def save(self):
        """
        Save memory to JSON file.
        """

        with self.path.open("w", encoding="utf-8") as file:
            json.dump(
                self.data,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def add_semantic_fact(self, fact: str):
        """
        Store a stable semantic fact.
        """

        self.data["semantic_facts"].append(fact)
        self.save()

    def recall_semantic(self, query: str) -> list[str]:
        """
        Recall semantic facts using simple keyword overlap.

        This is intentionally deterministic for the homework demo.
        """

        query_tokens = self._tokens(query)
        matches = []

        for fact in self.data["semantic_facts"]:
            fact_tokens = self._tokens(fact)

            if query_tokens.intersection(fact_tokens):
                matches.append(fact)

        return matches

    def add_episode(
        self,
        email_text: str,
        decision: str,
        reason: str,
    ):
        """
        Store a concrete past email example.
        """

        episode = {
            "email_text": email_text,
            "decision": decision,
            "reason": reason,
        }

        self.data["episodic_examples"].append(episode)
        self.save()

    def retrieve_similar_episode(self, email_text: str) -> dict[str, str] | None:
        """
        Retrieve the most similar stored episode using keyword overlap.
        """

        email_tokens = self._tokens(email_text)

        best_episode = None
        best_score = 0

        for episode in self.data["episodic_examples"]:
            episode_tokens = self._tokens(episode["email_text"])
            score = len(email_tokens.intersection(episode_tokens))

            if score > best_score:
                best_score = score
                best_episode = episode

        if best_score == 0:
            return None

        return best_episode

    def get_procedural_instructions(self) -> list[str]:
        """
        Return current procedural instructions.
        """

        return list(self.data["procedural_instructions"])

    def rewrite_procedural_instructions(self, feedback: str):
        """
        Permanently rewrite procedural instructions based on user feedback.

        For this homework demo, we preserve safety instructions and append
        the new user feedback as an instruction.
        """

        safety_instructions = [
            "Never send emails automatically.",
            "Always create a Gmail draft and require human review before sending.",
        ]

        updated_instructions = safety_instructions + [
            feedback,
        ]

        self.data["procedural_instructions"] = updated_instructions
        self.save()

    def context(self) -> str:
        """
        Assemble all memory types into one readable context block.
        """

        parts = []

        parts.append("Semantic facts:")
        if self.data["semantic_facts"]:
            for fact in self.data["semantic_facts"]:
                parts.append(f"- {fact}")
        else:
            parts.append("- No semantic facts stored.")

        parts.append("")
        parts.append("Episodic examples:")
        if self.data["episodic_examples"]:
            for episode in self.data["episodic_examples"]:
                parts.append(
                    f"- Email: {episode['email_text']} | "
                    f"Decision: {episode['decision']} | "
                    f"Reason: {episode['reason']}"
                )
        else:
            parts.append("- No episodic examples stored.")

        parts.append("")
        parts.append("Procedural instructions:")
        for instruction in self.data["procedural_instructions"]:
            parts.append(f"- {instruction}")

        return "\n".join(parts)

    def _tokens(self, text: str) -> set[str]:
        """
        Convert text to simple lowercase tokens.
        """

        cleaned = (
            text.lower()
            .replace(".", " ")
            .replace(",", " ")
            .replace("?", " ")
            .replace("!", " ")
            .replace("'", " ")
            .replace('"', " ")
            .replace(":", " ")
            .replace(";", " ")
        )

        return {
            token
            for token in cleaned.split()
            if len(token) > 2
        }

    def demo(self):
        """
        Demo all three memory types.
        """

        print("=" * 100)
        print("WEEK 5 EMAIL MEMORY DEMO")
        print("=" * 100)

        print("\n1. Semantic memory")
        self.add_semantic_fact(
            "Hayk prefers concise, warm, professional email replies."
        )

        semantic_matches = self.recall_semantic(
            "What style should be used for Hayk's replies?"
        )

        print("Semantic recall result:")
        for match in semantic_matches:
            print(f"- {match}")

        print("\n2. Episodic memory")
        self.add_episode(
            email_text="Just checking if there are any updates.",
            decision="reply",
            reason="A follow-up from an important client should receive an acknowledgment.",
        )

        similar_episode = self.retrieve_similar_episode(
            "Just checking if there are any updates on this."
        )

        print("Similar episode result:")
        print(similar_episode)

        print("\n3. Procedural memory before feedback")
        for instruction in self.get_procedural_instructions():
            print(f"- {instruction}")

        self.rewrite_procedural_instructions(
            "Use a formal banking tone and avoid casual phrases."
        )

        print("\n4. Procedural memory after feedback")
        for instruction in self.get_procedural_instructions():
            print(f"- {instruction}")

        print("\n5. Full memory context")
        print(self.context())

        print("=" * 100)


if __name__ == "__main__":
    store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=True,
    )

    store.demo()

    print("\nReloading memory from JSON to prove persistence...")
    reloaded_store = EmailMemoryStore(
        path="email_memory_store.json",
        reset=False,
    )

    print("\nReloaded procedural instructions:")
    for instruction in reloaded_store.get_procedural_instructions():
        print(f"- {instruction}")