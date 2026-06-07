from langchain_google_genai import ChatGoogleGenerativeAI


def test_gemini_chat() -> str:
    """
    Test ChatGoogleGenerativeAI with a simple question.
    """

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    response = llm.invoke("Answer in one short sentence: What is LangChain?")

    print("ChatGoogleGenerativeAI response:")
    print(response.content)
    print("-" * 60)

    return response.content