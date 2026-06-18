import re

def netflix_style(name):
    name = name.replace(".", " ").replace("_", " ")
    name = re.sub(r'\s+', ' ', name)

    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)

    base = re.sub(r'(S\d+.*|E\d+.*|480p|720p|1080p|2160p|4k)', '', name, flags=re.I)

    return f"{base.strip().title()} {' '.join(season)} {' '.join(episode)} {' '.join(quality)}".strip()


def smart_name(name: str):

    # REMOVE TAGS
    name = re.sub(r'@\w+', '', name)
    name = re.sub(r'https?://\S+', '', name)

    # CLEAN BRACKETS
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    # EXTRACT DATA
    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)

    # REMOVE TRASH WORDS
    name = re.sub(r'\b(HDRip|WEBRip|BluRay|x264|x265|HEVC|AAC|Dual Audio|ESub)\b', '', name, flags=re.I)

    # CLEAN SYMBOLS
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    base = name.title()
    extra = " ".join(season + episode + quality)

    final = f"{base} {extra}".strip()

    return final if final else "AniToon_File"


# ===== BATCH RENAME =====
def batch_rename(files):
    return [smart_name(f) for f in files]


# ===== AI STYLE CLEANER =====
def ai_clean(name):
    name = name.lower()
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.title()
