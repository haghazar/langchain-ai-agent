from config import Config
from chat_test import test_gemini_chat
from embeddings_test import test_gemini_embeddings


def main():
    """
    Main entry point for Step 4.

    This script:
    1. loads API keys from .env;
    2. tests Gemini chat model;
    3. tests Gemini embeddings;
    4. checks cosine similarity.
    """

    config = Config()
    config.print_config_status()

    print("-" * 60)

    test_gemini_chat()

    similarity_check = test_gemini_embeddings()

    if similarity_check:
        print("Gemini connection and embeddings test completed successfully.")
    else:
        print("Gemini connection and embeddings test failed.")


if __name__ == "__main__":
    main()