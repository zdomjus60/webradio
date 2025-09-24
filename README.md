# Python VLC Radio Player

A simple, filterable radio player built with Python, Tkinter, and VLC. It uses a SQLite database populated with station data from the extensive collection maintained by junguler.

This project allows you to browse, filter, and play thousands of internet radio stations. It displays station logos and currently playing song metadata where available.

## Features

*   **Large Station Database**: Utilizes data from thousands of M3U playlists.
*   **Filter by Country and Genre**: Easily narrow down the station list.
*   **Logo Display**: Shows the selected station's logo.
*   **Song Metadata**: Displays the currently playing song title if the stream provides it.
*   **Real-time Status Check**: Checks if a station is online before attempting to play.
*   **Modern UI**: A clean and simple interface built with Tkinter.

## Prerequisites

*   Python 3.7+
*   VLC Media Player must be installed on your system, as this application relies on `libvlc`.

## Setup Instructions

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    *(On Windows, use `venv\Scripts\activate`)*

3.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

The application requires a one-time database setup.

1.  **Build the Database:**
    Run the `build_db.py` script to create and populate the `radio.db` file. This will scrape station information.
    ```bash
    python3 build_db.py
    ```

2.  **Update Logos:**
    After the initial build, run the `update_logos.py` script to specifically parse and update the station logo URLs from the source files.
    ```bash
    python3 update_logos.py
    ```

3.  **Run the Player:**
    Once the database is ready, you can launch the radio player.
    ```bash
    python3 radio_player.py
    ```

## Acknowledgements

This project would not be possible without the incredible work done by **[junguler](https://github.com/junguler)** and contributors in maintaining the **[m3u-radio-music-playlists](https://github.com/junguler/m3u-radio-music-playlists)** repository. It serves as the primary source for all station data used in this application.

## Disclaimer

This application is a player for publicly available internet radio streams. The stream URLs and associated metadata (including station names, logos, and song titles) are provided by third-party services and are not hosted or controlled by this project.

The availability and content of streams are subject to change without notice. The developers of this application are not responsible for the content broadcasted by these stations or for any potential copyright or policy violations. Users are responsible for ensuring they have the right to access the content in their jurisdiction.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
