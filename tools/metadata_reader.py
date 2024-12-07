from pathlib import Path
from typing import Dict, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.table import Table
from rich.prompt import Prompt
from rich import print as rprint
import json
from safetensors.torch import safe_open
from .base_tool import BaseTool

class MetadataReader:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/StableSwarmUI/Models/loras/flux')

    def verify_paths(self) -> bool:
        """Verify that base path exists."""
        if not self.base_path.exists():
            rprint(f"[red]Error: Directory {self.base_path} does not exist[/red]")
            return False
        return True

    def _display_items_in_panels(self, items: List[str], title: str) -> List[str]:
        """Display items in panels, with special handling for versions."""
        is_versions_display = "Versions" in title
        
        if is_versions_display:
            # For versions, create a single panel
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            # Extract model name from title
            model_name = title.split("for ")[-1]
            
            # Sort versions for display (reverse order)
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
            # Original grouping logic for models
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

    def list_model_paths(self) -> List[str]:
        """Get unique model paths from safetensors files."""
        try:
            # Get all unique model directories
            model_paths = set()
            
            # Use rglob (recursive glob) to find all safetensors files
            for file in self.base_path.rglob("*.safetensors"):
                # Get the model path (parent directory)
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

    def list_model_versions(self, model_path: str) -> List[str]:
        """List safetensors files for a specific model."""
        try:
            path = self.base_path / model_path
            versions = [f.name for f in path.glob("*.safetensors")]
            
            if not versions:
                rprint(f"[yellow]No versions found for model {model_path}[/yellow]")
                return []
                
            rprint(f"\n[cyan]Available Versions for {model_path}:[/cyan]")
            return self._display_items_in_panels(versions, f"Available Versions for {model_path}")
        except Exception as e:
            rprint(f"[red]Error scanning versions: {str(e)}[/red]")
            return []

    def read_metadata(self, file_path: Path) -> Optional[Dict]:
        """Read metadata from a safetensors file."""
        try:
            with safe_open(file_path, framework="pt", device="cpu") as f:
                metadata = dict(f.metadata())
                return metadata
        except Exception as e:
            rprint(f"[red]Error reading metadata: {str(e)}[/red]")
            return None

    def display_metadata(self, metadata: Dict) -> None:
        """Display formatted metadata."""
        try:
            # Try to parse and format specific sections
            try:
                training_params = json.loads(metadata.get("training_params", "{}"))
                dataset_info = json.loads(metadata.get("dataset_info", "{}"))
                
                training_str = "\n".join(f"{k}: {v}" for k, v in sorted(training_params.items()))
                dataset_str = "\n".join(f"{k}: {v}" for k, v in sorted(dataset_info.items()))
                
                other_metadata = {k: v for k, v in metadata.items() 
                                if k not in ["training_params", "dataset_info"]}
                other_str = "\n".join(f"{k}: {v}" for k, v in sorted(other_metadata.items()))
                
                content = (
                    f"[cyan]Training Parameters:[/cyan]\n{training_str}\n\n"
                    f"[cyan]Dataset Information:[/cyan]\n{dataset_str}\n\n"
                    f"[cyan]Other Metadata:[/cyan]\n{other_str}"
                )
            except:
                # Fallback to raw display if parsing fails
                content = json.dumps(metadata, indent=2)
            
            panel = Panel.fit(
                content,
                title="[bold magenta]Safetensors Metadata[/bold magenta]",
                border_style="blue"
            )
            self.console.print(panel)
        except Exception as e:
            rprint(f"[red]Error displaying metadata: {str(e)}[/red]")

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Metadata Reader Tool"
        self.reader = MetadataReader()
        
    def process(self):
        """Main process implementation."""
        while True:
            self.clear_screen()
            rprint("[magenta]=== Metadata Reader Tool ===[/magenta]\n")
            
            if not self.reader.verify_paths():
                return
            
            # List and select model
            model_paths = self.reader.list_model_paths()
            if not model_paths:
                return

            rprint("[cyan]Enter number to select model path (or press Enter to exit):[/cyan]")
            model_num = Prompt.ask("").strip()
            
            if not model_num:  # Empty input exits to tools index
                self.exit_tool()
                return

            try:
                selected_model = model_paths[int(model_num) - 1]
                
                # Get the first safetensors file in the selected model path
                model_dir = self.reader.base_path / selected_model
                safetensors_files = list(model_dir.glob("*.safetensors"))
                
                if not safetensors_files:
                    rprint("[red]No safetensors files found in selected path[/red]")
                    return
                    
                # Use the first file found
                file_path = safetensors_files[0]
                
                # Only read metadata once
                metadata = self.reader.read_metadata(file_path)
                if metadata:
                    self.reader.display_metadata(metadata)
                
                # Simple prompt for continuation
                Prompt.ask("\nPress Enter to read more Models")
                    
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                Prompt.ask("\nPress Enter to continue")
            except Exception as e:
                rprint(f"[red]Error: {str(e)}[/red]")
                Prompt.ask("\nPress Enter to continue")

if __name__ == "__main__":
    tool = Tool()
    tool.run()