import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt

class Tool:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.paths_config = Path('/workspace/file-scripts/paths.json')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Config directory {self.base_path} does not exist[/red]")
            return False
        if not self.paths_config.exists():
            rprint(f"[red]Error: paths.json not found at {self.paths_config}[/red]")
            return False
        return True

    def load_paths_config(self) -> Dict:
        """Load paths configuration from paths.json."""
        try:
            with open(self.paths_config) as f:
                return json.load(f)
        except Exception as e:
            rprint(f"[red]Error loading paths configuration: {str(e)}[/red]")
            return {}

    def get_dropbox_path(self, token_name: str) -> Optional[str]:
        """Get Dropbox path for a given token from paths.json."""
        paths_config = self.load_paths_config()
        token_base = token_name.split('-')[0]
        
        if token_base in paths_config:
            base_path = paths_config[token_base]['path']
            return f"{base_path}/4training/config"
        return None

    def show_progress(self, description: str, progress_task=None) -> None:
        """Show a progress bar with the given description."""
        if progress_task:
            progress_task.update(description=description)
        else:
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(description, total=100)
                while not progress.finished:
                    progress.update(task, advance=1)
                    import time
                    time.sleep(0.02)

    def list_token_paths(self) -> List[str]:
        """List all token directories in the config path."""
        try:
            token_paths = [f.name for f in self.base_path.iterdir() 
                          if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not token_paths:
                rprint("[yellow]No token paths found in config directory[/yellow]")
                return []
            
            # Group tokens by base name
            grouped = {}
            for token in sorted(token_paths):
                base_name = token.split('-', 1)[0]
                grouped.setdefault(base_name, []).append(token)
            
            panels = []
            ordered_tokens = []
            index = 1
            
            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                for token in sorted(grouped[base_name], key=str.lower, reverse=True):
                    table.add_row(f"[yellow]{index}. {token}[/yellow]")
                    ordered_tokens.append(token)
                    index += 1
                    
                panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                                  border_style="blue", width=36))
            
            # Display panels in rows of three
            panels_per_row = 3
            for i in range(0, len(panels), panels_per_row):
                row_panels = panels[i:i + panels_per_row]
                while len(row_panels) < panels_per_row:
                    row_panels.append(Panel("", border_style="blue", width=36))
                self.console.print(Columns(row_panels, equal=True, expand=True))
                
            return ordered_tokens
            
        except Exception as e:
            rprint(f"[red]Error scanning config directory: {str(e)}[/red]")
            return []

    def list_config_versions(self, token_path: str) -> List[str]:
        """List all configuration versions for a given token."""
        try:
            version_path = self.base_path / token_path
            versions = [f.name for f in version_path.iterdir() 
                       if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not versions:
                rprint(f"[yellow]No configurations found for token {token_path}[/yellow]")
                return []
            
            # Create single panel with all versions in reverse order
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            ordered_versions = sorted(versions, key=str.lower, reverse=True)
            for idx, version in enumerate(ordered_versions, 1):
                table.add_row(f"[yellow]{idx}. {version}[/yellow]")
            
            # Create panel with token name as title
            panel = Panel(table, title=f"[magenta]{token_path}[/magenta]", 
                         border_style="blue", width=36)
            
            # Display with two empty panels for consistent layout
            panels = [
                panel,
                Panel("", border_style="blue", width=36),
                Panel("", border_style="blue", width=36)
            ]
            self.console.print(Columns(panels, equal=True, expand=True))
            
            return ordered_versions
            
        except Exception as e:
            rprint(f"[red]Error scanning versions: {str(e)}[/red]")
            return []

    def download_config(self, token_path: str, version: Optional[str] = None) -> bool:
        """Download configuration(s) to Dropbox."""
        try:
            # Get Dropbox destination path
            dropbox_path = self.get_dropbox_path(token_path)
            if not dropbox_path:
                rprint(f"[red]No Dropbox path configured for token {token_path}[/red]")
                return False

            # Prepare source path
            source_base = self.base_path / token_path
            if version:
                source_path = source_base / version
                if not source_path.exists():
                    rprint(f"[red]Configuration path does not exist: {source_path}[/red]")
                    return False
            else:
                source_path = source_base

            # Confirm download
            rprint(f"\n[yellow]About to download configuration(s):[/yellow]")
            rprint(f"[cyan]From: {source_path}[/cyan]")
            rprint(f"[cyan]To: {dropbox_path}[/cyan]")
            
            confirm = Prompt.ask(
                "\nProceed with download?",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() != 'y':
                rprint("[yellow]Operation cancelled[/yellow]")
                return False

            # Prepare rclone command
            cmd = [
                "rclone",
                "copy",
                "--checksum",
                str(source_path),
                str(dropbox_path),
                "--progress"
            ]

            # Execute download with progress tracking
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task("Starting download...", total=100)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                # Update progress
                while True:
                    if process.poll() is not None:
                        break
                    progress.update(task, advance=1)
                    import time
                    time.sleep(0.1)
                
                # Check result
                if process.returncode == 0:
                    self.show_progress("Download complete", task)
                    rprint(f"[green]Successfully downloaded configuration(s)[/green]")
                    return True
                else:
                    rprint("[red]Error during download[/red]")
                    return False
                    
        except Exception as e:
            rprint(f"[red]Error downloading configuration: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Configuration Download Tool ===[/magenta]\n")
        
        # Choose download mode
        rprint("[cyan]Select download mode:[/cyan]")
        rprint("[yellow]1. Download single configuration[/yellow]")
        rprint("[yellow]2. Download all configurations for a token[/yellow]")
        
        mode = Prompt.ask("\nEnter choice", choices=["1", "2"]).strip()
        
        # List and select token
        rprint("\n[cyan]Available Tokens:[/cyan]")
        tokens = self.list_token_paths()
        if not tokens:
            return
            
        token_num = Prompt.ask("\nEnter number to select token").strip()
        if not token_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_token = tokens[int(token_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        if mode == "1":
            # Single configuration mode
            rprint("\n[cyan]Available Configurations:[/cyan]")
            versions = self.list_config_versions(selected_token)
            if not versions:
                return
                
            version_num = Prompt.ask("\nEnter number to select configuration").strip()
            if not version_num:
                rprint("[red]Exited--no input given[/red]")
                return
                
            try:
                selected_version = versions[int(version_num) - 1]
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                return
                
            # Download single configuration
            self.download_config(selected_token, selected_version)
        else:
            # Download all configurations for token
            self.download_config(selected_token)