import json
import re
import urllib.request
from datetime import datetime, timezone

PITCHING_URL = "https://stats.knbsbstats.nl/api/v1/stats/events/2026-lucky-day-hoofdklasse/index?section=players&stats-section=pitching&language=en"

def fetch_json(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "nl-NL,nl;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def parse_name(html):
    last = re.search(r'class="lastname">(.*?)<', html)
    first = re.search(r'class="firstname">(.*?)<', html)
    return f"{first.group(1)} {last.group(1)}" if first and last else html

def ip_to_float(ip_str):
    # "25.2" betekent 25 innings en 2 outs = 25.667
    parts = str(ip_str).split('.')
    innings = int(parts[0])
    outs = int(parts[1]) if len(parts) > 1 else 0
    return innings + outs / 3

def top5_laag(data, key, label, min_ip=5):
    # Laagste waarde wint (ERA)
    filtered = [p for p in data if p.get(key) is not None]
    filtered = [p for p in filtered if ip_to_float(p.get('pitch_ip', '0.0')) >= min_ip]
    filtered = sorted(filtered, key=lambda x: float(x[key]))[:5]
    return {
        "label": label,
        "leaders": [
            {
                "naam": parse_name(p['name']),
                "team": p['teamcode'],
                "waarde": str(p[key])
            }
            for p in filtered
        ]
    }

def top5_hoog(data, key, label, formatter=None):
    # Hoogste waarde wint
    filtered = [p for p in data if p.get(key, 0) > 0]
    filtered = sorted(filtered, key=lambda x: x[key], reverse=True)[:5]
    return {
        "label": label,
        "leaders": [
            {
                "naam": parse_name(p['name']),
                "team": p['teamcode'],
                "waarde": formatter(p[key]) if formatter else str(p[key])
            }
            for p in filtered
        ]
    }

def main():
    print(f"Ophalen van {PITCHING_URL}...")
    data = fetch_json(PITCHING_URL)
    pitching = data["data"]
    print(f"Pitchers ontvangen: {len(pitching)}")

    with open("pitching.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ pitching.json opgeslagen")

    output = {
        "bijgewerkt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "bron": PITCHING_URL,
        "categories": [
            top5_laag(pitching,  "era",      "ERA",             min_ip=5),
            top5_hoog(pitching,  "pitch_so", "Strikeouts"),
            top5_hoog(pitching,  "pitch_ip", "Innings Pitched", formatter=lambda v: str(v)),
            top5_hoog(pitching,  "pitch_win","Wins"),
        ]
    }

    with open("leaders.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("✅ leaders.json opgeslagen")

if __name__ == "__main__":
    main()
