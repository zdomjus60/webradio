import tkinter as tk
from tkinter import ttk
import vlc
import sqlite3
import requests
import threading
import io
from PIL import Image, ImageTk

# --- Database Functions ---
def db_connect():
    return sqlite3.connect('radio.db')

def get_countries(conn):
    c = conn.cursor()
    c.execute("SELECT name FROM countries ORDER BY name")
    return [row[0] for row in c.fetchall()]

def get_genres(conn):
    c = conn.cursor()
    c.execute("SELECT name FROM genres ORDER BY name")
    return [row[0] for row in c.fetchall()]

def get_genres_for_country(conn, country):
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT g.name
        FROM genres g
        JOIN station_genres sg ON g.id = sg.genre_id
        JOIN stations s ON sg.station_id = s.id
        JOIN countries c ON s.country_id = c.id
        WHERE c.name = ?
        ORDER BY g.name
    """, (country,))
    return [row[0] for row in c.fetchall()]

def get_countries_for_genre(conn, genre):
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT c.name
        FROM countries c
        JOIN stations s ON c.id = s.country_id
        JOIN station_genres sg ON s.id = sg.station_id
        JOIN genres g ON sg.genre_id = g.id
        WHERE g.name = ?
        ORDER BY c.name
    """, (genre,))
    return [row[0] for row in c.fetchall()]

def get_stations(conn, country=None, genre=None):
    c = conn.cursor()
    query = """
        SELECT s.name, s.url, s.status, s.logo_url
        FROM stations s
        LEFT JOIN countries c ON s.country_id = c.id
        LEFT JOIN station_genres sg ON s.id = sg.station_id
        LEFT JOIN genres g ON sg.genre_id = g.id
    """
    filters = []
    params = []
    if country:
        filters.append("c.name = ?")
        params.append(country)
    if genre:
        filters.append("g.name = ?")
        params.append(genre)

    if filters:
        query += " WHERE " + " AND ".join(filters)
    
    c.execute(query + " ORDER BY s.name", tuple(params))
    return c.fetchall()

# --- UI Functions ---
def populate_countries(country_listbox, countries):
    country_listbox.delete(0, tk.END)
    for country in countries:
        country_listbox.insert(tk.END, country)

def populate_genres(genre_listbox, genres):
    genre_listbox.delete(0, tk.END)
    for genre in genres:
        genre_listbox.insert(tk.END, genre)

def apply_filters(country_listbox, genre_listbox, station_tree, conn):
    country_indices = country_listbox.curselection()
    genre_indices = genre_listbox.curselection()

    country = None
    if country_indices:
        country = country_listbox.get(country_indices[0])

    genre = None
    if genre_indices:
        genre = genre_listbox.get(genre_indices[0])

    update_station_list(station_tree, conn, country, genre)

def clear_filters(country_listbox, genre_listbox, station_tree, conn):
    country_listbox.selection_clear(0, tk.END)
    genre_listbox.selection_clear(0, tk.END)
    update_station_list(station_tree, conn)

def update_station_list(station_tree, conn, country=None, genre=None):
    station_tree.delete(*station_tree.get_children())
    stations = get_stations(conn, country, genre)
    for station in stations:
        station_tree.insert("", "end", values=station)

def on_station_select(event, station_tree, play_button, stop_button, info_label, song_label, logo_label, root):
    selected_item = station_tree.focus()
    if not selected_item:
        return

    item = station_tree.item(selected_item)
    values = item['values']
    name = values[0]
    url = values[1]
    logo_url = values[3] if len(values) > 3 else None

    info_label.config(text=f"Station: {name}")
    song_label.config(text="") # Reset song title
    play_button.config(state=tk.NORMAL if url else tk.DISABLED)
    stop_button.config(state=tk.DISABLED)

    load_logo(logo_url, logo_label, root)

    station_tree.set(selected_item, "Status", "Checking...")
    threading.Thread(target=check_station_status, args=(url, selected_item, root, station_tree), daemon=True).start()

# --- Player Functions ---
def play_radio(station_tree, player, info_label, song_label, stop_button, root):
    selected_item = station_tree.focus()
    if not selected_item:
        return

    status = station_tree.set(selected_item, "Status")
    if status != "Online":
        info_label.config(text="Station is offline.")
        return

    item = station_tree.item(selected_item)
    name = item['values'][0]
    url = item['values'][1]

    if url:
        media = player.get_instance().media_new(url)
        player.set_media(media)
        player.play()
        info_label.config(text=f"Now playing: {name}")
        song_label.config(text="...") # Placeholder for song
        stop_button.config(state=tk.NORMAL)

        # Update window title and song_label with NowPlaying metadata
        def meta_changed(event, player, song_label, root):
            meta = player.get_media().get_meta(vlc.Meta.NowPlaying)
            if meta:
                root.title(f"Radio Player - {meta}")
                song_label.config(text=f"Song: {meta}")
        
        events = player.event_manager()
        # Clear previous events to avoid duplicates
        events.event_detach(vlc.EventType.MediaMetaChanged)
        events.event_attach(vlc.EventType.MediaMetaChanged, lambda event: meta_changed(event, player, song_label, root))

def stop_radio(player, info_label, song_label, stop_button):
    player.stop()
    info_label.config(text="Playback stopped.")
    song_label.config(text="")
    stop_button.config(state=tk.DISABLED)

def check_station_status(url, item_id, root, station_tree):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }
        response = requests.get(url, headers=headers, stream=True, timeout=2)
        if response.status_code == 200:
            status = "Online"
        else:
            status = "Offline"
    except requests.exceptions.RequestException:
        status = "Offline"
    
    root.after(0, update_status_in_ui, item_id, status, station_tree)

