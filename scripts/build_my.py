import csv, io, json, time, urllib.request

URL_CHANNELS = "https://iptv-org.github.io/api/channels.csv"
URL_STREAMS  = "https://iptv-org.github.io/api/streams.json"
OUT_M3U      = "playlist_malaysia.m3u"
OUT_STATS    = "build_stats.txt"
COUNTRY_CODE = "MY"

def fetch(url):
    with urllib.request.urlopen(url, timeout=40) as r:
        return r.read()

def read_csv_bytes(b):
    return list(csv.DictReader(io.StringIO(b.decode("utf-8"))))

def main():
    print("Downloading channels + streams…")
    channels = read_csv_bytes(fetch(URL_CHANNELS))
    streams  = json.loads(fetch(URL_STREAMS).decode("utf-8"))

    my_channels = {c["id"]: c for c in channels if c["country"].upper() == COUNTRY_CODE}

    uniq, seen = [], set()
    for s in streams:
        cid, url = s.get("channel"), s.get("url")
        if cid in my_channels and url:
            key = (cid, url)
            if key not in seen:
                seen.add(key)
                uniq.append((my_channels[cid], url))

    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    with open(OUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write(f"# Malaysia playlist | Generated {ts} UTC\n")
        for ch,u in uniq:
            f.write(f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" '
                    f'tvg-logo="{ch["logo"]}" group-title="{",".join(ch["categories"].split(";"))}",'
                    f'{ch["name"]}\n{u}\n')

    with open(OUT_STATS,"w") as s:
        s.write(f"Generated {ts} UTC\nChannels: {len(my_channels)}\nStreams: {len(uniq)}\n")

    print(f"OK -> {OUT_M3U} ({len(uniq)} streams)")

if __name__ == "__main__":
    main()
