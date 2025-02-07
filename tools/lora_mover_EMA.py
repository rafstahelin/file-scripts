import os
import shutil
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt
from .base_tool import BaseTool

try:
    from .metadata_handler import MetadataHandler
    METADATA_AVAILABLE = True
except ImportError:
    METADATA_AVAILABLE = False
    rprint("[yellow]Warning: MetadataHandler not available - metadata features will be disabled[/yellow]")

class LoRAMoverEMA:
    def __init__(self):
        self.console = Console()
        self.base_path = Path.cwd()
        self.destination_base = Path('/workspace/ComfyUI/models/loras/flux')
        self.metadata_handler = None
        if METADATA_AVAILABLE:
            try:
                self.metadata_handler = MetadataHandler()
            except Exception as e:
                rprint(f"[yellow]Warning: Failed to initialize MetadataHandler: {str(e)}[/yellow]")

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
            """Verify that required paths exist."""
            rprint(f"[cyan]Debug: Checking base path: {self.base_path}[/cyan]")
            if not self.base_path.exists():
                rprint(f"[red]Error: Directory {self.base_path} does not exist[/red]")
                input("Press Enter to continue...")  # Added pause
                return False
            
            rprint(f"[cyan]Debug: Base path exists. Creating destination: {self.destination_base}[/cyan]")
            # Create destination base if it doesn't exist
            self.destination_base.mkdir(parents=True, exist_ok=True)
            return True

    def modify_version_name(self, version: str) -> str:
        """Add 'ema' after the first digit-hyphen pattern in version name."""
        import re
        # Match the first occurrence of digits followed by a hyphen
        pattern = r'(\d+)(-)'
        modified = re.sub(pattern, r'\1-ema-', version, count=1)
        return modified

    def show_progress(self, description: str, file_count: int) -> None:
        """Show a progress bar with the given description."""
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green"),
            TaskProgressColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task(description, total=file_count)
            while not progress.finished:
                progress.update(task, advance=1)
                time.sleep(0.02)

    def list_model_paths(self) -> List[str]:
        """Scan current directory for model paths and display them in a formatted table."""
        try:
            model_paths = [f.name for f in self.base_path.iterdir() 
                         if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not model_paths:
                rprint("[yellow]No model paths found in current directory[/yellow]")
                return []
                
            rprint("[cyan]Available Models:[/cyan]")
            return self._display_items_in_panels(model_paths, "Available Models")
        except Exception as e:
            rprint(f"[red]Error scanning directory: {str(e)}[/red]")
            return []

    def list_model_versions(self, model_path: str) -> List[str]:
        """Scan selected model path for versions and display them in a formatted table."""
        try:
            version_path = self.base_path / model_path
            versions = [f.name for f in version_path.iterdir() 
                      if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            
            if not versions:
                rprint(f"[yellow]No versions found for model {model_path}[/yellow]")
                return []
                
            rprint(f"\n[cyan]Available Versions for {model_path}:[/cyan]")
            return self._display_items_in_panels(versions, f"Available Versions for {model_path}")
        except Exception as e:
            rprint(f"[red]Error scanning versions: {str(e)}[/red]")
            return []

    def _display_items_in_panels(self, items: List[str], title: str) -> List[str]:
        """Display items in panels, with special handling for versions."""
        # Check if we're displaying versions
        is_versions_display = "Versions" in title
        
        if is_versions_display:
            # For versions, create a single panel with all versions
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            # Extract model name from title
            model_name = title.split("for ")[-1]
            
            # Sort versions for display (reverse order)
            ordered_items = sorted(items, key=str.lower, reverse=True)
            
            # Add rows in chronological order
            for idx, item in enumerate(ordered_items, 1):
                table.add_row(f"[yellow]{idx}. {item}[/yellow]")
            
            panel = Panel(table, title=f"[magenta]{model_name}[/magenta]", 
                         border_style="blue", width=36)
            
            panels = [panel, Panel("", border_style="blue", width=36), 
                     Panel("", border_style="blue", width=36)]
            self.console.print(Columns(panels, equal=True, expand=True))
            
            return ordered_items
        else:
            # Original grouping logic for non-version displays
            grouped = {}
            for item in sorted(items):
                base_name = item.split('-', 1)[0]
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

            for i in range(0, len(panels), 3):
                row_panels = panels[i:i + 3]
                while len(row_panels) < 3:
                    row_panels.append(Panel("", border_style="blue", width=36))
                self.console.print(Columns(row_panels, equal=True, expand=True))

            return ordered_items

    def sync_to_dropbox(self, model_path: str, is_single_version: bool = False) -> None:
        """Sync processed files to Dropbox using rclone with simplified progress."""
        try:
            rprint("\n[cyan]Starting Dropbox synchronization...[/cyan]")
            
            source_path = str(self.destination_base / model_path)
            base_destination = "dbx:/studio/ai/libs/SD/loras/flux"
            destination = f"{base_destination}/{model_path}"
            
            # First, get list of files to be transferred
            cmd_check = ["rclone", "lsf", source_path, "--files-only", "-R"]
            files_to_transfer = subprocess.check_output(cmd_check, 
                                                      universal_newlines=True).splitlines()
            
            if not files_to_transfer:
                rprint("[yellow]No files to transfer[/yellow]")
                return
                
            rprint(f"[yellow]Found {len(files_to_transfer)} files to process[/yellow]")
            
            cmd = [
                "rclone", "copy", "--checksum", source_path, destination,
                "--ignore-existing", "-P"
            ]
            
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(f"[cyan]Uploading {model_path}", total=100)
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                
                for _ in range(100):
                    if process.poll() is not None:
                        break
                    progress.update(task, advance=1)
                    time.sleep(0.1)
                
                process.wait()
                
                if process.returncode == 0:
                    progress.update(task, completed=100)
                    rprint("\n[green]Dropbox synchronization completed successfully![/green]")
                else:
                    rprint("\n[red]Error during Dropbox synchronization[/red]")
                    
        except Exception as e:
            rprint(f"[red]Error during Dropbox sync: {str(e)}[/red]")

    def process_safetensors(self, source_path: Path, dest_path: Path, 
                            model_name: str, version: str) -> int:
            """Process and copy EMA safetensors files with proper naming."""
            try:
                rprint(f"[cyan]Debug: Starting process_safetensors[/cyan]")
                rprint(f"[cyan]Debug: Source path: {source_path}[/cyan]")
                rprint(f"[cyan]Debug: Destination path: {dest_path}[/cyan]")
                
                processed_count = 0
                
                # Look for checkpoints with EMA files
                checkpoints = [d for d in source_path.iterdir() if d.is_dir() 
                            and d.name.startswith('checkpoint-')]
                
                rprint(f"[cyan]Debug: Found {len(checkpoints)} checkpoints[/cyan]")
                
                for checkpoint_dir in checkpoints:
                    ema_path = checkpoint_dir / "ema" / "pytorch_lora_weights.safetensors"
                    rprint(f"[cyan]Debug: Checking EMA path: {ema_path}[/cyan]")
                    
                    if ema_path.exists():
                        rprint(f"[green]Debug: Found EMA file in {checkpoint_dir.name}[/green]")
                        step_count = checkpoint_dir.name.split('-')[1]
                        step_count = str(int(step_count)).zfill(5)
                        
                        # Modify version name to include 'ema'
                        modified_version = self.modify_version_name(version)
                        
                        # Create new filename with EMA designation
                        new_filename = f"{model_name}-{modified_version}-{step_count}.safetensors"
                        dest_file = dest_path / new_filename
                        
                        rprint(f"[cyan]Debug: Will save as: {dest_file}[/cyan]")
                        
                        # Create destination directory if it doesn't exist
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy the file
                        shutil.copy2(ema_path, dest_file)
                        processed_count += 1
                        rprint(f"[green]Copied EMA: {new_filename}[/green]")
                    else:
                        rprint(f"[yellow]Debug: No EMA file found in {checkpoint_dir.name}[/yellow]")
                
                return processed_count
                
            except Exception as e:
                rprint(f"[red]Error processing EMA safetensors: {str(e)}[/red]")
                rprint("[red]Full error trace:[/red]")
                import traceback
                rprint(traceback.format_exc())
                input("Press Enter to continue...")  # Added pause
                return 0

    def process_single_version(self):
            """Handle processing of a single model version."""
            try:
                rprint("[cyan]Debug: Starting process_single_version[/cyan]")
                
                model_paths = self.list_model_paths()
                if not model_paths:
                    rprint("[red]Debug: No model paths found[/red]")
                    input("Press Enter to continue...")  # Added pause
                    return

                model_num = Prompt.ask("\nEnter number to select model path").strip()
                if not model_num:
                    rprint("[red]Exited--no input given[/red]")
                    return

                try:
                    selected_model = model_paths[int(model_num) - 1]
                    rprint(f"[cyan]Debug: Selected model: {selected_model}[/cyan]")
                except (ValueError, IndexError):
                    rprint("[red]Invalid selection[/red]")
                    input("Press Enter to continue...")  # Added pause
                    return

                versions = self.list_model_versions(selected_model)
                if not versions:
                    rprint("[red]Debug: No versions found[/red]")
                    input("Press Enter to continue...")  # Added pause
                    return

                version_num = Prompt.ask("\nEnter number to select version").strip()
                if not version_num:
                    rprint("[red]Exited--no input given[/red]")
                    return

                try:
                    selected_version = versions[int(version_num) - 1]
                    rprint(f"[cyan]Debug: Selected version: {selected_version}[/cyan]")
                except (ValueError, IndexError):
                    rprint("[red]Invalid selection[/red]")
                    input("Press Enter to continue...")  # Added pause
                    return

                # Process the selected version
                source_path = self.base_path / selected_model / selected_version
                modified_version = self.modify_version_name(selected_version)
                dest_path = self.destination_base / selected_model / modified_version
                
                rprint(f"[cyan]Debug: Processing paths:[/cyan]")
                rprint(f"[cyan]Source: {source_path}[/cyan]")
                rprint(f"[cyan]Destination: {dest_path}[/cyan]")
                
                rprint(f"\n[cyan]Processing EMA version {selected_version} of {selected_model}...[/cyan]")
                files_processed = self.process_safetensors(source_path, dest_path, 
                                                        selected_model, selected_version)
                
                if files_processed > 0:
                    self.show_progress("Processing complete", 100)
                    rprint(f"[green]Successfully processed {files_processed} EMA files![/green]")
                    
                    # Sync to Dropbox with modified version name
                    sync_path = f"{selected_model}/{modified_version}"
                    self.sync_to_dropbox(sync_path, is_single_version=True)
                else:
                    rprint("[yellow]No EMA files were processed[/yellow]")
                    input("Press Enter to continue...")  # Added pause
                    
            except Exception as e:
                rprint(f"[red]Error in process_single_version: {str(e)}[/red]")
                rprint("[red]Full error trace:[/red]")
                import traceback
                rprint(traceback.format_exc())
                input("Press Enter to continue...")  # Added pause
                return

    def process_all_versions(self):
        """Handle processing of all versions for a selected model."""
        try:
            rprint("[cyan]Debug: Starting process_all_versions[/cyan]")
            
            model_paths = self.list_model_paths()
            if not model_paths:
                rprint("[red]Debug: No model paths found[/red]")
                input("Press Enter to continue...")  # Added pause
                return

            model_num = Prompt.ask("\nEnter number to select model path").strip()
            if not model_num:
                rprint("[red]Exited--no input given[/red]")
                return

            try:
                selected_model = model_paths[int(model_num) - 1]
                rprint(f"[cyan]Debug: Selected model: {selected_model}[/cyan]")
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                input("Press Enter to continue...")  # Added pause
                return

            model_path = self.base_path / selected_model
            versions = [d.name for d in model_path.iterdir() 
                       if d.is_dir() and d.name != '.ipynb_checkpoints']
            
            if not versions:
                rprint(f"[yellow]No versions found for model {selected_model}[/yellow]")
                input("Press Enter to continue...")  # Added pause
                return

            total_processed = 0
            rprint(f"\n[cyan]Processing all EMA versions of {selected_model}...[/cyan]")
            
            for version in sorted(versions, reverse=True):
                source_path = model_path / version
                modified_version = self.modify_version_name(version)
                dest_path = self.destination_base / selected_model / modified_version
                
                rprint(f"[cyan]Debug: Processing paths for version {version}:[/cyan]")
                rprint(f"[cyan]Source: {source_path}[/cyan]")
                rprint(f"[cyan]Destination: {dest_path}[/cyan]")
                
                rprint(f"[yellow]Processing version {version}...[/yellow]")
                files_processed = self.process_safetensors(source_path, dest_path, 
                                                         selected_model, version)
                total_processed += files_processed
            
            if total_processed > 0:
                self.show_progress("Processing complete", 100)
                rprint(f"[green]Successfully processed {total_processed} EMA files across all versions![/green]")
                
                # Sync to Dropbox - for all versions, we sync the entire model directory
                self.sync_to_dropbox(selected_model, is_single_version=False)
            else:
                rprint("[yellow]No EMA files were processed[/yellow]")
                input("Press Enter to continue...")  # Added pause
                
        except Exception as e:
            rprint(f"[red]Error in process_all_versions: {str(e)}[/red]")
            rprint("[red]Full error trace:[/red]")
            import traceback
            rprint(traceback.format_exc())
            input("Press Enter to continue...")  # Added pause
            return

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        # Verify paths before proceeding
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== LoRA EMA Model Management Tool ===[/magenta]")
        
        rprint("\n[cyan]Select processing mode:[/cyan]")
        rprint("[yellow]1. Process single version[/yellow]")
        rprint("[yellow]2. Process all versions of a model[/yellow]")
        
        choice = Prompt.ask("\nEnter choice").strip()
        if not choice:
            rprint("[red]Exited--no input given[/red]")
            return
        
        if choice == "1":
            self.process_single_version()
        elif choice == "2":
            self.process_all_versions()
        else:
            rprint("[red]Invalid choice[/red]")
            return


class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.tool_name = "LoRA EMA Model Management Tool"
        self.mover = LoRAMoverEMA()
        self.mover.base_path = self.workspace_path / 'SimpleTuner/output'
        self.mover.destination_base = self.workspace_path / 'ComfyUI/models/loras/flux'
        
    def process(self):
        """Main process implementation."""
        self.clear_screen()
        
        if not self.verify_paths():
            self.exit_tool()
            return
            
        rprint("[magenta]=== LoRA EMA Model Management Tool ===[/magenta]")
        
        rprint("\n[cyan]Select processing mode:[/cyan]")
        rprint("[yellow]1. Process single version[/yellow]")
        rprint("[yellow]2. Process all versions of a model[/yellow]")
        rprint("[cyan]Press Enter to return to main menu[/cyan]")
        
        choice = Prompt.ask("\nEnter choice").strip()
        if not choice:
            self.exit_tool()
            return
        
        if choice == "1":
            self.mover.process_single_version()
        elif choice == "2":
            self.mover.process_all_versions()
        else:
            rprint("[red]Invalid choice[/red]")
            time.sleep(1)

if __name__ == "__main__":
    tool = Tool()
    tool.run()