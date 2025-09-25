# import asyncio
# import csv
# from playwright.async_api import async_playwright
# from bs4 import BeautifulSoup
# import re


# async def scrape_metars_to_dict(url: str) -> dict:
#     """
#     Scrape METAR reports from the given URL and return as dictionary.
#     Key = Station (ICAO code), Value = METAR string.
#     """
#     async with async_playwright() as p:
#         # Launch browser in headless mode
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         await page.goto(url, wait_until='networkidle')
#         html_content = await page.content()
#         await browser.close()

#     # Parse HTML content
#     soup = BeautifulSoup(html_content, 'lxml')

#     # Remove scripts and styles
#     for script_or_style in soup(['script', 'style']):
#         script_or_style.extract()

#     # Extract text
#     text = soup.get_text(separator='\n')

#     # Regex to capture station code and METAR
#     pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\n)?[^=]*=)")

#     metar_dict = {}
#     for match in pattern.finditer(text):
#         station = match.group(1)
#         metar = match.group(2).strip()
#         metar = metar.replace('\n', ' ')
#         if not metar.endswith('='):
#             metar += '='
#         metar_dict[station] = metar

#     return metar_dict


# async def main():
#     url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
#     url2 = "https://amssdelhi.gov.in/Palam1.php"

#     V1 = await scrape_metars_to_dict(url1)
#     V2 = await scrape_metars_to_dict(url2)

#     print("✅ Scraped METARs from Chennai site:", V1.keys())
#     print("✅ Scraped METARs from Delhi site:", V2.keys())
#     print("\n🔎 Comparison Results:\n")

#     results = []  # store results for CSV export

#     for station, metar1 in V1.items():
#         metar2 = V2.get(station)
#         if metar2 is None:
#             print(f"⚠️ {station} is missing in Delhi data")
#             results.append([station, metar1, "N/A", "Missing in Delhi"])
#         elif metar1 != metar2:
#             print(f"❌ {station} exists in both but differs")
#             print(f"   Chennai: {metar1}")
#             print(f"   Delhi  : {metar2}")
#             results.append([station, metar1, metar2, "Different"])
#         else:
#             print(f"✅ {station} matches in both sources")
#             results.append([station, metar1, metar2, "Match"])

#     # Save results to CSV
#     with open("metar_comparison.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow(["Station", "Chennai_METAR", "Delhi_METAR", "Status"])
#         writer.writerows(results)

#     print("\n📂 Comparison results saved to 'metar_comparison.csv'")


# if __name__ == "__main__":
#     asyncio.run(main())





# import asyncio
# import csv
# from playwright.async_api import async_playwright
# from bs4 import BeautifulSoup
# import re


# async def scrape_metars_to_dict(url: str) -> dict:
#     """
#     Scrape METAR reports from the given URL and return as dictionary.
#     Key = Station (ICAO code), Value = METAR string.
#     """
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         page = await browser.new_page()
#         await page.goto(url, wait_until='networkidle')
#         html_content = await page.content()
#         await browser.close()

#     soup = BeautifulSoup(html_content, 'lxml')

#     for script_or_style in soup(['script', 'style']):
#         script_or_style.extract()

#     text = soup.get_text(separator='\n')

#     pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\n)?[^=]*=)")

#     metar_dict = {}
#     for match in pattern.finditer(text):
#         station = match.group(1)
#         metar = match.group(2).strip()
#         metar = metar.replace('\n', ' ')
#         if not metar.endswith('='):
#             metar += '='
#         metar_dict[station] = metar

#     return metar_dict


# async def main():
#     url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
#     url2 = "https://amssdelhi.gov.in/Palam1.php"

#     V1 = await scrape_metars_to_dict(url1)
#     V2 = await scrape_metars_to_dict(url2)

#     print("✅ Scraped METARs from Chennai site:", V1.keys())
#     print("✅ Scraped METARs from Delhi site:", V2.keys())
#     print("\n🔎 Comparison Results:\n")

#     results = []

#     # Merge keys from both dictionaries
#     all_stations = set(V1.keys()) | set(V2.keys())

#     for station in sorted(all_stations):
#         metar1 = V1.get(station, "N/A")
#         metar2 = V2.get(station, "N/A")

#         if metar1 == "N/A":
#             status = "Missing in Chennai"
#         elif metar2 == "N/A":
#             status = "Missing in Delhi"
#         elif metar1 != metar2:
#             status = "Different"
#         else:
#             status = "Match"

#         # Print to console
#         print(f"{station}: {status}")

#         # Store for CSV
#         results.append([station, metar1, metar2, status])

#     # Save comparison results to CSV
#     with open("metar_comparison.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.writer(f)
#         writer.writerow(["Station", "Chennai_METAR", "Delhi_METAR", "Status"])
#         writer.writerows(results)

#     print("\n📂 Comparison results saved to 'metar_comparison.csv'")

#     # Save merged dataset to TXT
#     with open("metar_merged.txt", "w", encoding="utf-8") as f:
#         for station, metar1, metar2, status in results:
#             f.write(f"{station}\n")
#             f.write(f"  Chennai: {metar1}\n")
#             f.write(f"  Delhi  : {metar2}\n")
#             f.write(f"  Status : {status}\n")
#             f.write("-" * 50 + "\n")

#     print("📄 Full merged dataset saved to 'metar_merged.txt'")


# if __name__ == "__main__":
#     asyncio.run(main())






import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Function to scrape METAR data into dict
async def scrape_metars_to_dict(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle')
        html_content = await page.content()
        await browser.close()

    soup = BeautifulSoup(html_content, 'lxml')

    # Remove scripts/styles
    for script_or_style in soup(['script', 'style']):
        script_or_style.extract()

    text = soup.get_text(separator='\n')

    # Regex pattern for METAR codes
    pattern = re.compile(r"(V[A-Z]{3,4})\s+((?:.*?\n)?[^=]*=)")
    metar_dict = {}

    for match in pattern.finditer(text):
        station = match.group(1)
        metar = match.group(2).strip()
        metar = metar.replace('\n', ' ')
        if not metar.endswith('='):
            metar += '='
        metar_dict[station] = metar

    return metar_dict


# Main function
async def main():
    url1 = "https://olbs.amsschennai.gov.in/nsweb/FlightBriefing/showmetars.php"
    url2 = "https://amssdelhi.gov.in/Palam1.php"

    V1 = await scrape_metars_to_dict(url1)
    V2 = await scrape_metars_to_dict(url2)

    # Prepare results
    results = []
    results.append("══════════════════════════════════════════════════════════════")
    results.append("                 METAR COMPARISON REPORT")
    results.append(f"   Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    results.append("══════════════════════════════════════════════════════════════\n")

    for station, metar1 in V1.items():
        metar2 = V2.get(station)
        if metar2 is None:
            results.append(f"[MISSING] {station} → Present in Chennai but NOT in Delhi")
        elif metar1 != metar2:
            results.append(f"[MISMATCH] {station}")
            results.append(f"  Chennai: {metar1}")
            results.append(f"  Delhi  : {metar2}\n")
        else:
            results.append(f"[MATCH] {station} → Data is consistent")

    results.append("\n══════════════════════════════════════════════════════════════\n")

    # Save to file
    file_name = "METAR_Comparison_Report.txt"
    with open(file_name, "w", encoding="utf-8") as f:
        f.write("\n".join(results))

    print(f"✅ Comparison completed. Results saved to '{file_name}'")


# Run
asyncio.run(main())
