def smart_name(name: str):

    name = re.sub(r'@\w+', '', name)

    season = re.findall(r'(S\d{1,2}|Season ?\d+)', name, re.I)
    episode = re.findall(r'(E\d{1,3}|Ep ?\d+)', name, re.I)
    quality = re.findall(r'(480p|720p|1080p|2160p|4k)', name, re.I)

    name = re.sub(r'\[.*?\]|\(.*?\)', '', name)
    name = re.sub(r'[._\-]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    base = name.title()
    extra = " ".join(season + episode + quality)

    return f"{base} {extra}".strip()
