import re

def smart_rename(name):

    # REMOVE TELEGRAM TAGS
    name = re.sub(r'@\w+', '', name)

    # REMOVE URLS
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    # REMOVE BRACKETS
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    # DETECT QUALITY
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)
    quality = quality[0].upper() if quality else ""

    # DETECT SEASON/EPISODE
    season = re.findall(r'(S\d{1,2})', name, re.I)
    episode = re.findall(r'(E\d{1,3})', name, re.I)

    # REMOVE JUNK WORDS
    name = re.sub(
        r'\b(HDRip|WEBRip|BluRay|x264|x265|HEVC|AAC|Dual Audio|ESub)\b',
        '',
        name,
        flags=re.I
    )

    # CLEAN SYMBOLS
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    # FINAL FORMAT (NETFLIX STYLE)
    final = name.title()

    if season:
        final += f" {season[0].upper()}"
    if episode:
        final += f" {episode[0].upper()}"
    if quality:
        final += f" {quality}"

    return final if final else "AniToon_File"


# ===== EXTRA: TITLE OPTIMIZER =====
def title_optimize(name):
    name = smart_rename(name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


# ===== EXTRA: SAFE NAME =====
def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)
