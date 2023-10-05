from supabase import create_client, Client
from supabase.client import SupabaseException
from datasets import load_dataset
from collections import defaultdict
import json

def huberman_metadata(token: str) -> dict:
    metadata = load_dataset("hbattu/huberman-youtube-metadata", token=token)["train"]
    def modify_yt_url(row):
        row["url"] = "https://youtu.be/" + row["video_id"]
        return row
    def modify_thumbnail(row):
        row["thumbnail"] = f"https://img.youtube.com/vi/{row['video_id']}/maxresdefault.jpg"
        return row
    def add_col(meta):
        embed_url_col = [f"https://www.youtube.com/embed/{row['video_id']}" for row in meta]
        return meta.add_column("embed_url", embed_url_col)

    metadata = add_col(metadata.map(modify_yt_url).map(modify_thumbnail))
    channel_meta = defaultdict(lambda: defaultdict(dict))
    for row in metadata:
       channel_meta[row["video_id"]] = row
    
    return channel_meta

def init_supabase(url: str, key: str) -> Client:
    try:
        supabase: Client = create_client(url, key)
        return supabase
    except SupabaseException:
        print("Invalid something. Check credentials passed in.")

def upsert_data(supabase: Client, channel_meta: dict) -> None:
    try:
        for video_id in channel_meta:
            episode_meta = channel_meta[video_id]
            data, count = supabase.table("episodes").insert({
                "id": video_id,
                "title": episode_meta["title"],
                "description": episode_meta["description"],
                "url": episode_meta["url"],
                "embed_url": episode_meta["embed_url"],
                "thumbnail": episode_meta["thumbnail"],
                "keywords": json.dumps(episode_meta["keywords"]),
                "published": episode_meta["published"]
            }).execute()
    except Exception as e:
        print("Error in upserting to Supabase -> ", e)



if __name__ == "__main__":
    hf_token = input("Enter HF token: ")
    channel_meta = huberman_metadata(hf_token)
    db_url = input("Enter Supabase URL: ")
    db_key = input("Enter Supabase service role secret key: ")
    supabase = init_supabase(url=db_url, key=db_key)
    # Upsert to Supabase
    upsert_data(supabase, channel_meta)

    