# build_my.py — Malaysia-only playlist using iptv-org API
# Works with CSV or JSON streams endpoints.

import csv, io, json, time, urllib.request

OUT_M3U   = "playlist_malaysia.m3u"
OUT_STATS = "build_stats.txt"

COUNTRY_CODE = "MY"
STATUS_OK = {"online", "geo_blocked"}  # keep online + geo-blocked

API_BASE = "https://iptv-org.github.io/api"
URL_CHANNELS = f"{API_BASE}/channels.csv"
URL_STREAMS_CSV = f"{API_BASE}/streams.csv"
URL_STREAMS_JSON = f"{API_BASE}/streams.json"  # fallback

def fetch(url):
    with urllib.request.urlopen(url, timeout=40) as r:
        return r.read()

def read_csv_bytes(b):
    return list(csv.DictReader(io.StringIO(b.decode("utf-8", errors="replace"))))

def extinf_line(ch, stream_url):
    name  = (ch.get("name") or "").strip()
    logo  = (ch.get("logo") or ch.get("icon") or "").strip()
    gid   = (ch.get("id") or ch.get("tvg-id") or "").strip()
    group = (ch.get("categories") or ch.get("category") or "").strip()
    title = name.replace(",", " ")
    return (f'#EXTINF:-1 tvg-id="{gid}" tvg-name="{title}" '
            f'tvg-logo="{logo}" group-title="{group}",{title}\n{stream_url}\n')

def main():
    print("Downloading channels.csv from API…")
    channels = read_csv_bytes(fetch(URL_CHANNELS))

    print("Trying streams.csv from API…")
    streams = None
    tried_csv = tried_json = False

    # Try CSV first
    try:
        streams = read_csv_bytes(fetch(URL_STREAMS_CSV))
        tried_csv = True
        print("Using streams.csv")
    except Exception as e:
        print(f"streams.csv not available ({e}); falling back to streams.json…")

    # Fallback to JSON if CSV missing
    if streams is None:
        try:
            data = json.loads(fetch(URL_STREAMS_JSON).decode("utf-8", errors="replace"))
            tried_json = True
            # Normalize JSON -> list of dicts with keys like the CSV
            # JSON fields: channel, url, http_referrer, user_agent, status, etc.
            streams = []
            for s in data:
                streams.append({
                    "channel": s.get("channel") or s.get("channel_id") or "",
                    "url": s.get("url") or "",
                    "status": (s.get("status") or "").lower()
                })
            print("Using streams.json")
        except Exception as e:
            raise RuntimeError(
                "Failed to download streams from both CSV and JSON API endpoints.\n"
                f"Tried: {URL_STREAMS_CSV}\n       {URL_STREAMS_JSON}\nError: {e}"
            )

    # Build map of MY channels
    my_channels = {
        ch["id"]: ch
        for ch in channels
        if (ch.get("country") or "").strip().upper() == COUNTRY_CODE and ch.get("id")
    }

    # Collect streams for MY channels
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

    # Deduplicate
    seen, uniq = set(), []
    for ch, u in items:
        key = (ch.get("id", ""), u)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((ch, u))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Source: iptv-org API | Country: {COUNTRY_CODE} | Generated: {ts} UTC\n")
        for ch, u in uniq:
            f.write(extinf_line(ch, u))

    with open(OUT_STATS, "w", encoding="utf-8") as s:
        s.write(f"Generated: {ts} UTC\n")
        s.write(f"MY channels: {len(my_channels)}\n")
        s.write(f"Streams kept: {len(uniq)}\n")
        s.write(f"Streams source: {'CSV' if tried_csv else 'JSON'}\n")

    print(f"OK -> {OUT_M3U} ({len(uniq)} streams)")

if __name__ == "__main__":
    main()
