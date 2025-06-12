## Current version:
- 0.2.2 Added DT file generation function with Excel formatting preservation

## Updates history:
- 0.2.2 Added a new function for generating DT files with full formatting preservation using Excel COM. The "Generate DT" button in the spot card extracts an integer array from sysmast.sv, writes values to the DT Excel file, and opens the result automatically.
- 0.2.1 Centralized all UI styles (colors, fonts, paddings, shadows) in styles.py. Improved spot card visuals, unified timer button styles, enhanced error handling and user feedback via snackbars, and fixed several UI/logic bugs.
- 0.1.5 Login function
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
  - `main.py` — Application entry point.
  - `config.py` — Loads and manages configuration settings.
  - `styles.py` — Centralized UI styles (colors, fonts, paddings, shadows, etc.).
  - `sv_converter.py` — Utilities for SV file conversion.
  - `controllers/` — Business logic and data controllers:
     - `station_controller.py` — Core logic for the station dashboard.
     - `timer_component.py` — Timer and time counter logic.
     - `ro_customization_tools.py` — Functions for WO, SW, USB, and DT file search.
     - `dt_generator.py` — DT file generation and Excel editing logic.
     - `sharepoint_controller.py` — SharePoint integration logic.
  - `views/` — User interface components:
     - `station_view.py` — UI for station modules and spot generation.
     - `spot_view.py` — UI for individual spot cards (robot info, DT generation, etc.).
     - `dashboard_view.py` — Dashboard overview UI.
     - `settings_view.py` — UI for settings module.
     - `welcome_view.py` — UI for the initial welcome screen.
     - `navigation_rail_view.py` — Navigation rail UI component.
     - `top_bar.py` — Top bar UI component.
  - `models/` — Data models and database connectors:
     - `user_model.py` — User authentication and info.
     - `db_connector.py` — Database connection logic.
  - `data/` — App data and cache files (e.g., users_cache.json).
  - `assets/` — Images, icons, and other static resources.

- **`.venv/`** — Python virtual environment.
- **`requirements.txt`** — Project dependencies.
- **`config.json`** — Dashboard and app configuration.
- **`README.md`** — Project documentation.
- **`version.txt`** — Current project version.

---


