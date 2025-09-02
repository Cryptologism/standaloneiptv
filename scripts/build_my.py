# build_my.py — Malaysia-only playlist from iptv-org/database (/data/*.csv)

import csv, io, time, urllib.request

OUT_M3U   = "playlist_malaysia.m3u"
OUT_STATS = "build_stats.txt"

COUNTRY_CODE = "MY"
STATUS_OK = {"online", "geo_blocked"}  # keep online + geo-blocked

# ---------- helpers ----------
def fetch(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")

def try_urls(urls):
    last_err = None
    for u in urls:
        try:
            return fetch(u), u
        except Exception as e:
            last_err = e
    raise RuntimeError(f"Failed to download from all candidates:\n" +
                       "\n".join(urls) + f"\nLast error: {last_err}")

def read_csv(text):
    return list(csv.DictReader(io.StringIO(text)))

def extinf_line(ch, stream_url):
    name  = (ch.get("name") or "").strip()
    logo  = (ch.get("logo") or ch.get("icon") or "").strip()
    gid   = (ch.get("id") or ch.get("tvg-id") or "").strip()
    group = (ch.get("categories") or ch.get("category") or "").strip()
    title = name.replace(",", " ")
    return (f'#EXTINF:-1 tvg-id="{gid}" tvg-name="{title}" '
            f'tvg-logo="{logo}" group-title="{group}",{title}\n{stream_url}\n')

# ---------- main ----------
def main():
    print("Downloading iptv-org/database CSVs...")

    # Candidate raw URLs (branch + path variants)
    bases = [
        "https://raw.githubusercontent.com/iptv-org/database/main/data",
        "https://raw.githubusercontent.com/iptv-org/database/master/data",
    ]
    channels_urls = [f"{b}/channels.csv" for b in bases]
    streams_urls  = [f"{b}/streams.csv"  for b in bases] + [f"{b}/links.csv" for b in bases]

    channels_csv, used_channels = try_urls(channels_urls)
    print(f"OK channels.csv -> {used_channels}")
    streams_csv, used_streams   = try_urls(streams_urls)
    print(f"OK streams      -> {used_streams}")

    channels = read_csv(channels_csv)
    streams  = read_csv(streams_csv)

    # Malaysia channels only
    my_channels = {
        ch["id"]: ch
        for ch in channels
        if (ch.get("country") or "").strip().upper() == COUNTRY_CODE and ch.get("id")
    }

    # Streams for those channels
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

    # Write playlist + stats
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
