import os
import shutil
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
        self.base_path = Path('/workspace/SimpleTuner/config')
        self._should_exit = False
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Config directory {self.base_path} does not exist[/red]")
            return False
        return True

    def list_token_paths(self) -> tuple[List[str], Dict[str, List[str]]]:
        """List all token directories in the config path."""
        try:
            token_paths = []
            # First check if direct paths exist, excluding specific directories
            excluded_dirs = ['.ipynb_checkpoints', 'templates']
            direct_tokens = [f.name for f in self.base_path.iterdir() 
                           if f.is_dir() and f.name not in excluded_dirs]
            
            # Then check inside 'lora' directory if it exists
            lora_path = self.base_path / 'lora'
            if lora_path.exists():
                token_paths.extend([f.name for f in lora_path.iterdir() 
                                  if f.is_dir() and f.name not in excluded_dirs])
            
            token_paths.extend(direct_tokens)
            
            if not token_paths:
                rprint("[yellow]No token paths found in config directory[/yellow]")
                return [], {}
            
            # Group tokens by base name
            grouped = {}
            for token in sorted(token_paths):
                base_name = token.split('-')[0]
                if base_name != 'templates':  # Extra check to ensure templates don't get included
                    grouped.setdefault(base_name, []).append(token)
            
            # Prepare indices and token list
            token_indices = {}
            index = 1
            ordered_tokens = []
            
            for base_name in sorted(grouped.keys()):
                token_indices[base_name] = {}
                for name in sorted(grouped[base_name], key=str.lower, reverse=True):
                    token_indices[base_name][name] = index
                    ordered_tokens.append(name)
                    index += 1
            
            # Create panels for each group
            panels = []
            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
                for name in names_in_group:
                    idx = token_indices[base_name][name]
                    table.add_row(f"[yellow]{idx}. {name}[/yellow]")
                
                panel = Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                            border_style="blue", width=36)
                panels.append(panel)
            
            # Arrange panels into rows with three panels each
            rprint("\n[cyan]Available Configs:[/cyan]")
            panels_per_row = 3
            panel_rows = [panels[i:i + panels_per_row] for i in range(0, len(panels), panels_per_row)]
            
            # Add placeholder panels to the last row if necessary
            if panels and len(panel_rows[-1]) < panels_per_row:
                for _ in range(panels_per_row - len(panel_rows[-1])):
                    panel_rows[-1].append(Panel("", border_style="blue", width=36))
            
            # Display panels
            for row in panel_rows:
                self.console.print(Columns(row, equal=True, expand=True))
            
            return ordered_tokens, grouped
            
        except Exception as e:
            rprint(f"[red]Error scanning config directory: {str(e)}[/red]")
            return [], {}

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
                shutil.rmtree(target_path)
                rprint(f"[green]Successfully removed configuration: {token}[/green]")
                return True
            else:
                rprint(f"[red]Configuration path does not exist for token: {token}[/red]")
            
            return False
            
        except Exception as e:
            rprint(f"[red]Error removing configuration: {str(e)}[/red]")
            return False

    def remove_all_configs_for_token(self, base_token: str, grouped_tokens: Dict[str, List[str]]) -> bool:
        """Remove all configurations for a specific token base name."""
        if base_token not in grouped_tokens:
            rprint(f"[red]No configurations found for token: {base_token}[/red]")
            return False
            
        success = True
        for config in grouped_tokens[base_token]:
            if not self.remove_config(config):
                success = False
                
        return success

    def process_removal(self) -> bool:
        """Process config removal with continuous iteration."""
        while not self._should_exit:
            self.clear_screen()
            rprint("[magenta]=== Configuration Removal Tool ===[/magenta]\n")
            
            tokens, grouped_tokens = self.list_token_paths()
            if not tokens:
                return True
                
            choice = Prompt.ask("\nEnter config number to remove")
            if not choice:
                return True  # Clean exit
                
            # Check for bulk removal command
            if choice.lower().endswith(' all'):
                base_token = choice[:-4].strip()
                self.remove_all_configs_for_token(base_token, grouped_tokens)
                continue
                
            try:
                selected_token = tokens[int(choice) - 1]
                self.remove_config(selected_token)
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
        
        return True

    def run(self) -> int:
        """Main execution method."""
        if not self.verify_paths():
            return 1
            
        success = self.process_removal()
        return 0 if success else 1

if __name__ == "__main__":
    tool = Tool()
    exit_code = tool.run()
    # No sys.exit() here - let the launcher handle the return gracefully