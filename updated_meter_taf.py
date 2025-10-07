
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re, json, os
from urllib.parse import urlparse
from datetime import datetime

# ---------------------------
# Parse METARs and TAFs dynamically
# ---------------------------
def parse_metars_tafs(text: str) -> dict:
    """Parse METAR and TAF strings into {station: {'METAR': str, 'TAF': str}}"""
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    data = {}

    # ---------- METAR ----------
    for m in re.finditer(r"METAR\s+(V[A-Z]{3,4})\s+([^=]*=)", text, re.I):
        station = m.group(1).upper()
        data.setdefault(station, {})["METAR"] = re.sub(r"\s+", " ", m.group(2).strip())

    for m in re.finditer(r"(^|\n)\s*(V[A-Z]{3,4})\s+(\d{6}Z\b[^=]*=)", text, re.I | re.M):
        station = m.group(2).upper()
        if "METAR" not in data.get(station, {}):
            data.setdefault(station, {})["METAR"] = re.sub(r"\s+", " ", m.group(3).strip())

    # ---------- TAF ----------
    for m in re.finditer(r"TAF\s+(V[A-Z]{3,4})\s+([^=]*=)", text, re.I):
        station = m.group(1).upper()
        data.setdefault(station, {})["TAF"] = re.sub(r"\s+", " ", m.group(2).strip())

    for m in re.finditer(r"(^|\n)\s*(V[A-Z]{3,4})\s+(\d{6}Z\s+\d{4}/\d{4}[^=]*=)", text, re.I | re.M):
        station = m.group(2).upper()
        if "TAF" not in data.get(station, {}):
            data.setdefault(station, {})["TAF"] = re.sub(r"\s+", " ", m.group(3).strip())

    # ---------- No data ----------
    for m in re.finditer(r"No data for\s+(V[A-Z]{3,4})", text, re.I):
        station = m.group(1).upper()
        data.setdefault(station, {}).setdefault("METAR", None)
        data.setdefault(station, {}).setdefault("TAF", None)

    return data


# ---------------------------
# Scraping dynamically (fixed)
# ---------------------------
async def scrape_url(url: str) -> dict:
    """Scrape URL and return {source_label: {station: {'METAR':..., 'TAF':...}}}"""
    print(f"🌍 Scraping: {url}")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            # ✅ Use DOMContentLoaded + timeout + wait delay
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(5000)
            html = await page.content()
            await browser.close()
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return {urlparse(url).netloc.replace('.', '_'): {}}

    # Extract clean text
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style"]):
        s.extract()
    text = soup.get_text("\n")

    source_label = urlparse(url).netloc.replace(".", "_")
    parsed = parse_metars_tafs(text)
    return {source_label: parsed}


# ---------------------------
# Aggregation & Comparison
# ---------------------------
async def scrape_all(sources_file=r"C:\Users\krishna.jaiswal\Downloads\scraping\matar_taf.txt"):
    with open(sources_file) as f:
        lines = [line.strip() for line in f if line.strip()]

    base_metar_url, base_taf_url = None, None
    urls = []

    for line in lines:
        if line.startswith("BASE_METAR="):
            base_metar_url = line.split("=", 1)[1].strip()
        elif line.startswith("BASE_TAF="):
            base_taf_url = line.split("=", 1)[1].strip()
        else:
            urls.append(line)

    if not base_metar_url or not base_taf_url:
        raise ValueError("Missing BASE_METAR= or BASE_TAF= in sources file!")

    print(f"\n🌐 Base METAR URL: {base_metar_url}")
    print(f"🌐 Base TAF URL:   {base_taf_url}\n")

    base_metar_data = await scrape_url(base_metar_url)
    base_taf_data = await scrape_url(base_taf_url)

    base_metar_source = list(base_metar_data.keys())[0]
    base_taf_source = list(base_taf_data.keys())[0]

    base_metar_stations = base_metar_data[base_metar_source]
    base_taf_stations = base_taf_data[base_taf_source]

    combined = {}

    for url in urls:
        print(f"🔍 Comparing -> {url}")
        parsed = await scrape_url(url)
        for source, stations in parsed.items():
            for station, obs in stations.items():
                # METAR comparison
                base_metar = base_metar_stations.get(station, {}).get("METAR")
                metar_value = obs.get("METAR")
                combined.setdefault(station, {}).setdefault("METAR", {"base": base_metar, "comparisons": []})
                combined[station]["METAR"]["comparisons"].append({source: metar_value})

                # TAF comparison
                base_taf = base_taf_stations.get(station, {}).get("TAF")
                taf_value = obs.get("TAF")
                combined.setdefault(station, {}).setdefault("TAF", {"base": base_taf, "comparisons": []})
                combined[station]["TAF"]["comparisons"].append({source: taf_value})

    # Evaluate match/partial/no_data
    for station, obs_types in combined.items():
        for dtype, info in obs_types.items():
            base_value = info["base"]
            comparisons = info["comparisons"]

            present = [list(r.keys())[0] for r in comparisons if list(r.values())[0] is not None]
            missing = [list(r.keys())[0] for r in comparisons if list(r.values())[0] is None]

            if base_value is None:
                status = "no_data"
            else:
                matches = [list(r.keys())[0] for r in comparisons if list(r.values())[0] == base_value]
                if len(matches) == len(comparisons):
                    status = "match"
                elif any(matches):
                    status = "partial_match"
                else:
                    status = "no_match"

            info.update({
                "present_sources": present,
                "missing_sources": missing,
                "status": status
            })

    return combined


# ---------------------------
# Save METAR and TAF results into separate folders
# ---------------------------
def save_results(data: dict):
    timestamp = datetime.utcnow().isoformat() + "Z"
    os.makedirs("metar", exist_ok=True)
    os.makedirs("taf", exist_ok=True)

    categorized = {
        "METAR": {"match": {}, "partial_match": {}, "no_match": {}, "no_data": {}},
        "TAF": {"match": {}, "partial_match": {}, "no_match": {}, "no_data": {}}
    }

    for station, types in data.items():
        for dtype, info in types.items():
            status = info["status"]
            categorized[dtype][status][station] = {dtype: info}

    # Save METAR results
    for status, stations in categorized["METAR"].items():
        if stations:
            filename = os.path.join("metar", f"results_metar_{status}.json")
            with open(filename, "w") as f:
                json.dump({timestamp: stations}, f, indent=2)
            print(f"✅ Saved {len(stations)} METAR stations in {filename}")

    # Save TAF results
    for status, stations in categorized["TAF"].items():
        if stations:
            filename = os.path.join("taf", f"results_taf_{status}.json")
            with open(filename, "w") as f:
                json.dump({timestamp: stations}, f, indent=2)
            print(f"✅ Saved {len(stations)} TAF stations in {filename}")


# ---------------------------
# Main runner
# ---------------------------
async def main():
    results = await scrape_all()
    save_results(results)


if __name__ == "__main__":
    asyncio.run(main())
