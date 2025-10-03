

import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re, json
from urllib.parse import urlparse
from datetime import datetime


# ---------------------------
# Parse METARs dynamically
# ---------------------------
def parse_metars(text: str) -> dict:
    """Parse METAR strings into {station: metar}"""
    text = text.replace('\xa0', ' ').replace('\u200b', '')
    metar_dict = {}

    # Standard "METAR VXXX .... ="
    for m in re.finditer(r"METAR\s+(V[A-Z]{3,4})\s+([^=]*=)", text, re.I):
        metar_dict[m.group(1).upper()] = re.sub(r"\s+", " ", m.group(2).strip())

    # IMD style "VXXX 251800Z .... ="
    for m in re.finditer(r"(^|\n)\s*(V[A-Z]{3,4})\s+(\d{6}Z\b[^=]*=)", text, re.I | re.M):
        code = m.group(2).upper()
        if code not in metar_dict:
            metar_dict[code] = re.sub(r"\s+", " ", m.group(3).strip())

    # No data
    for m in re.finditer(r"No data for\s+(V[A-Z]{3,4})", text, re.I):
        metar_dict.setdefault(m.group(1).upper(), None)

    return metar_dict


# ---------------------------
# Scraping dynamically
# ---------------------------
async def scrape_url(url: str) -> dict:
    """Scrape URL and return {source_label: {station: metar}}"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="networkidle")
        html = await page.content()
        await browser.close()

    # Extract text only
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style"]):
        s.extract()
    text = soup.get_text("\n")

    # Dynamic label = domain name
    source_label = urlparse(url).netloc.replace(".", "_")

    # Parse METARs
    metars = parse_metars(text)
    return {source_label: metars}


# ---------------------------
# Aggregation & Comparison
# ---------------------------
async def scrape_all(sources_file=r"C:\Users\krishna.jaiswal\Downloads\scraping\venv\sources.txt"):
    with open(sources_file) as f:
        urls = [line.strip() for line in f if line.strip()]  # remove empty lines

    combined = {}

    for url in urls:
        print(f"Scraping -> {url}")
        parsed = await scrape_url(url)

        for source, stations in parsed.items():
            for station, value in stations.items():
                combined.setdefault(station, {}).setdefault("METAR", {"raw": []})
                combined[station]["METAR"]["raw"].append({source: value})

    # Comparison logic
    for station, types in combined.items():
        for dtype, info in types.items():
            raws = info["raw"]

            present = [list(r.keys())[0] for r in raws if list(r.values())[0] is not None]
            missing = [list(r.keys())[0] for r in raws if list(r.values())[0] is None]
            values = [list(r.values())[0] for r in raws if list(r.values())[0]]
            representative = values[0] if values else None

            if len(values) == 0:
                status = "no_data"
            elif len(set(values)) == 1:
                status = "match"
            else:
                status = "partial_match"

            info.update({
                "present_sources": present,
                "missing_sources": missing,
                "representative": representative,
                "status": status
            })

    return combined


# ---------------------------
# Save results into separate files
# ---------------------------
def save_results(data: dict):
    timestamp = datetime.utcnow().isoformat() + "Z"

    categorized = {"match": {}, "partial_match": {}, "no_data": {}}

    for station, info in data.items():
        status = info["METAR"]["status"]
        categorized[status][station] = info

    # Save each category separately
    for status, stations in categorized.items():
        if stations:  # only save if not empty
            filename = f"results_{status}.json"
            wrapped = {timestamp: stations}
            with open(filename, "w") as f:
                json.dump(wrapped, f, indent=2)
            print(f"✅ Saved {len(stations)} stations in {filename}")


# ---------------------------
# Main runner
# ---------------------------
async def main():
    results = await scrape_all()
    save_results(results)


if __name__ == "__main__":
    asyncio.run(main())

