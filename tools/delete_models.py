import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint

# Platform-specific imports
if os.name == 'nt':
    import msvcrt
else:
    import tty
    import termios

class Tool:
    """
    Delete Models Tool
    -----------------
    Manages deletion of model directories in SimpleTuner output path.
    """
    
    handles_own_exit = True
    
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/output')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def getch(self) -> str:
        """Get a single character from the user."""
        if os.name == 'nt':
            return msvcrt.getch().decode()
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            self.console.print(f"[red]Error: Output directory {self.base_path} does not exist[/red]")
            return False
        return True

    def list_model_dirs(self) -> Dict[str, List[str]]:
        """List all model families and their version directories."""
        try:
            model_families = {}
            
            if not self.base_path.exists():
                self.console.print("[red]Output directory does not exist![/red]")
                return {}
                
            for family_dir in self.base_path.iterdir():
                if family_dir.is_dir():
                    versions = []
                    for version_dir in family_dir.iterdir():
                        if version_dir.is_dir():
                            versions.append(version_dir.name)
                    if versions:
                        model_families[family_dir.name] = sorted(versions, reverse=True)
            
            return model_families
            
        except Exception as e:
            self.console.print(f"[red]Error scanning directories: {str(e)}[/red]")
            return {}

    def display_models(self, model_families: Dict[str, List[str]]) -> List[tuple]:
        """Display model families and versions in organized panels."""
        if not model_families:
            self.console.print("[yellow]No model directories found[/yellow]")
            return []
            
        panels = []
        model_map = []  # Store (family, version) tuples for selection
        index = 1
        
        for family_name, versions in sorted(model_families.items()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=40)
            
            # Add all versions option
            table.add_row(f"[yellow]{index}. {family_name} (ALL VERSIONS)[/yellow]")
            model_map.append((family_name, None))
            index += 1
            
            # Add individual versions
            for version in versions:
                table.add_row(f"[yellow]{index}. {family_name}/{version}[/yellow]")
                model_map.append((family_name, version))
                index += 1
                
            panels.append(Panel(table, title=f"[magenta]{family_name}[/magenta]", 
                              border_style="blue", width=46))
        
        # Display panels in rows of two
        panels_per_row = 2
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            self.console.print(Columns(row_panels, equal=True, expand=True))
                
        return model_map

    def delete_model(self, family: str, version: Optional[str] = None) -> bool:
        """Delete model directory or specific version."""
        try:
            target_path = self.base_path / family
            if version:
                target_path = target_path / version
            
            if not target_path.exists():
                self.console.print(f"[red]Path does not exist: {target_path}[/red]")
                return False
            
            # Count items to delete for progress bar
            total_items = sum(1 for _ in target_path.rglob('*')) + 1
            
            # Show what we're about to delete
            self.console.print(f"\n[cyan]Deleting:[/cyan] [yellow]{target_path.relative_to(self.base_path)}[/yellow]")
            
            # Delete with progress bar
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Deleting {target_path.name}...", total=total_items)
                shutil.rmtree(target_path, onerror=lambda f, p, e: progress.advance(task))
                
            self.console.print(f"[green]Successfully deleted {target_path.relative_to(self.base_path)}![/green]")
            return True
                
        except Exception as e:
            self.console.print(f"[red]Error during deletion: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        if not self.verify_paths():
            return
            
        self.console.print("[cyan]Loading tool: delete_models[/cyan]\n")
        
        while True:
            # List and display models
            model_families = self.list_model_dirs()
            model_map = self.display_models(model_families)
            
            if not model_map:
                return
                
            # Get user selection
            self.console.print("\n[yellow]Select model(s) to delete:[/yellow]")
            selection = input().strip()
            
            # Handle empty input to exit
            if not selection:
                return
                
            try:
                index = int(selection) - 1
                if 0 <= index < len(model_map):
                    family, version = model_map[index]
                    if self.delete_model(family, version):
                        # Clear screen and continue loop to show updated listing
                        self.clear_screen()
                        self.console.print("[cyan]Loading tool: delete_models[/cyan]\n")
                        continue
                else:
                    self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                if selection.lower() == 'q':
                    return
                self.console.print("[red]Please enter a valid number[/red]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()