import os
import json

DEFAULT_SETTINGS = {
    "refresh_interval": 15,          # seconds
    "bulk_threshold": 5000,          # number of shares
    "data_folder": "data",           # folder to store YYYY-MM-DD.csv
    "auto_start_collector": True,    # start collector process automatically in app.py
    "enable_sound": True             # enable buzzer/sound in Streamlit
}

def get_settings_file_path():
    # Store settings.json in the current working directory (project root)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "settings.json"))

def load_settings():
    filepath = get_settings_file_path()
    if not os.path.exists(filepath):
        # Create default settings
        save_settings(DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(filepath, "r") as f:
            settings = json.load(f)
            # Ensure all default keys exist
            updated = False
            for k, v in DEFAULT_SETTINGS.items():
                if k not in settings:
                    settings[k] = v
                    updated = True
            if updated:
                save_settings(settings)
            return settings
    except Exception as e:
        print(f"Error loading settings, using defaults: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    filepath = get_settings_file_path()
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(settings, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving settings to {filepath}: {e}")
        return False
