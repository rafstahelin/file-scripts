from pathlib import Path
from typing import List, Tuple
from .base_tool import BaseTool
from rich import print as rprint
import time

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Remove Dataset .ipynb_checkpoints"
        
    def find_checkpoint_dirs(self) -> List[Path]:
        """Find .ipynb_checkpoints directories in SimpleTuner datasets."""
        checkpoints = []
        simpletuner_datasets = self.workspace_path / 'SimpleTuner/datasets'
        
        if simpletuner_datasets.exists():
            # First check immediate dataset folders
            for dataset_dir in simpletuner_datasets.iterdir():
                if dataset_dir.is_dir():
                    # Check for checkpoints in dataset root
                    checkpoint_dir = dataset_dir / '.ipynb_checkpoints'
                    if checkpoint_dir.is_dir():
                        checkpoints.append(checkpoint_dir)
                        
                    # Check one level deeper (dataset subfolders)
                    for subfolder in dataset_dir.iterdir():
                        if subfolder.is_dir():
                            sub_checkpoint = subfolder / '.ipynb_checkpoints'
                            if sub_checkpoint.is_dir():
                                checkpoints.append(sub_checkpoint)
        
        return sorted(checkpoints)

    def run(self):
        """Main execution method."""
        self.clear_screen()
        rprint("[magenta]=== Remove Dataset .ipynb_checkpoints ===[/magenta]")
        rprint("[yellow]Purpose: Remove .ipynb_checkpoints from SimpleTuner dataset directories to prevent training issues[/yellow]\n")
        
        if not self.verify_paths():
            return
            
        simpletuner_path = self.workspace_path / 'SimpleTuner'
        if not simpletuner_path.exists():
            rprint("[red]Error: SimpleTuner directory not found at /workspace/SimpleTuner[/red]")
            return
            
        # Find checkpoint directories in datasets
        rprint("[cyan]Scanning SimpleTuner dataset directories for checkpoints...[/cyan]")
        checkpoint_dirs = self.find_checkpoint_dirs()
        
        if not checkpoint_dirs:
            rprint("[green]No .ipynb_checkpoints found in SimpleTuner dataset directories.[/green]")
            return
            
        # Display found directories
        rprint("\n[cyan]Found checkpoint directories in datasets:[/cyan]")
        for idx, path in enumerate(checkpoint_dirs, 1):
            # Show path relative to SimpleTuner/datasets for clarity
            relative_path = path.relative_to(self.workspace_path / 'SimpleTuner/datasets')
            rprint(f"[yellow]{idx}.[/yellow] datasets/{relative_path}")
            
        # Confirm removal
        if not self.get_yes_no_input("\nRemove these checkpoint directories from SimpleTuner datasets?"):
            rprint("[yellow]\nOperation cancelled.[/yellow]")
            return
            
        # Remove directories with progress bar
        total = len(checkpoint_dirs)
        with self.show_progress("Removing checkpoints", total) as progress:
            task = progress.tasks[0]
            removed_count = 0
            
            for path in checkpoint_dirs:
                if self.safe_remove(path, recursive=True):
                    removed_count += 1
                progress.update(task.id, advance=1)
                time.sleep(0.05)
                
        rprint(f"\n[green]Successfully removed {removed_count} checkpoint directories from SimpleTuner datasets![/green]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()