import re

def detect_quality(name):
    match = re.search(r'(144p|240p|360p|480p|720p|1080p|2160p|4k)', name, re.I)
    return match.group(0).upper() if match else ""

def detect_episode(name):
    match = re.search(r'(S\d+E\d+)', name, re.I)
    return match.group(0).upper() if match else ""

def ultra_clean(name):

    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+|www\.\S+', '', name)
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'\b(x264|x265|HEVC|AAC|HDRip|WEBRip|BluRay)\b', '', name, flags=re.I)

    words = name.split()
    if len(words) > 4:
        words.pop()

    name = " ".join(words)

    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()

def smart_rename(name):

    quality = detect_quality(name)
    episode = detect_episode(name)

    clean = ultra_clean(name)

    final = clean

    if episode:
        final += f" {episode}"

    if quality:
        final += f" [{quality}]"

    return final.title() if final else "AniToon_File"
