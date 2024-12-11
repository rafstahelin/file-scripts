"""
Set Config Tool
--------------
Interactive configuration editor for SimpleTuner training parameters.
Features discrete updates and immediate parameter selection with improved error handling.
"""

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.columns import Columns
from rich.prompt import Prompt
from pathlib import Path
import json
import re
import os
import sys
import termios
import tty
from contextlib import contextmanager
from typing import Dict, Any, Optional

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

class ConfigEditor:
    """Handles the interactive configuration editing interface"""
    
    def __init__(self):
        self.console = Console()
        self.parameters = {
            "1": {
                "name": "Learning Rate",
                "value": "1e-4",
                "type": "float",
                "description": "Initial learning rate for training"
            },
            "2": {
                "name": "Optimizer",
                "value": "adamw_bf16",
                "type": "choice",
                "options": ["adamw_bf16", "optimi-lion", "optimi-stableadamw"],
                "description": "Optimization algorithm for training"
            },
            "3": {
                "name": "LR Scheduler",
                "value": "constant",
                "type": "choice",
                "options": ["constant", "constant_with_warmup", "cosine", "polynomial"],
                "description": "Learning rate adjustment strategy"
            },
            "4": {
                "name": "LoRA Rank",
                "value": "32",
                "type": "int",
                "description": "Dimension of LoRA update matrices"
            },
            "5": {
                "name": "Train Batch Size",
                "value": "1",
                "type": "int",
                "description": "Number of samples per training batch"
            },
            "6": {
                "name": "Max Train Steps",
                "value": "1500",
                "type": "int",
                "description": "Maximum number of training steps"
            }
        }
        self.current_config: Optional[str] = None
        self.current_parameter: Optional[str] = None
        self.status_message: str = ""

    def make_parameters_panel(self) -> Panel:
        """Create the top panel showing current parameter values"""
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Parameter", style="cyan", width=30)
        table.add_column("Value", style="white", width=20)
        table.add_column("Description", style="dim white", width=40)
        
        for param_id, param in self.parameters.items():
            table.add_row(
                f"[yellow]{param_id}[/yellow] {param['name']}",
                param['value'],
                param['description']
            )

        return Panel(
            table,
            title=f"[gold1]Parameter Settings - {self.current_config}[/gold1]",
            border_style="blue",
            padding=(1, 1)
        )

    def make_options_panel(self) -> Panel:
        """Create the options panel with parameter editing interface"""
        if not self.current_parameter:
            content = "\n".join([
                "Select parameter to edit (press number key):",
                *(f"[yellow]{k}[/yellow] {v['name']}" for k, v in self.parameters.items()),
                "",
                "Press Enter to save and exit"
            ])
        else:
            param = self.parameters[self.current_parameter]
            if param['type'] == 'choice':
                options = [f"[yellow]{i}[/yellow] {option}" 
                          for i, option in enumerate(param['options'], 1)]
                content = "\n".join([
                    f"Select {param['name']} option:",
                    *options
                ])
            else:
                type_hint = ("Enter number in scientific notation"
                            if param['type'] == 'float' else "Enter a whole number")
                content = "\n".join([
                    f"Enter new value for {param['name']}",
                    f"Current: {param['value']}",
                    type_hint,
                    "Press Enter to cancel"
                ])
    
        return Panel(content, title="[gold1]Parameter Options[/gold1]",
                    border_style="blue", padding=(1, 1))

    def update_display(self) -> None:
        """Update the screen display"""
        os.system('cls' if os.name == 'nt' else 'clear')
        layout = Layout()
        layout.split_column(
            Layout(self.make_parameters_panel(), size=12),
            Layout(self.make_options_panel())
        )
        self.console.print(layout)

    def get_immediate_char(self) -> str:
        """Get a single character input immediately"""
        if os.name == 'nt':
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:
            return sys.stdin.read(1)

    def parse_scientific_notation(self, value: str) -> str:
        """Parse simplified scientific notation input"""
        try:
            parts = value.strip().split()
            if len(parts) == 1:
                current_value = self.parameters[self.current_parameter]["value"]
                if 'e-' in current_value:
                    current_exp = int(current_value.split('e-')[1])
                    return f"{float(parts[0])}e-{current_exp}"
                elif 'e+' in current_value:
                    current_exp = int(current_value.split('e+')[1])
                    return f"{float(parts[0])}e+{current_exp}"
                return value
            elif len(parts) == 2:
                first, second = parts
                return f"{float(first)}e-{int(second)}"
            return value
        except:
            return value

    def handle_parameter_input(self, value: str, immediate: bool = False) -> bool:
        """Handle parameter value input with validation"""
        if not value:
            return True
            
        param = self.parameters[self.current_parameter]
        
        if param['type'] == 'choice' and immediate:
            try:
                idx = int(value) - 1
                if 0 <= idx < len(param['options']):
                    param['value'] = param['options'][idx]
                    self.current_parameter = None
                    return True
            except ValueError:
                pass
            return False
        
        if param['type'] == 'choice':
            try:
                idx = int(value) - 1
                if 0 <= idx < len(param['options']):
                    param['value'] = param['options'][idx]
                    return True
                self.status_message = f"Please select 1-{len(param['options'])}"
            except ValueError:
                self.status_message = "Please enter a valid number"
        
        elif param['type'] == 'float':
            try:
                value = self.parse_scientific_notation(value)
                float_val = float(eval(value)) if 'e' in value else float(value)
                param['value'] = f"{float_val:.1e}"
                return True
            except:
                self.status_message = "Enter number in scientific notation"
        
        elif param['type'] == 'int':
            try:
                int_val = int(value)
                param['value'] = str(int_val)
                return True
            except ValueError:
                self.status_message = "Please enter a valid integer"
        
        return False

    def edit_config(self, config_path: Path) -> None:
        """Main config editing interface"""
        self.current_config = config_path.parent.name
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                for param in self.parameters.values():
                    key = param['name'].lower().replace(' ', '_')
                    if key in config:
                        if param['type'] == 'float':
                            param['value'] = f"{float(config[key]):.1e}"
                        else:
                            param['value'] = str(config[key])
        except Exception as e:
            self.console.print(f"[red]Error loading config: {str(e)}[/red]")
            return

        self.update_display()

        # Handle parameter editing
        with raw_mode(sys.stdin):
            while True:
                if not self.current_parameter:
                    key = self.get_immediate_char()
                    if key in ('\r', '\n'):
                        break
                    elif key in self.parameters:
                        self.current_parameter = key
                        self.update_display()
                        
                        if self.parameters[key]['type'] == 'choice':
                            while True:
                                choice = self.get_immediate_char()
                                if choice in ('\r', '\n'):
                                    self.current_parameter = None
                                    break
                                if self.handle_parameter_input(choice, immediate=True):
                                    break
                            self.update_display()
                else:
                    value = self.console.input("\nEnter value: ").strip()
                    if self.handle_parameter_input(value):
                        self.current_parameter = None
                        self.update_display()

        # Handle save prompt
        self.console.print("\nSave changes? [y/n]: ", end="")
        save_changes = False
        with raw_mode(sys.stdin):
            while True:
                key = self.get_immediate_char().lower()
                if key in ('y', 'n'):
                    save_changes = key == 'y'
                    self.console.print(key)
                    break

        # Save or discard changes
        if save_changes:
            try:
                config_data = {}
                for param in self.parameters.values():
                    key = param['name'].lower().replace(' ', '_')
                    if param['type'] == 'float':
                        config_data[key] = float(param['value'])
                    elif param['type'] == 'int':
                        config_data[key] = int(param['value'])
                    else:
                        config_data[key] = param['value']
                
                with open(config_path, 'w') as f:
                    json.dump(config_data, f, indent=4)
                self.console.print("[green]Config saved successfully![/green]")
            except Exception as e:
                self.console.print(f"[red]Error saving config: {str(e)}[/red]")
        else:
            self.console.print("[yellow]Changes discarded.[/yellow]")

