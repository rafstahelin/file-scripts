import os
import shutil
import time
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt

class LoRaMover:
    def __init__(self):
        self.console = Console()
        # Use current working directory
        self.base_path = Path.cwd()
        self.destination_base = Path('/workspace/StableSwarmUI/Models/Lora')

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def show_progress(self, description: str, file_count: int) -> None:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=file_count)
            while not progress.finished:
                progress.update(task, advance=1)
                time.sleep(0.02)

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Directory {self.base_path} does not exist[/red]")
            return False
        
        # Create destination base if it doesn't exist
        self.destination_base.mkdir(parents=True, exist_ok=True)
        return True

    def list_model_paths(self) -> List[str]:
        """Scan current directory for model paths and display them in a formatted table."""
        try:
            model_paths = [f.name for f in self.base_path.iterdir() 
                         if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not model_paths:
                rprint("[yellow]No model paths found in current directory[/yellow]")
                return []
                
            rprint("[cyan]Available Models:[/cyan]")
            return self._display_items_in_panels(model_paths, "Available Models")
        except Exception as e:
            rprint(f"[red]Error scanning directory: {str(e)}[/red]")
            return []

    def list_model_versions(self, model_path: str) -> List[str]:
        """Scan selected model path for versions and display them in a formatted table."""
        try:
            version_path = self.base_path / model_path
            versions = [f.name for f in version_path.iterdir() 
                      if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not versions:
                rprint(f"[yellow]No versions found for model {model_path}[/yellow]")
                return []
                
            rprint(f"\n[cyan]Available Versions for {model_path}:[/cyan]")
            return self._display_items_in_panels(versions, f"Available Versions for {model_path}")
        except Exception as e:
            rprint(f"[red]Error scanning versions: {str(e)}[/red]")
            return []

    def _display_items_in_panels(self, items: List[str], title: str) -> List[str]:
        """Display items in a three-column panel layout."""
        # Group items by base name
        grouped = {}
        for item in sorted(items):
            base_name = item.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(item)

        # Create panels for each group
        panels = []
        ordered_items = []
        index = 1

        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            for item in sorted(grouped[base_name], key=str.lower, reverse=True):
                table.add_row(f"[yellow]{index}. {item}[/yellow]")
                ordered_items.append(item)
                index += 1

            panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                              border_style="blue", width=36))

        # Arrange panels in rows of three
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))

        return ordered_items

    def process_safetensors(self, source_path: Path, dest_path: Path, 
                          model_name: str, version: str) -> int:
        """Process and copy safetensors files with proper naming."""
        try:
            processed_count = 0
            checkpoints = [d for d in source_path.iterdir() if d.is_dir() 
                          and d.name.startswith('checkpoint-')]
            
            for checkpoint_dir in checkpoints:
                # Extract step count from checkpoint directory name
                step_count = checkpoint_dir.name.split('-')[1]
                step_count = str(int(step_count)).zfill(4)
                
                # Source and destination files
                source_file = checkpoint_dir / "pytorch_lora_weights.safetensors"
                if source_file.exists():
                    new_filename = f"{model_name}-{version}-{step_count}.safetensors"
                    dest_file = dest_path / new_filename
                    
                    # Create destination directory if it doesn't exist
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy the file
                    shutil.copy2(source_file, dest_file)
                    processed_count += 1
                    rprint(f"[green]Copied: {new_filename}[/green]")
                    
            return processed_count
        except Exception as e:
            rprint(f"[red]Error processing safetensors: {str(e)}[/red]")
            return 0

    def process_single_version(self):
        """Handle processing of a single model version."""
        model_paths = self.list_model_paths()
        if not model_paths:
            return

        model_num = Prompt.ask("\nEnter number to select model path").strip()
        if not model_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_model = model_paths[int(model_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        versions = self.list_model_versions(selected_model)
        if not versions:
            return

        version_num = Prompt.ask("\nEnter number to select version").strip()
        if not version_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_version = versions[int(version_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        # Process the selected version
        source_path = self.base_path / selected_model / selected_version
        dest_path = self.destination_base / selected_model / selected_version
        
        rprint(f"\n[cyan]Processing version {selected_version} of {selected_model}...[/cyan]")
        files_processed = self.process_safetensors(source_path, dest_path, 
                                                 selected_model, selected_version)
        if files_processed > 0:
            self.show_progress("Processing complete", 100)
            rprint(f"[green]Successfully processed {files_processed} files![/green]")
        else:
            rprint("[yellow]No files were processed[/yellow]")

    def process_all_versions(self):
        """Handle processing of all versions for a selected model."""
        model_paths = self.list_model_paths()
        if not model_paths:
            return

        model_num = Prompt.ask("\nEnter number to select model path").strip()
        if not model_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_model = model_paths[int(model_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        model_path = self.base_path / selected_model
        versions = [d.name for d in model_path.iterdir() 
                   if d.is_dir() and d.name != '.ipynb_checkpoints']
        
        if not versions:
            rprint(f"[yellow]No versions found for model {selected_model}[/yellow]")
            return

        total_processed = 0
        rprint(f"\n[cyan]Processing all versions of {selected_model}...[/cyan]")
        for version in versions:
            source_path = model_path / version
            dest_path = self.destination_base / selected_model / version
            rprint(f"[yellow]Processing version {version}...[/yellow]")
            files_processed = self.process_safetensors(source_path, dest_path, 
                                                     selected_model, version)
            total_processed += files_processed
        
        if total_processed > 0:
            self.show_progress("Processing complete", 100)
            rprint(f"[green]Successfully processed {total_processed} files across all versions![/green]")
        else:
            rprint("[yellow]No files were processed[/yellow]")

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        # Verify paths before proceeding
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== LoRA Model Management Tool ===[/magenta]")
        
        rprint("\n[cyan]Select processing mode:[/cyan]")
        rprint("[yellow]1. Process single version[/yellow]")
        rprint("[yellow]2. Process all versions of a model[/yellow]")
        
        choice = Prompt.ask("\nEnter choice").strip()
        if not choice:
            rprint("[red]Exited--no input given[/red]")
            return
        
        if choice == "1":
            self.process_single_version()
        elif choice == "2":
            self.process_all_versions()
        else:
            rprint("[red]Invalid choice[/red]")
            return

if __name__ == "__main__":
    mover = LoRaMover()
    mover.run()