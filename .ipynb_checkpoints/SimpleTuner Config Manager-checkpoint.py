import os
import shutil
import json
import time
from pathlib import Path
from typing import Optional, Tuple
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import print as rprint
from rich.panel import Panel
from rich.table import Table
from rich.style import Style

class ConfigManager:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')
        self.source_dir: Optional[str] = None
        self.token_name: Optional[str] = None
        self.new_version: Optional[str] = None
        self.dataset_dir: Optional[str] = None
        self.token_name_version: Optional[str] = None

    def print_header(self):
        header = Panel(
            "[bold magenta]SimpleTuner Configuration Manager[/]",
            style="bold blue",
            width=80
        )
        self.console.print(header)

    def list_folders(self) -> list:
        """List existing folders excluding lora and lokr."""
        folders = [
            d for d in self.base_path.iterdir()
            if d.is_dir() and d.name not in ['lora', 'lokr', '.ipynb_checkpoints']
        ]
        if not folders:
            return []
        
        table = Table(title="Existing Folders", show_header=False)
        table.add_column("Index", style="cyan")
        table.add_column("Folder", style="yellow")
        
        for idx, folder in enumerate(folders, 1):
            table.add_row(str(idx), folder.name)
        
        self.console.print(table)
        return folders

    def list_datasets(self) -> list:
        """List available datasets."""
        datasets = [
            d for d in self.datasets_path.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ]
        if not datasets:
            return []
        
        table = Table(title="Available Datasets", show_header=False)
        table.add_column("Index", style="cyan")
        table.add_column("Dataset", style="yellow")
        
        for idx, dataset in enumerate(datasets, 1):
            table.add_row(str(idx), dataset.name)
        
        self.console.print(table)
        return datasets

    def parse_folder_name(self, folder: str) -> Tuple[str, str]:
        """Parse folder name into token name and version."""
        parts = folder.split('-', 1)
        return parts[0], parts[1] if len(parts) > 1 else ''

    def show_rainbow_progress(self, description: str, duration: float = 1.0):
        """Show a colorful progress bar with spinner."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(style="rainbow"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        ) as progress:
            task = progress.add_task(description, total=100)
            while not progress.finished:
                progress.update(task, advance=1)
                time.sleep(duration/100)

    def update_config_files(self, new_folder: Path):
        """Update configuration files with new values."""
        files_to_update = {
            'config.json': self._update_config_json,
            'multidatabackend.json': self._update_multidatabackend_json,
            'user_prompt_library.json': self._update_prompt_library
        }

        for filename, update_func in files_to_update.items():
            file_path = new_folder / filename
            if file_path.exists():
                update_func(file_path)
                self.console.print(f"✓ Updated {filename}", style="green")
            else:
                self.console.print(f"⚠ Warning: {filename} not found", style="yellow")

    def _update_config_json(self, file_path: Path):
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        # Update paths
        config_pattern = f'config/{self.token_name_version}/'
        output_pattern = f'output/{self.token_name}/{self.new_version}'
        
        def update_paths(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        if 'config/' in v:
                            obj[k] = v.replace('config/[^/"]*/", config_pattern)
                        elif 'output/' in v:
                            obj[k] = v.replace('output/[^/"]*/[^"]*', output_pattern)
                    elif isinstance(v, (dict, list)):
                        update_paths(v)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        update_paths(item)
        
        update_paths(config)
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _update_multidatabackend_json(self, file_path: Path):
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        config['instance_data_dir'] = f'datasets/{self.dataset_dir}'
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _update_prompt_library(self, file_path: Path):
        with open(file_path, 'r') as f:
            config = json.load(f)
        
        def replace_tokens(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        obj[k] = v.replace('__TOKEN_NAME__', self.token_name)
                    elif isinstance(v, (dict, list)):
                        replace_tokens(v)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        replace_tokens(item)
        
        replace_tokens(config)
        
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)

    def copy_directory(self, source: Path, dest: Path):
        """Copy directory using rsync-like behavior."""
        if not source.exists():
            raise FileNotFoundError(f"Source directory '{source}' does not exist.")
        
        shutil.copytree(source, dest, dirs_exist_ok=True, ignore=shutil.ignore_patterns('.ipynb_checkpoints'))

    def run(self):
        """Main execution flow."""
        try:
            os.chdir(self.base_path)
            self.print_header()

            # Source folder selection
            choices = {
                "1": "Use existing folder",
                "2": "Use 'lora' template",
                "3": "Use 'lokr' template"
            }
            choice = Prompt.ask(
                "\nSelect source folder type",
                choices=choices,
                default="1"
            )

            if choice == "1":
                folders = self.list_folders()
                if not folders:
                    self.console.print("No existing folders found!", style="bold red")
                    return
                
                folder_num = int(Prompt.ask("Enter number to select source folder", default="1"))
                if not 1 <= folder_num <= len(folders):
                    self.console.print("Invalid selection!", style="bold red")
                    return
                
                self.source_dir = folders[folder_num - 1].name
                self.token_name, _ = self.parse_folder_name(self.source_dir)
                self.new_version = Prompt.ask("Enter new version number")
                
                # Dataset selection
                if Confirm.ask("Use same dataset?", default=True):
                    config_file = Path(self.source_dir) / "multidatabackend.json"
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    self.dataset_dir = config['instance_data_dir'].replace('datasets/', '')
                else:
                    datasets = self.list_datasets()
                    dataset_num = int(Prompt.ask("Enter dataset number", default="1"))
                    self.dataset_dir = datasets[dataset_num - 1].name
            else:
                self.source_dir = "lora" if choice == "2" else "lokr"
                self.token_name = Prompt.ask("Enter new token name")
                self.new_version = Prompt.ask("Enter version number")
                
                datasets = self.list_datasets()
                dataset_num = int(Prompt.ask("Enter dataset number", default="1"))
                self.dataset_dir = datasets[dataset_num - 1].name

            self.token_name_version = f"{self.token_name}-{self.new_version}"

            # Show configuration summary
            summary = Table(title="Configuration Summary", show_header=False)
            summary.add_column("Parameter", style="cyan")
            summary.add_column("Value", style="yellow")
            
            summary.add_row("Source Directory", self.source_dir)
            summary.add_row("Token Name", self.token_name)
            summary.add_row("New Version", self.new_version)
            summary.add_row("New Folder Name", self.token_name_version)
            summary.add_row("Dataset", self.dataset_dir)
            
            self.console.print(summary)

            if not Confirm.ask("\nProceed with these settings?", default=True):
                self.console.print("Operation cancelled.", style="yellow")
                return

            # Execute operations
            self.show_rainbow_progress("Copying files...")
            self.copy_directory(
                self.base_path / self.source_dir,
                self.base_path / self.token_name_version
            )

            self.show_rainbow_progress("Updating configuration files...")
            self.update_config_files(self.base_path / self.token_name_version)

            self.console.print("\n✨ Operation completed successfully! ✨", style="bold green")
            self.console.print(
                f"Created new configuration in: [cyan]{self.token_name_version}[/]"
            )

        except Exception as e:
            self.console.print(f"\n❌ Error: {str(e)}", style="bold red")
            raise

def main():
    manager = ConfigManager()
    manager.run()

if __name__ == "__main__":
    main()