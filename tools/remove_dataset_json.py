import os
import glob
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
        self.base_path = Path('/workspace/SimpleTuner')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Base directory {self.base_path} does not exist[/red]")
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

    def list_model_dirs(self) -> List[str]:
        """List all model directories containing JSON files."""
        try:
            # Find all directories that contain relevant JSON files
            model_dirs = set()
            json_patterns = [
                'aspect_ratio_bucket_indices_*.json',
                'aspect_ratio_bucket_metadata_*.json'
            ]
            
            for pattern in json_patterns:
                for json_file in self.base_path.glob(f"*/{pattern}"):
                    model_dirs.add(json_file.parent.name)
            
            if not model_dirs:
                rprint("[yellow]No model directories with JSON files found[/yellow]")
                return []
            
            # Group models by base name
            grouped = {}
            for model_dir in sorted(model_dirs):
                base_name = model_dir.split('-')[0]
                grouped.setdefault(base_name, []).append(model_dir)
            
            panels = []
            ordered_dirs = []
            index = 1
            
            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                for model_dir in sorted(grouped[base_name], key=str.lower, reverse=True):
                    table.add_row(f"[yellow]{index}. {model_dir}[/yellow]")
                    ordered_dirs.append(model_dir)
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
                
            return ordered_dirs
            
        except Exception as e:
            rprint(f"[red]Error scanning directories: {str(e)}[/red]")
            return []

    def remove_json_files(self, model_dir: str) -> bool:
        """Remove all dataset JSON files from the specified model directory."""
        try:
            dir_path = self.base_path / model_dir
            json_files = []
            
            # Find all relevant JSON files
            json_patterns = [
                'aspect_ratio_bucket_indices_*.json',
                'aspect_ratio_bucket_metadata_*.json'
            ]
            
            for pattern in json_patterns:
                json_files.extend(dir_path.glob(pattern))
            
            if not json_files:
                rprint(f"[yellow]No JSON files found in {model_dir}[/yellow]")
                return False
            
            # Display files to be removed
            rprint("\n[cyan]Found the following JSON files to remove:[/cyan]")
            for json_file in json_files:
                rprint(f"[yellow]- {json_file.name}[/yellow]")
            
            # Confirm deletion
            confirm = Prompt.ask(
                "\nAre you sure you want to delete these files? This cannot be undone",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() == 'y':
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(complete_style="green"),
                    TaskProgressColumn(),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Removing JSON files...", total=len(json_files))
                    
                    deleted_count = 0
                    for json_file in json_files:
                        if json_file.exists():
                            json_file.unlink()
                            deleted_count += 1
                        progress.advance(task)
                
                rprint(f"[green]Successfully removed {deleted_count} JSON files![/green]")
                return True
            else:
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error removing JSON files: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Dataset JSON Removal Tool ===[/magenta]\n")
        
        # List and select model directory
        rprint("[cyan]Model Directories with JSON Files:[/cyan]")
        model_dirs = self.list_model_dirs()
        if not model_dirs:
            return
            
        dir_num = Prompt.ask("\nEnter number to select directory").strip()
        if not dir_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_dir = model_dirs[int(dir_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return
            
        # Remove JSON files from selected directory
        self.remove_json_files(selected_dir)