import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
 
 
 
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
   
    # print(text)  # Debugging line to see the scraped text
 
    pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\\n)?[^=]*=)")
    metar_dict = {}
    for match in pattern.finditer(text):
        station = match.group(1)
        metar = match.group(2).strip()
        metar = metar.replace('\n', ' ')
        if not metar.endswith('='):
            metar += '='
        metar_dict[station] = metar
    return metar_dict
 
# Use this in a script
async def main():
    url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
    url2 = "https://amssdelhi.gov.in/Palam1.php"
 
    V1 = await scrape_metars_to_dict(url1)
    V2 = await scrape_metars_to_dict(url2)
 
    # print("its is V1 : ",V1)
    # print("its is V2 : ",V2)
 
    # Comparison logic
    for station, metar1 in V1.items():
        metar2 = V2.get(station)
        if metar2 is None:
            print(f"{station} is not in 2nd file")
        elif metar1 != metar2:
            print(f"{station} is present in both but not same")
        else:
            print(f"{station} matches")
 
asyncio.run(main())