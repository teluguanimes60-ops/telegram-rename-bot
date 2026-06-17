import re

def smart_rename(name):

    # REMOVE @words
    name = re.sub(r'@\w+', '', name)

    # REMOVE URLS
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    # REMOVE BRACKETS
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    # KEEP QUALITY (IMPORTANT FEATURE)
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)
    quality = quality[0] if quality else ""

    # REMOVE WASTE WORDS (LAST TAGS)
    name = re.sub(r'\b(HDRip|WEBRip|BluRay|x264|x265|HEVC|AAC|Dual Audio)\b', '', name, flags=re.I)

    # CLEAN SYMBOLS
    name = re.sub(r'[._\-]', ' ', name)

    # CLEAN SPACES
    name = re.sub(r'\s+', ' ', name).strip()

    # ADD QUALITY BACK
    if quality:
        name = f"{name} {quality.upper()}"

    return name.title() if name else "AniToon_File"
