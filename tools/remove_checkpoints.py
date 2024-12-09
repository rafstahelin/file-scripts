from pathlib import Path
from typing import List
from .base_tool import BaseTool
from rich import print as rprint
import time

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Remove Dataset .ipynb_checkpoints"
        self.datasets_path = self.workspace_path / 'SimpleTuner/datasets'

    def find_checkpoint_dirs(self) -> List[Path]:
        """Find .ipynb_checkpoints directories in SimpleTuner datasets."""
        checkpoints = []
        
        if not self.datasets_path.exists():
            return checkpoints

        try:
            # Check immediate dataset folders
            for dataset_dir in self.datasets_path.iterdir():
                if dataset_dir.is_dir():
                    # Check for checkpoints in dataset root
                    checkpoint_dir = dataset_dir / '.ipynb_checkpoints'
                    if checkpoint_dir.is_dir():
                        checkpoints.append(checkpoint_dir)

                    # Check one level deeper for model subdirectories
                    for subfolder in dataset_dir.iterdir():
                        if subfolder.is_dir():
                            sub_checkpoint = subfolder / '.ipynb_checkpoints'
                            if sub_checkpoint.is_dir():
                                checkpoints.append(sub_checkpoint)
        except Exception as e:
            rprint(f"[red]Error scanning directories: {str(e)}[/red]")

        return sorted(checkpoints)

    def display_checkpoints(self, checkpoint_dirs: List[Path]):
        """Display found checkpoint directories in a simple numbered list."""
        rprint("\n[cyan]Found checkpoint directories:[/cyan]")
        for idx, path in enumerate(checkpoint_dirs, 1):
            relative_path = path.relative_to(self.datasets_path)
            rprint(f"[yellow]{idx}.[/yellow] {relative_path}")

    def wait_for_input(self) -> bool:
        """Wait for Enter or 'q'. Returns True if Enter was pressed."""
        response = input("\n[Press Enter to remove, 'q' to cancel] ")
        return response.lower() != 'q'

    def run(self):
        """Main execution method."""
        self.clear_screen()
        rprint("[magenta]=== Remove Dataset .ipynb_checkpoints ===[/magenta]\n")
        
        if not self.verify_paths():
            return

        # Find checkpoint directories
        checkpoint_dirs = self.find_checkpoint_dirs()
        
        if not checkpoint_dirs:
            rprint("[green]No .ipynb_checkpoints found.[/green]")
            return

        self.display_checkpoints(checkpoint_dirs)

        # Simple prompt
        if not self.wait_for_input():
            rprint("[yellow]\nOperation cancelled.[/yellow]")
            return

        # Remove directories with progress bar
        with self.show_progress("Removing checkpoints", len(checkpoint_dirs)) as progress:
            task = progress.tasks[0]
            removed_count = 0
            
            for path in checkpoint_dirs:
                if self.safe_remove(path, recursive=True):
                    removed_count += 1
                progress.update(task.id, advance=1)
                time.sleep(0.05)

        rprint(f"\n[green]Successfully removed {removed_count} checkpoint directories![/green]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()