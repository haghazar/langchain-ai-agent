import os
from dataclasses import dataclass, field
from dotenv import load_dotenv


@dataclass
class Config:
    """
    Application configuration class.

    This class loads API keys from the .env file
    and validates that required keys exist.
    """

    __google_api_key: str | None = field(default=None, init=False)
    __openai_api_key: str | None = field(default=None, init=False)

    def __post_init__(self):
        """
        This method is called automatically after Config object is created.
        It loads environment variables and validates API keys.
        """

        load_dotenv()

        self.__google_api_key = os.getenv("GOOGLE_API_KEY")
        self.__openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.__google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY is missing. Please add it to your .env file."
            )

        if not self.__openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is missing. Please add it to your .env file."
            )

    @property
    def google_api_key(self) -> str:
        """
        Return Google Gemini API key.
        """

        return self.__google_api_key

    @property
    def openai_api_key(self) -> str:
        """
        Return OpenAI API key.
        """

        return self.__openai_api_key

    def print_config_status(self):
        """
        Print safe status information without exposing full API keys.
        """

        print("Configuration loaded successfully.")
        print(f"GOOGLE_API_KEY loaded: {self.__mask_key(self.__google_api_key)}")
        print(f"OPENAI_API_KEY loaded: {self.__mask_key(self.__openai_api_key)}")

    @staticmethod
    def __mask_key(api_key: str | None) -> str:
        """
        Hide most of the API key for safe printing.
        """

        if not api_key:
            return "Not found"

        if len(api_key) <= 8:
            return "****"

        return f"{api_key[:6]}...{api_key[-4:]}"