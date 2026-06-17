import re

def smart_name(name: str):

    # ===== REMOVE @tags =====
    name = re.sub(r'@\w+', '', name)

    # ===== REMOVE URLs =====
    name = re.sub(r'https?://\S+|www\.\S+', '', name)

    # ===== KEEP QUALITY (IMPORTANT FEATURE) =====
    # (DO NOT REMOVE 720p, 1080p, 4K etc)

    # ===== REMOVE BRACKETS =====
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)

    # ===== CLEAN SYMBOLS =====
    name = re.sub(r'[._\-]', ' ', name)

    # ===== REMOVE EXTRA SPACES =====
    name = re.sub(r'\s+', ' ', name).strip()

    # ===== REMOVE LAST WASTE WORD =====
    parts = name.split(" ")
    if len(parts) > 2:
        parts = parts[:-1]  # remove last word

    final = " ".join(parts)

    return final.title() if final else "AniToon_File"
