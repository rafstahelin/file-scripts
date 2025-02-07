import os
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
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

@contextmanager
def temporary_sys_path(path):
    """Temporarily add a path to sys.path."""
    import sys
    sys.path.insert(0, str(path))  # Add the path to the start of sys.path
    try:
        yield
    finally:
        sys.path.remove(str(path))  # Ensure the path is removed after use

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
                ("train_daisy", "train daisy", "OK"),
                ('set_config', 'Set Config', 'fix'),
                ('set_prompts', 'Set Prompts', 'OK'),
                ('config_manager', 'Config Manager', 'OK')
            ],
            "File Management": [
                ('lora_mover', 'LoRA Mover', 'fix: doesnt dl to dbx'),
                ('lora_sync', 'LoRA Sync', 'fix'),
                ('metadata_reader', 'Metadata Reader', 'fix'),
                ('download_configs', 'Download Configs', 'fix')
            ],
            "Dev Tools": [
                ('validation_grid', 'Validation Grid', 'fix- cli ok'),
                ('dataset_grid', 'Dataset Grid', 'fix - cli ok'),
                ('dataset_captions', 'Dataset Captions', 'OK'),
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
                ('setup', 'Setup', 'OK-needs optimisation'),
                ('create_prompt_group', 'Create Prompt Group', 'OK')
            ]
        }

    def get_all_tools(self) -> List[Tuple[str, str, str]]:
        """Get a flattened list of all tools."""
        all_tools = []
        for category in self.tool_categories.values():
            all_tools.extend(category)
        return all_tools

    def display_shortcuts(self) -> None:
        """Display shortcuts without numbering."""
        shortcuts = [
            ('tools', 'Launch tools menu'),
            ('config', 'Navigate to configs directory'),
            ('data', 'Navigate to datasets directory'),
            ('out', 'Navigate to output directory'),
            ('flux', 'Navigate to flux directory'),
            ('scripts', 'Navigate to scripts directory')
        ]
        
        table = Table(show_header=False, box=None, show_edge=False, padding=(1, 1), width=55)
        table.add_column("Command", style="white", width=15)
        table.add_column("Description", style="white", width=40)
        
        for shortcut, description in shortcuts:
            table.add_row(
                f"[cyan]{shortcut}[/cyan]",
                description
            )
            
        panel = Panel(table, title="[gold1]Shortcuts[/gold1]", border_style="blue", width=60, padding=(1, 1))
        self.console.print(panel)
        print()

    def display_menu(self) -> None:
        """Display categorized menu of available tools in two columns."""
        print()
        
        # Split categories into two columns
        categories = list(self.tool_categories.items())
        mid_point = (len(categories) + 1) // 2
        left_categories = categories[:mid_point]
        right_categories = categories[mid_point:]
        
        # Calculate total tools in left column for numbering
        left_tools_count = 1
        for _, tools in left_categories:
            for _ in tools:
                left_tools_count += 1
                
        # Process columns side by side but number them separately
        columns = []
        left_idx = 1
        right_idx = left_tools_count
        
        # Create both panels but maintain separate numbering
        while left_categories or right_categories:
            columns = []
            
            # Process left column
            if left_categories:
                category_name, tools = left_categories.pop(0)
                left_table = Table(show_header=False, box=None, show_edge=False, padding=(1, 1), width=55)
                left_table.add_column("Tool", style="white", width=45)
                left_table.add_column("Status", style="yellow", width=10)
                
                for tool_name, description, status in tools:
                    status_color = "green" if status == "OK" else "red" if status == "-" else "yellow"
                    left_table.add_row(
                        f"[yellow]{left_idx}.[/yellow] {description}",
                        f"[{status_color}]{status}[/{status_color}]"
                    )
                    left_idx += 1
                
                left_panel = Panel(
                    left_table,
                    title=f"[gold1]{category_name}[/gold1]",
                    border_style="blue",
                    width=60,
                    padding=(1, 1)
                )
                columns.append(left_panel)
            
            # Process right column
            if right_categories:
                category_name, tools = right_categories.pop(0)
                right_table = Table(show_header=False, box=None, show_edge=False, padding=(1, 1), width=55)
                right_table.add_column("Tool", style="white", width=45)
                right_table.add_column("Status", style="yellow", width=10)
                
                for tool_name, description, status in tools:
                    status_color = "green" if status == "OK" else "red" if status == "-" else "yellow"
                    right_table.add_row(
                        f"[yellow]{right_idx}.[/yellow] {description}",
                        f"[{status_color}]{status}[/{status_color}]"
                    )
                    right_idx += 1
                
                right_panel = Panel(
                    right_table,
                    title=f"[gold1]{category_name}[/gold1]",
                    border_style="blue",
                    width=60,
                    padding=(1, 1)
                )
                columns.append(right_panel)
            
            self.console.print(Columns(columns, equal=True, expand=True))
            print()
        
        # Display shortcuts without numbering
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

        tool_path = self.tools_path / f"{tool_name}.py"

        if not tool_path.exists():
            self.console.print(f"[red]Error: Tool file not found: {tool_path}[/red]")
            return

        try:
            with temporary_sys_path(self.tools_path.parent):
                module = __import__(f"tools.{tool_name}", fromlist=['Tool'])
                if not hasattr(module, 'Tool'):
                    self.console.print(f"[red]Error: 'Tool' class not found in {tool_name}[/red]")
                    return
                tool = module.Tool()
                if not callable(getattr(tool, 'run', None)):
                    self.console.print(f"[red]Error: 'run' method not found in Tool class of {tool_name}[/red]")
                    return
                tool.run()

        except Exception as e:
            self.console.print(f"[red]Error running tool: {str(e)}[/red]")
            self.console.print(traceback.format_exc())

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
        # os.system('clear' if os.name == 'posix' else 'cls')

    def run(self):
        """Main execution method."""
        if not self.verify_paths():
            return

        while True:
            try:
                self.clear_screen()
                self.display_menu()
                
                user_input = Prompt.ask("\n[cyan]Enter a tool number or press Enter to quit: [/cyan]").strip()
                
                if not user_input:  # Empty input -> quit
                    self.console.print("[yellow]Exiting File Management Tools...[/yellow]")
                    return

                tool_name = self.get_tool_by_input(user_input)
                if tool_name:
                    self.clear_screen()
                    self.run_tool(tool_name)
                else:
                    self.console.print("[red]Invalid input. Please enter a valid tool number.[/red]")
                    input("Press Enter to try again...")

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
