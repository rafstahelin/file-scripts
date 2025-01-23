from pathlib import Path
from typing import Dict, Optional, List, Any
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint
import json
import traceback
import sys
import os
from .base_tool import BaseTool

# Environment verification and safetensors import
console = Console()
console.print(f"[cyan]Using Python from:[/cyan] {sys.executable}")

# Try to import safetensors and set availability flag
try:
    import safetensors
    from safetensors import safe_open
    console.print(f"[cyan]Using safetensors version:[/cyan] {safetensors.__version__}")
    console.print(f"[cyan]Safetensors location:[/cyan] {safetensors.__file__}")
    SAFETENSORS_AVAILABLE = True
except ImportError:
    console.print("[red]Error: safetensors not available[/red]")
    SAFETENSORS_AVAILABLE = False
except Exception as e:
    console.print(f"[red]Error importing safetensors: {str(e)}[/red]")
    SAFETENSORS_AVAILABLE = False

class MetadataReader:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/ComfyUI/models/loras/flux')

    def verify_environment(self) -> bool:
        """Verify that the environment is properly set up."""
        try:
            # Check if we're in a virtual environment
            in_venv = sys.prefix != sys.base_prefix
            self.console.print(f"[cyan]Running in virtual environment:[/cyan] {'Yes' if in_venv else 'No'}")
            
            if not in_venv:
                self.console.print("[yellow]Warning: Not running in a virtual environment[/yellow]")
            
            # Check safetensors installation
            if not SAFETENSORS_AVAILABLE:
                self.console.print("[red]Error: safetensors module not available[/red]")
                self.console.print("[yellow]Installing safetensors...[/yellow]")
                
                try:
                    import subprocess
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "safetensors"])
                    self.console.print("[green]Successfully installed safetensors[/green]")
                    
                    # Try importing again without modifying global
                    import safetensors
                    return True
                    
                except Exception as e:
                    self.console.print(f"[red]Failed to install safetensors: {str(e)}[/red]")
                    return False
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error verifying environment: {str(e)}[/red]")
            return False

    def verify_paths(self) -> bool:
        """Verify that base path exists."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Directory {self.base_path} does not exist[/red]")
            rprint("[yellow]Note: Make sure ComfyUI is properly mounted and the loras directory exists[/yellow]")
            return False
        return True

    def list_model_paths(self) -> List[str]:
        """Get unique model paths from safetensors files."""
        try:
            model_paths = set()
            
            for file in self.base_path.rglob("*.safetensors"):
                model_path = file.parent.relative_to(self.base_path)
                model_paths.add(str(model_path))
            
            if not model_paths:
                rprint("[yellow]No models found[/yellow]")
                return []
                
            rprint("[cyan]Available Models:[/cyan]")
            return self._display_items_in_panels(sorted(model_paths), "Available Models")
        except Exception as e:
            rprint(f"[red]Error scanning models: {str(e)}[/red]")
            return []

    def read_metadata(self, file_path: Path) -> Optional[Dict]:
        """Read metadata from a safetensors file."""
        if not SAFETENSORS_AVAILABLE:
            rprint("[red]Error: safetensors module not available.[/red]")
            return None
        
        try:
            # Try different frameworks in order
            frameworks = ["pt", "tf", "flax"]
            for framework in frameworks:
                try:
                    with safe_open(file_path, framework=framework) as f:
                        metadata = dict(f.metadata())
                        self.console.print(f"[green]Successfully read metadata using {framework} framework[/green]")
                        return metadata
                except Exception:
                    continue
            
            # If all frameworks fail, show detailed error
            raise Exception("Failed to read with all available frameworks")
            
        except Exception as e:
            rprint(f"[red]Error reading metadata from {file_path.name}[/red]")
            rprint(f"[yellow]Details: {str(e)}[/yellow]")
            rprint("[cyan]Verify that the file is a valid safetensors file and not corrupted[/cyan]")
            return None

    def _display_items_in_panels(self, items: List[str], title: str) -> List[str]:
        """Display items in panels, with special handling for versions."""
        is_versions_display = "Versions" in title
        
        if is_versions_display:
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            model_name = title.split("for ")[-1]
            ordered_items = sorted(items, key=str.lower, reverse=True)
            
            for idx, item in enumerate(ordered_items, 1):
                table.add_row(f"[yellow]{idx}. {item}[/yellow]")
            
            panel = Panel(table, title=f"[magenta]{model_name}[/magenta]", 
                         border_style="blue", width=36)
            
            panels = [
                panel,
                Panel("", border_style="blue", width=36),
                Panel("", border_style="blue", width=36)
            ]
            self.console.print(Columns(panels, equal=True, expand=True))
            
            return ordered_items
        else:
            grouped = {}
            for item in sorted(items):
                base_name = item.split('/')[0]
                grouped.setdefault(base_name, []).append(item)

            panels = []
            ordered_items = []
            index = 1

            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
                
                for item in sorted(grouped[base_name], key=str.lower, reverse=True):
                    table.add_row(f"[yellow]{index}. {item}[/yellow]")
                    ordered_items.append(item)
                    index += 1

                panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                                  border_style="blue", width=36))

            panels_per_row = 3
            for i in range(0, len(panels), panels_per_row):
                row_panels = panels[i:i + panels_per_row]
                while len(row_panels) < panels_per_row:
                    row_panels.append(Panel("", border_style="blue", width=36))
                self.console.print(Columns(row_panels, equal=True, expand=True))

            return ordered_items

    def display_metadata(self, metadata: Dict) -> None:
        """Display complete formatted metadata with colors."""
        try:
            # First, let's show what keys are available in the metadata
            self.console.print("\n[cyan]Available metadata keys:[/cyan]")
            for key in metadata.keys():
                self.console.print(f"[yellow]- {key}[/yellow]")

            # Try to parse json configurations if they exist
            if 'complete_config' in metadata:
                try:
                    config_data = json.loads(metadata.get('complete_config', '{}'))
                    self.console.print("\n[bold cyan]Complete Configuration:[/bold cyan]")
                    formatted_config = self._format_json_with_colors(config_data)
                    self.console.print(formatted_config)
                except json.JSONDecodeError:
                    self.console.print("[yellow]Warning: Could not parse complete_config as JSON[/yellow]")
                    self.console.print(metadata.get('complete_config', ''))

            if 'complete_backend' in metadata:
                try:
                    backend_data = json.loads(metadata.get('complete_backend', '{}'))
                    self.console.print("\n[bold cyan]Complete Backend Configuration:[/bold cyan]")
                    formatted_backend = self._format_json_with_colors(backend_data)
                    self.console.print(formatted_backend)
                except json.JSONDecodeError:
                    self.console.print("[yellow]Warning: Could not parse complete_backend as JSON[/yellow]")
                    self.console.print(metadata.get('complete_backend', ''))

            # Display other metadata keys
            other_keys = [k for k in metadata.keys() if k not in ['complete_config', 'complete_backend']]
            if other_keys:
                self.console.print("\n[bold cyan]Other Metadata:[/bold cyan]")
                for key in other_keys:
                    value = metadata[key]
                    try:
                        # Try to parse as JSON if it looks like JSON
                        if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                            parsed_value = json.loads(value)
                            formatted_value = self._format_json_with_colors(parsed_value)
                            self.console.print(f"[cyan]{key}:[/cyan]")
                            self.console.print(formatted_value)
                        else:
                            self.console.print(f"[cyan]{key}:[/cyan] {value}")
                    except json.JSONDecodeError:
                        self.console.print(f"[cyan]{key}:[/cyan] {value}")
            
        except Exception as e:
            rprint(f"[red]Error displaying metadata: {str(e)}[/red]")
            if self.console.is_interactive:
                self.console.print(traceback.format_exc())

    def _format_value(self, value: Any) -> str:
        """Format a value with appropriate color."""
        if value is None:
            return "[yellow]null[/yellow]"
        elif isinstance(value, (int, float)):
            return f"[yellow]{value}[/yellow]"
        elif isinstance(value, bool):
            return f"[yellow]{str(value).lower()}[/yellow]"
        elif isinstance(value, str):
            return f"[yellow]\"{value}\"[/yellow]"
        elif isinstance(value, (list, dict)):
            return self._format_json_with_colors(value)
        return f"[yellow]{value}[/yellow]"

    def _format_json_with_colors(self, obj: Any, indent_level: int = 0) -> str:
        """Recursively format JSON with colors."""
        indent = "  " * indent_level
        lines = []

        if isinstance(obj, dict):
            lines.append("{")
            items = list(obj.items())
            for i, (key, value) in enumerate(items):
                if key.startswith('--'):
                    key_str = f"{indent}  [cyan]{key}[/cyan]:"
                else:
                    key_str = f"{indent}  [cyan]\"{key}\"[/cyan]:"
                
                if isinstance(value, (dict, list)):
                    value_str = self._format_json_with_colors(value, indent_level + 1)
                    lines.append(f"{key_str} {value_str}")
                else:
                    value_str = self._format_value(value)
                    lines.append(f"{key_str} {value_str}")
                
                if i < len(items) - 1:
                    lines[-1] += ","
                    
            lines.append(f"{indent}}}")
            
        elif isinstance(obj, list):
            lines.append("[")
            for i, item in enumerate(obj):
                if isinstance(item, (dict, list)):
                    item_str = self._format_json_with_colors(item, indent_level + 1)
                    lines.append(f"{indent}  {item_str}")
                else:
                    item_str = self._format_value(item)
                    lines.append(f"{indent}  {item_str}")
                
                if i < len(obj) - 1:
                    lines[-1] += ","
                    
            lines.append(f"{indent}]")
            
        return "\n".join(lines)

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Metadata Reader Tool"
        self.reader = MetadataReader()
        
    def process(self):
        """Main process implementation."""
        try:
            self.clear_screen()
            rprint("[magenta]=== Metadata Reader Tool ===[/magenta]\n")
            
            # Verify environment first
            if not self.reader.verify_environment():
                rprint("[red]Environment verification failed[/red]")
                Prompt.ask("\nPress Enter to exit")
                self.exit_tool()
                return

            while True:
                try:
                    if not self.reader.verify_paths():
                        if self.get_yes_no_input("Would you like to create the required directory structure?"):
                            try:
                                self.reader.base_path.mkdir(parents=True, exist_ok=True)
                                rprint("[green]Directory structure created successfully![/green]")
                            except Exception as e:
                                rprint(f"[red]Error creating directories: {str(e)}[/red]")
                                self.exit_tool()
                                return
                        else:
                            self.exit_tool()
                            return

                    model_paths = self.reader.list_model_paths()
                    if not model_paths:
                        self.exit_tool()
                        return

                    rprint("\n[cyan]Enter number to select model path (or press Enter to exit):[/cyan]")
                    model_num = Prompt.ask("").strip()
                    
                    if not model_num:
                        self.exit_tool()
                        return

                    selected_model = model_paths[int(model_num) - 1]
                    model_dir = self.reader.base_path / selected_model
                    safetensors_files = list(model_dir.glob("*.safetensors"))
                    
                    if not safetensors_files:
                        rprint("[red]No safetensors files found in selected path[/red]")
                        continue
                    
                    # If multiple files exist, let user choose
                    if len(safetensors_files) > 1:
                        rprint("\n[cyan]Multiple safetensors files found. Please select one:[/cyan]")
                        for idx, file in enumerate(safetensors_files, 1):
                            rprint(f"[yellow]{idx}.[/yellow] {file.name}")
                        
                        file_num = Prompt.ask("\nEnter number to select file").strip()
                        if not file_num:
                            continue
                            
                        try:
                            file_path = safetensors_files[int(file_num) - 1]
                        except (ValueError, IndexError):
                            rprint("[red]Invalid file selection[/red]")
                            continue
                    else:
                        file_path = safetensors_files[0]
                    
                    # Read and display metadata
                    metadata = self.reader.read_metadata(file_path)
                    if metadata:
                        self.reader.display_metadata(metadata)
                    
                    # Prompt for continuation
                    rprint("\n[cyan]Options:[/cyan]")
                    rprint("[yellow]1.[/yellow] Read another file from same model")
                    rprint("[yellow]2.[/yellow] Select different model")
                    rprint("[yellow]Enter[/yellow] Exit to menu")
                    
                    choice = Prompt.ask("\nEnter choice").strip()
                    if not choice:
                        self.exit_tool()
                        return
                    elif choice == "2":
                        self.clear_screen()
                        continue
                    elif choice != "1":
                        self.exit_tool()
                        return
                        
                except (ValueError, IndexError):
                    rprint("[red]Invalid selection[/red]")
                    Prompt.ask("\nPress Enter to continue")
                except Exception as e:
                    rprint(f"[red]Error: {str(e)}[/red]")
                    if self.console.is_interactive:
                        self.console.print(traceback.format_exc())
                    Prompt.ask("\nPress Enter to continue")
                    
        except Exception as e:
            rprint(f"[red]Critical error in process: {str(e)}[/red]")
            if self.console.is_interactive:
                self.console.print(traceback.format_exc())
            Prompt.ask("\nPress Enter to exit")
            return

if __name__ == "__main__":
    try:
        tool = Tool()
        tool.run()
    except Exception as e:
        console = Console(stderr=True)
        console.print(f"[red]Fatal error:[/red]")
        console.print(f"[red]{str(e)}[/red]")
        console.print(traceback.format_exc())
        input("Press Enter to exit...")