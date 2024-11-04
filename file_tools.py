import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from rich.prompt import Prompt

class FileTools:
    def __init__(self):
        self.console = Console()
        self.tools_dir = Path('/workspace/file-scripts/tools')
        self.tools = [
            ('remove_configs', 'Remove configuration files', 'rc'),
            ('download_configs', 'Download configurations to Dropbox', 'dc'),
            ('delete_models', 'Remove model files and associated data', 'dm'),
            ('remove_dataset_json', 'Clean up dataset JSON files', 'rj'),
            ('remove_dataset_cache', 'Clear dataset cache directories', 'rd'),
            ('remove_checkpoints', 'Delete .ipynb_checkpoints directories', 'cp'),
            ('debug_crops', 'Run image preparation debug routine', 'db')
        ]
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
        """Verify that tools directory exists."""
        if not self.tools_dir.exists():
            rprint(f"[red]Error: Tools directory {self.tools_dir} does not exist[/red]")
            return False
        return True

    def display_menu(self) -> None:
        """Display the main menu of available tools."""
        rprint("[magenta]=== File Management Tools ===[/magenta]\n")
        
        # Create main tools table with borders
        table = Table(
            show_header=True,
            box=None,
            padding=(0, 2)
        )
        
        # Add columns with headers
        table.add_column(
            "[cyan]Available Tools[/cyan]",
            style="white",
            width=40
        )
        table.add_column(
            "[cyan]Shortcuts[/cyan]",
            style="white",
            width=10,
            justify="left"
        )
        
        # Add tools to table
        for idx, (name, _, shortcut) in enumerate(self.tools, 1):
            tool_cell = f"[yellow]{idx}.[/yellow] [cyan]{name}[/cyan]"
            shortcut_cell = f"[yellow]{shortcut}[/yellow]"
            table.add_row(tool_cell, shortcut_cell)
        
        # Print tools table
        self.console.print(table)

    def run_tool(self, tool_name: str) -> None:
        """Run a specific tool."""
        try:
            # Add tools directory to Python path
            sys.path.append(str(self.tools_dir.parent))
            
            # Import and run the tool
            module = __import__(f"tools.{tool_name}", fromlist=['Tool'])
            tool = module.Tool()
            tool.run()
        except ImportError:
            rprint(f"[red]Error: Tool '{tool_name}' not found[/red]")
        except Exception as e:
            rprint(f"[red]Error running tool: {str(e)}[/red]")
        finally:
            # Remove tools directory from Python path
            sys.path.remove(str(self.tools_dir.parent))

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
        
        while True:
            self.display_menu()
            
            choice = Prompt.ask(
                "\nSelect Tool # or shortcut (press Enter to exit)",
                default=""
            ).strip().lower()
            
            if choice == '':
                rprint("\n[yellow]Exiting File Management Tools...[/yellow]")
                break
            
            # Check if input is a shortcut
            shortcut_match = None
            for name, _, shortcut in self.tools:
                if choice == shortcut:
                    shortcut_match = name
                    break
            
            if shortcut_match:
                self.clear_screen()
                self.run_tool(shortcut_match)
                input("\nPress Enter to continue...")
                self.clear_screen()
                continue
            
            # Check if input is a number
            try:
                choice_num = int(choice)
                if 1 <= choice_num <= len(self.tools):
                    tool_name = self.tools[choice_num - 1][0]
                    self.clear_screen()
                    self.run_tool(tool_name)
                    input("\nPress Enter to continue...")
                    self.clear_screen()
                else:
                    rprint("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                if choice != '':  # Don't show error for empty input (exit)
                    rprint("[red]Invalid input. Please enter a tool number or shortcut.[/red]")

if __name__ == "__main__":
    tools = FileTools()
    tools.run()