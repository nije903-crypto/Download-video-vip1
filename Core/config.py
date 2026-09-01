import json
from pathlib import Path

CONFIG_DIR = Path.home() / '.khdiamond'
CONFIG_FILE = CONFIG_DIR / 'config.json'

class ConfigManager:
    @staticmethod
    def load():
        """Load configuration from file"""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        
        # Default configuration
        default_config = {
            'save_path': str(Path.home() / 'Downloads')
        }
        ConfigManager.save(default_config)
        return default_config
    
    @staticmethod
    def save(config):
        """Save configuration to file"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass
