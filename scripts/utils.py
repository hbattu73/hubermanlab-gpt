import json
import os
from constants import AUDIO_PATH, MP3_PATH

def preprocess_metadata(meta):
    # embedding title, keywords, and description with the content
    # to provide a global context for insightful retrieval
    title = meta['title'].split('|')[0].rstrip() if '|' in meta['title'] else meta['title']
    remove_keywords = set(['huberman', 'neuroscience', 'podcast'])
    keywords = [k for k in meta['keywords'] if not remove_keywords & set(k.split())]
    description = meta['description'].split('\n')[0]
    meta['title'] = title
    meta['keywords'] = keywords
    meta['description'] = description
    return meta


def write_to_jsonl(meta):
    metadata = preprocess_metadata(meta)
    audio_file = 'mp3/' + metadata['video_id'] + '.mp3'
    metadata['file_name'] = audio_file
    with open(os.path.join(AUDIO_PATH, 'metadata.jsonl'), 'a', encoding='utf8') as meta_file:
        json.dump(metadata, meta_file)
        meta_file.write('\n')

