# /workspace/file-scripts/tools/base_tool.py

from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from rich.prompt import Prompt
import shutil
import os

class BaseTool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTrainer'
        self.models_path = self.workspace_path / 'models'
        self.datasets_path = self.workspace_path / 'datasets'
        self.cache_path = self.workspace_path / 'cache'
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        required_paths = {
            'workspace': self.workspace_path,
        }
        
        missing_paths = []
        for name, path in required_paths.items():
            if not path.exists():
                missing_paths.append(name)
                
        if missing_paths:
            rprint(f"[red]Error: Missing required directories: {', '.join(missing_paths)}[/red]")
            return False
        return True

    def get_yes_no_input(self, prompt_text: str) -> bool:
        """Get yes/no confirmation from user."""
        response = Prompt.ask(
            f"{prompt_text} [y/n]",
            choices=['y', 'n'],
            default='n'
        ).lower()
        return response == 'y'

    def show_progress(self, description: str, total: int) -> Progress:
        """Create and return a progress bar."""
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        )
        progress.add_task(description, total=total)
        return progress

    def safe_remove(self, path: Path, recursive: bool = False) -> bool:
        """Safely remove file or directory with error handling."""
        try:
            if path.exists():
                if path.is_file():
                    path.unlink()
                elif recursive:
                    shutil.rmtree(path)
                else:
                    path.rmdir()
                return True
            return False
        except Exception as e:
            rprint(f"[red]Error removing {path}: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method to be implemented by child classes."""
        raise NotImplementedError("Each tool must implement its own run() method.")