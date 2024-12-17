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
from .metadata_handler import MetadataHandler
import logging
import os
from datetime import datetime

# Ensure log directory exists
log_dir = '/workspace/file-scripts/logs'
os.makedirs(log_dir, exist_ok=True)

# Set up logging with timestamp in filename
log_file = os.path.join(log_dir, f'lora_sync_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Add console handler to see logs in terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s: %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)

class LoRaMover:
    def __init__(self):
        logging.info("LoRaMover __init__ started")
        self.console = Console()
        logging.info("Console initialized")
        self.base_path = Path.cwd()
        logging.info(f"Base path set to: {self.base_path}")
        self.destination_base = Path('/workspace/StableSwarmUI/Models/loras/flux')
        logging.info(f"Destination base set to: {self.destination_base}")
        self.metadata_handler = MetadataHandler()
        logging.info("Metadata handler initialized")
        logging.info("LoRaMover __init__ completed")

    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')

    def verify_paths(self) -> bool:
        """Verify that required paths exist and can be accessed."""
        print("Starting path verification")  # Basic print for immediate feedback
        
        try:
            # Check local paths first
            if not self.base_path.exists():
                print(f"Error: Local path {self.base_path} does not exist")
                return False
            
            # Create destination base if it doesn't exist
            self.destination_base.mkdir(parents=True, exist_ok=True)
            print("Basic path verification completed")
            
            # Quick dbx connection check with timeout
            try:
                result = subprocess.run(
                    ["rclone", "lsf", "dbx:/", "--max-depth", "1"],
                    check=True,
                    capture_output=True,
                    timeout=10  # 10 second timeout
                )
                logging.info("rclone can connect to Dropbox.")
            except subprocess.TimeoutExpired:
                logging.error("Dropbox connection check timed out")
                rprint("[red]Error: Dropbox connection check timed out.[/red]")
                return False
            except subprocess.CalledProcessError as e:
                logging.error(f"Dropbox connection check failed: {e}")
                rprint("[red]Error: Cannot connect to Dropbox. Please check your rclone configuration.[/red]")
                return False
            
            logging.info("Path verification completed successfully.")
            return True
            
        except Exception as e:
            print(f"Error in verify_paths: {str(e)}")
            return False

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
            model_paths = [f.name for f in self.base_path.iterdir() if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            if not model_paths:
                rprint("[yellow]No model paths found in current directory[/yellow]")
                return []
            rprint("[cyan]Available Models:[/cyan]")
            return self._display_items_in_panels(model_paths, "Available Models")
        except Exception as e:
            logging.error(f"Error scanning directory: {str(e)}")
            rprint(f"[red]Error scanning directory: {str(e)}[/red]")
            return []

    def list_model_versions(self, model_path: str) -> List[str]:
        """Scan selected model path for versions and display them in a formatted table."""
        try:
            version_path = self.base_path / model_path
            versions = [f.name for f in version_path.iterdir() if f.is_dir() and f.name not in ['.ipynb_checkpoints']]
            if not versions:
                rprint(f"[yellow]No versions found for model {model_path}[/yellow]")
                return []
            rprint(f"\n[cyan]Available Versions for {model_path}:[/cyan]")
            return self._display_items_in_panels(versions, f"Available Versions for {model_path}")
        except Exception as e:
            logging.error(f"Error scanning versions: {str(e)}")
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

            # Create single panel with model name as title
            panel = Panel(table, title=f"[magenta]{model_name}[/magenta]", border_style="blue", width=36)

            # Create row with one filled panel and two empty panels
            panels = [
                panel,
                Panel("", border_style="blue", width=36),
                Panel("", border_style="blue", width=36)
            ]
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

                panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", border_style="blue", width=36))

            panels_per_row = 3
            for i in range(0, len(panels), panels_per_row):
                row_panels = panels[i:i + panels_per_row]
                while len(row_panels) < panels_per_row:
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
            cmd_check = [
                "rclone",
                "lsf",
                source_path,
                "--files-only",
                "-R"
            ]
            files_to_transfer = subprocess.check_output(cmd_check, universal_newlines=True).splitlines()

            if not files_to_transfer:
                rprint("[yellow]No files to transfer[/yellow]")
                return

            rprint(f"[yellow]Found {len(files_to_transfer)} files to process[/yellow]")
            
            logging.info(f"Syncing {len(files_to_transfer)} from '{source_path}' to '{destination}'")

            # Run transfer with simpler progress tracking
            cmd = [
                "rclone",
                "copy",
                "--checksum",
                source_path,
                destination,
                "--ignore-existing",
                "-P"
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

                # Update progress in chunks
                for _ in range(100):
                    if process.poll() is not None:
                        break
                    progress.update(task, advance=1)
                    time.sleep(0.1)

                # Ensure process completes
                process.wait()

                if process.returncode == 0:
                    progress.update(task, completed=100)
                    rprint("\n[green]Dropbox synchronization completed successfully![/green]")
                else:
                    rprint("\n[red]Error during Dropbox synchronization[/red]")
                    output = process.communicate()[0]
                    logging.error(f"rclone copy process failed with code {process.returncode} and output: {output}")
        except Exception as e:
            logging.error(f"Error during Dropbox sync: {str(e)}")
            rprint(f"[red]Error during Dropbox sync: {str(e)}[/red]")

    def process_safetensors(self, source_path: Path, dest_path: Path, model_name: str, version: str) -> int:
        """Process and copy safetensors files with proper naming."""
        try:
            processed_count = 0
            # Get metadata once for all checkpoints
            metadata = self.metadata_handler.create_metadata(model_name, version)
            if metadata:
                self.console.print("[cyan]Extracted training configuration[/cyan]")

            checkpoints = [d for d in source_path.iterdir() if d.is_dir() and d.name.startswith('checkpoint-')]
            for checkpoint_dir in checkpoints:
                step_count = checkpoint_dir.name.split('-')[1]
                step_count = str(int(step_count)).zfill(5)
                source_file = checkpoint_dir / "pytorch_lora_weights.safetensors"
                if source_file.exists():
                    new_filename = f"{model_name}-{version}-{step_count}.safetensors"
                    dest_file = dest_path / new_filename

                    # Create destination directory if it doesn't exist
                    dest_file.parent.mkdir(parents=True, exist_ok=True)

                    # Update metadata if available
                    if metadata:
                        self.console.print(f"[cyan]Updating metadata for checkpoint {step_count}...[/cyan]")
                        if not self.metadata_handler.update_safetensors_metadata(source_file, metadata):
                            self.console.print("[yellow]Warning: Failed to update metadata[/yellow]")

                    # Copy the file
                    shutil.copy2(source_file, dest_file)
                    processed_count += 1
                    rprint(f"[green]Copied: {new_filename}[/green]")

            return processed_count
        except Exception as e:
            logging.error(f"Error processing safetensors: {str(e)}")
            rprint(f"[red]Error processing safetensors: {str(e)}[/red]")
            return 0

    def process_single_version(self):
        """Handle processing of a single model version."""
        model_paths = self.list_model_paths()
        if not model_paths:
            return

        model_num = Prompt.ask("\nEnter number to select model path").strip()
        if not model_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_model = model_paths[int(model_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        versions = self.list_model_versions(selected_model)
        if not versions:
            return

        version_num = Prompt.ask("\nEnter number to select version").strip()
        if not version_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_version = versions[int(version_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        # Process the selected version
        source_path = self.base_path / selected_model / selected_version
        dest_path = self.destination_base / selected_model / selected_version

        rprint(f"\n[cyan]Processing version {selected_version} of {selected_model}...[/cyan]")
        files_processed = self.process_safetensors(source_path, dest_path, selected_model, selected_version)

        if files_processed > 0:
            self.show_progress("Processing complete", 100)
            rprint(f"[green]Successfully processed {files_processed} files![/green]")

            # Sync to Dropbox - for single version, we use the full path including version
            sync_path = f"{selected_model}/{selected_version}"
            self.sync_to_dropbox(sync_path, is_single_version=True)
        else:
            rprint("[yellow]No files were processed[/yellow]")

    def process_all_versions(self):
        """Handle processing of all versions for a selected model."""
        model_paths = self.list_model_paths()
        if not model_paths:
            return

        model_num = Prompt.ask("\nEnter number to select model path").strip()
        if not model_num:
            rprint("[red]Exited--no input given[/red]")
            return

        try:
            selected_model = model_paths[int(model_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return

        model_path = self.base_path / selected_model
        versions = [d.name for d in model_path.iterdir() if d.is_dir() and d.name != '.ipynb_checkpoints']

        if not versions:
            rprint(f"[yellow]No versions found for model {selected_model}[/yellow]")
            return

        total_processed = 0
        rprint(f"\n[cyan]Processing all versions of {selected_model}...[/cyan]")

        for version in sorted(versions, reverse=True):
            # Process versions in reverse order
            source_path = model_path / version
            dest_path = self.destination_base / selected_model / version

            rprint(f"[yellow]Processing version {version}...[/yellow]")
            files_processed = self.process_safetensors(source_path, dest_path, selected_model, version)
            total_processed += files_processed
    def verify_paths(self) -> bool:
            if total_processed > 0:
                self.show_progress("Processing complete", 100)
                rprint(f"[green]Successfully processed {total_processed} files across all versions![/green]")

            # Sync to Dropbox - for all versions, we sync the entire model directory
            self.sync_to_dropbox(selected_model, is_single_version=False)
        else:
            rprint("[yellow]No files were processed[/yellow]")

    def run(self):
        """Main execution method."""
        logging.info("Starting LoRA sync tool")
        try:
            self.clear_screen()  # Add this line
            if not self.verify_paths():
                logging.error("Path verification failed, exiting.")
                return
    
            rprint("[magenta]=== LoRA Model Management Tool ===[/magenta]")
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
        except Exception as e:
            logging.error(f"Error in run method: {e}")
            logging.error(traceback.format_exc())
            rprint(f"[red]An error occurred: {str(e)}[/red]")
        finally:
            logging.info("LoRA sync tool finished")


class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        print("Tool initialization started")  # Basic print for immediate feedback
        
        # Set up logging first
        log_dir = '/workspace/file-scripts/logs'
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, 'lora_sync.log')
        
        # Configure logging
        logging.basicConfig(
            filename=log_file,
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True  # Force reconfiguration of the root logger
        )
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(console_handler)
        
        logging.info("Starting Tool initialization")
        
        try:
            self.mover = LoRaMover()
            self.mover.base_path = self.workspace_path / 'SimpleTuner/output'
            self.mover.destination_base = self.workspace_path / 'StableSwarmUI/Models/loras/flux'
            
            logging.info(f"Tool initialized with base_path: {self.mover.base_path}")
            logging.info(f"Destination path: {self.mover.destination_base}")
            
            print("Tool initialization completed")  # Basic print for immediate feedback
            
        except Exception as e:
            print(f"Error during initialization: {str(e)}")  # Basic print for immediate feedback
            logging.error(f"Error initializing Tool: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def process(self):
        print("Starting process method")  # Basic print for immediate feedback
        try:
            self.clear_screen()
            logging.info("Starting tool process")
            
            if not self.verify_paths():
                logging.error("Path verification failed")
                self.exit_tool()
                return
                
            self.mover.run()
            
        except Exception as e:
            print(f"Error in process: {str(e)}")  # Basic print for immediate feedback
            logging.error(f"Critical error in tool process: {str(e)}")
            logging.error(traceback.format_exc())
            self.console.print("[red]Tool execution failed. Check logs for details.[/red]")
            self.exit_tool()