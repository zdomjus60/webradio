import tkinter as tk
from tkinter import ttk
import vlc
import threading
import sqlite3

import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class RadioPlayerApp:
    def __init__(self, root):
        logging.debug("Initializing application")
        self.root = root
        self.root.title("Radio Player")
        self.root.geometry("1024x768")

        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=("Helvetica", 10, "bold"))
        self.style.configure("Treeview", font=("Helvetica", 9))

        # VLC player setup
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        self.catalog = {"countries": {}, "genres": {}}
        self.radio_data = []

        self.create_widgets()
        self.start_cataloging()

    def create_widgets(self):
        # PanedWindow per dividere la finestra
        paned_window = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        sidebar_frame = ttk.Frame(paned_window, width=250)
        paned_window.add(sidebar_frame, weight=1)

        # Pulsanti per cambiare vista
        button_frame = ttk.Frame(sidebar_frame)
        button_frame.pack(fill=tk.X, pady=5)

        self.countries_button = ttk.Button(button_frame, text="Paesi", command=self.show_countries)
        self.countries_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.genres_button = ttk.Button(button_frame, text="Generi", command=self.show_genres)
        self.genres_button.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Treeview per le categorie
        self.category_tree = ttk.Treeview(sidebar_frame, show="tree")
        self.category_tree.pack(fill=tk.BOTH, expand=True)
        self.category_tree.bind("<<TreeviewSelect>>", self.on_category_select)

        # Frame principale per le stazioni
        main_frame = ttk.Frame(paned_window)
        paned_window.add(main_frame, weight=3)

        # Treeview per le stazioni
        columns = ("Nome",)
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        self.tree.heading("Nome", text="Nome Radio")
        
        self.tree.column("Nome", width=300, anchor=tk.W)

        # Scrollbar per il Treeview delle stazioni
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self.on_radio_select)

        # Frame per i dettagli
        self.detail_frame = ttk.Frame(self.root, padding="10")
        self.detail_frame.pack(fill=tk.X)

        self.info_label = ttk.Label(self.detail_frame, text="Seleziona una radio per iniziare.", wraplength=400, justify=tk.LEFT, font=("Helvetica", 10))
        self.info_label.pack(side=tk.LEFT, padx=10)

        self.play_button = ttk.Button(self.detail_frame, text="Play", command=self.play_radio, state=tk.DISABLED)
        self.play_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(self.detail_frame, text="Stop", command=self.stop_radio, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def show_countries(self):
        logging.debug("Showing countries")
        self.category_tree.delete(*self.category_tree.get_children())
        for country in sorted(self.catalog["countries"].keys()):
            self.category_tree.insert("", "end", text=country, iid=country, open=False)

    def show_genres(self):
        logging.debug("Showing genres")
        self.category_tree.delete(*self.category_tree.get_children())
        for genre in sorted(self.catalog["genres"].keys()):
            self.category_tree.insert("", "end", text=genre, iid=genre, open=False)

    def on_category_select(self, event):
        selected_item = self.category_tree.focus()
        logging.debug(f"Selected item: {selected_item}")
        if not selected_item:
            return

        self.tree.delete(*self.tree.get_children())

        if not self.category_tree.get_children(selected_item):
            parent_iid = self.category_tree.parent(selected_item)
            logging.debug(f"Parent iid: {parent_iid}")
            if parent_iid:
                parent_text = self.category_tree.item(parent_iid, "text")
                logging.debug(f"Parent text: {parent_text}")
                selected_text = self.category_tree.item(selected_item, "text")
                logging.debug(f"Selected text: {selected_text}")
                if parent_text in self.catalog["countries"]:
                    logging.debug("Parent is a country")
                    self.radio_data = self.catalog["countries"][parent_text][selected_text]
                elif parent_text in self.catalog["genres"]:
                    logging.debug("Parent is a genre")
                    self.radio_data = self.catalog["genres"][parent_text][selected_text]
                
                logging.debug(f"Radio data: {self.radio_data}")
                for radio in self.radio_data:
                    self.tree.insert("", "end", values=(radio["name"],))
            else: # top level item
                logging.debug("Top level item")
                if selected_item in self.catalog["countries"]:
                    logging.debug("Selected item is a country")
                    for genre in sorted(self.catalog["countries"][selected_item].keys()):
                        self.category_tree.insert(selected_item, "end", text=genre, iid=f"{selected_item}/{genre}")
                elif selected_item in self.catalog["genres"]:
                    logging.debug("Selected item is a genre")
                    for country in sorted(self.catalog["genres"][selected_item].keys()):
                        self.category_tree.insert(selected_item, "end", text=country, iid=f"{selected_item}/{country}")


    def start_cataloging(self):
        """Avvia la catalogazione di tutte le stazioni."""
        self.info_label.config(text="Avvio catalogazione...")
        
        catalog_thread = threading.Thread(target=self._cataloging_thread)
        catalog_thread.daemon = True
        catalog_thread.start()

    def _cataloging_thread(self):
        self.load_data_from_db()
        print("Cataloging finished.")
        self.root.after(0, lambda: self.info_label.config(text="Catalogazione completata."))
        self.root.after(0, self.show_countries)

    def load_data_from_db(self):
        conn = sqlite3.connect('radio.db')
        c = conn.cursor()

        # Load countries and their genres
        c.execute("SELECT c.name, g.name, s.name, s.url FROM countries c JOIN stations s ON c.id = s.country_id JOIN station_genres sg ON s.id = sg.station_id JOIN genres g ON sg.genre_id = g.id")
        for country, genre, station_name, station_url in c.fetchall():
            if country not in self.catalog["countries"]:
                self.catalog["countries"][country] = {}
            if genre not in self.catalog["countries"][country]:
                self.catalog["countries"][country][genre] = []
            self.catalog["countries"][country][genre].append({"name": station_name, "stream_url": station_url})

        # Load genres and their countries
        c.execute("SELECT g.name, c.name, s.name, s.url FROM genres g JOIN station_genres sg ON g.id = sg.genre_id JOIN stations s ON sg.station_id = s.id JOIN countries c ON s.country_id = c.id")
        for genre, country, station_name, station_url in c.fetchall():
            if genre not in self.catalog["genres"]:
                self.catalog["genres"][genre] = {}
            if country not in self.catalog["genres"][genre]:
                self.catalog["genres"][genre][country] = []
            self.catalog["genres"][genre][country].append({"name": station_name, "stream_url": station_url})

        conn.close()

    def on_radio_select(self, event):
        """Gestisce la selezione di una radio nel Treeview."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_index = self.tree.index(selected_item)
        radio_info = self.radio_data[item_index]
        
        name = radio_info["name"]
        stream_url = radio_info.get("stream_url")

        self.info_label.config(text=f"Nome: {name}")
        
        if stream_url:
            self.play_button.config(state=tk.NORMAL)
        else:
            self.play_button.config(state=tk.DISABLED)

        self.stop_button.config(state=tk.DISABLED)

    def play_radio(self):
        """Avvia la riproduzione della radio."""
        selected_item = self.tree.focus()
        if not selected_item:
            return

        item_index = self.tree.index(selected_item)
        radio_info = self.radio_data[item_index]
        stream_url = radio_info.get("stream_url")

        if stream_url:
            media = self.instance.media_new(stream_url)
            self.player.set_media(media)
            self.player.play()
            self.info_label.config(text=f"In riproduzione: {radio_info['name']}")
            self.stop_button.config(state=tk.NORMAL)

    def stop_radio(self):
        """Farma la riproduzione."""
        self.player.stop()
        self.info_label.config(text="Riproduzione fermata.")
        self.stop_button.config(state=tk.DISABLED)


if __name__ == "__main__":
    root = tk.Tk()
    app = RadioPlayerApp(root)
    root.mainloop()
