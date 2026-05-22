import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

# ── Configuration ──────────────────────────────────────────────────────────────
LIST_URL = (
    "https://www.kultunaut.dk/perl/arrlist/type-nynaut"
    "?Area=Kolding-storkommune"
    "&ArrSlutdato=5%2F6%202026"
    "&ArrStartdato=1%2F1%202026"
    "&Order=ArrStartdato"
    "&nearmeradius=2000"
    "&periode="
)
PAGINATE_URL = (
    "https://www.kultunaut.dk/perl/arrlist2/type-nynaut"
    "?startnr={start}"
    "&Area=Kolding-storkommune"
    "&ArrSlutdato=5%2F6%202026"
    "&ArrStartdato=1%2F1%202026"
    "&Order=ArrStartdato"
    "&nearmeradius=2000"
    "&periode="
)
PAGE_SIZE = 13
DELAY = 0.5  # Throttling time between hits to be safe

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8",
}

def parse_page_events(soup):
    page_events = []
    
    # Target the main product anchor tags you found via Inspect element
    event_containers = soup.find_all("a", class_="product-content")
    
    # Fallback to structural regex matching if some pages render a legacy layout list view
    if not event_containers:
        event_containers = soup.find_all("a", href=re.compile(r"/perl/arrmore/type-nynaut"))

    for container in event_containers:
        # 1. Title Extraction
        title_tag = container.find("h3")
        title = title_tag.get_text(strip=True) if title_tag else "Untitled Event"
        
        # 2. Description Extraction
        desc_tag = container.find("div", class_="arr-description")
        description = desc_tag.get_text(strip=True) if desc_tag else "No description available"
        
        # 3. Date & Time Extraction from the <time> tag inside .kult-month-day
        time_tag = container.find("time")
        
        date_clean = "Unknown Date"
        time_clean = "See description"
        
        if time_tag:
            raw_time_text = time_tag.get_text(strip=True)
            
            # If a venue name b-tag leaks into the time string, drop it to isolate temporal data
            bold_tag = container.find("b")
            if bold_tag:
                venue_text = bold_tag.get_text(strip=True)
                raw_time_text = raw_time_text.replace(venue_text, "").strip().rstrip(",")

            # Extract time configurations (e.g., matching shapes like "10 a.m.", "14:30")
            time_match = re.search(r"\b(\d{1,2}(?:\s*[a-p]\.m\.)|(?:\d{2}[:.]\d{2}))", raw_time_text, re.IGNORECASE)
            if time_match:
                time_clean = time_match.group(1)
                
            # Strip out time configurations from the raw text to leave just the clean date string
            date_clean = re.sub(r"\b\d{1,2}\s*[a-p]\.m\..*$", "", raw_time_text, flags=re.IGNORECASE).strip()
            # General fallback check to clear out raw Danish 'kl' time strings if present
            date_clean = re.sub(r"kl\..*$", "", date_clean, flags=re.IGNORECASE).strip().rstrip(",").strip()

        page_events.append({
            "Title": title,
            "Description": description,
            "Date": date_clean,
            "Time": time_clean
        })
        
    return page_events

# ── Main Scrape Execution Loop ─────────────────────────────────────────────────
if __name__ == "__main__":
    all_events = []

    print("[+] Loading primary landing index...")
    response = requests.get(LIST_URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the total event counter to set up pagination boundaries
    total_match = re.search(r"Viser\s+(\d+)\s+events", soup.get_text())
    total_events = int(total_match.group(1)) if total_match else 150
    print(f"[i] Discovered {total_events} available regional listings.")

    # Harvest first page details
    first_page_results = parse_page_events(soup)
    all_events.extend(first_page_results)
    print(f"    → Registered {len(first_page_results)} entries from page 1.")

    # Loop over the remaining items via pagination
    start_idx = PAGE_SIZE + 1
    page_num = 2
    
    while start_idx <= total_events:
        time.sleep(DELAY)
        print(f"[+] Requesting entries starting at index position {start_idx} (Page {page_num})...")
        
        response = requests.get(PAGINATE_URL.format(start=start_idx), headers=HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")
        
        page_results = parse_page_events(soup)
        if not page_results:
            print("    [i] No more items found on this layout format. Ending pagination sequence.")
            break
            
        all_events.extend(page_results)
        print(f"    → Registered {len(page_results)} items.")
        
        start_idx += PAGE_SIZE
        page_num += 1

    # ── Save Clean Dataset ─────────────────────────────────────────────────────
    df = pd.DataFrame(all_events).drop_duplicates(subset=["Title", "Date"])
    output_filename = "clean_kolding_events.csv"
    df.to_csv(output_filename, index=False, encoding="utf-8-sig")

    print(f"\n✅ Pipeline Complete! Extracted {len(df)} unique events.")
    print(f"File saved cleanly to: '{output_filename}'")
