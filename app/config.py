import os
from pydantic import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class LogConfig(BaseSettings):
    # Logging config
    logger_name: str = os.getenv("LOGGER_NAME")
    log_level: str = os.getenv("LOG_LEVEL")
    log_format: str = "%(levelprefix)s | %(asctime)s | %(message)s"
    version = 1
    disable_existing_loggers = False
    formatters = {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": log_format,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    }
    handlers = {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    }
    loggers = {
        logger_name: {"handlers": ["default"], "level": log_level},
    }

class Settings(BaseSettings):
    # FastAPI Stuff
    title: str = "hubermanGPT"
    description: str = "Generative QA App on the Huberman Lab Podcast"
    version: str = "0.1.0"
    # Hugging Face Stuff
    hf_api_key: str = os.getenv("HUGGINGFACE_API_KEY")
    hf_inference_endpoint: str = "https://s2anvoabfag2is7a.us-east-1.aws.endpoints.huggingface.cloud"
    # Pinecone Stuff
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY")
    pinecone_env: str = os.getenv("PINECONE_ENV")
    pinecone_index: str = "huberman-search"
    pinecone_namespace: str = "nocontext-default"
    # Pinecone Querying Stuff
    hybrid_scale: bool = True
    top_k: int = 10
    sparse_alpha_value: float = 0.3
    dense_alpha_value: float = 0.8
    # OpenAI Stuff
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    embedding_model: str = "text-embedding-ada-002"
    embedding_endpoint: str = "https://api.openai.com/v1/embeddings"
    gpt_model: str = "gpt-3.5-turbo-16k-0613"
    gpt_endpoint: str = "https://api.openai.com/v1/chat/completions"
    gpt_sys_message: str = "You are a helpful AI agent designed to help users better understand the content of the episodes in the Huberman Lab podcast. Your task is to answer the subsequent query to the best of your ability by using the following passages from your podcast, which are delimited by triple quotes. If the answer cannot be found, write 'Unfortunately, I don't believe I've covered that topic in my podcast. Please note that my podcast is limited to neuroscience and its connections to human perception, behavior and health.' Crucially, be accurate, concise, and clear."
    # Redis Stuff
    expiry_time: int = 120
    # Logging Stuff
    logger_name: str = os.getenv("LOGGER_NAME")
    log_level: str = os.getenv("LOG_LEVEL")
    logger: LogConfig = LogConfig()
    # TODO: ADD SOME STUFF FOR RATE LIMITS
    stream_retry_timeout: int = 3000   # milliseconds
    # TODO: ADD CORS ORIGINS WHEN YOU GET TO THAT PART
    origins: list = [
        "http://localhost",
        "http://localhost:5173"
    ]

settings = Settings()
