"""
Set Config Tool - Enhanced Version
--------------------------------
Interactive configuration editor for SimpleTuner training parameters.
"""

import json
import os
import sys
import termios
import tty
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.columns import Columns

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

class ParameterLibrary:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.library_path = self.base_path / 'config' / 'set_config_lib.json'
        self.parameters: Dict[str, Dict] = {}
        self.load_parameter_library()
    
    def load_parameter_library(self) -> None:
        try:
            if not self.library_path.exists():
                raise FileNotFoundError(f"Parameter library not found: {self.library_path}")
                
            with open(self.library_path) as f:
                raw_data = json.load(f)
                if not isinstance(raw_data, dict):
                    raise ValueError("Invalid parameter library format")
                self.parameters = raw_data
        except Exception as e:
            raise RuntimeError(f"Failed to load parameter library: {str(e)}")
    
    def get_parameter_definition(self, param_key: str) -> Dict:
        key = param_key.lstrip('-')
        for category, params in self.parameters.items():
            if key in params:
                return params[key]
            if f"--{key}" in params:
                return params[f"--{key}"]
        raise KeyError(f"Parameter not found in library: {param_key}")

class ParameterSelector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.selection_path = self.base_path / 'config' / 'set_config_params.txt'
        self.selected_params: List[str] = []
        self.load_parameter_selection()
    
    def load_parameter_selection(self) -> None:
        try:
            if not self.selection_path.exists():
                raise FileNotFoundError(f"Parameter selection file not found: {self.selection_path}")
            with open(self.selection_path) as f:
                self.selected_params = [line.strip() for line in f if line.strip()]
        except Exception as e:
            raise RuntimeError(f"Failed to load parameter selection: {str(e)}")

