from pathlib import Path
import traceback
import shutil
import subprocess
from typing import List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.prompt import Prompt

# Import the required tools
from tools.lora_mover import LoRaMover
from tools.dataset_grid import DatasetGridTool
from tools.validation_grid import ValidationGridTool
from tools.download_configs import Tool as ConfigDownloader

class ProcessOrchestrator:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTuner'
        self.config_path = self.simpletuner_path / 'config'
        
        # Initialize tool instances
        self.lora_mover = LoRaMover()
        self.dataset_grid = DatasetGridTool()
        self.validation_grid = ValidationGridTool()
        self.config_downloader = ConfigDownloader()
        
        # Configure paths for tools
        self.lora_mover.base_path = self.workspace_path / 'SimpleTuner/output'
        self.lora_mover.destination_base = self.workspace_path / 'ComfyUI/models/loras/flux'

    def get_output_version_path(self, config_name: str) -> str:
        """Extract the version path for output directory from config name."""
        parts = config_name.split('_', 1)
        if len(parts) > 1:
            return parts[1]
        return config_name

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        required_paths = {
            'workspace': self.workspace_path,
            'SimpleTuner': self.simpletuner_path,
            'config': self.config_path,
        }
        
        missing_paths = []
        for name, path in required_paths.items():
            if not path.exists():
                missing_paths.append(f"{name}: {path}")
                
        if missing_paths:
            self.console.print("[red]Error: Missing required directories:[/red]")
            for path in missing_paths:
                self.console.print(f"[red]- {path}[/red]")
            return False
        return True

    def list_config_families(self) -> Tuple[List[str], Dict[str, List[str]]]:
        """List families (base names) grouped from configuration folders."""
        folders = [f for f in self.config_path.iterdir() 
                if f.is_dir() and f.name != 'templates' 
                and not f.name.startswith('.ipynb_checkpoints')]

        grouped = {}
        for folder in folders:
            if "_" in folder.name:
                base_name = folder.name.split('_', 1)[0]
            elif "-" in folder.name:
                base_name = folder.name.split('-', 1)[0]
            else:
                base_name = folder.name
            grouped.setdefault(base_name, []).append(folder.name)

        return sorted(grouped.keys()), grouped

    def display_families(self, families: List[str]) -> None:
        """Display available model families."""
        table = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table.add_column("Family", style="white", no_wrap=True)
        
        for idx, family in enumerate(families, 1):
            table.add_row(f"[yellow]{idx}.[/yellow] {family}")
        
        panel = Panel(table, title="[gold1]Available Families[/gold1]", border_style="blue")
        self.console.print(panel)
        print()

    def display_versions(self, family: str, versions: List[str]) -> None:
        """Display available versions for a family."""
        table = Table(show_header=False, box=None, show_edge=False, padding=(1, 1))
        table.add_column("Version", style="white", no_wrap=True)
        
        for idx, version in enumerate(versions, 1):
            table.add_row(f"[yellow]{idx}.[/yellow] {version}")
        
        panel = Panel(table, title=f"[gold1]{family} Versions[/gold1]", border_style="blue")
        self.console.print(panel)
        print()

    def process_all(self, family: str, version: str) -> bool:
        """Run all processing steps for selected model and version."""
        try:
            success = True
            output_version = self.get_output_version_path(version)
            source_path = self.lora_mover.base_path / family / output_version
            dest_path = self.lora_mover.destination_base / family / output_version
            
            # Step 1: Process LoRA movement
            self.console.print("\n[cyan]Step 1: Processing LoRA movement...[/cyan]")
            try:
                if not source_path.exists():
                    self.console.print(f"[red]Source path does not exist: {source_path}[/red]")
                    return False
                
                self.console.print(f"[cyan]Source path: {source_path}[/cyan]")
                self.console.print(f"[cyan]Destination path: {dest_path}[/cyan]")
                
                dest_path.mkdir(parents=True, exist_ok=True)
                checkpoints = [d for d in source_path.iterdir() 
                             if d.is_dir() and d.name.startswith('checkpoint-')]
                
                if not checkpoints:
                    self.console.print("[yellow]No checkpoints found to process[/yellow]")
                    return False
                
                for checkpoint_dir in checkpoints:
                    step_count = checkpoint_dir.name.split('-')[1]
                    step_count = str(int(step_count)).zfill(5)
                    
                    source_file = checkpoint_dir / "pytorch_lora_weights.safetensors"
                    if source_file.exists():
                        new_filename = f"{version}-{step_count}.safetensors"
                        dest_file = dest_path / new_filename
                        shutil.copy2(source_file, dest_file)
                        self.console.print(f"[green]Copied: {new_filename}[/green]")
                
                # Sync to Dropbox using just the relative path
                self.lora_mover.sync_to_dropbox(f"{family}/{output_version}")
                
            except Exception as e:
                self.console.print(f"[red]Error in LoRA move: {str(e)}[/red]")
                traceback.print_exc()
                success = False
            
            # Step 2: Create validation grid
            self.console.print("\n[cyan]Step 2: Creating validation grid...[/cyan]")
            try:
                validation_path = source_path / 'validation_images'
                if validation_path.exists():
                    images = list(validation_path.glob('*.png'))
                    if images:
                        # Just pass the images for validation grid
                        grid_image = self.validation_grid.create_grid(
                            images=images,
                            model=family,
                            version=output_version
                        )
                        if grid_image:
                            if self.validation_grid.save_grid(grid_image, family, output_version):
                                self.console.print("[green]Validation grid created successfully![/green]")
                            else:
                                self.console.print("[red]Error saving validation grid[/red]")
                                success = False
                    else:
                        self.console.print("[yellow]No validation images found[/yellow]")
                else:
                    self.console.print(f"[yellow]No validation images found at: {validation_path}[/yellow]")
                
            except Exception as e:
                self.console.print(f"[red]Validation grid creation failed: {str(e)}[/red]")
                traceback.print_exc()
                success = False
            
            # Step 3: Create dataset grid
            self.console.print("\n[cyan]Step 3: Creating dataset grid...[/cyan]")
            try:
                config_dir = self.config_path / version
                dataset_dir = self.dataset_grid.get_dataset_path(config_dir)
                
                if dataset_dir and dataset_dir.exists():
                    images = list(dataset_dir.glob("*.jpg")) + \
                            list(dataset_dir.glob("*.jpeg")) + \
                            list(dataset_dir.glob("*.png"))
                    
                    if images:
                        output_file = config_dir / f"{version}-dataset_grid.jpg"
                        low_res_file = config_dir / f"{version}-dataset_grid_lores.jpg"
                        title = f"{version} - {dataset_dir.name}"
                        
                        self.console.print("[cyan]Creating dataset grid...[/cyan]")
                        grid_image = self.dataset_grid.create_grid(
                            images=images,
                            output_path=output_file,
                            title=title
                        )
                        
                        if grid_image:
                            self.dataset_grid.save_low_res_version(grid_image, low_res_file)
                            self.console.print("[green]Dataset grid saved successfully![/green]")
                        else:
                            self.console.print("[red]Error creating dataset grid[/red]")
                            success = False
                    else:
                        self.console.print("[red]No images found in dataset directory[/red]")
                else:
                    self.console.print("[red]Dataset directory not found or invalid[/red]")
                    success = False
                
            except Exception as e:
                self.console.print(f"[red]Dataset grid creation failed: {str(e)}[/red]")
                traceback.print_exc()
                success = False
            
            # Step 4: Download configs
            self.console.print("\n[cyan]Step 4: Downloading configs...[/cyan]")
            try:
                source_path = self.config_path / version
                if source_path.exists():
                    # Use the ConfigDownloader to find matching folder
                    dropbox_folder = self.config_downloader.find_matching_dropbox_folder(family)
                    if not dropbox_folder:
                        self.console.print("[red]Could not find matching Dropbox folder[/red]")
                        return False
                        
                    # Construct the full path
                    dropbox_path = f"{self.config_downloader.dropbox_base}/{dropbox_folder}/4training/config/{version}"
                    
                    self.console.print(f"[cyan]Copying config to: {dropbox_path}[/cyan]")
                    
                    try:
                        cmd = [
                            "rclone",
                            "copy",
                            "--checksum",
                            str(source_path),
                            dropbox_path,
                            "-P"
                        ]
                        
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            self.console.print("[green]Config files copied successfully![/green]")
                        else:
                            self.console.print(f"[red]Rclone command failed: {result.stderr}[/red]")
                            success = False
                            
                    except Exception as e:
                        self.console.print(f"[red]Error running rclone: {str(e)}[/red]")
                        success = False
                else:
                    self.console.print(f"[red]Config path not found: {source_path}[/red]")
                    success = False
                        
            except Exception as e:
                self.console.print(f"[red]Config download failed: {str(e)}[/red]")
                traceback.print_exc()
                success = False
            
            return success
            
        except Exception as e:
            self.console.print(f"[red]Error in processing: {str(e)}[/red]")
            traceback.print_exc()
            return False

    def run(self):
        """Main execution method."""
        if not self.verify_paths():
            return

        try:
            # Step 1: List and select family
            families, grouped_configs = self.list_config_families()
            if not families:
                self.console.print("[red]No configuration families found[/red]")
                return

            self.display_families(families)
            family_num = Prompt.ask("\nSelect family number").strip()
            
            if not family_num:
                return
                
            try:
                selected_family = families[int(family_num) - 1]
            except (ValueError, IndexError):
                self.console.print("[red]Invalid family selection[/red]")
                return

            # Step 2: List and select version
            versions = sorted(grouped_configs[selected_family])
            if not versions:
                self.console.print(f"[red]No versions found for family {selected_family}[/red]")
                return

            self.display_versions(selected_family, versions)
            version_num = Prompt.ask("\nSelect version number").strip()
            
            if not version_num:
                return
                
            try:
                selected_version = versions[int(version_num) - 1]
            except (ValueError, IndexError):
                self.console.print("[red]Invalid version selection[/red]")
                return

            # Step 3: Run all processes
            if not self.process_all(selected_family, selected_version):
                self.console.print("[red]Some processes failed. Check the logs above for details.[/red]")
            else:
                self.console.print("[green]All processes completed successfully![/green]")

        except Exception as e:
            self.console.print(f"[red]An error occurred: {str(e)}[/red]")
            traceback.print_exc()

class Tool:
    def __init__(self):
        self.tool = ProcessOrchestrator()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()