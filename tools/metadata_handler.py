from pathlib import Path
import json
from typing import Dict, Optional, Any
from rich.console import Console
from safetensors import safe_open, serialize_file

class MetadataHandler:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace/SimpleTuner')

    def _load_json_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """Safely load and parse a JSON file."""
        try:
            if not filepath.exists():
                self.console.print(f"[yellow]Warning: File not found: {filepath}[/yellow]")
                return None
                
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to load {filepath.name}: {str(e)}[/yellow]")
            return None

    def create_metadata(self, model_path: str) -> Optional[Dict[str, str]]:
        """Create metadata from config files with complete preservation."""
        try:
            # Construct paths using full model path
            config_dir = self.workspace_path / 'config' / model_path
            config_path = config_dir / 'config.json'
            backend_path = config_dir / 'multidatabackend.json'

            if self.console.is_debug:
                self.console.print(f"[dim]Looking for configs in: {config_dir}[/dim]")
                self.console.print(f"[dim]Config path: {config_path}[/dim]")
                self.console.print(f"[dim]Backend path: {backend_path}[/dim]")

            # Load configuration files
            config_data = self._load_json_file(config_path)
            backend_data = self._load_json_file(backend_path)

            if not config_data or not backend_data:
                return None

            # Extract key training parameters
            training_params = {
                "model_type": str(config_data.get("--model_type", "")),
                "lora_rank": str(config_data.get("--lora_rank", "")),
                "learning_rate": str(config_data.get("--learning_rate", "")),
                "lr_scheduler": str(config_data.get("--lr_scheduler", "")),
                "train_batch_size": str(config_data.get("--train_batch_size", "")),
                "resolution_type": str(config_data.get("--resolution_type", "")),
                "instance_prompt": str(config_data.get("--instance_prompt", "")),
                "model_family": str(config_data.get("--model_family", ""))
            }

            # Store full configurations and training summary
            metadata = {
                'complete_config': json.dumps(config_data),
                'complete_backend': json.dumps(backend_data),
                'training_params': json.dumps(training_params)
            }

            return metadata

        except Exception as e:
            self.console.print(f"[red]Error creating metadata: {str(e)}[/red]")
            return None

    def update_safetensors_metadata(self, filepath: Path, metadata: Dict[str, str]) -> bool:
        """Update safetensors file with new metadata."""
        try:
            # Read the existing tensors and metadata
            with safe_open(filepath, framework="numpy") as f:
                # Get existing tensors
                tensors = {k: f.get_tensor(k) for k in f.keys()}
                existing_metadata = f.metadata()

            # Update metadata
            if existing_metadata:
                metadata = {**existing_metadata, **metadata}

            # Write back with updated metadata
            serialize_file(tensors, filepath, metadata)
            return True

        except Exception as e:
            self.console.print(f"[red]Error updating safetensors metadata: {str(e)}[/red]")
            return False