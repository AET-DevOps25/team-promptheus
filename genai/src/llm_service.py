"""LLM service for centralized language model configuration and initialization."""

import os
from typing import cast

import structlog
from langchain.chat_models.base import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

logger = structlog.get_logger()


class LLMService:
    """Service for managing and configuring different LLM providers."""

    @staticmethod
    def create_llm(
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 60.0,
        model_override: str | None = None,
    ) -> BaseChatModel:
        """Create an LLM instance based on available API keys.

        Priority order:
        1. OpenAI (if OPENAI_API_KEY is available)
        2. Ollama (fallback, if OLLAMA_API_KEY is available)

        Args:
            temperature: Model temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate (None for unlimited)
            timeout: Request timeout in seconds
            model_override: Override the default model name

        Returns:
            Configured LLM instance (ChatOpenAI, or ChatOllama)

        Raises:
            ValueError: If no valid API key is found
        """
        # Check for OpenAI API key first
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            logger.info("Using OpenAI LLM provider")
            return LLMService._create_openai_llm(
                api_key=openai_api_key,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                model_override=model_override,
            )

        # Fall back to Ollama
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")

        if ollama_api_key or ollama_base_url:
            logger.info("Using Ollama LLM provider")
            connection_config = {"api_key": ollama_api_key, "base_url": ollama_base_url}
            return LLMService._create_ollama_llm(
                connection_config=connection_config,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
                model_override=model_override,
            )

        msg = "No valid LLM API key found. Please set one of: OPENAI_API_KEY, or OLLAMA_API_KEY"
        raise ValueError(msg)

    @staticmethod
    def _create_openai_llm(
        api_key: str,
        temperature: float,
        max_tokens: int | None,
        timeout: float,
        model_override: str | None,
    ) -> ChatOpenAI:
        """Create ChatOpenAI instance."""
        model_name = cast("str", model_override or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"))

        openai_instance = ChatOpenAI(
            model=model_name, api_key=SecretStr(api_key), temperature=temperature, timeout=timeout
        )

        if max_tokens is not None:
            openai_instance.max_tokens = max_tokens

        return openai_instance

    @staticmethod
    def _create_ollama_llm(
        connection_config: dict[str, str | None],
        temperature: float,
        max_tokens: int | None,
        timeout: float,
        model_override: str | None,
    ) -> ChatOllama:
        """Create ChatOllama instance."""
        model_name = cast("str", model_override or os.getenv("LANGCHAIN_MODEL_NAME", "llama3.3:latest"))

        api_key = connection_config.get("api_key")
        base_url = connection_config.get("base_url")
        base_url_final = base_url or "https://gpu.aet.cit.tum.de/ollama"

        # Build client kwargs with proper types
        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        client_kwargs: dict[str, object] = {"timeout": timeout}
        if headers:
            client_kwargs["headers"] = headers

        if timeout is not None:
            client_kwargs["timeout"] = timeout

        # For Ollama, use num_predict instead of max_tokens
        num_predict = max_tokens if max_tokens is not None else -1

        return ChatOllama(
            model=model_name,
            base_url=base_url_final,
            temperature=temperature,
            client_kwargs=client_kwargs,
            num_predict=num_predict,
        )

    @staticmethod
    def get_provider_info() -> dict[str, object]:
        """Get information about which LLM provider would be used."""
        openai_api_key = os.getenv("OPENAI_API_KEY")
        ollama_api_key = os.getenv("OLLAMA_API_KEY")
        ollama_base_url = os.getenv("OLLAMA_BASE_URL")

        if openai_api_key:
            return {
                "provider": "openai",
                "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                "available": True,
                "env_vars": {"api_key": "OPENAI_API_KEY", "model": "OPENAI_MODEL_NAME"},
            }
        if ollama_api_key or ollama_base_url:
            return {
                "provider": "ollama",
                "model": os.getenv("LANGCHAIN_MODEL_NAME", "llama3.3:latest"),
                "base_url": ollama_base_url or "https://gpu.aet.cit.tum.de/ollama",
                "available": True,
                "env_vars": {
                    "api_key": "OLLAMA_API_KEY",
                    "base_url": "OLLAMA_BASE_URL",
                    "model": "LANGCHAIN_MODEL_NAME",
                },
            }
        return {
            "provider": "none",
            "available": False,
            "error": "No valid API key found",
            "required_env_vars": [
                "OPENAI_API_KEY + OPENAI_MODEL_NAME",
                "OLLAMA_API_KEY/OLLAMA_BASE_URL + LANGCHAIN_MODEL_NAME",
            ],
        }

    @staticmethod
    def get_current_model_name() -> str:
        """Get the model name that would be used by the current provider."""
        provider_info = LLMService.get_provider_info()
        if provider_info["available"]:
            return str(provider_info["model"])
        return "unknown"
