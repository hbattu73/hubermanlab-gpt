import torch
import logging
import json
import redis.asyncio as redis

from httpx import AsyncClient
from pinecone_text.sparse import SpladeEncoder
from typing import Any
from contextlib import asynccontextmanager
from logging.config import dictConfig
from sse_starlette.sse import EventSourceResponse
from fastapi import status, BackgroundTasks, Request, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from pinecone_db import PineconeDB
from ml import splade_encode, ada_encode, gpt_complete
from utils import passage, gpt_message
from schemas import Query
from globals import g, GlobalsMiddleware


dictConfig(settings.logger.dict())
logger = logging.getLogger(settings.logger_name)

def startup() -> None:
    # Initialize connection to Pinecone
    pinecone_db = PineconeDB()
    g.set_default("pinecone_db", pinecone_db)
    # Load the ML models
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    splade = SpladeEncoder(device=device)
    hf_client = AsyncClient(timeout=5.0)
    ada_client = AsyncClient(timeout=10.0)
    gpt_client = AsyncClient(timeout=20.0)
    g.set_default("splade", splade)
    g.set_default("hf_client", hf_client)
    g.set_default("ada_client", ada_client)
    g.set_default("gpt_client", gpt_client)
    # Initialize connection to Redis
    connection = redis.Redis(
        host='usw1-unbiased-stingray-33643.upstash.io',
        port=33643,
        password='5a3bd41eefb543c988ec22afe00b95a7',
        ssl=True
    )
    g.set_default("redis_client", connection)
    logger.info("App initialized!")

async def shutdown() -> None:
    logger.info("Shutting down...")
    # Clean up the ML models and release the resources
    await g.hf_client.aclose()
    await g.ada_client.aclose()
    await g.gpt_client.aclose()
    await g.redis_client.flushall(asynchronous=True)
    await g.redis_client.close()
    g.cleanup()
    logger.info("Cleaned up resources...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    startup()
    yield
    await shutdown()

def create_app() -> FastAPI:
    app = None
    if settings.aws_env:
        app = FastAPI(
            title=settings.title,
            description=settings.description,
            version=settings.version
        )
        startup()
    else:
        app = FastAPI(
            title=settings.title,
            description=settings.description,
            version=settings.version,
            lifespan=lifespan
        )
    app.add_middleware(GlobalsMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    return app

app = create_app()

async def get_cache(query: Query) -> None | tuple[dict[str, list], None | list[float]]:
    cache = await g.redis_client.exists(query.text.lower())
    if not cache: return None, None
    logger.debug(f"Cache hit for query: {query.text}")
    embeddings = await g.redis_client.get(query.text.lower())
    dense, sparse = json.loads(embeddings)["dense"], json.loads(embeddings)["sparse"]
    return dense, sparse

async def set_cache(query: Query, dense: list[float], sparse: dict[str, list], exp: int):
    embeddings = {
        "dense": dense,
        "sparse": sparse
    }
    await g.redis_client.setex(query.text.lower(), exp, json.dumps(embeddings))


@app.post("/query")
async def query(payload: Query, background_tasks: BackgroundTasks) -> Any:
    dense, sparse = await get_cache(payload)
    if not (dense and sparse):
        logger.debug(f"Cache miss for query: {payload.text}")
        dense, sparse = await ada_encode(payload), await splade_encode(payload)
        background_tasks.add_task(set_cache, payload, dense, sparse, settings.expiry_time)

    matches = await g.pinecone_db.query_db(payload, dense, sparse)
    passages = [passage(m) for m in matches]
    message = gpt_message(payload, passages)
    gpt_comp = gpt_complete(message, passages)
    return EventSourceResponse(gpt_comp, media_type='text/event-stream')

@app.get("/", status_code=status.HTTP_200_OK)
async def healthcheck(request: Request):
    return {
        "title": request.app.title,
        "description": request.app.description,
        "version": request.app.version,
        "redis_ping": await g.redis_client.ping(),
        "health": "All is well!"
    }
