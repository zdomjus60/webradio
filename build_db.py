
import sqlite3
import os
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse

country_codes = {
    "ad": "Andorra", "ae": "United Arab Emirates", "af": "Afghanistan", "ag": "Antigua and Barbuda",
    "ai": "Anguilla", "al": "Albania", "am": "Armenia", "ao": "Angola", "aq": "Antarctica",
    "ar": "Argentina", "as": "American Samoa", "at": "Austria", "au": "Australia", "aw": "Aruba",
    "ax": "Åland Islands", "az": "Azerbaijan", "ba": "Bosnia and Herzegovina", "bb": "Barbados",
    "bd": "Bangladesh", "be": "Belgium", "bf": "Burkina Faso", "bg": "Bulgaria", "bh": "Bahrain",
    "bi": "Burundi", "bj": "Benin", "bl": "Saint Barthélemy", "bm": "Bermuda", "bn": "Brunei Darussalam",
    "bo": "Bolivia", "bq": "Bonaire, Sint Eustatius and Saba", "br": "Brazil", "bs": "Bahamas",
    "bt": "Bhutan", "bv": "Bouvet Island", "bw": "Botswana", "by": "Belarus", "bz": "Belize",
    "ca": "Canada", "cc": "Cocos (Keeling) Islands", "cd": "Congo, The Democratic Republic of the",
    "cf": "Central African Republic", "cg": "Congo", "ch": "Switzerland", "ci": "Côte d'Ivoire",
    "ck": "Cook Islands", "cl": "Chile", "cm": "Cameroon", "cn": "China", "co": "Colombia",
    "cr": "Costa Rica", "cu": "Cuba", "cv": "Cabo Verde", "cw": "Curaçao", "cx": "Christmas Island",
    "cy": "Cyprus", "cz": "Czechia", "de": "Germany", "dj": "Djibouti", "dk": "Denmark",
    "dm": "Dominica", "do": "Dominican Republic", "dz": "Algeria", "ec": "Ecuador", "ee": "Estonia",
    "eg": "Egypt", "eh": "Western Sahara", "er": "Eritrea", "es": "Spain", "et": "Ethiopia",
    "fi": "Finland", "fj": "Fiji", "fk": "Falkland Islands (Malvinas)", "fm": "Micronesia, Federated States of",
    "fo": "Faroe Islands", "fr": "France", "ga": "Gabon", "gb": "United Kingdom", "gd": "Grenada",
    "ge": "Georgia", "gf": "French Guiana", "gg": "Guernsey", "gh": "Ghana", "gi": "Gibraltar",
    "gl": "Greenland", "gm": "Gambia", "gn": "Guinea", "gp": "Guadeloupe", "gq": "Equatorial Guinea",
    "gr": "Greece", "gs": "South Georgia and the South Sandwich Islands", "gt": "Guatemala",
    "gu": "Guam", "gw": "Guinea-Bissau", "gy": "Guyana", "hk": "Hong Kong", "hm": "Heard Island and McDonald Islands",
    "hn": "Honduras", "hr": "Croatia", "ht": "Haiti", "hu": "Hungary", "id": "Indonesia",
    "ie": "Ireland", "il": "Israel", "im": "Isle of Man", "in": "India", "io": "British Indian Ocean Territory",
    "iq": "Iraq", "ir": "Iran, Islamic Republic of", "is": "Iceland", "it": "Italy", "je": "Jersey",
    "jm": "Jamaica", "jo": "Jordan", "jp": "Japan", "ke": "Kenya", "kg": "Kyrgyzstan", "kh": "Cambodia",
    "ki": "Kiribati", "km": "Comoros", "kn": "Saint Kitts and Nevis", "kp": "Korea, Democratic People's Republic of",
    "kr": "Korea, Republic of", "kw": "Kuwait", "ky": "Cayman Islands", "kz": "Kazakhstan",
    "la": "Lao People's Democratic Republic", "lb": "Lebanon", "lc": "Saint Lucia", "li": "Liechtenstein",
    "lk": "Sri Lanka", "lr": "Liberia", "ls": "Lesotho", "lt": "Lithuania", "lu": "Luxembourg",
    "lv": "Latvia", "ly": "Libya", "ma": "Morocco", "mc": "Monaco", "md": "Moldova, Republic of",
    "me": "Montenegro", "mf": "Saint Martin (French part)", "mg": "Madagascar", "mh": "Marshall Islands",
    "mk": "North Macedonia", "ml": "Mali", "mm": "Myanmar", "mn": "Mongolia", "mo": "Macao",
    "mp": "Northern Mariana Islands", "mq": "Martinique", "mr": "Mauritania", "ms": "Montserrat",
    "mt": "Malta", "mu": "Mauritius", "mv": "Maldives", "mw": "Malawi", "mx": "Mexico",
    "my": "Malaysia", "mz": "Mozambique", "na": "Namibia", "nc": "New Caledonia", "ne": "Niger",
    "nf": "Norfolk Island", "ng": "Nigeria", "ni": "Nicaragua", "nl": "Netherlands", "no": "Norway",
    "np": "Nepal", "nr": "Nauru", "nu": "Niue", "nz": "New Zealand", "om": "Oman", "pa": "Panama",
    "pe": "Peru", "pf": "French Polynesia", "pg": "Papua New Guinea", "ph": "Philippines",
    "pk": "Pakistan", "pl": "Poland", "pm": "Saint Pierre and Miquelon", "pn": "Pitcairn",
    "pr": "Puerto Rico", "ps": "Palestine, State of", "pt": "Portugal", "pw": "Palau",
    "py": "Paraguay", "qa": "Qatar", "re": "Réunion", "ro": "Romania", "rs": "Serbia",
    "ru": "Russian Federation", "rw": "Rwanda", "sa": "Saudi Arabia", "sb": "Solomon Islands",
    "sc": "Seychelles", "sd": "Sudan", "se": "Sweden", "sg": "Singapore", "sh": "Saint Helena, Ascension and Tristan da Cunha",
    "si": "Slovenia", "sj": "Svalbard and Jan Mayen", "sk": "Slovakia", "sl": "Sierra Leone",
    "sm": "San Marino", "sn": "Senegal", "so": "Somalia", "sr": "Suriname", "ss": "South Sudan",
    "st": "Sao Tome and Principe", "sv": "El Salvador", "sx": "Sint Maarten (Dutch part)",
    "sy": "Syrian Arab Republic", "sz": "Eswatini", "tc": "Turks and Caicos Islands", "td": "Chad",
    "tf": "French Southern Territories", "tg": "Togo", "th": "Thailand", "tj": "Tajikistan",
    "tk": "Tokelau", "tl": "Timor-Leste", "tm": "Turkmenistan", "tn": "Tunisia", "to": "Tonga",
    "tr": "Turkey", "tt": "Trinidad and Tobago", "tv": "Tuvalu", "tw": "Taiwan, Province of China",
    "tz": "Tanzania, United Republic of", "ua": "Ukraine", "ug": "Uganda", "um": "United States Minor Outlying Islands",
    "us": "United States", "uy": "Uruguay", "uz": "Uzbekistan", "va": "Holy See (Vatican City State)",
    "vc": "Saint Vincent and the Grenadines", "ve": "Venezuela", "vg": "Virgin Islands, British",
    "vi": "Virgin Islands, U.S.", "vn": "Viet Nam", "vu": "Vanuatu", "wf": "Wallis and Futuna",
    "ws": "Samoa", "ye": "Yemen", "yt": "Mayotte", "za": "South Africa", "zm": "Zambia",
    "zw": "Zimbabwe", "italian": "Italy"
}

