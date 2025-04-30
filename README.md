
## Current version: 
- 0.1.5 Login function


## Updates history: 
- 0.1.3 Single station mode release.
- 0.1.1 Robot info section in spot modified. SW and backup section in spot updated.
- 0.0.11 General improvements. Robot info section added in spot. General functions for SW generating added. PyPDF2 added for memorysize parsing. 
- 0.0.10 Search SW file and parsing of E-number functions added
- 0.0.8 Performance updates. Dashboard test mode in settings page added
- 0.0.7 Single Station Mode added. (to Activate put "stations": 1 in config.json)
- 0.0.6 Dashboard overview added. + spot status update
- 0.0.5 Update: Minor UI updates. Dashboard configuration file config.JSON added
- 0.0.4 Navigation Rail added. Time Counter function added.
- 0.0.3 Modular restructuring. Welcome screen added. UI update.




### 📌 Project structure description:

- **`src/`** — Main application code:
  - `main.py` — Runs the application. 
  - `config.py` — Loads configuration settings.
  - `controllers/` — Folder with controllers.
     - 'station_controller.py' - Manages the core logic for the station dashboard
     - 'timer_component.py' - Time counter function
     - 'ro_customization_tools.py' - WO, SW and USB related functions
  - `views/` — Handles the user interface.
     - 'setting_view.py' - UI for settings module
     - 'station_view.py' - UI for station modules with spots generation. 
     - 'spot_view.py' - UI for spot 
     - 'welcome_view.py' - UI for initial screen module
     - 'overview_view.py' - UI for Dashboard overview
    
- **`.venv/`** — Python virtual environment.
- **`requirements.txt`** — Project dependencies.
- **`config.json`**  — Dashboard configuration 
- **`README.md`** — Project documentation.
- **`version.txt`** — Current project version.

---


