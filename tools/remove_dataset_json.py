from pathlib import Path
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt
from .base_tool import BaseTool

class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "Remove Dataset JSON Tool"
        self.base_path = self.workspace_path / 'SimpleTuner' / 'datasets'
        self.json_patterns = [
            "aspect_ratio_bucket_indices_*.json",
            "aspect_ratio_bucket_metadata_*.json"
        ]

    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        if not super().verify_paths():
            return False
            
        if not self.base_path.exists():
            rprint(f"[red]Error: SimpleTuner datasets directory not found at {self.base_path}[/red]")
            return False
            
        return True

    def should_skip_directory(self, dir_path: str) -> bool:
        """Check if directory should be skipped."""
        return '.ipynb_checkpoints' in dir_path or '__pycache__' in dir_path

    def list_model_dirs(self) -> Tuple[List[Dict[str, str]], Dict[str, List[str]]]:
        """List all model directories containing target JSON files."""
        try:
            model_dirs = set()
            
            for pattern in self.json_patterns:
                for json_file in self.base_path.glob(f"*/**/{pattern}"):
                    dir_path = str(json_file.parent.relative_to(self.base_path))
                    if not self.should_skip_directory(dir_path):
                        model_dirs.add(dir_path)
            
            if not model_dirs:
                rprint("[yellow]No model directories with aspect ratio bucket JSON files found.[/yellow]")
                return [], {}
            
            grouped = {}
            selection_entries = []
            token_groups = {}
            display_index = 1
            
            for model_dir in sorted(model_dirs):
                dataset_name = model_dir.split('/')[0]
                if dataset_name not in grouped:
                    grouped[dataset_name] = []
                    token_groups[dataset_name] = []
                    selection_entries.append({
                        'index': display_index,
                        'type': 'group',
                        'dataset': dataset_name,
                        'path': dataset_name
                    })
                    display_index += 1
                grouped[dataset_name].append(model_dir)
                token_groups[dataset_name].append(model_dir)
                selection_entries.append({
                    'index': display_index,
                    'type': 'dir',
                    'dataset': dataset_name,
                    'path': model_dir
                })
                display_index += 1
            
            self._display_directory_panels(grouped, selection_entries)
            
            return selection_entries, token_groups
            
        except Exception as e:
            rprint(f"[red]Error scanning directories: {str(e)}[/red]")
            return [], {}

    def _display_directory_panels(self, grouped: Dict[str, List[str]], selection_entries: List[Dict[str, str]]):
        """Display directory panels in a formatted layout."""
        panels = []
        for dataset_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            dataset_entries = [entry for entry in selection_entries 
                             if entry['dataset'] == dataset_name]
            
            for entry in dataset_entries:
                if entry['type'] == 'group':
                    table.add_row(f"[yellow]{entry['index']}. {dataset_name} all[/yellow]")
                else:
                    table.add_row(f"[yellow]{entry['index']}. {entry['path'].split('/')[-1]}[/yellow]")
            
            panels.append(Panel(table, 
                              title=f"[magenta]{dataset_name}[/magenta]", 
                              border_style="blue",
                              width=36))
        
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))

    def find_json_files(self, model_dir: Path) -> List[Path]:
        """Find all matching JSON files in a model directory."""
        json_files = []
        try:
            for pattern in self.json_patterns:
                found_files = sorted(model_dir.glob(pattern))
                json_files.extend(found_files)
            return json_files
        except Exception as e:
            return []

    def remove_json_files(self, model_dir: str, skip_confirm: bool = False) -> bool:
        """Remove aspect ratio bucket JSON files from the specified model directory."""
        try:
            dir_path = self.base_path / model_dir
            json_files = self.find_json_files(dir_path)
            
            if not json_files:
                return False
            
            deleted_count = 0
            for json_file in json_files:
                if json_file.exists():
                    try:
                        self.safe_remove(json_file)
                        deleted_count += 1
                    except Exception as e:
                        rprint(f"[red]Error removing {json_file.name}: {str(e)}[/red]")
            
            return deleted_count > 0
                
        except Exception as e:
            rprint(f"[red]Error removing files: {str(e)}[/red]")
            return False

    def remove_group(self, group_name: str, model_dirs: List[str]) -> bool:
        """Remove all JSON files for a specific group."""
        try:
            dir_file_counts = {}
            for model_dir in model_dirs:
                dir_path = self.base_path / model_dir
                if not dir_path.exists():
                    continue
                
                files = self.find_json_files(dir_path)
                count = len(files)
                if count > 0:
                    dir_file_counts[model_dir] = count

            if not dir_file_counts:
                return False

            success_count = 0
            total = len(dir_file_counts)
            
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"Processing {group_name}...", total=total)
                
                for model_dir in dir_file_counts.keys():
                    if self.remove_json_files(model_dir, skip_confirm=True):
                        success_count += 1
                    progress.advance(task)
            
            return success_count > 0
                
        except Exception as e:
            rprint(f"[red]Error removing group files: {str(e)}[/red]")
            return False

    def process(self):
            """Main process implementation."""
            self.clear_screen()
            
            if not self.verify_paths():
                self._should_exit = True
                return
                
            rprint("[magenta]Remove Dataset JSON Tool[/magenta]")
            
            entries, token_groups = self.list_model_dirs()
            if not entries:
                self._should_exit = True
                return
    
            while True:
                dir_input = input("Enter number to select: ").strip()
                
                # Exit on empty input - set both flags for immediate exit
                if not dir_input:
                    self._should_exit = True
                    self.console.quiet = True  # This prevents the "Press Enter to continue"
                    return
                
                try:
                    selection = int(dir_input)
                    entry = next((e for e in entries if e['index'] == selection), None)
                    
                    if not entry:
                        rprint("[red]Invalid selection[/red]")
                        continue
                    
                    if entry['type'] == 'group':
                        self.remove_group(entry['dataset'], token_groups[entry['dataset']])
                    else:
                        self.remove_json_files(entry['path'])
                        
                    # Refresh the directory listing after operation
                    entries, token_groups = self.list_model_dirs()
                    if not entries:
                        self._should_exit = True
                        self.console.quiet = True
                        return
                        
                except ValueError:
                    rprint("[red]Invalid selection[/red]")
                    continue