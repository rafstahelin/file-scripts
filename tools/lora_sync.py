import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import subprocess

class Tool:

    def __init__(self):
        self.console = Console()
<<<<<<< HEAD
        self.source = Path('/workspace/ComfyUI/models/loras/flux')
        self.dropbox_base = 'dbx:/studio/ai/libs/SD/loras/flux'
=======
        logging.info("Console initialized")
        self.base_path = Path.cwd()
        logging.info(f"Base path set to: {self.base_path}")
        self.destination_base = Path('/workspace/ComfyUI/models/loras/flux')
        logging.info(f"Destination base set to: {self.destination_base}")
        self.metadata_handler = MetadataHandler()
        logging.info("Metadata handler initialized")
        logging.info("LoRaMover __init__ completed")
>>>>>>> main

    def list_folders(self, path):
        """List folders in the given path."""
        try:
            skip_dirs = {'templates', '.ipynb_checkpoints'}
            folders = [f for f in path.iterdir() if f.is_dir() and f.name not in skip_dirs]
        except FileNotFoundError:
            self.console.print(f"[red]The path '{path}' does not exist.[/red]")
            return []

        if not folders:
            self.console.print(f"[red]No folders found in {path}.[/red]")
            return []

        folders = sorted(folders, key=lambda x: x.name.lower())

        # Clear the screen
        self.console.clear()

        # Display folders using a rich panel
        folder_names = "\n".join([f"{i + 1}. {folder.name}" for i, folder in enumerate(folders)])
        panel = Panel(folder_names, title=f"Folders in {path}", title_align="left", border_style="blue", width=36)

        self.console.print(panel)

<<<<<<< HEAD
        return folders
=======
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
        source_path = model_path / version
        dest_path = self.destination_base / selected_model / version

        rprint(f"[yellow]Processing version {version}...[/yellow]")
        files_processed = self.process_safetensors(source_path, dest_path, selected_model, version)
        total_processed += files_processed

    if total_processed > 0:
        self.show_progress("Processing complete", 100)
        rprint(f"[green]Successfully processed {total_processed} files across all versions![/green]")
        self.sync_to_dropbox(selected_model, is_single_version=False)
    else:
        rprint("[yellow]No files were processed[/yellow]")

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
        files_processed = self.process_safetensaors(source_path, dest_path, selected_model, version)
        total_processed += files_processed

    if total_processed > 0:
        self.show_progress("Processing complete", 100)
        rprint(f"[green]Successfully processed {total_processed} files across all versions![/green]")
        # Sync to Dropbox - for all versions, we sync the entire model directory
        self.sync_to_dropbox(selected_model, is_single_version=False)
    else:
        rprint("[yellow]No files were processed[/yellow]")

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

            if total_processed > 0:
                self.show_progress("Processing complete", 100)
                rprint(f"[green]Successfully processed {total_processed} files across all versions![/green]")

            # Sync to Dropbox - for all versions, we sync the entire model directory
            self.sync_to_dropbox(selected_model, is_single_version=False)
            else:
            rprint("[yellow]No files were processed[/yellow]")
>>>>>>> main

    def run(self):
        """Run the folder selection tool."""

        os.system('clear' if os.name == 'posix' else 'cls')

        current_path = self.source
        path_history = []

        sfi = None
        dfi = None

        print("\n")
        self.console.print("[magenta]=== RClone ===[/magenta]")

        while True:
            try:
                # List folders in the current path
                folders = self.list_folders(current_path)

                if not folders:
                    self.console.print("[yellow]No folders found. Exiting tool.[/yellow]")
                    return

                # Map input numbers to folder paths
                folder_map = {i + 1: folders[i] for i in range(len(folders))}

                # Prompt user to select a folder
                self.console.print("\n[yellow]Select a folder to sync, navigate into, (b) Back, or (q) Quit[/yellow]")
                selection = input(f"\nEnter your choice for {current_path}:   ")

                if selection.lower() in ("q", "quit"):
                    self.console.print("[green]Exiting tool.[/green]")
                    return

                if selection.lower() in ("b", "back"):
                    if path_history:
                        current_path = path_history.pop()
                        self.console.print(f"[cyan]Returning to:[/cyan] {current_path}")
                    else:
                        self.console.print("[red]No previous folder to go back to.[/red]")
                    continue

                # Handle folder selection
                try:
                    selection = int(selection)
                    if selection not in folder_map:
                        raise ValueError
                except ValueError:
                    self.console.print("[red]Invalid selection! Please enter a valid number.[/red]")
                    continue

                # Get the selected folder
                selected_folder = folder_map[selection]

                # Check for subfolders in the selected folder
                subfolders = self.list_folders(selected_folder)
                if subfolders:
                    path_history.append(current_path)
                    self.console.print(f"[cyan]Navigating into folder:[/cyan] {selected_folder}")
                    current_path = selected_folder
                    continue

                # If no subfolders, proceed with sync
                sfi = selected_folder

                # Calculate the destination folder
                relative_path = sfi.relative_to(self.source)
                dfi = Path(self.dropbox_base) / relative_path

                self.console.print(f"[cyan]Selected source folder:[/cyan] {sfi}")
                self.console.print(f"[cyan]Destination folder:[/cyan] {dfi}")

                if sfi and dfi:
                    command = [
                        "rclone", "sync",
                        "--include", "*.safetensors",
                        "--checksum", "--verbose",
                        str(sfi), str(dfi)
                    ]
                    self.console.print(f"\n[yellow]Executing command:[/yellow] {' '.join(command)}")
                    result = subprocess.run(command, text=True)
                    self.console.print(f"[blue]{result.stdout}[/blue]")
                    self.console.print(f"[red]{result.stderr}[/red]")

                    while True:
                        choice = input("\nPerform another operation or go back? (b to go back, q to quit): ").lower()
                        if choice == "b":
                            current_path = path_history.pop() if path_history else self.source
                            break
                        elif choice == "q":
                            self.console.print("[green]Exiting tool.[/green]")
                            return
                        else:
                            self.console.print("[red]Invalid choice! Please enter 'b' or 'q'.[/red]")

            except KeyboardInterrupt:
                self.console.print("\n[red]Process interrupted by user.[/red]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()
