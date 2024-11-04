import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
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
        self.cache_paths = {
            'vae': Path('/workspace/SimpleTuner/cache/vae'),
            'text': Path('/workspace/SimpleTuner/cache/text')
        }
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required cache paths exist."""
        missing = []
        for cache_type, path in self.cache_paths.items():
            if not path.exists():
                missing.append(f"{cache_type}: {path}")
        
        if missing:
            rprint("[red]Error: The following cache paths do not exist:[/red]")
            for path in missing:
                rprint(f"[red]- {path}[/red]")
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

    def get_cache_info(self, cache_dir: Path) -> List[Tuple[str, str, Path]]:
        """Get information about cache directories."""
        cache_info = []
        if cache_dir.exists():
            for path in cache_dir.iterdir():
                if path.is_dir() and path.name != '.ipynb_checkpoints':
                    # Split into token and dataset names
                    parts = path.name.split('-', 1)
                    if len(parts) == 2:
                        token_name, dataset_name = parts
                        cache_info.append((token_name, dataset_name, path))
        return sorted(cache_info, key=lambda x: (x[0].lower(), x[1].lower()))

    def list_cache_directories(self) -> List[Tuple[str, str, Dict[str, Path]]]:
        """List all cache directories grouped by token-dataset pairs."""
        try:
            # Get all cache directories
            all_caches = []
            for cache_type, path in self.cache_paths.items():
                for token, dataset, cache_path in self.get_cache_info(path):
                    all_caches.append((token, dataset, cache_type, cache_path))
            
            if not all_caches:
                rprint("[yellow]No cache directories found[/yellow]")
                return []
            
            # Group by token name
            grouped = {}
            for token, dataset, cache_type, path in all_caches:
                key = (token, dataset)
                if key not in grouped:
                    grouped[key] = {}
                grouped[key][cache_type] = path
            
            # Create display panels
            panels = []
            display_items = []
            index = 1
            
            current_token = None
            table = None
            
            for (token, dataset), cache_paths in sorted(grouped.items()):
                if current_token != token:
                    if table is not None:
                        panels.append(Panel(table, title=f"[magenta]{current_token}[/magenta]", 
                                          border_style="blue", width=36))
                    
                    table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                    table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                    current_token = token
                
                cache_types = sorted(cache_paths.keys())
                table.add_row(f"[yellow]{index}. {dataset}[/yellow]")
                table.add_row(f"   [blue]{', '.join(cache_types)} cache[/blue]")
                display_items.append((token, dataset, cache_paths))
                index += 1
            
            # Add the last table
            if table is not None:
                panels.append(Panel(table, title=f"[magenta]{current_token}[/magenta]", 
                                  border_style="blue", width=36))
            
            # Display panels in rows of three
            panels_per_row = 3
            for i in range(0, len(panels), panels_per_row):
                row_panels = panels[i:i + panels_per_row]
                while len(row_panels) < panels_per_row:
                    row_panels.append(Panel("", border_style="blue", width=36))
                self.console.print(Columns(row_panels, equal=True, expand=True))
                
            return display_items
            
        except Exception as e:
            rprint(f"[red]Error scanning cache directories: {str(e)}[/red]")
            return []

    def remove_cache(self, token: str, dataset: str, cache_paths: Dict[str, Path]) -> bool:
        """Remove cache directories for a specific token-dataset pair."""
        try:
            # Display what will be removed
            rprint(f"\n[cyan]Will remove the following cache directories for {token}-{dataset}:[/cyan]")
            for cache_type, path in cache_paths.items():
                rprint(f"[yellow]- {cache_type}: {path}[/yellow]")
            
            # Confirm deletion
            confirm = Prompt.ask(
                "\nAre you sure you want to delete these cache directories? This cannot be undone",
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
                    task = progress.add_task("Removing cache directories...", total=len(cache_paths))
                    
                    removed_count = 0
                    for cache_type, path in cache_paths.items():
                        if path.exists():
                            shutil.rmtree(path)
                            removed_count += 1
                        progress.advance(task)
                
                if removed_count > 0:
                    rprint(f"[green]Successfully removed {removed_count} cache directories![/green]")
                    return True
                else:
                    rprint("[yellow]No cache directories were removed[/yellow]")
                    return False
            else:
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error removing cache directories: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Dataset Cache Removal Tool ===[/magenta]\n")
        
        # List and select cache directories
        rprint("[cyan]Available Cache Directories:[/cyan]")
        cache_items = self.list_cache_directories()
        if not cache_items:
            return
            
        cache_num = Prompt.ask("\nEnter number to select cache").strip()
        if not cache_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_token, selected_dataset, selected_caches = cache_items[int(cache_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return
            
        # Remove selected cache directories
        self.remove_cache(selected_token, selected_dataset, selected_caches)

if __name__ == "__main__":
    tool = Tool()
    tool.run()