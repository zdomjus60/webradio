

import sqlite3
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urlparse, urljoin
import time
import signal
from datetime import datetime
import warnings

# Suppress the XMLParsedAsHTMLWarning as we expect to handle HTML-like XML
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# --- Timeout Handler ---
class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException()

signal.signal(signal.SIGALRM, timeout_handler)
# --- End Timeout Handler ---

def find_logo_on_website(website_url):
    """
    Tries to find a logo URL on a given website by scraping its content.
    """
    try:
        # Add a small delay to be polite
        time.sleep(0.5)
        response = requests.get(website_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Try to find logo in meta tags (e.g., Open Graph)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
            
        # Try to find logo in link tags (e.g., favicon, apple-touch-icon)
        icon_link = soup.find("link", rel=["icon", "apple-touch-icon", "shortcut icon"])
        if icon_link and icon_link.get("href"):
            return urljoin(website_url, icon_link["href"])
            
        # Try to find logo in img tags with common alt/src attributes
        for img in soup.find_all("img"):
            img_src = img.get("src", "").lower()
            img_alt = img.get("alt", "").lower()
            if "logo" in img_src or "logo" in img_alt:
                return urljoin(website_url, img.get("src"))
                
    except requests.exceptions.RequestException as e:
        print(f"    -> Scraping Error: {e}")
    except Exception as e:
        print(f"    -> Parsing Error: {e}")
    return None

def scrape_missing_logos():
    """
    Scans the database for stations without a logo and tries to find one
    using a waterfall method: API first, then scraping.
    """
    start_time = datetime.now()
    print(f"--- Script started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')} ---")

    conn = sqlite3.connect('radio.db')
    c = conn.cursor()

    c.execute("SELECT id, url, name, logo_url FROM stations ORDER BY name")
    all_stations = c.fetchall()
    
    total_stations = len(all_stations)
    print(f"Checking {total_stations} total stations...")
    
    newly_found_count = 0
    existing_logo_count = 0
    failed_count = 0
    api_success_count = 0
    scrape_success_count = 0

    for i, (station_id, station_url, station_name, logo_url) in enumerate(all_stations):
        
        progress_prefix = f"[{i+1}/{total_stations}] {station_name}:"

        if logo_url:
            existing_logo_count += 1
            continue

        print(f"{progress_prefix} Logo MISSING. Starting search...")
        
        if not station_url or not station_url.startswith('http'):
            print("  -> Invalid or missing station URL. Skipping.")
            failed_count += 1
            continue

        logo_found = False
        
        # --- METHOD 1: Clearbit API ---
        try:
            domain = urlparse(station_url).netloc
            if domain:
                clearbit_url = f"https://logo.clearbit.com/{domain}"
                print(f"  -> Phase 1 (API): Checking {clearbit_url}")
                response = requests.get(clearbit_url, timeout=5)
                
                if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                    print(f"  -> SUCCESS (API): Found logo at {response.url}")
                    c.execute("UPDATE stations SET logo_url = ? WHERE id = ?", (response.url, station_id))
                    conn.commit()
                    newly_found_count += 1
                    api_success_count += 1
                    logo_found = True
                else:
                    print("  -> FAILED (API): No logo found via Clearbit.")
            else:
                print("  -> FAILED (API): Could not extract domain from station URL.")

        except Exception as e:
            print(f"  -> ERROR (API): An error occurred: {e}")

        if logo_found:
            continue

        # --- METHOD 2: Web Scraping (Fallback) ---
        print("  -> Phase 2 (Scraping): Starting website scraping...")
        signal.alarm(20) # More generous timeout for full scraping
        try:
            parsed_url = urlparse(station_url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            scrape_target_url = base_url
            
            new_logo_url = find_logo_on_website(scrape_target_url)
            
            if new_logo_url:
                final_logo_url = urljoin(scrape_target_url, new_logo_url)
                print(f"  -> SUCCESS (Scraping): Found logo at {final_logo_url}")
                c.execute("UPDATE stations SET logo_url = ? WHERE id = ?", (final_logo_url, station_id))
                conn.commit()
                newly_found_count += 1
                scrape_success_count += 1
            else:
                print("  -> FAILED (Scraping): No logo found on website.")
                failed_count += 1

        except TimeoutException:
            print("  -> TIMEOUT (Scraping): Website took too long to respond. Skipping.")
            failed_count += 1
        except Exception as e:
            print(f"  -> ERROR (Scraping): An unexpected error occurred: {e}")
            failed_count += 1
        finally:
            signal.alarm(0) # Disable the alarm
            
    conn.close()

    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n--- SCRAPING COMPLETE ---")
    print(f"Started at:   {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Finished at:  {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: {str(duration).split('.')[0]}")
    print("-" * 30)
    print(f"Total stations scanned:   {total_stations}")
    print(f"Logos already existing:   {existing_logo_count}")
    print(f"New logos found (TOTAL):  {newly_found_count}")
    print(f"  - Found via API:        {api_success_count}")
    print(f"  - Found via Scraping:   {scrape_success_count}")
    print(f"Failed attempts:          {failed_count}")
    print("------------------------------")

if __name__ == '__main__':
    scrape_missing_logos()
