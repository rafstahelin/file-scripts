from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt
from .base_tool import BaseTool

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Dataset Cache Removal Tool"
        self.cache_paths = {
            'vae': self.workspace_path / 'SimpleTuner/cache/vae',
            'text': self.workspace_path / 'SimpleTuner/cache/text'
        }

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

    def list_cache_directories(self) -> Tuple[List[Tuple[str, str, Dict[str, Path]]], Dict[str, List[Tuple[str, str, Dict[str, Path]]]]]:
        """List all cache directories grouped by token-dataset pairs."""
        try:
            # Get all cache directories
            all_caches = []
            for cache_type, path in self.cache_paths.items():
                for token, dataset, cache_path in self.get_cache_info(path):
                    all_caches.append((token, dataset, cache_type, cache_path))
            
            if not all_caches:
                rprint("[yellow]No cache directories found[/yellow]")
                return [], {}
            
            # Group by token name
            grouped = {}
            token_groups = {}  # Store items by token for group removal
            display_items = []
            index = 1
            
            # First pass - organize items
            for token, dataset, cache_type, path in all_caches:
                key = (token, dataset)
                if key not in grouped:
                    grouped[key] = {}
                grouped[key][cache_type] = path
            
            # Second pass - create display items and group mapping
            for (token, dataset), cache_paths in sorted(grouped.items()):
                display_item = (token, dataset, cache_paths)
                display_items.append(display_item)
                if token not in token_groups:
                    token_groups[token] = []
                token_groups[token].append(display_item)
            
            # Create display panels
            panels = []
            current_token = None
            table = None
            
            # Display organization
            for (token, dataset, cache_paths) in display_items:
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
                
            return display_items, token_groups
            
        except Exception as e:
            rprint(f"[red]Error scanning cache directories: {str(e)}[/red]")
            return [], {}

    def remove_cache(self, token: str, dataset: str, cache_paths: Dict[str, Path], 
                    skip_confirm: bool = False) -> bool:
        """Remove cache directories for a specific token-dataset pair."""
        try:
            # Display what will be removed
            rprint(f"\n[cyan]Removing cache directories for {token}-{dataset}:[/cyan]")
            for cache_type, path in cache_paths.items():
                rprint(f"[yellow]- {cache_type}: {path}[/yellow]")
                
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
                        self.safe_remove(path, recursive=True)
                        removed_count += 1
                    progress.advance(task)
            
            if removed_count > 0:
                if not skip_confirm:  # Only show individual success if not batch operation
                    rprint(f"[green]Successfully removed {removed_count} cache directories![/green]")
                return True
            else:
                if not skip_confirm:
                    rprint("[yellow]No cache directories were removed[/yellow]")
                return False
                    
        except Exception as e:
            rprint(f"[red]Error removing cache directories: {str(e)}[/red]")
            return False

    def remove_group(self, token: str, items: List[Tuple[str, str, Dict[str, Path]]]) -> bool:
        """Remove all cache directories for a specific token group."""
        try:
            # Display all items to be removed
            rprint(f"\n[cyan]Will remove ALL cache directories for token '{token}':[/cyan]")
            for _, dataset, cache_paths in items:
                rprint(f"\n[yellow]{token}-{dataset}:[/yellow]")
                for cache_type, path in cache_paths.items():
                    rprint(f"[yellow]- {cache_type}: {path}[/yellow]")
            
            # Confirm group deletion
            confirm = Prompt.ask(
                f"\nAre you sure you want to delete ALL cache directories for '{token}'? This cannot be undone",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() != 'y':
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
            
            # Process all items in group
            success_count = 0
            total = len(items)
            
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Removing all {token} cache directories...", total=total)
                
                for item_token, dataset, cache_paths in items:
                    if self.remove_cache(item_token, dataset, cache_paths, skip_confirm=True):
                        success_count += 1
                    progress.advance(task)
            
            rprint(f"[green]Successfully removed {success_count}/{total} cache groups for '{token}'![/green]")
            return success_count > 0
                
        except Exception as e:
            rprint(f"[red]Error removing cache group: {str(e)}[/red]")
            return False

    def process(self):
        """Main process implementation."""
        self.clear_screen()
        
        if not self.verify_paths():
            self.exit_tool()
            return
            
        rprint("[magenta]=== Dataset Cache Removal Tool ===[/magenta]")
        rprint("[cyan]Press Enter to return to main menu[/cyan]")
        rprint("[cyan]Use group name + all to delete whole group (e.g. 'lulu15 all')[/cyan]")
        
        # List and select cache directories
        rprint("\n[cyan]Available Cache Directories:[/cyan]")
        cache_items, token_groups = self.list_cache_directories()
        if not cache_items:
            self.exit_tool()
            return
            
        cache_input = Prompt.ask("\nEnter number or group command").strip()
        if not cache_input:
            self.exit_tool()
            return
            
        # Check for group removal command
        if cache_input.lower().endswith(" all"):
            token_name = cache_input[:-4].strip()
            if token_name in token_groups:
                self.remove_group(token_name, token_groups[token_name])
            else:
                rprint(f"[red]Invalid token name: {token_name}[/red]")
            return
            
        # Handle single item removal
        try:
            selected_token, selected_dataset, selected_caches = cache_items[int(cache_input) - 1]
            self.remove_cache(selected_token, selected_dataset, selected_caches)
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()