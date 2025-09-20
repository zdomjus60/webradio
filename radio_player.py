import tkinter as tk
from tkinter import ttk
import vlc
import sqlite3
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
    
    c.execute(query, tuple(params))
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

def on_station_select(event, station_tree, play_button, stop_button, info_label, root):
    selected_item = station_tree.focus()
    if not selected_item:
        return

    item = station_tree.item(selected_item)
    name = item['values'][0]
    url = item['values'][1]

    info_label.config(text=f"Nome: {name}")
    play_button.config(state=tk.NORMAL if url else tk.DISABLED)
    stop_button.config(state=tk.DISABLED)

    station_tree.set(selected_item, "Status", "Checking...")
    threading.Thread(target=check_station_status, args=(url, selected_item, root, station_tree), daemon=True).start()

# --- Player Functions ---
def play_radio(station_tree, player, info_label, stop_button, root, artwork_label):
    selected_item = station_tree.focus()
    if not selected_item:
        return

    status = station_tree.set(selected_item, "Status")
    if status != "Online":
        info_label.config(text="La stazione è offline.")
        return

    item = station_tree.item(selected_item)
    name = item['values'][0]
    url = item['values'][1]
    logo_url = item['values'][3] # Get logo_url from the database

    if url:
        media = player.get_instance().media_new(url)
        player.set_media(media)
        player.play()
        info_label.config(text=f"In riproduzione: {name}")
        stop_button.config(state=tk.NORMAL)

        # Update window title with NowPlaying metadata (still from VLC)
        def meta_changed(event, player, info_label):
            meta = player.get_media().get_meta(vlc.Meta.NowPlaying)
            if meta:
                root.title(f"Radio Player - {meta}")
                info_label.config(text=f"In riproduzione: {meta}")
        events = player.event_manager()
        events.event_attach(vlc.EventType.MediaMetaChanged, lambda event: meta_changed(event, player, info_label))

        events = player.event_manager()
        events.event_attach(vlc.EventType.MediaMetaChanged, lambda event: meta_changed(event, player))

        # Download and display logo from database
        if logo_url:
            threading.Thread(target=download_artwork, args=(logo_url, root, artwork_label), daemon=True).start()

def download_artwork(url, root, artwork_label):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            image_data = response.content
            image = Image.open(io.BytesIO(image_data))
            image = image.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            root.after(0, update_artwork_in_ui, photo, artwork_label)
    except Exception as e:
        pass # Ignore artwork download errors

def update_artwork_in_ui(photo, artwork_label):
    artwork_label.config(image=photo)
    artwork_label.image = photo # Keep a reference

def stop_radio(player, info_label, stop_button):
    player.stop()
    info_label.config(text="Riproduzione fermata.")
    stop_button.config(state=tk.DISABLED)

import requests
import threading

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

    country_frame = ttk.LabelFrame(filter_frame, text="Paesi")
    country_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    country_listbox = tk.Listbox(country_frame, exportselection=False)
    country_listbox.pack(fill=tk.BOTH, expand=True)
    populate_countries(country_listbox, countries)

    genre_frame = ttk.LabelFrame(filter_frame, text="Generi")
    genre_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    genre_listbox = tk.Listbox(genre_frame, exportselection=False)
    genre_listbox.pack(fill=tk.BOTH, expand=True)
    populate_genres(genre_listbox, genres)

    # Main frame for stations
    main_frame = ttk.Frame(paned_window)
    paned_window.add(main_frame, weight=3)

    station_tree = ttk.Treeview(main_frame, columns=("Nome", "URL", "Status"), show="headings")
    station_tree.heading("Nome", text="Nome Radio")
    station_tree.heading("URL", text="URL")
    station_tree.heading("Status", text="Status")
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

    artwork_frame = tk.Frame(detail_frame, width=100, height=100, bg="black")
    artwork_frame.pack(side=tk.LEFT, padx=10)
    artwork_frame.pack_propagate(False) # Prevent the frame from resizing to fit its content

    artwork_label = tk.Label(artwork_frame, bg="black")
    artwork_label.pack(fill=tk.BOTH, expand=True)

    info_label = ttk.Label(detail_frame, text="Seleziona una radio per iniziare.", wraplength=400, justify=tk.LEFT, font=("Helvetica", 10))
    info_label.pack(side=tk.LEFT, padx=10)

    play_button = ttk.Button(detail_frame, text="Play", state=tk.DISABLED)
    play_button.pack(side=tk.LEFT, padx=5)

    stop_button = ttk.Button(detail_frame, text="Stop", state=tk.DISABLED)
    stop_button.pack(side=tk.LEFT, padx=5)

    # --- Bindings --- # 
    apply_button.config(command=lambda: apply_filters(country_listbox, genre_listbox, station_tree, conn))
    clear_button.config(command=lambda: clear_filters(country_listbox, genre_listbox, station_tree, conn))

    station_tree.bind("<<TreeviewSelect>>", lambda event: on_station_select(event, station_tree, play_button, stop_button, info_label, root))

    play_button.config(command=lambda: play_radio(station_tree, player, info_label, stop_button, root, artwork_label))
    stop_button.config(command=lambda: stop_radio(player, info_label, stop_button))

    # --- Initial State --- #
    update_station_list(station_tree, conn)

    root.mainloop()

    conn.close()

if __name__ == "__main__":
    main()