
import sqlite3
import os
import glob
import re

def update_logo_urls():
    """
    Parses all .m3u files to find tvg-logo attributes and updates the
    logo_url field for the corresponding station in the radio.db database.
    """
    db_path = 'radio.db'
    m3u_directory = 'm3u-radio-music-playlists'
    
    if not os.path.exists(db_path):
        print(f"Error: Database '{db_path}' not found. Please run build_db.py first.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("Starting to update logo URLs...")
    
    # Regex to find tvg-logo
    logo_regex = re.compile(r'tvg-logo="([^"]+)"')
    
    # Use glob to find all .m3u files recursively
    m3u_files = glob.glob(os.path.join(m3u_directory, '**', '*.m3u'), recursive=True)
    
    updated_count = 0
    
    for m3u_file in m3u_files:
        try:
            with open(m3u_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                i = 0
                while i < len(lines):
                    if lines[i].startswith("#EXTINF"):
                        # The stream URL is expected on the next line
                        if i + 1 < len(lines):
                            stream_url = lines[i+1].strip()
                            
                            # Search for the logo in the #EXTINF line
                            match = logo_regex.search(lines[i])
                            if match:
                                logo_url = match.group(1)
                                
                                # Update the database
                                c.execute("UPDATE stations SET logo_url = ? WHERE url = ?", (logo_url, stream_url))
                                if c.rowcount > 0:
                                    updated_count += 1
                        i += 2 # Move to the line after the URL
                    else:
                        i += 1
        except Exception as e:
            print(f"Error processing file {m3u_file}: {e}")

    conn.commit()
    conn.close()
    
    print(f"Finished. Updated {updated_count} station logos.")

if __name__ == "__main__":
    update_logo_urls()
