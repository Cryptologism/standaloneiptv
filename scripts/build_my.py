import csv, io, time, urllib.request

RAW_BASE = "https://raw.githubusercontent.com/iptv-org/database/master"
URL_CHANNELS = f"{RAW_BASE}/channels.csv"
URL_STREAMS  = f"{RAW_BASE}/streams.csv"  # if iptv-org renames, change to links.csv

OUT_M3U   = "playlist_malaysia.m3u"
OUT_STATS = "build_stats.txt"

COUNTRY_CODE = "MY"
STATUS_OK = {"online", "geo_blocked"}

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
    channels = read_csv(fetch(URL_CHANNELS))
    streams  = read_csv(fetch(URL_STREAMS))

    my_channels = {ch["id"]: ch for ch in channels if ch.get("country","").upper() == COUNTRY_CODE and ch.get("id")}

    items = []
    for s in streams:
        cid = (s.get("channel") or s.get("channel_id") or "").strip()
        if cid in my_channels:
            url = (s.get("url") or "").strip()
            status = (s.get("status") or "").strip().lower()
            if url and (not status or status in STATUS_OK):
                items.append((my_channels[cid], url))

    seen, uniq = set(), []
    for ch,u in items:
        key = (ch.get("id",""), u)
        if key not in seen:
            seen.add(key)
            uniq.append((ch,u))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Malaysia playlist generated {ts} UTC\n")
        for ch,u in uniq:
            f.write(extinf_line(ch,u))

    with open(OUT_STATS,"w",encoding="utf-8") as s:
        s.write(f"Generated {ts} UTC\nMY channels: {len(my_channels)}\nStreams kept: {len(uniq)}\n")

    print(f"OK -> {OUT_M3U} ({len(uniq)} streams)")

if __name__ == "__main__":
    main()
