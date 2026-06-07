from langchain_google_genai import GoogleGenerativeAIEmbeddings
from vector_utils import cosine_similarity


def test_gemini_embeddings() -> bool:
    """
    Test GoogleGenerativeAIEmbeddings on 3 sentences.

    The test verifies that:
    1. vectors are generated;
    2. vector count is 3;
    3. semantically similar sentences have higher cosine similarity
       than unrelated sentences.
    """

    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview"
    )

    sentences = [
        "I love programming in Python.",
        "Python coding is very enjoyable for me.",
        "The weather is rainy today."
    ]

    vectors = embeddings.embed_documents(sentences)

    if not vectors:
        raise ValueError("No vectors were generated.")

    if len(vectors) != len(sentences):
        raise ValueError(
            f"Expected {len(sentences)} vectors, but got {len(vectors)}."
        )

    print("Embedding test:")
    print(f"Number of vectors: {len(vectors)}")
    print(f"Vector dimension: {len(vectors[0])}")
    print("-" * 60)

    similarity_0_1 = cosine_similarity(vectors[0], vectors[1])
    similarity_0_2 = cosine_similarity(vectors[0], vectors[2])

    print("Cosine similarity results:")
    print(f"Sentence 1 vs Sentence 2: {similarity_0_1}")
    print(f"Sentence 1 vs Sentence 3: {similarity_0_2}")
    print("-" * 60)

    similarity_check = similarity_0_1 > similarity_0_2

    print(f"Similarity check returns: {similarity_check}")

    if similarity_check:
        print("SUCCESS: Similar sentences scored higher than unrelated sentences.")
    else:
        print("FAILED: Similar sentences did not score higher.")

    print("-" * 60)

    return similarity_check