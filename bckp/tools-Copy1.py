import os
import sys
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
        self.archive_path = self.workspace_path / 'file-scripts' / 'archive'
        self.docs_path = self.workspace_path / 'file-scripts' / 'docs'
        
        # Tool categories and their toolsUself.tool_categories = {
        self.tool_categories = {
    "Model Management": [
        ('config_manager', 'Configure training configurations', 'cm'),
        ('lora_mover', 'Process and organize LoRA models', 'lm')
    ],
    "Cleanup Tools": [
        ('remove_configs', 'Remove configuration files', 'rc'),
        ('remove_dataset_cache', 'Clear Dataset Cache', 'rd'),
        ('remove_dataset_json', 'Clear Dataset JSON', 'rj'),
        ('remove_checkpoints', 'Delete .ipynb_checkpoints directories', 'cp'),
        ('delete_models', 'Remove model files and associated data', 'dm')
    ],
    "Utilities": [
        ('download_configs', 'Sync configurations with Dropbox', 'dc'),
        ('debug_crops', 'Debug image preparation issues', 'db')
    ]
}

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        required_paths = {
            'workspace': self.workspace_path,
            'tools': self.tools_path,
        }
        
        missing_paths = []
        for name, path in required_paths.items():
            if not path.exists():
                missing_paths.append(name)
                
        if missing_paths:
            rprint(f"[red]Error: Missing required directories: {', '.join(missing_paths)}[/red]")
            return False
        return True

    def display_menu(self) -> None:
        """Display categorized menu of available tools."""
        rprint("[magenta]=== File Management Tools ===[/magenta]\n")
        
        total_idx = 1
        for category_name, tools in self.tool_categories.items():
            # Create category panel with compact table
            table = Table(
                show_header=False,
                box=None,
                show_edge=False,
                padding=(1, 1),
                width=60
            )
            
            # Two columns: tool description and shortcut
            table.add_column("Tool", style="white", width=45)
            table.add_column("Shortcut", style="yellow", width=10)
            
            # Add tools to table with spacing
            for tool_name, description, shortcut in tools:
                table.add_row(
                    f"[yellow]{total_idx}.[/yellow] {description}",
                    f"[yellow]{shortcut}[/yellow]"
                )
                total_idx += 1
            
            # Create panel with category name and padding
            panel = Panel(
                table,
                title=f"[gold1]{category_name}[/gold1]",
                border_style="blue",
                width=60,
                padding=(1, 1)
            )
            self.console.print(panel)
            print()  # Add spacing between categories

    def get_tool_by_input(self, user_input: str) -> Optional[str]:
        """Get tool name from user input (number or shortcut)."""
        # Check shortcuts first
        for category in self.tool_categories.values():
            for tool_name, _, shortcut in category:
                if user_input.lower() == shortcut.lower():
                    return tool_name
        
        # Check numerical input
        try:
            choice_num = int(user_input)
            total_idx = 1
            for category in self.tool_categories.values():
                for tool_name, _, _ in category:
                    if total_idx == choice_num:
                        return tool_name
                    total_idx += 1
        except ValueError:
            pass
        
        return None

    def run_tool(self, tool_name: str) -> None:  # Fixed indentation - part of class
        """Run a specific tool."""
        try:
            tool_path = self.tools_path / f"{tool_name}.py"
            if not tool_path.exists():
                rprint(f"[red]Error: Tool '{tool_name}' not found at {tool_path}[/red]")
                return

            sys.path.append(str(self.tools_path.parent))
            module = __import__(f"tools.{tool_name}", fromlist=['Tool'])
            tool = module.Tool()
            tool.run()  # BaseTool now handles its own loop and exit
        except ImportError as e:
            rprint(f"[red]Error importing tool '{tool_name}': {str(e)}[/red]")
        except Exception as e:
            rprint(f"[red]Error running tool: {str(e)}[/red]")
        finally:
            if str(self.tools_path.parent) in sys.path:
                sys.path.remove(str(self.tools_path.parent))
            self.clear_screen()

    def run(self):  # Fixed indentation - part of class
        """Main execution method."""
        self.clear_screen()
        
        # Verify paths
        if not self.verify_paths():
            return
        
        while True:
            self.clear_screen()
            self.display_menu()
            
            choice = Prompt.ask(
                "\nSelect Tool # or shortcut (press Enter to exit)",
                default=""
            ).strip()
            
            if not choice:
                rprint("\n[yellow]Exiting File Management Tools...[/yellow]")
                break
            
            tool_name = self.get_tool_by_input(choice)
            if tool_name:
                self.clear_screen()
                self.run_tool(tool_name)
                # Removed the input prompt here since BaseTool handles it
            else:
                rprint("[red]Invalid selection. Please try again.[/red]")


if __name__ == "__main__":
    manager = ToolsManager()
    manager.run()
