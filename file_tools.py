import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.prompt import Prompt

class FileTools:
    def __init__(self):
        self.console = Console()
        self.tools_dir = Path('/workspace/file-scripts/tools')
        self.tools = [
            ('remove_configs.py', 'Remove configuration files', 'rc'),
            ('download_configs.py', 'Download configurations to Dropbox', 'dc'),
            ('delete_models.py', 'Remove model files and associated data', 'dm'),
            ('remove_dataset_json.py', 'Clean up dataset JSON files', 'rj'),
            ('remove_dataset_cache.py', 'Clear dataset cache directories', 'rd'),
            ('remove_checkpoints.py', 'Delete .ipynb_checkpoints directories', 'cp'),
            ('debug_crops.py', 'Run image preparation debug routine', 'db')
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
        # Create main tools table
        tools_table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            title="[magenta]File Management Tools[/magenta]",
            title_style="bold magenta"
        )
        tools_table.add_column("Number", style="yellow", width=4)
        tools_table.add_column("Tool", style="cyan", width=30)
        tools_table.add_column("Description", style="white")
        
        # Add tools to table
        for idx, (filename, description, shortcut) in enumerate(self.tools, 1):
            tools_table.add_row(
                f"{idx}.",
                filename.replace('.py', ''),
                description
            )
        
        # Create shortcuts table
        shortcuts_table = Table(
            show_header=False,
            box=None,
            padding=(0, 2),
            title="\n[blue]Shortcuts[/blue]",
            title_style="bold blue"
        )
        shortcuts_table.add_column("Shortcut", style="yellow", width=12)
        shortcuts_table.add_column("Description", style="white")
        
        # Add shortcuts in rows of three
        shortcuts = [(f"[yellow]{sc}[/yellow]", f"{desc}") 
                    for _, desc, sc in self.tools]
        
        for i in range(0, len(shortcuts), 3):
            row = shortcuts[i:i+3]
            while len(row) < 3:
                row.append(("", ""))
            shortcuts_table.add_row(
                f"{row[0][0]}: {row[0][1]}",
                f"{row[1][0]}: {row[1][1]}",
                f"{row[2][0]}: {row[2][1]}"
            )
        
        # Create main panel with both tables
        panel = Panel(
            f"{tools_table}\n{shortcuts_table}",
            border_style="blue",
            padding=(1, 2)
        )
        
        self.console.print(panel)

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
                "\nEnter tool number, shortcut, or 'q' to quit",
                default="q"
            ).strip().lower()
            
            if choice == 'q':
                rprint("\n[yellow]Exiting File Management Tools...[/yellow]")
                break
            
            # Check if input is a shortcut
            shortcut_match = None
            for filename, _, shortcut in self.tools:
                if choice == shortcut:
                    shortcut_match = filename.replace('.py', '')
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
                    tool_name = self.tools[choice_num - 1][0].replace('.py', '')
                    self.clear_screen()
                    self.run_tool(tool_name)
                    input("\nPress Enter to continue...")
                    self.clear_screen()
                else:
                    rprint("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                rprint("[red]Invalid input. Please enter a number, shortcut, or 'q' to quit.[/red]")

if __name__ == "__main__":
    tools = FileTools()
    tools.run()