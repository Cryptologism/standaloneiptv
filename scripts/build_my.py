# ---------- BEGIN PYTHON (build_my.py) ----------
import csv, io, sys, time, urllib.request

RAW_BASE = "https://raw.githubusercontent.com/iptv-org/database/master"
URL_CHANNELS = f"{RAW_BASE}/channels.csv"
URL_STREAMS  = f"{RAW_BASE}/streams.csv"  # change to links.csv if iptv-org renames later

OUT_M3U   = "playlist_malaysia.m3u"
OUT_STATS = "build_stats.txt"

COUNTRY_CODE = "MY"   # Malaysia
STATUS_OK = {"online", "geo_blocked"}  # keep streams that are online or geo-blocked

def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))

def extinf_line(ch, stream_url):
    name  = (ch.get("name") or "").strip()
    logo  = (ch.get("logo") or ch.get("icon") or "").strip()
    gid   = (ch.get("id") or ch.get("tvg-id") or "").strip()
    group = (ch.get("categories") or ch.get("category") or "").strip()
    title = name.replace(",", " ")
    return f'#EXTINF:-1 tvg-id="{gid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{group}",{title}\n{stream_url}\n'

def main():
    print("Downloading iptv-org/database CSVs...")
    channels_csv = fetch(URL_CHANNELS)
    streams_csv  = fetch(URL_STREAMS)

    channels = read_csv(channels_csv)
    streams  = read_csv(streams_csv)

    my_channels = {}
    for ch in channels:
        if (ch.get("country") or "").strip().upper() == COUNTRY_CODE:
            cid = (ch.get("id") or "").strip()
            if cid:
                my_channels[cid] = ch

    items = []
    for s in streams:
        cid = (s.get("channel") or s.get("channel_id") or "").strip()
        if not cid or cid not in my_channels:
            continue
        status = (s.get("status") or "").strip().lower()
        url    = (s.get("url") or "").strip()
        if not url:
            continue
        if status and status not in STATUS_OK:
            continue
        items.append((my_channels[cid], url))

    # dedupe
    seen = set()
    uniq = []
    for ch, u in items:
        key = (ch.get("id",""), u)
        if key in seen: 
            continue
        seen.add(key)
        uniq.append((ch,u))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Source: iptv-org/database | Country: {COUNTRY_CODE} | Generated: {ts} UTC\n")
        for ch, u in uniq:
            f.write(extinf_line(ch, u))

    with open(OUT_STATS, "w", encoding="utf-8") as s:
        s.write(f"Generated: {ts} UTC\n")
        s.write(f"MY channels: {len(my_channels)}\n")
        s.write(f"Streams kept: {len(uniq)}\n")

    print(f"OK -> {OUT_M3U} ({len(uniq)} streams)")

if __name__ == "__main__":
    main()
# ----------- END PYTHON (build_my.py) -----------
