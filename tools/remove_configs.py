import os
import shutil
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
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Config directory {self.base_path} does not exist[/red]")
            return False
        return True
        
    def show_progress(self, description: str) -> None:
        """Show a progress bar with the given description."""
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

    def remove_config(self, token_path: str, version: str) -> bool:
        """Remove a specific configuration version."""
        try:
            config_path = self.base_path / token_path / version
            if config_path.exists():
                # Confirm deletion
                rprint(f"\n[yellow]About to remove configuration:[/yellow]")
                rprint(f"[cyan]Path: {config_path}[/cyan]")
                
                confirm = Prompt.ask(
                    "\nAre you sure? This cannot be undone",
                    choices=["y", "n"],
                    default="n"
                )
                
                if confirm.lower() == 'y':
                    shutil.rmtree(config_path)
                    self.show_progress("Removing configuration")
                    rprint(f"[green]Successfully removed configuration: {version}[/green]")
                    return True
                else:
                    rprint("[yellow]Operation cancelled[/yellow]")
            else:
                rprint(f"[red]Configuration path does not exist: {config_path}[/red]")
            
            return False
            
        except Exception as e:
            rprint(f"[red]Error removing configuration: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Configuration Removal Tool ===[/magenta]\n")
        
        # List and select token
        rprint("[cyan]Available Tokens:[/cyan]")
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
            
        # List and select version
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
            
        # Remove selected configuration
        self.remove_config(selected_token, selected_version)