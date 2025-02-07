import os
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint


class Tool:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.dropbox_base = "dbx:/studio/ai/data/1models"
        self.excluded_dirs = {'.ipynb_checkpoints', 'templates'}

    def verify_paths(self) -> bool:
        if not self.base_path.exists():
            rprint(f"[red]Error: Base config directory not found at {self.base_path}[/red]")
            return False
        try:
            result = self._run_rclone_command(["lsf", self.dropbox_base])
            if not result:
                return False
        except Exception as e:
            rprint(f"[red]Error checking Dropbox access: {str(e)}[/red]")
            return False
        return True

    def _run_rclone_command(self, args: List[str], check_output: bool = True) -> Optional[str]:
        try:
            cmd = ["rclone"] + args
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                rprint(f"[red]Rclone command failed: {result.stderr}[/red]")
                return None
            return result.stdout if check_output else ""
        except Exception as e:
            rprint(f"[red]Error running rclone command: {str(e)}[/red]")
            return None

    def find_matching_dropbox_folder(self, base_name: str) -> Optional[str]:
        """Find a matching Dropbox folder for a given base name."""
        result = self._run_rclone_command([
            "lsf", self.dropbox_base,
            "--dirs-only",
            "-R",
            "--max-depth", "1"
        ])
        
        if not result:
            return None

        matches = []
        base_name_lower = base_name.lower()

        for folder in result.splitlines():
            folder_cleaned = folder.strip('/')
            if not folder_cleaned:
                continue

            folder_lower = folder_cleaned.lower()
            
            if base_name_lower in folder_lower:  # Case-insensitive match
                score = 10 + (5 if any(c.isdigit() for c in folder_cleaned) else 0)
                matches.append((score, folder_cleaned))

        if matches:
            matches.sort(key=lambda x: (-x[0], len(x[1])))  # Sort by score and shortest length
            best_match = matches[0][1]
            rprint(f"[cyan]Found matching Dropbox folder: {best_match}[/cyan]")
            return best_match
            
        rprint(f"[yellow]No matching Dropbox folder found for {base_name}[/yellow]")
        return None

    def download_config(self, source_path: Path, base_name: str) -> bool:
        """Download a single config file to its corresponding Dropbox folder."""
        dropbox_folder = self.find_matching_dropbox_folder(base_name)
        if not dropbox_folder:
            return False

        # Construct destination path dynamically
        dest_path = f"{self.dropbox_base}/{dropbox_folder}/4training/config/{source_path.name}"
        dest_path = dest_path.replace('//', '/')  # Ensure no double slashes

        # Create the target directory in Dropbox
        mkdir_result = self._run_rclone_command([
            "mkdir",
            f"{self.dropbox_base}/{dropbox_folder}/4training/config"
        ], check_output=False)
        
        if mkdir_result is None:
            return False

        rprint(f"[cyan]Copying {source_path.name} to {dest_path}[/cyan]")
        
        # Copy the file to Dropbox
        copy_result = self._run_rclone_command([
            "copy",
            "--checksum",
            str(source_path),
            dest_path,
            "-v",
            "--progress",
            "--exclude", ".ipynb_checkpoints/**"
        ], check_output=False)
        
        if copy_result is not None:
            rprint(f"[green]Successfully downloaded {source_path.name}[/green]")
            return True
        return False

    def get_config_dirs(self) -> List[Path]:
        try:
            return [
                d for d in self.base_path.iterdir()
                if d.is_dir() and d.name not in self.excluded_dirs
            ]
        except Exception as e:
            rprint(f"[red]Error scanning config directory: {str(e)}[/red]")
            return []

    def display_families(self, configs: List[Path]) -> Tuple[List[str], Dict[str, List[Path]]]:
        """Group configurations by families and display them."""
        grouped = {}
        for config in sorted(configs, key=lambda x: x.name):
            base_name = config.name.split('_')[0].lower()  # Group by base name (case-insensitive)
            grouped.setdefault(base_name, []).append(config)

        families = sorted(grouped.keys())
        self.console.print("\n[bold yellow]Available Families[/bold yellow]")
        for idx, family in enumerate(families, start=1):
            self.console.print(f"[yellow]{idx}.[/yellow] {family}")

        return families, grouped

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        self.clear_screen()
        
        if not self.verify_paths():
            return

        configs = self.get_config_dirs()
        if not configs:
            rprint("[yellow]No config directories found to process[/yellow]")
            return

        while True:
            # Step 1: Display families
            families, grouped_configs = self.display_families(configs)
            
            # Step 2: Prompt user to select a family
            family_num = input("Select a family number (or press Enter to exit): ").strip()
            
            if not family_num:  # Exit if no input
                break
            
            if not family_num.isdigit() or int(family_num) < 1 or int(family_num) > len(families):
                rprint("[red]Invalid selection. Please try again.[/red]")
                continue
            
            selected_family = families[int(family_num) - 1]

            # Step 3: Show configurations within the selected family
            while True:
                self.console.print(f"\n[bold yellow]Configurations in {selected_family}[/bold yellow]")
                configs_in_family = grouped_configs[selected_family]
                
                for idx, config in enumerate(configs_in_family, start=1):
                    self.console.print(f"[yellow]{idx}.[/yellow] {config.name}")
                
                # Step 4: Prompt user to select a configuration or go back
                config_num = input(
                    "Enter configuration number to download (or press Enter to go back): "
                ).strip()
                
                if not config_num:  # Go back to families list
                    break
                
                if not config_num.isdigit() or int(config_num) < 1 or int(config_num) > len(configs_in_family):
                    rprint("[red]Invalid selection. Please try again.[/red]")
                    continue
                
                selected_config = configs_in_family[int(config_num) - 1]
                base_name = selected_config.name.split('_')[0].lower()
                
                # Download the selected configuration
                self.download_config(selected_config, base_name)
                
                input("\nPress Enter to continue...")
