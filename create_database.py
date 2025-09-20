import sqlite3
import os

def parse_m3u(file_path):
    stations = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 2):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                name = lines[i].split(',')[-1].strip()
                if name.startswith('▶ '):
                    name = name[2:].split(' - ')[0]
                url = lines[i+1].strip()
                stations.append({"name": name, "url": url})
    return stations

def populate_database():
    conn = sqlite3.connect('radio.db')
    c = conn.cursor()

    # Populate genres
    genre_path = "/home/debian/Scrivania/webradio/m3u-radio-music-playlists"
    for filename in os.listdir(genre_path):
        if filename.endswith(".m3u"):
            genre_name = os.path.splitext(filename)[0]
            c.execute("INSERT OR IGNORE INTO genres (name) VALUES (?)", (genre_name,))
            genre_id = c.lastrowid
            stations = parse_m3u(os.path.join(genre_path, filename))
            for station in stations:
                c.execute("INSERT OR IGNORE INTO stations (name, url) VALUES (?, ?)", (station["name"], station["url"]))
                station_id = c.lastrowid
                c.execute("INSERT OR IGNORE INTO station_genres (station_id, genre_id) VALUES (?, ?)", (station_id, genre_id))

    # Populate countries
    country_path = "/home/debian/Scrivania/webradio/m3u-radio-music-playlists/world-radio_map"
    for filename in os.listdir(country_path):
        if filename.endswith(".m3u") and not filename.startswith("---"):
            parts = os.path.splitext(filename)[0].split('-')
            if len(parts) > 1:
                country_name = parts[0]
                city = parts[1] if len(parts) > 1 else None
                c.execute("INSERT OR IGNORE INTO countries (name) VALUES (?)", (country_name,))
                country_id = c.lastrowid
                stations = parse_m3u(os.path.join(country_path, filename))
                for station in stations:
                    c.execute("INSERT OR IGNORE INTO stations (name, url, country_id, city) VALUES (?, ?, ?, ?)", (station["name"], station["url"], country_id, city))

    conn.commit()
    conn.close()

def create_database():
    conn = sqlite3.connect('radio.db')
    c = conn.cursor()

    # Create tables
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
            url TEXT,
            country_id INTEGER,
            city TEXT,
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
    conn.close()

if __name__ == '__main__':
    create_database()
    populate_database()
    print("Database created and populated successfully.")
