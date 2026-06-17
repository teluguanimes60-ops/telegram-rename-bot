import re

# ===== QUALITY DETECTOR =====
def detect_quality(name):
    match = re.search(r'\b(144p|240p|360p|480p|720p|1080p|1440p|2160p|4k)\b', name, re.I)
    return match.group(0).upper() if match else ""

# ===== ULTRA CLEAN =====
def ultra_clean(name):

    # REMOVE @tags
    name = re.sub(r'@\w+', '', name)

    # REMOVE LINKS
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    # REMOVE BRACKETS
    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)

    # REMOVE CODECS
    name = re.sub(r'\b(x264|x265|HEVC|AAC|HDRip|WEBRip|BluRay|DVDRip)\b', '', name, flags=re.I)

    # REMOVE LAST JUNK WORD
    words = name.split()
    if len(words) > 3:
        words.pop()  # remove last waste word
    name = " ".join(words)

    # CLEAN SYMBOLS
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name)

    return name.strip()

# ===== FINAL SMART NAME =====
def smart_rename(name):

    quality = detect_quality(name)

    cleaned = ultra_clean(name)

    if quality:
        final = f"{cleaned} [{quality}]"
    else:
        final = cleaned

    return final.title() if final else "AniToon_File"
