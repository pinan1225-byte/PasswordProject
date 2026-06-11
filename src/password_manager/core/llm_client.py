"""LLM Client factory supporting multiple providers (OpenAI, Doubao, etc.)."""

from typing import Optional
from openai import OpenAI

from src.password_manager.config import get_settings


class LLMClient:
    """
    Universal LLM client supporting multiple providers.

    Supports:
    - OpenAI (GPT models)
    - Doubao (DeepSeek models)
    - OpenAI-compatible APIs
    """

    def __init__(self):
        """Initialize LLM client."""
        self.settings = get_settings()
        self._client: Optional[OpenAI] = None

    @property
    def client(self) -> OpenAI:
        """
        Get OpenAI client instance.

        Works with OpenAI-compatible APIs including:
        - OpenAI official API
        - Doubao (https://ark.cn-beijing.volces.com/api/v3/)
        - SENSEAUTO services
        - Other OpenAI-compatible services
        """
        if self._client is None:
            api_key = self.settings.llm_api_key
            api_base = self.settings.llm_base_url

            if not api_key:
                raise ValueError(
                    "LLM API key not configured. "
                    "Please set LLM_API_KEY (or legacy SENSEAUTO_OPENAI_API_KEY) in .env"
                )

            import httpx
            http_client = httpx.Client(verify=self.settings.LLM_SSL_VERIFY) if not self.settings.LLM_SSL_VERIFY else None

            # For OpenAI provider, use official API if no custom base URL
            if self.settings.LLM_PROVIDER == "openai" and not api_base:
                self._client = OpenAI(api_key=api_key, http_client=http_client)
            elif self.settings.LLM_PROVIDER == "doubao" and not api_base:
                # Default Doubao API endpoint
                self._client = OpenAI(
                    api_key=api_key,
                    base_url="https://ark.cn-beijing.volces.com/api/v3/",
                    http_client=http_client,
                )
            else:
                # Custom endpoint or explicitly configured base URL (including senseauto)
                if not api_base:
                    raise ValueError(
                        f"LLM_BASE_URL is required for provider '{self.settings.LLM_PROVIDER}' "
                        "or when using custom providers. "
                        "Please set LLM_BASE_URL in .env"
                    )
                self._client = OpenAI(
                    api_key=api_key,
                    base_url=api_base,
                    http_client=http_client,
                )

        return self._client

    @property
    def model(self) -> str:
        """Get configured model name."""
        return self.settings.llm_model_name

    @property
    def provider(self) -> str:
        """Get configured LLM provider."""
        return self.settings.LLM_PROVIDER

    def create_chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 100,
    ) -> str:
        """
        Create a chat completion and return the response text.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response

        Returns:
            The generated text response

        Raises:
            RuntimeError: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_msg = f"LLM API call failed with provider '{self.provider}': {str(e)}"
            raise RuntimeError(error_msg) from e

    def __repr__(self) -> str:
        """String representation of LLM client."""
        return f"LLMClient(provider={self.provider}, model={self.model})"
