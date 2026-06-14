"""
Golden evaluation set for retrieval and answer-quality evaluation.

Each item contains:
- id: stable query id
- query: user question
- expected: substring used for retrieval evaluation
- reference: ideal answer used for answer-quality evaluation
- in_domain: whether the question is answerable from the private document
"""


GOLDEN_QUERIES = [
    {
        "id": "Q1A",
        "query": "How is an asset tracked in public chaincode state?",
        "expected": "UUID key",
        "reference": (
            "An asset is tracked by a UUID key in public chaincode state, "
            "and only ownership is recorded publicly."
        ),
        "in_domain": True,
    },
    {
        "id": "Q1B",
        "query": "What is publicly visible about the asset if its sensitive details are hidden?",
        "expected": "only ownership",
        "reference": (
            "Only the asset ownership is publicly visible. "
            "The sensitive asset details are hidden in private data collections."
        ),
        "in_domain": True,
    },
    {
        "id": "Q2A",
        "query": "Which organizations must endorse any transfer requests?",
        "expected": "owner’s organization and a regulator’s organization",
        "reference": (
            "A peer from the owner’s organization and a regulator’s organization "
            "must endorse any transfer requests."
        ),
        "in_domain": True,
    },
    {
        "id": "Q2B",
        "query": "Whose sign-off is required before the owner can hand the asset to someone else?",
        "expected": "owner’s organization and a regulator’s organization",
        "reference": (
            "The transfer requires endorsement from a peer in the owner’s organization "
            "and from a regulator’s organization."
        ),
        "in_domain": True,
    },
    {
        "id": "Q3A",
        "query": "How does the seller provide proof of ownership to the buyer?",
        "expected": "out of band",
        "reference": (
            "The seller provides proof by passing the private asset details to the buyer "
            "out of band, or by giving the buyer credentials to query the private data "
            "on the seller’s node or on the regulator’s node."
        ),
        "in_domain": True,
    },
    {
        "id": "Q3B",
        "query": "How can the buyer avoid simply trusting the seller’s word?",
        "expected": "verifies the hash",
        "reference": (
            "The buyer can verify that the private asset details match the public hash, "
            "instead of simply trusting the seller’s claim."
        ),
        "in_domain": True,
    },
    {
        "id": "Q4A",
        "query": "Where does the buyer record their bid details?",
        "expected": "buyer’s private data collection",
        "reference": (
            "The buyer records the bid details in their own private data collection."
        ),
        "in_domain": True,
    },
    {
        "id": "Q4B",
        "query": "Where is the buyer’s purchase proposal kept away from other channel members?",
        "expected": "buyer’s private data collection",
        "reference": (
            "The buyer’s purchase proposal or bid details are kept in the buyer’s "
            "own private data collection, away from other channel members."
        ),
        "in_domain": True,
    },
    {
        "id": "Q5A",
        "query": "What does the chaincode verify before transferring the asset?",
        "expected": "submitting client is the owner",
        "reference": (
            "Before transferring the asset, the chaincode verifies that the submitting "
            "client is the owner, verifies the private details against the hash in the "
            "seller’s collection, and verifies the bid details against the hash in the "
            "buyer’s collection."
        ),
        "in_domain": True,
    },
    {
        "id": "Q5B",
        "query": "What validation happens before the asset leaves the seller’s side?",
        "expected": "private details against the hash",
        "reference": (
            "Before the asset leaves the seller’s side, the chaincode validates that "
            "the submitting client is the owner, checks the private details against "
            "the hash in the seller’s collection, and checks the bid details against "
            "the hash in the buyer’s collection."
        ),
        "in_domain": True,
    },
]


def get_in_domain_queries():
    """
    Return only in-domain queries.

    These are the questions that should be answerable from the private document.
    """

    return [
        item
        for item in GOLDEN_QUERIES
        if item["in_domain"]
    ]


def main():
    """
    Print the golden evaluation set.
    """

    print(f"Total golden queries: {len(GOLDEN_QUERIES)}")
    print(f"In-domain queries: {len(get_in_domain_queries())}")
    print()

    for item in GOLDEN_QUERIES:
        print("=" * 80)
        print(f"ID: {item['id']}")
        print(f"Query: {item['query']}")
        print(f"Expected substring: {item['expected']}")
        print(f"Reference answer: {item['reference']}")
        print(f"In domain: {item['in_domain']}")
        print("=" * 80)
        print()


if __name__ == "__main__":
    main()