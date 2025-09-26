import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from datetime import datetime


 
def parse_metars_from_text(text: str) -> dict:
    """
    Parse METARs and 'No data for' lines from a page text and return a dict:
      { 'VXYZ': '251800Z ... =' , 'VABC': None, ... }
    """
    # normalize problematic whitespace characters
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')  # zero-width if present
 
    metar_dict = {}
 
    # 1) Explicit METAR entries: "METAR VXXX ... ="
    for m in re.finditer(r"METAR\s+(V[A-Z]{3,4})\s+([^=]*=)", text, re.IGNORECASE):
        code = m.group(1).upper()
        metar = m.group(2).strip()
        metar = re.sub(r"\s+", " ", metar)
        metar_dict[code] = metar
 
    # 2) IMD-style plain entries: "VXXX 251800Z ... =" (only if not already captured)
    for m in re.finditer(r"(^|\n)\s*(V[A-Z]{3,4})\s+(\d{6}Z\b[^=]*=)",
                         text, re.IGNORECASE | re.MULTILINE):
        code = m.group(2).upper()
        if code not in metar_dict:
            metar = m.group(3).strip()
            metar = re.sub(r"\s+", " ", metar)
            metar_dict[code] = metar
 
    # 3) "No data for VXXX" occurrences -> set to None if not already present
    for m in re.finditer(r"No data for\s+(V[A-Z]{3,4})", text, re.IGNORECASE):
        code = m.group(1).upper()
        if code not in metar_dict:
            metar_dict[code] = None
 
    return metar_dict
 
 
async def scrape_metars_to_dict(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        html_content = await page.content()
        await browser.close()
 
    soup = BeautifulSoup(html_content, 'lxml')
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()
    text = soup.get_text(separator='\n')
    metar_dict = parse_metars_from_text(text)
 
    # print(text)  # Debugging line to see the scraped text

    return metar_dict
 


# Use this in a script
async def main():
    url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
    url2 = "https://amssdelhi.gov.in/Palam1.php"

    V1 = await scrape_metars_to_dict(url1)
    V2 = await scrape_metars_to_dict(url2)

    # Collect station lists
    not_in_amss = []
    not_in_olbs = []
    not_same = []
    # matches = []

    # Comparison logic
    for station, metar1 in V1.items():
        metar2 = V2.get(station)
        if metar2 is None:
            not_in_amss.append(station)
        elif metar1 != metar2:
            not_same.append(station)
        else:
            pass

    # Reverse check: stations in V2 but missing in V1
    for station in V2.keys():
        if station not in V1:
            not_in_olbs.append(station)

    # Get current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write grouped station codes into files
    with open("not_in_amss.txt", "a") as f_not2, \
         open("not_in_olbs.txt", "a") as f_not1, \
         open("not_same.txt", "a") as f_diff:
        #  open("matches.txt", "a") as f_match:

        f_not2.write(f"{timestamp} : {not_in_amss}\n")
        f_not1.write(f"{timestamp} : {not_in_olbs}\n")
        f_diff.write(f"{timestamp} : {not_same}\n")
        # f_match.write(f"{timestamp} : {matches}\n")
 
 
# asyncio.run(main())
