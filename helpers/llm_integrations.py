from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from .types import Model, Engine
from .llm_mappings import LLM_MAPPING


def get_llm(model: Model, temperature: float = 0.0) -> ChatAnthropic | ChatOpenAI:
    chat_engine: Engine = LLM_MAPPING.get(model, "gpt-4o")
    match chat_engine:
        case "openai":
            return ChatOpenAI(
                model=model, temperature=temperature, max_completion_tokens=16000
            )
        case "anthropic":
            return ChatAnthropic(model=model, temperature=temperature, max_tokens=8000)
        case "google":
            return ChatGoogleGenerativeAI(
                model=model, temperature=temperature, max_tokens=8000
            )
        case _:
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                max_completion_tokens=16000,
            )
