"""
File Scripts Tools Manager
-------------------------
Central menu system for managing and running file-scripts tools.
"""

import os
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.prompt import Prompt
from contextlib import contextmanager
import termios
import tty

@contextmanager 
def raw_mode(file):
    """Context manager for handling raw terminal input"""
    if os.name == 'nt':
        yield
    else:
        old_attrs = termios.tcgetattr(file.fileno())
        new_attrs = old_attrs[:]
        new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
        try:
            termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
            yield
        finally:
            termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)

class ToolsManager:
    def __init__(self):
        self.console = Console()
        # Base paths
        self.workspace_path = Path('/workspace')
        self.tools_path = self.workspace_path / 'file-scripts' / 'tools'
        self.docs_path = self.workspace_path / 'file-scripts' / 'docs'

        # Tool categories and their tools
        self.tool_categories = {
            "Training": [
                ("train", "train", "OK"),
                ('set_config', 'Set Config', 'ok'),
                ('set_prompts', 'Set Prompts', '-'),
                ('config_manager', 'Config Manager', 'OK')
            ],
            "File Management": [
                ('lora_mover', 'LoRA Mover', 'OK'),
                ('metadata_reader', 'Metadata Reader', 'OK'),
                ('download_configs', 'Download Configs', 'OK')
            ],
            "Dev Tools": [
                ('validation_grid', 'Validation Grid', 'OK'),
                ('debug_crops', 'Debug Crops', '-')
            ],
            "Cleanup Tools": [
                ('delete_models', 'Delete Models', 'OK'),
                ('remove_configs', 'Remove Configs', 'OK'),
                ('remove_dataset_cache', 'Remove Dataset Cache', 'OK'),
                ('remove_dataset_json', 'Remove Dataset JSON', 'OK'),
                ('remove_checkpoints', 'Remove Checkpoints', 'OK')
            ],
            "Utilities": [
                ('setup', 'Setup', 'OK')
            ]
        }

    def get_all_tools(self) -> List[Tuple[str, str, str]]:
            """Get a flattened list of all tools."""
            all_tools = []
            for category in self.tool_categories.values():
                all_tools.extend(category)
            return all_tools

    def display_shortcuts(self) -> None:
        """Display shortcuts using the same Panel and Table format."""
        shortcuts = [
            ('tools', 'Launch tools menu'),
            ('config', 'Navigate to configs directory'),
            ('data', 'Navigate to datasets directory'),
            ('out', 'Navigate to output directory'),
            ('flux', 'Navigate to flux directory'),
            ('scripts', 'Navigate to scripts directory')
        ]
        
        table = Table(
            show_header=False,
            box=None,
            show_edge=False,
            padding=(1, 1),
            width=55
        )
    
        table.add_column("Command", style="white", width=15)
        table.add_column("Description", style="white", width=40)
    
        for idx, (shortcut, description) in enumerate(shortcuts, 1):
            table.add_row(
                f"[yellow]{idx}.[/yellow] [cyan]{shortcut}[/cyan]",
                description
            )
    
        panel = Panel(
            table,
            title="[gold1]Shortcuts[/gold1]",
            border_style="blue",
            width=60,
            padding=(1, 1)
        )
        self.console.print(panel)
        print()

    def display_menu(self) -> None:
        """Display categorized menu of available tools."""
        print()
        
        total_idx = 1
        first_category = True
        for category_name, tools in self.tool_categories.items():
            table = Table(
                show_header=False,
                box=None,
                show_edge=False,
                padding=(1, 1),
                width=55
            )
    
            table.add_column("Tool", style="white", width=45)
            table.add_column("Status", style="yellow", width=10)
    
            for tool_name, description, status in tools:
                status_color = "green" if status == "OK" else "red" if status == "-" else "yellow"
                table.add_row(
                    f"[yellow]{total_idx}.[/yellow] {description}",
                    f"[{status_color}]{status}[/{status_color}]"
                )
                total_idx += 1
    
            panel = Panel(
                table,
                title=f"[gold1]{category_name}[/gold1]",
                border_style="blue",
                width=60,
                padding=(1, 1)
            )
            self.console.print(panel)
            print()

        # Display shortcuts at the end
        self.display_shortcuts()

    def get_tool_by_input(self, user_input: str) -> Optional[str]:
        """Get tool name from user input number."""
        all_tools = self.get_all_tools()
        
        try:
            choice_num = int(user_input)
            if 1 <= choice_num <= len(all_tools):
                return all_tools[choice_num - 1][0]
        except ValueError:
            pass

        return None

    def run_tool(self, tool_name: str) -> None:
        try:
            tool_path = self.tools_path / f"{tool_name}.py"
            self.console.print(f"[cyan]Loading tool: {tool_name}[/cyan]")
            
            if not tool_path.exists():
                self.console.print(f"[red]Error: Tool file not found: {tool_path}[/red]")
                return
    
            if str(self.tools_path.parent) not in sys.path:
                sys.path.insert(0, str(self.tools_path.parent))
            
            try:
                module = __import__(f"tools.{tool_name}", fromlist=['Tool'])
                tool = module.Tool()
                tool.run()
            except Exception as e:
                self.console.print(f"[red]Error running tool: {str(e)}[/red]")
                self.console.print("[yellow]Full error trace:[/yellow]")
                self.console.print(traceback.format_exc())
        finally:
            if str(self.tools_path.parent) in sys.path:
                sys.path.remove(str(self.tools_path.parent))
            input("\nPress Enter to continue...")
            self.clear_screen()

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        required_paths = {
            'workspace': self.workspace_path,
            'tools': self.tools_path,
        }
        missing_paths = []
        for name, path in required_paths.items():
            if not path.exists():
                missing_paths.append(f"{name}: {path}")
        if missing_paths:
            self.console.print("[red]Error: Missing required directories:[/red]")
            for path in missing_paths:
                self.console.print(f"[red]- {path}[/red]")
            return False
        return True


    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        """Main execution method."""
        self.clear_screen()
        if not self.verify_paths():
            return
            
        while True:
            try:
                self.clear_screen()
                self.display_menu()
                with raw_mode(sys.stdin):
                    while True:
                        key = sys.stdin.read(1)
                        if not key or key == '\x1b':  # Empty or Escape
                            self.console.print("\n[yellow]Exiting File Management Tools...[/yellow]")
                            return
                        if key == '\r' or key == '\n':  # Add Enter key detection
                            self.console.print("\n[yellow]Exiting File Management Tools...[/yellow]")
                            return
                        if key.isdigit():
                            tool_name = self.get_tool_by_input(key)
                            if tool_name:
                                self.clear_screen()
                                self.run_tool(tool_name)
                                break
            except Exception as e:
                self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
                self.console.print(traceback.format_exc())
                input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        manager = ToolsManager()
        manager.run()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        traceback.print_exc()