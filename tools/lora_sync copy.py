import os
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import subprocess

class Tool:

    def __init__(self):
        self.console = Console()
        self.source = Path('/workspace/ComfyUI/models/loras/flux')
        self.dropbox_base = 'dbx:/studio/ai/libs/SD/loras/flux'

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

        return folders

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
