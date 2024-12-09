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

class ToolsManager:
    def __init__(self):
        self.console = Console()
        # Base paths
        self.workspace_path = Path('/workspace')
        self.tools_path = self.workspace_path / 'file-scripts' / 'tools'
        self.docs_path = self.workspace_path / 'file-scripts' / 'docs'

        # Tool categories and their tools
        self.tool_categories = {
            "Model Management": [
                ('config_manager', 'Config Manager', 'OK'),
                ('lora_mover', 'LoRA Mover', 'OK'),
                ('metadata_reader', 'Metadata Reader', 'OK')
            ],
            "Development Tools": [
                ('validation_grid', 'Validation Grid', 'OK')
            ],
            "Cleanup Tools": [
                ('delete_models', 'Delete Models', 'OK'),
                ('remove_configs', 'Remove Configs', 'OK'),
                ('remove_dataset_cache', 'Remove Dataset Cache', 'OK'),
                ('remove_dataset_json', 'Remove Dataset JSON', 'OK'),
                ('remove_checkpoints', 'Remove Checkpoints', 'OK')
            ],
            "Utilities": [
                ('download_configs', 'Download Configs', '-'),
                ('debug_crops', 'Debug Crops', '-')
            ]
        }

    def get_all_tools(self) -> List[Tuple[str, str, str]]:
        """Get a flattened list of all tools."""
        all_tools = []
        for category in self.tool_categories.values():
            all_tools.extend(category)
        return all_tools

    def display_menu(self) -> None:
        """Display categorized menu of available tools."""
        rprint("[magenta]=== File Management Tools ===[/magenta]\n")
        
        total_idx = 1
        for category_name, tools in self.tool_categories.items():
            table = Table(
                show_header=False,
                box=None,
                show_edge=False,
                padding=(1, 1),
                width=60
            )

            table.add_column("Tool", style="white", width=45)
            table.add_column("Status", style="yellow", width=10)

            for tool_name, description, status in tools:
                # Add status color based on value
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

    def get_tool_by_input(self, user_input: str) -> Optional[str]:
        """Get tool name from user input number."""
        all_tools = self.get_all_tools()
        
        # Check numerical input only
        try:
            choice_num = int(user_input)
            if 1 <= choice_num <= len(all_tools):
                return all_tools[choice_num - 1][0]
        except ValueError:
            pass

        return None

    # [Rest of the class methods remain unchanged...]

    def run_tool(self, tool_name: str) -> None:
        """Run a specific tool."""
        try:
            tool_path = self.tools_path / f"{tool_name}.py"
            self.console.print(f"[cyan]Loading tool: {tool_name}[/cyan]")
            
            if not tool_path.exists():
                self.console.print(f"[red]Error: Tool file not found: {tool_path}[/red]")
                return

            sys.path.append(str(self.tools_path.parent))
            
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

                choice = Prompt.ask(
                    "\nSelect Tool # or shortcut (press Enter to exit)",
                    default=""
                ).strip()

                if not choice:
                    self.console.print("\n[yellow]Exiting File Management Tools...[/yellow]")
                    break

                tool_name = self.get_tool_by_input(choice)
                if tool_name:
                    self.clear_screen()
                    self.run_tool(tool_name)
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
                    input("\nPress Enter to continue...")
            
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