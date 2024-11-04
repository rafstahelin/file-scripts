import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt

class Tool:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Config directory {self.base_path} does not exist[/red]")
            return False
        return True

def list_token_paths(self) -> List[str]:
        """List all token directories in the config path."""
        try:
            token_paths = []
            # First check if direct paths exist
            direct_tokens = [f.name for f in self.base_path.iterdir() 
                           if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            # Then check inside 'lora' directory if it exists
            lora_path = self.base_path / 'lora'
            if lora_path.exists():
                token_paths.extend([f.name for f in lora_path.iterdir() 
                                  if f.is_dir() and f.name not in ['.ipynb_checkpoints']])
            
            token_paths.extend(direct_tokens)
            
            if not token_paths:
                rprint("[yellow]No token paths found in config directory[/yellow]")
                return []
            
            # Group tokens by base name
            grouped = {}
            for token in sorted(token_paths):
                base_name = token.split('-')[0]
                grouped.setdefault(base_name, []).append(token)
            
            ordered_tokens = []
            index = 1
            
            # Display tokens grouped by base name
            rprint("\n[cyan]Available Tokens:[/cyan]")
            
            for base_name in sorted(grouped.keys()):
                rprint(f"\n[magenta]{base_name}[/magenta]")
                for token in sorted(grouped[base_name], key=str.lower, reverse=True):
                    rprint(f"[yellow]{index}. {token}[/yellow]")
                    ordered_tokens.append(token)
                    index += 1
                
            return ordered_tokens
            
        except Exception as e:
            rprint(f"[red]Error scanning config directory: {str(e)}[/red]")
            return []

    def remove_config(self, token: str) -> bool:
        """Remove a specific configuration."""
        try:
            # Check both direct path and lora subdirectory
            config_path = self.base_path / token
            lora_config_path = self.base_path / 'lora' / token
            
            target_path = None
            if config_path.exists():
                target_path = config_path
            elif lora_config_path.exists():
                target_path = lora_config_path
            
            if target_path:
                # Confirm deletion
                rprint(f"\n[yellow]About to remove configuration:[/yellow]")
                rprint(f"[cyan]Path: {target_path}[/cyan]")
                
                confirm = Prompt.ask(
                    "\nAre you sure? This cannot be undone",
                    choices=["y", "n"],
                    default="n"
                )
                
                if confirm.lower() == 'y':
                    shutil.rmtree(target_path)
                    rprint(f"[green]Successfully removed configuration: {token}[/green]")
                    return True
                else:
                    rprint("[yellow]Operation cancelled[/yellow]")
            else:
                rprint(f"[red]Configuration path does not exist for token: {token}[/red]")
            
            return False
            
        except Exception as e:
            rprint(f"[red]Error removing configuration: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Configuration Removal Tool ===[/magenta]\n")
        
        # List and select token
        tokens = self.list_token_paths()
        if not tokens:
            return
            
        token_num = Prompt.ask("\nEnter number to select token").strip()
        if not token_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_token = tokens[int(token_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return
            
        # Remove selected configuration
        self.remove_config(selected_token)

if __name__ == "__main__":
    tool = Tool()
    tool.run()