class ConfigEditor:
    def __init__(self):
        self.console = Console()
        self.library = ParameterLibrary()
        self.selector = ParameterSelector()
        self.parameters: Dict[str, Dict] = {}
        self.current_config: Optional[str] = None
        self.current_parameter: Optional[str] = None
        self.status_message: str = ""
        self.initialize_parameters()
    
    def initialize_parameters(self) -> None:
        for idx, param_key in enumerate(self.selector.selected_params, 1):
            try:
                param_def = self.library.get_parameter_definition(param_key)
                is_choice, param_type = self.determine_parameter_type(param_def)
                
                self.parameters[str(idx)] = {
                    "name": param_key,
                    "value": "",
                    "is_choice": is_choice or param_type == 'bool',  # Boolean parameters are always choice
                    "type": param_type,
                    "options": self.get_parameter_options(param_def, param_type),
                    "config_key": f"--{param_key}" if not param_key.startswith('--') else param_key
                }
            except KeyError as e:
                self.console.print(f"[yellow]Warning: {str(e)}[/yellow]")
    
    def determine_parameter_type(self, param_def: Dict) -> Tuple[bool, str]:
        """Enhanced type detection with special handling for booleans"""
        if isinstance(param_def, dict):
            if any(isinstance(x, bool) for x in param_def.values()):
                return True, 'bool'
            elif any(isinstance(x, float) for x in param_def.values()):
                return False, 'float'
            elif any(isinstance(x, int) for x in param_def.values()):
                return False, 'int'
            return False, 'string'
        elif isinstance(param_def, list):
            if all(isinstance(x, bool) for x in param_def):
                return True, 'bool'
            elif all(isinstance(x, (int, float)) for x in param_def):
                return False, 'float' if any(isinstance(x, float) for x in param_def) else 'int'
            return True, 'choice'
        return False, 'string'
    
    def get_parameter_options(self, param_def: Union[Dict, List], param_type: str) -> List:
        """Get parameter options with special handling for booleans"""
        if param_type == 'bool':
            return ['true', 'false']
        if isinstance(param_def, list):
            return param_def
        return []
    
    def parse_number_format(self, value: str) -> str:
        """Enhanced number parsing"""
        try:
            value = value.strip().lower()
            
            # Split notation (e.g. "1.5 4" -> "1.5e-4")
            parts = value.split()
            if len(parts) == 2:
                try:
                    base = float(parts[0])
                    exp = int(parts[1])
                    return f"{base}e-{exp}"
                except ValueError:
                    raise ValueError("Invalid scientific notation format")
            
            # Handle decimal or scientific notation
            try:
                float(value)  # Validate format
                return value
            except ValueError:
                raise ValueError("Invalid number format")
                
        except ValueError as e:
            raise ValueError(str(e))

    def make_parameters_panel(self) -> Panel:
            """Create parameter display panel with two columns"""
            table = Table(show_header=False, box=None, padding=(0, 2))
            table.add_column("Parameter", style="cyan", width=30)
            table.add_column("Value", style="white", width=20)
            
            params = list(self.parameters.items())
            mid_point = (len(params) + 1) // 2
            
            for i in range(max(len(params[:mid_point]), len(params[mid_point:]))):
                left = params[i] if i < mid_point else None
                right = params[i + mid_point] if i + mid_point < len(params) else None
                
                if left and right:
                    table.add_row(
                        f"[yellow]{left[0]}[/yellow] [cyan]{left[1]['name']}[/cyan]", 
                        str(left[1]['value']) if left[1]['value'] else "",
                        f"[yellow]{right[0]}[/yellow] [cyan]{right[1]['name']}[/cyan]", 
                        str(right[1]['value']) if right[1]['value'] else ""
                    )
                elif left:
                    table.add_row(
                        f"[yellow]{left[0]}[/yellow] [cyan]{left[1]['name']}[/cyan]", 
                        str(left[1]['value']) if left[1]['value'] else "",
                        "", ""
                    )
        
            return Panel(
                table,
                title=f"[gold1]Parameter Settings - {self.current_config}[/gold1]",
                border_style="blue",
                padding=(1, 1)
            )

    def handle_save_and_rename(self, config_path: Path) -> None:
        """Handle save confirmation and potential rename"""
        self.console.print("\nSave changes? (Enter=Yes, Esc=No): ", end="")
        save_confirmed = False
        
        with raw_mode(sys.stdin):
            key = sys.stdin.read(1)
            if key == '\r' or key == '\n':  # Enter - Save changes
                self.console.print("Yes")
                self.save_changes(config_path)
                save_confirmed = True
            elif key == '\x1b':  # Escape - Discard changes
                self.console.print("No")
                self.console.print("[yellow]Changes discarded.[/yellow]")
    
        if save_confirmed:
            self.console.print("\nRename config? (Space=Yes, Enter=No): ", end="")
            with raw_mode(sys.stdin):
                key = sys.stdin.read(1)
                if key == ' ':  # Space - Do rename
                    self.console.print("Yes")
                    self.handle_rename(config_path)
                elif key == '\r':  # Enter - Skip rename
                    self.console.print("No")

    def make_options_panel(self) -> Panel:
        """Create parameter options panel with improved display logic"""
        content = ""
        
        if not self.current_parameter:
            content = "Select parameter to edit:"
        else:
            param = self.parameters[self.current_parameter]
            if param['is_choice']:
                options = [f"[yellow]{i}[/yellow] {option}" 
                          for i, option in enumerate(param['options'], 1)]
                content = "\n".join([
                    f"Select value for {param['name']}:",
                    *options
                ])
            else:
                type_hints = {
                    'float': "Enter number (format: 1.5e-4 or 1.5 4)",
                    'int': "Enter whole number",
                    'bool': "Enter true or false",
                    'string': "Enter value"
                }
                content = f"Enter value for {param['name']}:"
                if param['type'] in type_hints:
                    content += f"\n{type_hints[param['type']]}"
        
        return Panel(
            content,
            title="[gold1]Parameter Options[/gold1]",
            border_style="blue",
            padding=(1, 1)
        )

    def update_display(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        layout = Layout()
        layout.split_column(
            Layout(self.make_parameters_panel(), size=12),
            Layout(self.make_options_panel())
        )
        self.console.print(layout)
        if self.status_message:
            self.console.print(f"[red]{self.status_message}[/red]")
            self.status_message = ""

    def handle_parameter_input(self, value: str, immediate: bool = False) -> bool:
            """Enhanced parameter input handling with better boolean support"""
            if not value:
                return True
                
            param = self.parameters[self.current_parameter]
            
            try:
                if param['is_choice']:
                    if immediate:
                        try:
                            idx = int(value) - 1
                            if 0 <= idx < len(param['options']):
                                param['value'] = str(param['options'][idx])
                                self.current_parameter = None
                                self.console.print(f"\nSelected: {param['value']}")
                                return True
                        except ValueError:
                            pass
                        return False
                    
                    try:
                        idx = int(value) - 1
                        if 0 <= idx < len(param['options']):
                            param['value'] = str(param['options'][idx])
                            return True
                    except ValueError:
                        raise ValueError("Invalid option selection")
                elif param['type'] == 'float':
                    parsed_value = self.parse_number_format(value)
                    param['value'] = parsed_value
                    self.console.print(f"\nEntered: {param['value']}")
                elif param['type'] == 'int':
                    param['value'] = str(int(value))
                    self.console.print(f"\nEntered: {param['value']}")
                else:
                    param['value'] = str(value)
                    self.console.print(f"\nEntered: {param['value']}")
                
                return True
                
            except ValueError as e:
                self.status_message = str(e)
                return False

    def edit_config(self, config_path: Path) -> None:
        """Main configuration editing interface with improved value loading"""
        self.current_config = config_path.parent.name
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                for param in self.parameters.values():
                    config_key = param['config_key']
                    key_without_dashes = config_key.lstrip('-')
                    
                    value = None
                    if config_key in config:
                        value = config[config_key]
                    elif key_without_dashes in config:
                        value = config[key_without_dashes]
                    
                    if value is not None:
                        if isinstance(value, bool):
                            param['value'] = str(value).lower()
                        elif isinstance(value, float):
                            if abs(value) < 0.01 or abs(value) >= 1000:
                                param['value'] = f"{value:.2e}"
                            else:
                                param['value'] = str(value)
                        elif isinstance(value, (int, str)):
                            param['value'] = str(value)
                    
        except Exception as e:
            self.console.print(f"[red]Error loading config: {str(e)}[/red]")
            return

        self.update_display()

        with raw_mode(sys.stdin):
            while True:
                if not self.current_parameter:
                    key = sys.stdin.read(1)
                    if key in ('\r', '\n'):
                        break
                    elif key in self.parameters:
                        self.current_parameter = key
                        self.console.print(f"\nSelected parameter: {self.parameters[key]['name']}")
                        self.update_display()
                        
                        if self.parameters[key]['is_choice']:
                            while True:
                                choice = sys.stdin.read(1)
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

        self.handle_save_and_rename(config_path)

    def save_changes(self, config_path: Path) -> None:
        """Save the current configuration."""
        if not config_path.exists():
            self.console.print(f"[red]Config file not found: {config_path}[/red]")
            return

        try:
            # Load existing config
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    self.console.print(f"[red]Invalid JSON format in file: {config_path}[/red]")
                    return

            # Update config with parameter values
            for param in self.parameters.values():
                if 'config_key' not in param:
                    self.console.print(f"[yellow]Skipping parameter with missing config_key: {param}[/yellow]")
                    continue
                try:
                    if param['type'] == 'float':
                        config[param['config_key']] = float(param['value'])
                    elif param['type'] == 'int':
                        config[param['config_key']] = int(param['value'])
                    elif param['type'] == 'bool':
                        config[param['config_key']] = param['value'].lower() == 'true'
                    else:
                        config[param['config_key']] = param['value']
                except ValueError:
                    self.console.print(f"[red]Invalid value for {param['config_key']}: {param['value']}[/red]")

            # Write updated config back to file
            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                self.console.print("[green]Config saved successfully![/green]")
            except OSError as e:
                self.console.print(f"[red]Failed to save config: {str(e)}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error saving config: {str(e)}[/red]")

    def handle_rename(self, config_path: Path) -> None:
        """Handle the rename operation by renaming the folder and updating the config."""
        current_name = config_path.parent.name
        self.console.print(f"\nCurrent name: {current_name}")
        
        new_name = self.console.input("Enter new name: ").strip()

        if new_name and new_name != current_name:
            if self.validate_new_name(new_name):
                try:
                    old_folder = config_path.parent
                    new_folder = old_folder.parent / new_name

                    # Check if the new folder name already exists
                    if new_folder.exists():
                        self.console.print(f"[red]Error: Folder '{new_name}' already exists.[/red]")
                        return

                    # Rename the folder
                    old_folder.rename(new_folder)
                    self.console.print(f"[green]Successfully renamed folder to '{new_name}'.[/green]")

                    # Update the config file in the renamed folder
                    config_file = new_folder / 'config.json'
                    self.edit_config_family(new_name, config_file)

                except Exception as e:
                    self.console.print(f"[red]Error during rename operation: {str(e)}[/red]")
            else:
                self.console.print("[red]Invalid name format or name already exists.[/red]")    

    def edit_config_family(self, new_folder_name: str, config_path: Path):
        # Extract components from the new folder name
        try:
            # Example: "gala-01" -> name="gala", version="01"
            name, version = new_folder_name.split('-')
        except ValueError:
            raise ValueError("Invalid folder name format. Expected format: 'name-version' (e.g., 'gala-01')")

        # Load the existing config.json file
        try:
            with open(config_path, 'r') as file:
                config = json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at: {config_path}")
            return
        except json.JSONDecodeError:
            print(f"Failed to parse config file. Ensure it's valid JSON: {config_path}")
            return

        # Update the specific keys
        config["--instance_prompt"] = name
        config["--user_prompt_library"] = f"config/{new_folder_name}/user_prompt_library.json"
        config["--data_backend_config"] = f"config/{new_folder_name}/multidatabackend.json"
        config["--output_dir"] = f"output/{name}/{version}"

        # Save the updated config back to the file
        try:
            with open(config_path, 'w') as file:
                json.dump(config, file, indent=4)
            print(f"Config updated successfully: {config_path}")
        except Exception as e:
            print(f"Failed to save updated config: {e}")

    def validate_new_name(self, new_name: str) -> bool:
        """Validate the new config name"""
        # Check for invalid characters
        if not all(c.isalnum() or c in '-_' for c in new_name):
            return False
        
        # Check if name already exists
        new_path = Path(self.current_config).parent.parent / new_name
        if new_path.exists():
            return False
            
        # Validate family-version pattern (e.g., "family-001")
        parts = new_name.split('-')
        if len(parts) != 2:
            return False
            
        return True

class Tool:
    def __init__(self):
        self.console = Console()
        self.panel_width = 40
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.editor = ConfigEditor()

    def extract_family_name(self, config_path: Path) -> str:
        base_name = config_path.parent.name
        return base_name.split('-')[0] if '-' in base_name else base_name

    def create_family_panel(self, family_name: str, configs: list[Path], start_idx: int) -> Panel:
        content = []
        current_idx = start_idx
        
        for config in configs:
            env_name = config.parent.name
            content.append(f"[yellow]{current_idx}.[/yellow] {env_name}")
            current_idx += 1
        
        return Panel(
            "\n".join(content),
            title=f"[yellow]{family_name.upper()}[/yellow]",
            border_style="blue",
            width=self.panel_width
        )

    def group_configs_by_family(self, configs: list[Path]) -> Dict[str, list[Path]]:
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

    def display_configs(self, configs: list[Path]) -> None:
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
        if not self.base_path.exists():
            self.console.print(f"[red]Error: Directory not found: {self.base_path}[/red]")
            return
        
        configs = list(self.base_path.glob("**/config.json"))
        configs = [c for c in configs if "templates" not in str(c)]
        
        if not configs:
            self.console.print("[red]No config files found[/red]")
            return

        self.console.print("[cyan]Loading config editor...[/cyan]\n")
        self.display_configs(configs)
        
        with raw_mode(sys.stdin):
            while True:
                key = sys.stdin.read(1)
                if not key or key == '\x1b':  # Empty or Escape
                    break
                    
                if key.isdigit():
                    try:
                        idx = int(key) - 1
                        all_configs = []
                        families = self.group_configs_by_family(configs)
                        for family_configs in families.values():
                            all_configs.extend(family_configs)
                        
                        if 0 <= idx < len(all_configs):
                            self.editor.edit_config(all_configs[idx])
                            return
                    except ValueError:
                        self.console.print("[red]Invalid selection[/red]")


if __name__ == "__main__":
    try:
        tool = Tool()
        tool.run()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        import traceback
        traceback.print_exc()