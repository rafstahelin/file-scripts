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
        self.tool_name = "Clear Dataset JSON"
        self.base_path = self.workspace_path / 'SimpleTuner'

    def list_model_dirs(self) -> Tuple[List[str], Dict[str, List[str]]]:
        """List all model directories containing JSON files."""
        try:
            # Find all directories that contain JSON files
            model_dirs = set()
            all_jsons = list(self.base_path.glob("*/*.json"))  # Get all JSON files
            
            for json_file in all_jsons:
                model_dirs.add(json_file.parent.name)
            
            if not model_dirs:
                rprint("[yellow]No model directories with JSON files found[/yellow]")
                return [], {}
            
            # Group models by base name
            grouped = {}
            ordered_dirs = []
            token_groups = {}  # For group removal feature
            index = 1
            
            for model_dir in sorted(model_dirs):
                base_name = model_dir.split('-')[0]
                if base_name not in grouped:
                    grouped[base_name] = []
                    token_groups[base_name] = []
                grouped[base_name].append(model_dir)
                token_groups[base_name].append(model_dir)
                ordered_dirs.append(model_dir)
            
            # Create display panels
            panels = []
            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                for model_dir in sorted(grouped[base_name], key=str.lower, reverse=True):
                    json_count = len(list(self.base_path.glob(f"{model_dir}/*.json")))
                    table.add_row(f"[yellow]{index}. {model_dir}[/yellow]")
                    table.add_row(f"   [blue]{json_count} JSON files[/blue]")
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
                
            return ordered_dirs, token_groups
            
        except Exception as e:
            rprint(f"[red]Error scanning directories: {str(e)}[/red]")
            return [], {}

    def remove_json_files(self, model_dir: str, skip_confirm: bool = False) -> bool:
        """Remove all JSON files from the specified model directory."""
        try:
            dir_path = self.base_path / model_dir
            json_files = list(dir_path.glob("*.json"))  # Get all JSON files
            
            if not json_files:
                if not skip_confirm:
                    rprint(f"[yellow]No JSON files found in {model_dir}[/yellow]")
                return False
            
            # Display files to be removed
            if not skip_confirm:
                rprint(f"\n[cyan]Found the following JSON files to remove from {model_dir}:[/cyan]")
                for json_file in json_files:
                    rprint(f"[yellow]- {json_file.name}[/yellow]")
            
                # Confirm deletion
                confirm = Prompt.ask(
                    "\nAre you sure you want to delete these files? This cannot be undone",
                    choices=["y", "n"],
                    default="n"
                )
                
                if confirm.lower() != 'y':
                    rprint("[yellow]Operation cancelled[/yellow]")
                    return False
            
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
                        self.safe_remove(json_file)
                        deleted_count += 1
                    progress.advance(task)
            
            if deleted_count > 0:
                if not skip_confirm:  # Only show individual success if not batch operation
                    rprint(f"[green]Successfully removed {deleted_count} JSON files![/green]")
                return True
            else:
                if not skip_confirm:
                    rprint("[yellow]No JSON files were removed[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error removing JSON files: {str(e)}[/red]")
            return False

    def remove_group(self, token: str, model_dirs: List[str]) -> bool:
        """Remove all JSON files for a specific token group."""
        try:
            # Display all directories to be processed
            rprint(f"\n[cyan]Will remove ALL JSON files for token '{token}' from:[/cyan]")
            for model_dir in model_dirs:
                json_count = len(list(self.base_path.glob(f"{model_dir}/*.json")))
                rprint(f"[yellow]- {model_dir} ({json_count} JSON files)[/yellow]")
            
            # Confirm group deletion
            confirm = Prompt.ask(
                f"\nAre you sure you want to delete ALL JSON files for '{token}'? This cannot be undone",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() != 'y':
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
            
            # Process all directories in group
            success_count = 0
            total = len(model_dirs)
            
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Removing all JSON files for {token}...", total=total)
                
                for model_dir in model_dirs:
                    if self.remove_json_files(model_dir, skip_confirm=True):
                        success_count += 1
                    progress.advance(task)
            
            rprint(f"[green]Successfully processed {success_count}/{total} directories for '{token}'![/green]")
            return success_count > 0
                
        except Exception as e:
            rprint(f"[red]Error removing JSON files for group: {str(e)}[/red]")
            return False

    def process(self):
        """Main process implementation."""
        self.clear_screen()
        
        if not self.verify_paths():
            self.exit_tool()
            return
            
        rprint("[magenta]=== Clear Dataset JSON ===[/magenta]")
        rprint("[cyan]Press Enter to return to main menu[/cyan]")
        rprint("[cyan]Use group name + all to delete whole group (e.g. 'lulu15 all')[/cyan]")
        
        # List and select model directory
        rprint("\n[cyan]Model Directories with JSON Files:[/cyan]")
        model_dirs, token_groups = self.list_model_dirs()
        if not model_dirs:
            self.exit_tool()
            return
            
        dir_input = Prompt.ask("\nEnter number or group command").strip()
        if not dir_input:
            self.exit_tool()
            return
        
        # Check for group removal command
        if dir_input.lower().endswith(" all"):
            token_name = dir_input[:-4].strip()
            if token_name in token_groups:
                self.remove_group(token_name, token_groups[token_name])
            else:
                rprint(f"[red]Invalid token name: {token_name}[/red]")
            return
        
        # Handle single directory removal
        try:
            selected_dir = model_dirs[int(dir_input) - 1]
            self.remove_json_files(selected_dir)
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()