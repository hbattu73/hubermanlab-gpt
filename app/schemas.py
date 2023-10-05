from pydantic import BaseModel, HttpUrl
from datetime import date

class Query(BaseModel):
    text: str

class Message(BaseModel):
    text: str

class Passage(BaseModel):
    video_id: str
    video_description: str
    video_tags: list
    start: str
    end: str
    clip_url: HttpUrl
    published: str 
    thumbnail: HttpUrl
    title: str
    content: str
    score: float

class Completion(BaseModel):
    completion: str
    passages: list[Passage]