import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from datetime import datetime


# -----------------------------
# Function: Scrape METAR data from given URL
# -----------------------------
async def scrape_metars_to_dict(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        html_content = await page.content()
        await browser.close()

    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'lxml')

    # Remove unwanted <script> and <style> tags
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()

    text = soup.get_text(separator='\n')

    # Regex pattern to capture station codes (VXXX) and METAR strings
    pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\n)?[^=]*=)")

    metar_dict = {}
    for match in pattern.finditer(text):
        station = match.group(1)
        metar = match.group(2).strip()
        metar = metar.replace('\n', ' ')

        # ✅ Keep only the actual raw METAR up to the first "="
        if "=" in metar:
            metar = metar.split("=")[0] + "="

        # Ensure trailing "=" exists
        if not metar.endswith("="):
            metar += "="

        metar_dict[station] = metar

    return metar_dict


# -----------------------------
# Main script: Compare and Save Results
# -----------------------------
async def main():
    # Source URLs
    url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
    url2 = "https://amssdelhi.gov.in/Palam1.php"

    # Fetch METAR data from both sources
    V1 = await scrape_metars_to_dict(url1)
    V2 = await scrape_metars_to_dict(url2)

    # Prepare output filenames with timestamp (for uniqueness)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_missing = f"missing_{timestamp}.txt"
    file_mismatch = f"mismatch_{timestamp}.txt"
    file_match = f"match_{timestamp}.txt"

    # Open files for writing results
    with open(file_missing, "w", encoding="utf-8") as f_missing, \
         open(file_mismatch, "w", encoding="utf-8") as f_mismatch, \
         open(file_match, "w", encoding="utf-8") as f_match:

        # Write headers for better readability
        f_missing.write("══════════════════════════════════════════════\n")
        f_missing.write("      STATIONS PRESENT IN CHENNAI ONLY\n")
        f_missing.write("══════════════════════════════════════════════\n\n")

        f_mismatch.write("══════════════════════════════════════════════\n")
        f_mismatch.write("         STATIONS WITH MISMATCHED METARS\n")
        f_mismatch.write("══════════════════════════════════════════════\n\n")

        f_match.write("══════════════════════════════════════════════\n")
        f_match.write("         STATIONS WITH MATCHING METARS\n")
        f_match.write("══════════════════════════════════════════════\n\n")

        # -----------------------------
        # Comparison Logic
        # -----------------------------
        for station, metar1 in V1.items():
            metar2 = V2.get(station)

            if metar2 is None:
                # Case 1: Station missing in 2nd file
                f_missing.write(f"[MISSING] {station} → Present in Chennai but NOT in Delhi\n")

            elif metar1 != metar2:
                # Case 2: Station present in both, but METARs differ
                f_mismatch.write(f"[MISMATCH] {station}\n")
                f_mismatch.write(f"  Chennai: {metar1}\n")
                f_mismatch.write(f"  Delhi  : {metar2}\n\n")

            else:
                # Case 3: Station matches perfectly
                f_match.write(f"[MATCH] {station} → Data is consistent ✅\n")

    print(f"\n✅ Comparison complete! Results saved as:\n- {file_missing}\n- {file_mismatch}\n- {file_match}")


# Run the async main function
asyncio.run(main())