def update_status_in_ui(item_id, status, station_tree):
    station_tree.set(item_id, "Status", status)

def load_logo(url, logo_label, root):
    """Load a logo from a URL in a background thread and display it."""
    # Set a placeholder or clear the current image
    placeholder = ImageTk.PhotoImage(Image.new("RGB", (100, 100), "grey"))
    logo_label.config(image=placeholder)
    logo_label.image = placeholder # Keep a reference

    if not url or not url.startswith('http'):
        return # No valid URL to load

    def _load_image():
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # Resize the image to a fixed width, maintaining aspect ratio
                width = 100
                aspect_ratio = image.height / image.width
                height = int(width * aspect_ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(image)
                
                # Schedule UI update on the main thread
                root.after(0, lambda: update_logo_in_ui(photo, logo_label))
        except Exception as e:
            print(f"Failed to load logo from {url}: {e}")

    threading.Thread(target=_load_image, daemon=True).start()

def update_logo_in_ui(photo, logo_label):
    """Updates the logo label with the new photo."""
    logo_label.config(image=photo)
    logo_label.image = photo # Keep a reference!

# --- Main Application Setup ---
def main():
    conn = db_connect()
    countries = get_countries(conn)
    genres = get_genres(conn)

    root = tk.Tk()
    root.title("Radio Player")
    root.geometry("1200x800")

    style = ttk.Style()
    style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
    style.configure("Treeview", font=("Helvetica", 9))

    # VLC player setup
    instance = vlc.Instance()
    player = instance.media_player_new()

    # --- UI --- #
    paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
    paned_window.pack(fill=tk.BOTH, expand=True)

    # Sidebar for filters
    filter_frame = ttk.Frame(paned_window, width=400)
    paned_window.add(filter_frame, weight=1)

    button_frame = ttk.Frame(filter_frame)
    button_frame.pack(fill=tk.X, pady=5)

    apply_button = ttk.Button(button_frame, text="Apply Filters")
    apply_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

    clear_button = ttk.Button(button_frame, text="Clear Filters")
    clear_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

    country_frame = ttk.LabelFrame(filter_frame, text="Countries")
    country_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    country_listbox = tk.Listbox(country_frame, exportselection=False)
    country_listbox.pack(fill=tk.BOTH, expand=True)
    populate_countries(country_listbox, countries)

    genre_frame = ttk.LabelFrame(filter_frame, text="Genres")
    genre_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    genre_listbox = tk.Listbox(genre_frame, exportselection=False)
    genre_listbox.pack(fill=tk.BOTH, expand=True)
    populate_genres(genre_listbox, genres)

    # Main frame for stations
    main_frame = ttk.Frame(paned_window)
    paned_window.add(main_frame, weight=3)

    station_tree = ttk.Treeview(main_frame, columns=("Nome", "URL", "Status", "LogoURL"), show="headings")
    station_tree.heading("Nome", text="Radio Name")
    station_tree.heading("URL", text="URL")
    station_tree.heading("Status", text="Status")
    station_tree.heading("LogoURL", text="Logo") # Define heading even if not shown
    station_tree["displaycolumns"] = ("Nome", "URL", "Status")
    station_tree.column("Nome", width=250, anchor=tk.W)
    station_tree.column("URL", width=350, anchor=tk.W)
    station_tree.column("Status", width=100, anchor=tk.W)
    station_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=station_tree.yview)
    station_tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Detail frame for player controls
    detail_frame = ttk.Frame(root, height=120, padding="10")
    detail_frame.pack(fill=tk.X)

    logo_label = ttk.Label(detail_frame)
    logo_label.pack(side=tk.LEFT, padx=10, anchor=tk.N)
    # Set initial placeholder
    placeholder = ImageTk.PhotoImage(Image.new("RGB", (100, 100), "grey"))
    logo_label.config(image=placeholder)
    logo_label.image = placeholder

    # Frame for textual info (station name and song title)
    text_info_frame = ttk.Frame(detail_frame)
    text_info_frame.pack(side=tk.LEFT, anchor=tk.N, padx=10)

    info_label = ttk.Label(text_info_frame, text="Select a radio to start.", wraplength=400, justify=tk.LEFT, font=("Helvetica", 10, "bold"))
    info_label.pack(anchor=tk.W)

    song_label = ttk.Label(text_info_frame, text="", wraplength=400, justify=tk.LEFT, font=("Helvetica", 9))
    song_label.pack(anchor=tk.W)

    play_button = ttk.Button(detail_frame, text="Play", state=tk.DISABLED)
    play_button.pack(side=tk.LEFT, padx=5)

    stop_button = ttk.Button(detail_frame, text="Stop", state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=5)

    # --- Bindings --- # 
    apply_button.config(command=lambda: apply_filters(country_listbox, genre_listbox, station_tree, conn))
    clear_button.config(command=lambda: clear_filters(country_listbox, genre_listbox, station_tree, conn))

    station_tree.bind("<<TreeviewSelect>>", lambda event: on_station_select(event, station_tree, play_button, stop_button, info_label, song_label, logo_label, root))

    play_button.config(command=lambda: play_radio(station_tree, player, info_label, song_label, stop_button, root))
    stop_button.config(command=lambda: stop_radio(player, info_label, song_label, stop_button))

    # --- Initial State --- #
    update_station_list(station_tree, conn)

    root.mainloop()

    conn.close()

if __name__ == "__main__":
    main()