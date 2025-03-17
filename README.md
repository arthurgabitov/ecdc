
## Current version: 

- 0.0.4 Update: Minor UI updates. Overview screen added

## Updates history: 

- 0.0.3 Navigation Rail added. Time Counter function added.
- 0.0.3 Modular restructurisation. Welcome screen added. UI update.
- 0.0.2 Initial commit.



### 📌 Project structure description:

- **`config/`** — Contains project settings.
     - `config.ini` — Config file
- **`src/`** — Main application code:
  - `main.py` — Runs the application. 
  - `config.py` — Loads configuration settings.
  - `controllers/` — Folder with controllers.
     - 'station_controller.py' - Manages the core logic for the station dashboard
     - 'timer_component.py' - Time counter function
  - `views/` — Handles the user interface.
     - 'setting_view.py' - UI for settings module
     - 'station_view.py' - UI for station modules with spots generation. 
     - 'welcome_view.py' - UI for initial screen module
     - 'overview_view.py' - UI for Dashboard overview
    
- **`.venv/`** — Python virtual environment.
- **`requirements.txt`** — Project dependencies.
- **`config.json`**  — File for storing of all stations info
- **`README.md`** — Project documentation.
- **`version.txt`** — Current project version.

---