class Tool:
    """Main tool class for managing configuration files"""
    
    def __init__(self):
        self.console = Console()
        self.panel_width = 40
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.editor = ConfigEditor()

    def extract_family_name(self, config_path: Path) -> str:
        """Extract the base family name from config path"""
        base_name = config_path.parent.name
        family_name = re.match(r'^([a-zA-Z]+)', base_name)
        return family_name.group(1) if family_name else "other"

    def group_configs_by_family(self, configs: list[Path]) -> Dict[str, list[Path]]:
        """Group configs by their family name"""
        families = {}
        
        for config in configs:
            if "templates" in str(config.parent):
                continue
                
            family = self.extract_family_name(config)
            if family not in families:
                families[family] = []
            families[family].append(config)
            
        for family in families:
            families[family].sort(key=lambda x: x.parent.name)
            
        return families

    def create_family_panel(self, family_name: str, configs: list[Path], start_idx: int) -> Panel:
        """Create a panel for a config family"""
        content = []
        current_idx = start_idx
        
        for config in configs:
            env_name = config.parent.name
            content.append(f"[yellow]{current_idx}.[/yellow] {env_name}")
            current_idx += 1
            
        return Panel(
            "\n".join(content),
            title=f"[yellow]{family_name}[/yellow]",
            border_style="blue",
            width=self.panel_width
        )

    def display_configs(self, configs: list[Path]) -> None:
        """Display configs grouped by family in panels"""
        families = self.group_configs_by_family(configs)
        current_idx = 1
        panels = []
        
        for family_name, family_configs in sorted(families.items()):
            panel = self.create_family_panel(family_name, family_configs, current_idx)
            panels.append(panel)
            current_idx += len(family_configs)
            
            if len(panels) == 3:
                self.console.print(Columns(panels, equal=True, expand=True))
                panels = []
        
        if panels:
            self.console.print(Columns(panels, equal=True, expand=True))

    def run(self) -> None:
        """Main execution method"""
        if not self.base_path.exists():
            self.console.print(f"[red]Error: Directory not found: {self.base_path}[/red]")
            return
        
        configs = list(self.base_path.glob("**/config.json"))
        configs = [c for c in configs if "templates" not in str(c)]
        
        if not configs:
            self.console.print("[red]No config files found[/red]")
            return

        self.display_configs(configs)
        
        while True:
            selection = Prompt.ask("\nEnter config number to edit (or Enter to exit)")
            if not selection:
                return
                
            try:
                idx = int(selection) - 1
                all_configs = []
                families = self.group_configs_by_family(configs)
                for family_name, family_configs in sorted(families.items()):
                    all_configs.extend(family_configs)
                
                if 0 <= idx < len(all_configs):
                    self.editor.edit_config(all_configs[idx])
                    return
                self.console.print("[red]Invalid selection[/red]")
            except ValueError:
                if selection.strip() == '':
                    return
                self.console.print("[red]Invalid input[/red]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()