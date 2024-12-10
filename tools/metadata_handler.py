from pathlib import Path
import json
from typing import Dict, Optional, Any
from rich.console import Console
from safetensors.torch import safe_open, save_file

class MetadataHandler:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace/SimpleTuner')

    def _load_json_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Safely load and parse a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to load {filepath.name}: {str(e)}[/yellow]")
            return None

    def create_metadata(self, model_name: str, version: str) -> Optional[Dict[str, str]]:
        """Create metadata from config files with complete preservation."""
        try:
            # Construct paths
            config_dir = self.workspace_path / 'config' / f"{model_name}-{version}"
            config_path = config_dir / 'config.json'
            backend_path = config_dir / 'multidatabackend.json'

            # Load configuration files
            config_data = self._load_json_file(config_path)
            backend_data = self._load_json_file(backend_path)

            if not config_data or not backend_data:
                return None

            # Store the complete configurations without modification
            metadata = {
                'complete_config': json.dumps(config_data, indent=2),
                'complete_backend': json.dumps(backend_data, indent=2)
            }

            return metadata

        except Exception as e:
            self.console.print(f"[red]Error creating metadata: {str(e)}[/red]")
            return None

    def update_safetensors_metadata(self, filepath: Path, metadata: Dict[str, str]) -> bool:
        """Update safetensors file with new metadata."""
        try:
            # Read existing tensors
            tensors = {}
            with safe_open(filepath, framework="pt", device="cpu") as f:
                for key in f.keys():
                    tensors[key] = f.get_tensor(key)

            # Save with updated metadata
            save_file(tensors, filepath, metadata)
            return True

        except Exception as e:
            self.console.print(f"[red]Error updating safetensors metadata: {str(e)}[/red]")
            return False