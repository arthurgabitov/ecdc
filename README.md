
## Current version: 
- 0.0.7 Single Station Mode added. (to Activate put "stations": 1 in config.json)


## Updates history: 

- 0.0.6 Dashboard overview added. + spot status update
- 0.0.5 Update: Minor UI updates. Dashboard configuration file config.JSON added
- 0.0.4 Navigation Rail added. Time Counter function added.
- 0.0.3 Modular restructuring. Welcome screen added. UI update.
- 0.0.2 Initial commit.



### 📌 Project structure description:

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
- **`config.json`**  — Dashboard configuration 
- **`README.md`** — Project documentation.
- **`version.txt`** — Current project version.

---