def create_database():
    if os.path.exists('radio.db'):
        os.remove('radio.db')
    conn = sqlite3.connect('radio.db')
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS countries (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS stations (
            id INTEGER PRIMARY KEY,
            name TEXT,
            url TEXT UNIQUE,
            logo_url TEXT,
            country_id INTEGER,
            city TEXT,
            status TEXT DEFAULT 'unchecked',
            FOREIGN KEY (country_id) REFERENCES countries (id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS station_genres (
            station_id INTEGER,
            genre_id INTEGER,
            FOREIGN KEY (station_id) REFERENCES stations (id),
            FOREIGN KEY (genre_id) REFERENCES genres (id),
            PRIMARY KEY (station_id, genre_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            folder TEXT
        )
    ''')

    conn.commit()
    return conn

def parse_m3u(file_path):
    stations = []
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            i = 0
            while i < len(lines):
                if lines[i].startswith("#EXTINF"):
                    try:
                        name = lines[i].split(',', 1)[1].strip()
                        url = lines[i+1].strip()
                        stations.append({"name": name, "url": url})
                        i += 2
                    except IndexError:
                        i += 1
                else:
                    i += 1
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
    return stations

def scrape_sources_from_readme(conn):
    c = conn.cursor()
    readme_url = "https://raw.githubusercontent.com/junguler/m3u-radio-music-playlists/main/README.md"
    try:
        response = requests.get(readme_url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, 'lxml')
        
        sources_table = soup.find('h3', string='sources').find_next_sibling('table')
        if sources_table:
            for row in sources_table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 2:
                    website_url = cols[0].find('a').get('href')
                    folder_name = cols[1].find('a').get('href').split('/')[-1]
                    c.execute("INSERT OR IGNORE INTO sources (url, folder) VALUES (?, ?)", (website_url, folder_name))
                    conn.commit()
    except requests.exceptions.RequestException as e:
        print(f"Error scraping README.md for sources: {e}")
    except Exception as e:
        print(f"Error parsing README.md: {e}")

def populate_database(conn):
    c = conn.cursor()

    # Scrape sources from README.md
    scrape_sources_from_readme(conn)

    # Process genres from m3u-radio-music-playlists
    genre_path = "m3u-radio-music-playlists"
    for filename in os.listdir(genre_path):
        if filename.endswith(".m3u") and not filename.startswith("---"):
            genre_name = os.path.splitext(filename)[0]
            c.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre_name,))
            conn.commit()
            c.execute("SELECT id FROM genres WHERE name = ?", (genre_name,))
            genre_id_result = c.fetchone()
            if genre_id_result:
                genre_id = genre_id_result[0]
                stations = parse_m3u(os.path.join(genre_path, filename))
                for station in stations:
                    c.execute("INSERT OR IGNORE INTO stations (name, url) VALUES (?, ?)", (station["name"], station["url"]))
                    conn.commit()
                    c.execute("SELECT id FROM stations WHERE url = ?", (station["url"],))
                    station_id_result = c.fetchone()
                    if station_id_result:
                        station_id = station_id_result[0]
                        c.execute("INSERT OR IGNORE INTO station_genres (station_id, genre_id) VALUES (?, ?)", (station_id, genre_id))
                        conn.commit()

    # Process countries from m3u-radio-music-playlists/world-radio_map
    country_path = "m3u-radio-music-playlists/world-radio_map"
    for filename in os.listdir(country_path):
        if filename.endswith(".m3u") and not filename.startswith("---"):
            country_code = filename.split('-')[0]
            country_name = country_codes.get(country_code.lower())
            if country_name:
                c.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (country_name,))
                conn.commit()
                c.execute("SELECT id FROM countries WHERE name = ?", (country_name,))
                country_id_result = c.fetchone()
                if country_id_result:
                    country_id = country_id_result[0]
                    stations = parse_m3u(os.path.join(country_path, filename))
                    for station in stations:
                        c.execute("SELECT id FROM stations WHERE url = ?", (station["url"],))
                        existing_station = c.fetchone()
                        if existing_station:
                            c.execute("UPDATE stations SET country_id = ? WHERE id = ?", (country_id, existing_station[0]))
                        else:
                            c.execute("INSERT OR IGNORE INTO stations (name, url, country_id) VALUES (?, ?, ?)", (station["name"], station["url"], country_id))
                        conn.commit()

    # Special handling for italian.m3u
    country_name = "Italy"
    c.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (country_name,))
    conn.commit()
    c.execute("SELECT id FROM countries WHERE name = ?", (country_name,))
    country_id_result = c.fetchone()
    if country_id_result:
        country_id = country_id_result[0]
        stations = parse_m3u(os.path.join("m3u-radio-music-playlists", "italian.m3u"))
        for station in stations:
            c.execute("SELECT id FROM stations WHERE url = ?", (station["url"],))
            existing_station = c.fetchone()
            if existing_station:
                c.execute("UPDATE stations SET country_id = ? WHERE id = ?", (country_id, existing_station[0]))
            else:
                c.execute("INSERT OR IGNORE INTO stations (name, url, country_id) VALUES (?, ?, ?)", (station["name"], station["url"], country_id))
            conn.commit()

    # Now try to find logos for stations that don't have them
    # This part is commented out because it is very slow and may cause the script to hang.
    # c.execute("SELECT id, url FROM stations WHERE logo_url IS NULL")
    # stations_without_logo = c.fetchall()
    # for station_id, station_url in stations_without_logo:
    #     # Try to find the source website for this station
    #     # This is a very naive approach and will need to be improved
    #     try:
    #         parsed_url = urlparse(station_url)
    #         base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    #         c.execute("SELECT url FROM sources WHERE ? LIKE '%' || folder || '%'", (base_url,))
    #         source_website = c.fetchone()
    #         if source_website:
    #             source_url = source_website[0]
    #         else:
    #             source_url = base_url # Fallback to base URL if no specific source found

    #         logo_url = find_logo_on_website(source_url)
    #         if logo_url:
    #             c.execute("UPDATE stations SET logo_url = ? WHERE id = ?", (logo_url, station_id))
    #             conn.commit()
    #     except Exception as e:
    #         print(f"Error processing station {station_url} for logo: {e}")
    #         continue

def find_logo_on_website(website_url):
    try:
        response = requests.get(website_url, timeout=10)
        soup = BeautifulSoup(response.content, 'lxml')
        # Try to find logo in meta tags (e.g., Open Graph)
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return og_image["content"]
        # Try to find logo in link tags (e.g., favicon, apple-touch-icon)
        icon_link = soup.find("link", rel=["icon", "apple-touch-icon"])
        if icon_link and icon_link.get("href"):
            return icon_link["href"]
        # Try to find logo in img tags with common alt/src attributes
        for img in soup.find_all("img"):
            if "logo" in img.get("alt", "").lower() or "logo" in img.get("src", "").lower():
                return img["src"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching website {website_url}: {e}")
    except Exception as e:
        print(f"Error parsing website {website_url}: {e}")
    return None

if __name__ == '__main__':
    db_conn = create_database()
    populate_database(db_conn)
    db_conn.close()
    print("Database created and populated successfully.")
