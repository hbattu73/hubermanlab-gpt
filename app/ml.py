import logging
import json
import asyncio
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sse_starlette.sse import ServerSentEvent

from config import settings
from globals import g
from schemas import Passage, Query, Message


logger = logging.getLogger(settings.logger_name)

# Zero-shot classify if query is a question or search term
async def zero_shot_classify(query: Query) -> str:
    headers = {
        "Authorization": f"Bearer {settings.hf_api_key}"
    }
    payload = {
        "inputs": query.text,
        "parameters": {
            "candidate_labels": ["question", "search term"]
        }
    }
    try:
        res = await g.hf_client.post(url=settings.hf_inference_endpoint, headers=headers, json=payload)
        scores = sorted(zip(res.json()['scores'], res.json()['labels']), reverse=True)
        logger.info(f"Query <{query.text}> classified as <{scores[0][1]}>")
        return scores[0][1]
    except Exception as err:
        logger.error(f"Unable to reach inference endpoint for zero-shot classification")
        logger.warning("Defaulting to scaled dense vector similarity search...")
        return "question"

async def splade_encode(query: Query) -> dict[str, list]:
    return g.splade.encode_queries(query.text)

# Ada
async def ada_encode(query: Query) -> list[float]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.openai_api_key}"
    }
    payload = {
        "model": settings.embedding_model,
        "input": query.text
    }
    try:
        dense = await g.ada_client.post(url=settings.embedding_endpoint, headers=headers, json=payload)
        return dense.json()['data'][0]['embedding']
    except Exception as err:
        logger.error(f"Unable to reach OpenAI Ada client. Sending Internal Server Error Response to client.")
        detail = "There was a problem encountered in the server. Please wait a couple of seconds before trying again."
        raise HTTPException(status_code=500, detail=detail)

# Chat Completion
async def gpt_complete(message: Message, passages: list[Passage]):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.openai_api_key}"
    }
    payload = {
        "model": settings.gpt_model,
        "messages": [
            {"role": "system", "content": settings.gpt_sys_message},
            {"role": "user", "content": message.text}
        ],
        "stream": True,
    }
    try:
        yield {
            "event": "passages",
            "data": json.dumps([jsonable_encoder(p) for p in passages])
        }
        async with g.gpt_client.stream('POST', url=settings.gpt_endpoint, headers=headers, json=payload) as response:
            async for raw in response.aiter_lines():
                line = raw.rstrip("\n")
                if not line: continue
                _, _, value = line.partition(":")
                if value.startswith(" "): value = value[1:]
                if value != "[DONE]":
                    chunk = json.loads(value)
                    yield {
                        "event": "gpt-response",
                        "data": json.dumps(chunk),
                        "retry": settings.stream_retry_timeout
                    }    
                else:
                    yield {
                        "event": "close",
                        "data": {}
                    }
                await asyncio.sleep(0.05)
    except Exception as err:
        logger.error(f"Unable to reach OpenAI GPT-Turbo client. Sending Internal Server Error Response to client.")
        logger.debug(err)
        detail = "There was a problem encountered in the server. Please wait a couple of seconds before trying again."
        yield ServerSentEvent(**{
            "event": "error", 
            "data": detail
        })
        return
    