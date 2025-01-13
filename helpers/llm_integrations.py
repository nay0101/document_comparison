from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from .types import Model, Engine
from .llm_mappings import LLM_MAPPING

load_dotenv()


def get_llm(model: Model) -> ChatAnthropic | ChatOpenAI:
    chat_engine: Engine = LLM_MAPPING.get(model, "gpt-4o")
    match chat_engine:
        case "openai":
            return ChatOpenAI(model=model, temperature=0.0, max_completion_tokens=16000)
        case "anthropic":
            return ChatAnthropic(model=model, temperature=0.0, max_tokens=8000)
        case "google":
            return ChatGoogleGenerativeAI(model=model, temperature=0.0, max_tokens=8000)
        case _:
            return ChatOpenAI(
                model="gpt-4o-mini", temperature=0.0, max_completion_tokens=16000
            )
