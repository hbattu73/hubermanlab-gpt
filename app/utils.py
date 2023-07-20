from schemas import Passage, Message, Query
from pydantic import HttpUrl
import datetime

def passage(m: dict) -> Passage:
    return Passage(video_id = m['metadata']['video_id'],
                start = format_timestamps(m['metadata']['start']),
                end = format_timestamps(m['metadata']['end']),
                clip_url = get_video_url(m['metadata']['video_id'], m['metadata']['start']),
                published = format_date(m['metadata']['published']),
                thumbnail = format_thumbnail(m['metadata']['video_id']),
                title = m['metadata']['title'],
                content = m['metadata']['content'],
                score = m['score'])

def gpt_message(query: Query, passages: list[Passage]) -> Message:
    message = f"Query: {query.text}"
    for p in passages:
        next_passage = f'\n\nPassage: """Source={p.title}, Content={p.content}"""'
        message += next_passage
    return Message(text=message)

def format_thumbnail(video_id: str) -> HttpUrl:
    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

def get_video_url(video_id: str, start: float) -> HttpUrl:
    return f"https://youtu.be/{video_id}?t={str(int(start))}"

def format_timestamps(seconds: float) -> str:
    return str(datetime.timedelta(seconds=seconds))

def format_date(date: datetime) -> str:
    months = {
        "01": "Jan", 
        "02": "Feb", 
        "03": "Mar", 
        "04": "Apr", 
        "05": "May", 
        "06": "Jun", 
        "07": "Jul", 
        "08": "Aug", 
        "09": "Sep", 
        "10": "Oct", 
        "11": "Nov", 
        "12": "Dec"
    }
    str_date = date.strftime("%m-%d-%Y")
    m_d_y = str_date.split("-")
    month, day, year = months[m_d_y[0]], m_d_y[1], m_d_y[2]
    return f"{month} {day}, {year}"
