# build_my.py  (Malaysia-only playlist from iptv-org/database)

import csv, io, time, urllib.request

# --- CONFIG ---
BRANCH = "main"  # iptv-org/database default branch
RAW_BASE = f"https://raw.githubusercontent.com/iptv-org/database/{BRANCH}"

URL_CHANNELS = f"{RAW_BASE}/channels.csv"
URL_STREAMS_PRIMARY = f"{RAW_BASE}/streams.csv"   # older name used by iptv-org
URL_STREAMS_FALLBACK = f"{RAW_BASE}/links.csv"    # newer name in some commits

OUT_M3U   = "playlist_malaysia.m3u"
OUT_STATS = "build_stats.txt"

COUNTRY_CODE = "MY"
STATUS_OK = {"online", "geo_blocked"}  # keep online + geo-blocked (optional)

# --- HELPERS ---
def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def fetch_or_die(url):
    try:
        return fetch(url)
    except Exception as e:
        raise RuntimeError(f"Failed to download: {url}\n{e}")

def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))

def extinf_line(ch, stream_url):
    name  = (ch.get("name") or "").strip()
    logo  = (ch.get("logo") or ch.get("icon") or "").strip()
    gid   = (ch.get("id") or ch.get("tvg-id") or "").strip()
    group = (ch.get("categories") or ch.get("category") or "").strip()
    title = name.replace(",", " ")
    return (
        f'#EXTINF:-1 tvg-id="{gid}" tvg-name="{title}" '
        f'tvg-logo="{logo}" group-title="{group}",{title}\n{stream_url}\n'
    )

# --- MAIN ---
def main():
    print("Downloading iptv-org/database CSVs...")

    # channels.csv (must exist on branch=main)
    channels_csv = fetch_or_die(URL_CHANNELS)

    # streams: try streams.csv then links.csv
    try:
        streams_csv = fetch(URL_STREAMS_PRIMARY)
        print("Using streams.csv")
    except Exception:
        streams_csv = fetch_or_die(URL_STREAMS_FALLBACK)
        print("Using links.csv")

    channels = read_csv(channels_csv)
    streams  = read_csv(streams_csv)

    # Malaysia channels only
    my_channels = {
        ch["id"]: ch
        for ch in channels
        if (ch.get("country") or "").strip().upper() == COUNTRY_CODE and ch.get("id")
    }

    # Keep streams for those channels, filter by status
    items = []
    for s in streams:
        cid = (s.get("channel") or s.get("channel_id") or "").strip()
        if not cid or cid not in my_channels:
            continue
        url = (s.get("url") or "").strip()
        status = (s.get("status") or "").strip().lower()
        if not url:
            continue
        if status and status not in STATUS_OK:
            continue
        items.append((my_channels[cid], url))

    # Deduplicate by (channel_id, url)
    seen, uniq = set(), []
    for ch, u in items:
        k = (ch.get("id", ""), u)
        if k in seen:
            continue
        seen.add(k)
        uniq.append((ch, u))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Source: iptv-org/database | Country: {COUNTRY_CODE} | Generated: {ts} UTC\n")
        for ch, u in uniq:
            f.write(extinf_line(ch, u))

    with open(OUT_STATS, "w", encoding="utf-8") as s:
        s.write(f"Generated: {ts} UTC\n")
        s.write(f"M
