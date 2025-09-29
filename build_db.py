import sqlite3
import os
import glob

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
    "cr": "Costa Rica", "cu": "Cuba", "cw": "Curaçao", "cx": "Christmas Island",
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
    "zw": "Zimbabwe"
}

# New explicit genre list
VALID_GENRES = {
    '60s', '70s', '80s', '90s', 'acid_jazz', 'african', 'alternative',
    'ambient', 'americana', 'anime', 'arabic', 'asian', 'big_band',
    'bluegrass', 'blues', 'breakbeat', 'chillout', 'christian',
    'classical', 'club', 'college', 'comedy', 'country', 'dance',
    'deutsch', 'disco', 'discofox', 'downtempo', 'drum_and_bass',
    'easy_listening', 'ebm', 'electronic', 'eurodance', 'film', 'folk',
    'funk', 'goa', 'gospel', 'gothic', 'greek', 'hardcore', 'hardrock',
    'hip_hop', 'house', 'india', 'indie', 'industrial', 'instrumental',
    'jazz', 'jpop', 'jungle', 'latin', 'lounge', 'metal', 'mixed',
    'musical', 'oldies', 'opera', 'polish', 'polka', 'pop', 'progressive',
    'punk', 'quran', 'rap', 'reggae', 'retro', 'rnb', 'rock', 'romanian',
    'russian', 'salsa', 'schlager', 'ska', 'smooth_jazz', 'soul',
    'soundtrack', 'spiritual', 'sport', 'swing', 'symphonic', 'talk',
    'techno', 'top_40', 'trance', 'turk', 'urban', 'various', 'wave', 'world',
    'france', 'spain', 'italy', 'usa', 'portugal', 'uk' # Added country names that appear as top-level m3u files
}

def create_database():
    if os.path.exists('radio.db'):
        os.remove('radio.db')
        print("Removed old database.")
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

    conn.commit()
    print("Database tables created.")
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

def populate_database(conn):
    c = conn.cursor()
    
    country_names_to_codes = {v.lower(): k for k, v in country_codes.items()}

    print("Scanning all .m3u files recursively...")
    all_m3u_files = glob.glob('m3u-radio-music-playlists/**/*.m3u', recursive=True)
    
    print(f"Found {len(all_m3u_files)} playlist files to process.")

    for filepath in all_m3u_files:
        filename = os.path.basename(filepath)
        
        if '---' in filename or 'checked' in filepath.replace(os.path.sep, '/') :
            continue

        name_part = os.path.splitext(filename)[0].lower()
        
        current_country_name = None
        current_genre_name = None

        # 1. Try to identify country from filename (e.g., 'france.m3u', 'de-berlin.m3u')
        # Check if filename is a full country name (e.g., 'france.m3u')
        if name_part in country_names_to_codes:
            current_country_name = country_codes[country_names_to_codes[name_part]]
        # Check if filename is a country code (e.g., 'fr.m3u')
        elif name_part in country_codes:
            current_country_name = country_codes[name_part]
        # Check for hyphenated country code (e.g., 'de-berlin.m3u')
        elif '-' in name_part:
            code_part = name_part.split('-')[0]
            if code_part in country_codes:
                current_country_name = country_codes[code_part]
        
        # 2. Try to identify genre from filename (e.g., 'rock.m3u')
        if name_part in VALID_GENRES:
            current_genre_name = name_part.replace('_', ' ').title()

        # If neither country nor genre could be identified, skip this file for now
        if not current_country_name and not current_genre_name:
            # print(f"Skipping file with no clear country or genre: {filepath}") # For debugging
            continue

        stations = parse_m3u(filepath)
        if not stations:
            continue

        genre_id = None
        if current_genre_name:
            c.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (current_genre_name,))
            c.execute("SELECT id FROM genres WHERE name = ?", (current_genre_name,))
            genre_id_result = c.fetchone()
            if genre_id_result:
                genre_id = genre_id_result[0]

        country_id = None
        if current_country_name:
            c.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (current_country_name,))
            c.execute("SELECT id FROM countries WHERE name = ?", (current_country_name,))
            country_id_result = c.fetchone()
            if country_id_result:
                country_id = country_id_result[0]

        for station in stations:
            c.execute("INSERT OR IGNORE INTO stations (name, url) VALUES (?, ?)", (station["name"], station["url"]))
            
            c.execute("SELECT id FROM stations WHERE url = ?", (station["url"],))
            station_id_result = c.fetchone()
            if not station_id_result:
                continue
            station_id = station_id_result[0]

            if country_id:
                c.execute("UPDATE stations SET country_id = ? WHERE id = ? AND country_id IS NULL", (country_id, station_id))

            if genre_id:
                c.execute("INSERT OR IGNORE INTO station_genres (station_id, genre_id) VALUES (?, ?)", (station_id, genre_id))
        
        conn.commit()

    print("\nDatabase population complete.")

if __name__ == '__main__':
    db_conn = create_database()
    populate_database(db_conn)
    db_conn.close()
    print("Database created and populated successfully.")