from pathlib import Path
import json
from typing import Dict, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
import safetensors
from safetensors.torch import safe_open

class MetadataHandler:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner')
        
    def resolve_config_paths(self, model_name: str, version: str) -> Tuple[Optional[Path], Optional[Path]]:
        """Get paths to configuration files for a model version."""
        try:
            config_dir = self.base_path / 'config' / f"{model_name}-{version}"
            
            config_path = config_dir / "config.json"
            backend_path = config_dir / "multidatabackend.json"
            
            return (
                config_path if config_path.exists() else None,
                backend_path if backend_path.exists() else None
            )
        except Exception as e:
            self.console.print(f"[red]Error resolving config paths: {str(e)}[/red]")
            return None, None

    def extract_training_params(self, config_path: Path) -> Dict:
        """Extract training parameters from config.json."""
        try:
            with open(config_path) as f:
                config = json.load(f)
                
            params = {
                # Learning parameters
                "learning_rate": config.get("learning_rate"),
                "lr_scheduler": config.get("lr_scheduler"),
                "lr_warmup_steps": config.get("lr_warmup_steps"),
                "train_batch_size": config.get("train_batch_size"),
                "max_train_steps": config.get("max_train_steps"),
                "save_every_n_steps": config.get("save_every_n_steps"),
                
                # Model configuration
                "network_dim": config.get("network_dim"),
                "network_alpha": config.get("network_alpha"),
                "mixed_precision": config.get("mixed_precision"),
                "seed": config.get("seed"),
                "max_token_length": config.get("max_token_length"),
                "clip_skip": config.get("clip_skip"),
                
                # Optimizer settings
                "optimizer_type": config.get("optimizer_type"),
                "optimizer_args": config.get("optimizer_args"),
                
                # Training features
                "noise_offset": config.get("noise_offset"),
                "weighted_captions": config.get("weighted_captions"),
                "cache_latents": config.get("cache_latents", True),
                "cache_latents_to_disk": config.get("cache_latents_to_disk", True),
                
                # Additional settings
                "keep_tokens": config.get("keep_tokens"),
                "flip_aug": config.get("flip_aug"),
                "prior_loss_weight": config.get("prior_loss_weight"),
                "unit": config.get("unit")
            }
            
            return {k: v for k, v in params.items() if v is not None}
        except Exception as e:
            self.console.print(f"[red]Error extracting training parameters: {str(e)}[/red]")
            return {}

    def extract_dataset_info(self, backend_path: Path) -> Dict:
        """Extract dataset information from multidatabackend.json."""
        try:
            with open(backend_path) as f:
                backend = json.load(f)
                
            primary_backend = next(
                (b for b in backend if isinstance(b, dict) and b.get('dataset_type') == 'image'),
                None
            )
            
            if not primary_backend:
                return {}
                
            info = {
                "resolution": primary_backend.get("resolution"),
                "crop_aspect_ratio": primary_backend.get("crop_aspect"),
                "bucket_resolution_steps": primary_backend.get("bucket_resolution_steps"),
                "crop_aspect_buckets": primary_backend.get("crop_aspect_buckets"),
                "caption_strategy": primary_backend.get("caption_strategy")
            }
            
            return {k: v for k, v in info.items() if v is not None}
        except Exception as e:
            self.console.print(f"[red]Error extracting dataset information: {str(e)}[/red]")
            return {}

    def create_metadata(self, model_name: str, version: str) -> Optional[Dict]:
        """Create metadata dictionary for a model version."""
        try:
            config_path, backend_path = self.resolve_config_paths(model_name, version)
            if not config_path or not backend_path:
                return None
                
            # Extract metadata
            training_params = self.extract_training_params(config_path)
            dataset_info = self.extract_dataset_info(backend_path)
            
            # Combine metadata
            metadata = {
                "training_params": json.dumps(training_params),
                "dataset_info": json.dumps(dataset_info)
            }
            
            # Display metadata panel
            self.display_metadata_panel(metadata)
            
            return metadata
        except Exception as e:
            self.console.print(f"[red]Error creating metadata: {str(e)}[/red]")
            return None

    def display_metadata_panel(self, metadata: Dict) -> None:
        """Display metadata in a formatted panel."""
        try:
            training_params = json.loads(metadata.get("training_params", "{}"))
            dataset_info = json.loads(metadata.get("dataset_info", "{}"))
            
            training_str = "\n".join(f"{k}: {v}" for k, v in training_params.items())
            dataset_str = "\n".join(f"{k}: {v}" for k, v in dataset_info.items())
            
            panel = Panel.fit(
                f"[cyan]Training Parameters:[/cyan]\n{training_str}\n\n"
                f"[cyan]Dataset Information:[/cyan]\n{dataset_str}",
                title=f"[bold magenta]Training Configuration Summary[/bold magenta]",
                border_style="blue"
            )
            self.console.print(panel)
        except Exception as e:
            self.console.print(f"[red]Error displaying metadata: {str(e)}[/red]")

    def update_safetensors_metadata(self, model_path: Path, metadata: Dict) -> bool:
        """Update safetensors file with metadata."""
        try:
            # Read existing tensors and metadata
            tensors = {}
            with safe_open(model_path, framework="pt", device="cpu") as f:
                # Preserve any existing metadata
                existing_metadata = dict(f.metadata())
                for k in f.keys():
                    tensors[k] = f.get_tensor(k)
            
            # Merge existing metadata with new metadata
            combined_metadata = {**existing_metadata, **metadata}
            
            # Save with updated metadata
            safetensors.torch.save_file(tensors, model_path, combined_metadata)
            return True
        except Exception as e:
            self.console.print(f"[red]Error updating metadata: {str(e)}[/red]")
            return False