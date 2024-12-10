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
        result = self._run_rclone_command([
            "lsf", self.dropbox_base,
            "--dirs-only",
            "-R",
            "--max-depth", "1"
        ])
        
        if not result:
            return None

        matches = []
        for folder in result.splitlines():
            folder = folder.strip('/')
            if not folder:
                continue
                
            score = 0
            folder_lower = folder.lower()
            base_name_lower = base_name.lower()
            
            if base_name_lower in folder_lower:
                score += 10
                if any(c.isdigit() for c in folder):
                    score += 5
                matches.append((score, folder))

        if matches:
            matches.sort(key=lambda x: (-x[0], len(x[1])))
            best_match = matches[0][1]
            rprint(f"[cyan]Found matching Dropbox folder: {best_match}[/cyan]")
            return best_match
            
        rprint(f"[yellow]No matching Dropbox folder found for {base_name}[/yellow]")
        return None

    def download_config(self, source_path: Path, base_name: str) -> bool:
        dropbox_folder = self.find_matching_dropbox_folder(base_name)
        if not dropbox_folder:
            return False

        dest_path = f"{self.dropbox_base}/{dropbox_folder}/4training/config/{source_path.name}"
        dest_path = dest_path.replace('//', '/')

        mkdir_result = self._run_rclone_command([
            "mkdir",
            f"{self.dropbox_base}/{dropbox_folder}/4training/config"
        ], check_output=False)
        
        if mkdir_result is None:
            return False

        rprint(f"[cyan]Copying {source_path.name} to {dest_path}[/cyan]")
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

    def download_config_group(self, base_name: str) -> bool:
        dropbox_folder = self.find_matching_dropbox_folder(base_name)
        if not dropbox_folder:
            return False

        configs = list(self.base_path.glob(f"{base_name}-*"))
        if not configs:
            rprint(f"[yellow]No configs found matching {base_name}[/yellow]")
            return False

        success = True
        for config in configs:
            if not self.download_config(config, base_name):
                success = False
                rprint(f"[red]Failed to download {config.name}[/red]")

        return success

    def get_config_dirs(self) -> List[Path]:
        try:
            return [
                d for d in self.base_path.iterdir()
                if d.is_dir() and d.name not in self.excluded_dirs
            ]
        except Exception as e:
            rprint(f"[red]Error scanning config directory: {str(e)}[/red]")
            return []

    def display_configs(self, configs: List[Path]) -> List:
        grouped = {}
        for config in sorted(configs, key=lambda x: x.name):
            base_name = config.name.split('-')[0]
            grouped.setdefault(base_name, []).append(config)

        panels = []
        ordered_configs = []
        counter = 1
        
        for base_name, group_configs in sorted(grouped.items()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            table.add_row(f"[yellow]{counter}. {base_name} all[/yellow]")
            ordered_configs.append(("group", base_name, group_configs))
            counter += 1
            
            for config in sorted(group_configs, key=lambda x: x.name):
                table.add_row(f"[yellow]{counter}. {config.name}[/yellow]")
                ordered_configs.append(("single", config.name, config))
                counter += 1
                
            panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                              border_style="blue", width=36))

        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            self.console.print(Columns(row_panels, equal=True, expand=True))

        return ordered_configs

    def process_selection(self, selection: str, ordered_configs: List) -> tuple[Optional[str], Optional[Path]]:
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(ordered_configs):
                entry_type, name, data = ordered_configs[idx]
                return (entry_type, data if entry_type == "single" else name)
            rprint("[red]Invalid selection[/red]")
            return None, None
        except ValueError:
            rprint("[red]Invalid input[/red]")
            return None, None

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
            rprint("\n[cyan]Available configurations:[/cyan]")
            ordered_configs = self.display_configs(configs)

            try:
                selection = input("\nEnter config number to download (or press Enter to exit): ").strip()
                if not selection:
                    break

                entry_type, data = self.process_selection(selection, ordered_configs)
                if entry_type == "group":
                    self.download_config_group(data)
                elif entry_type == "single":
                    base_name = data.name.split('-')[0]
                    self.download_config(data, base_name)

                input("\nPress Enter to continue...")
                self.clear_screen()

            except KeyboardInterrupt:
                rprint("\n[yellow]Operation cancelled by user[/yellow]")
                break
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
                input("\nPress Enter to continue...")
                self.clear_screen()