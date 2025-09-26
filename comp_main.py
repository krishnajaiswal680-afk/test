import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
 
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
 
    print(text)  # Debugging line to see the scraped text
 
    # pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\\n)?[^=]*=)")
    # metar_dict = {}
    # for match in pattern.finditer(text):
    #     station = match.group(1)
    #     metar = match.group(2).strip()
    #     metar = metar.replace('\n', ' ')
    #     if not metar.endswith('='):
    #         metar += '='
    #     metar_dict[station] = metar
 
    return metar_dict
 
# Use this in a script
async def main():
    url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
    url2 = "https://amssdelhi.gov.in/Palam1.php"
 
    V1 = await scrape_metars_to_dict(url1)
    V2 = await scrape_metars_to_dict(url2)
 
    # print("its is V1 : ", V1)
    # print("its is V2 : ", V2)
 
    # Open files for writing results
    with open("not_in_2nd_file.txt", "w") as f_not2, \
        open("not_in_1st_file.txt", "w") as f_not1, \
        open("not_same.txt", "w") as f_diff, \
        open("matches.txt", "w") as f_match:
 
        # Comparison logic
        for station, metar1 in V1.items():
            metar2 = V2.get(station)
            if metar2 is None:
                print(f"{station} is not in 2nd file")
                f_not2.write(station + "\n")
            elif metar1 != metar2:
                print(f"{station} is present in both but not same")
                f_diff.write(station + "\n")
            else:
                print(f"{station} matches")
                f_match.write(station + "\n")
 
        # Now check the reverse: stations in V2 but missing in V1
        for station in V2.keys():
            if station not in V1:
                print(f"{station} is not in 1st file")
                f_not1.write(station + "\n")
 
 
asyncio.run(main())
