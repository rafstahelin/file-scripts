import os
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
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.datasets_path.exists():
            rprint(f"[red]Error: Datasets directory {self.datasets_path} does not exist[/red]")
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

    def has_checkpoints(self, path: Path) -> bool:
        """Check if directory contains .ipynb_checkpoints."""
        return (path / '.ipynb_checkpoints').exists()

    def list_datasets(self) -> List[str]:
        """List all dataset directories that contain .ipynb_checkpoints."""
        try:
            datasets = [
                f.name for f in self.datasets_path.iterdir() 
                if f.is_dir() and self.has_checkpoints(f)
            ]
            
            if not datasets:
                rprint("[yellow]No datasets with .ipynb_checkpoints found[/yellow]")
                return []
            
            # Group datasets by base name
            grouped = {}
            for dataset in sorted(datasets):
                base_name = dataset.split('-', 1)[0]
                grouped.setdefault(base_name, []).append(dataset)
            
            panels = []
            ordered_datasets = []
            index = 1
            
            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                for dataset in sorted(grouped[base_name], key=str.lower, reverse=True):
                    table.add_row(f"[yellow]{index}. {dataset}[/yellow]")
                    ordered_datasets.append(dataset)
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
                
            return ordered_datasets
            
        except Exception as e:
            rprint(f"[red]Error scanning datasets: {str(e)}[/red]")
            return []

    def remove_checkpoints(self, dataset: str) -> bool:
        """Remove .ipynb_checkpoints from dataset directory using bash command."""
        try:
            dataset_path = self.datasets_path / dataset
            checkpoints_path = dataset_path / '.ipynb_checkpoints'
            
            if not checkpoints_path.exists():
                rprint(f"[yellow]No .ipynb_checkpoints found in {dataset}[/yellow]")
                return False
            
            # Display what will be removed
            rprint(f"\n[cyan]Will remove:[/cyan]")
            rprint(f"[yellow]- {checkpoints_path}[/yellow]")
            
            # Confirm deletion
            confirm = Prompt.ask(
                "\nAre you sure you want to remove .ipynb_checkpoints? This cannot be undone",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() == 'y':
                # Use bash command for removal
                command = f"rm -rf {checkpoints_path}"
                
                # Show progress while executing command
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(complete_style="green"),
                    TaskProgressColumn(),
                    console=self.console,
                    transient=True
                ) as progress:
                    task = progress.add_task("Removing checkpoints...", total=100)
                    
                    # Execute command
                    process = subprocess.run(
                        command,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Update progress
                    progress.update(task, completed=100)
                    
                    if process.returncode == 0:
                        rprint(f"[green]Successfully removed .ipynb_checkpoints from {dataset}![/green]")
                        return True
                    else:
                        rprint(f"[red]Error removing checkpoints: {process.stderr}[/red]")
                        return False
            else:
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error removing checkpoints: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Jupyter Checkpoints Removal Tool ===[/magenta]\n")
        
        # List and select dataset
        rprint("[cyan]Datasets with .ipynb_checkpoints:[/cyan]")
        datasets = self.list_datasets()
        if not datasets:
            return
            
        dataset_num = Prompt.ask("\nEnter number to select dataset").strip()
        if not dataset_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_dataset = datasets[int(dataset_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return
            
        # Remove checkpoints from selected dataset
        self.remove_checkpoints(selected_dataset)

if __name__ == "__main__":
    tool = Tool()
    tool.run()