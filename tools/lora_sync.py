import os
import subprocess
from pathlib import Path
from typing import List
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt
from .base_tool import BaseTool
import logging

class LoraSync:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/ComfyUI/models/loras/flux')
        self.dropbox_path = "dbx:/studio/ai/libs/diffusion-models/models/loras/flux"

    def verify_paths(self) -> bool:
        """Verify that required paths exist and Dropbox is accessible."""
        try:
            if not self.base_path.exists():
                rprint(f"[red]Error: Local path {self.base_path} does not exist[/red]")
                return False
            
            # Quick dbx connection check
            result = subprocess.run(
                ["rclone", "lsf", "dbx:/", "--max-depth", "1"],
                check=True,
                capture_output=True,
                timeout=10
            )
            return True
            
        except subprocess.TimeoutExpired:
            rprint("[red]Error: Dropbox connection check timed out.[/red]")
            return False
        except subprocess.CalledProcessError:
            rprint("[red]Error: Cannot connect to Dropbox. Please check your rclone configuration.[/red]")
            return False
        except Exception as e:
            rprint(f"[red]Error checking paths: {str(e)}[/red]")
            return False

    def list_model_families(self) -> List[str]:
        """List available model families in the flux directory."""
        try:
            families = [f.name for f in self.base_path.iterdir() 
                       if f.is_dir() and not f.name.startswith('.')]
            if not families:
                rprint("[yellow]No model families found[/yellow]")
                return []
            return self._display_items_in_panels(families, "Available Models")
        except Exception as e:
            rprint(f"[red]Error listing models: {str(e)}[/red]")
            return []

    def list_versions(self, family: str) -> List[str]:
        """List available versions for a model family."""
        try:
            family_path = self.base_path / family
            versions = [f.name for f in family_path.iterdir() 
                       if f.is_dir() and not f.name.startswith('.')]
            if not versions:
                rprint(f"[yellow]No versions found for {family}[/yellow]")
                return []
            return self._display_items_in_panels(versions, f"Available Versions for {family}")
        except Exception as e:
            rprint(f"[red]Error listing versions: {str(e)}[/red]")
            return []

    def _display_items_in_panels(self, items: List[str], title: str) -> List[str]:
        """Display items in organized panels."""
        is_versions_display = "Versions" in title
        if is_versions_display:
            # Single panel for versions
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            model_name = title.split("for ")[-1]
            ordered_items = sorted(items, key=str.lower, reverse=True)
            
            for idx, item in enumerate(ordered_items, 1):
                table.add_row(f"[yellow]{idx}. {item}[/yellow]")
            
            panel = Panel(table, title=f"[magenta]{model_name}[/magenta]", 
                         border_style="blue", width=36)
            panels = [panel] + [Panel("", border_style="blue", width=36) for _ in range(2)]
            self.console.print(Columns(panels, equal=True, expand=True))
            return ordered_items
        else:
            # Group families by name
            grouped = {}
            for item in sorted(items):
                base_name = item.split('-', 1)[0]
                grouped.setdefault(base_name, []).append(item)

            panels = []
            ordered_items = []
            index = 1

            for base_name in sorted(grouped.keys()):
                table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
                table.add_column(justify="left", max_width=30)
                
                for item in sorted(grouped[base_name], key=str.lower):
                    table.add_row(f"[yellow]{index}. {item}[/yellow]")
                    ordered_items.append(item)
                    index += 1

                panels.append(Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                                  border_style="blue", width=36))

            # Display panels in rows of 3
            for i in range(0, len(panels), 3):
                row_panels = panels[i:i + 3]
                while len(row_panels) < 3:
                    row_panels.append(Panel("", border_style="blue", width=36))
                self.console.print(Columns(row_panels, equal=True, expand=True))

            return ordered_items

    def sync_to_dropbox(self, path: str) -> bool:
        """Sync a model family or version to Dropbox."""
        try:
            source = str(self.base_path / path)
            destination = f"{self.dropbox_path}/{path}"
            
            rprint(f"\n[cyan]Starting sync from:[/cyan] {source}")
            rprint(f"[cyan]To:[/cyan] {destination}")
            
            cmd = [
                "rclone",
                "sync",
                "--progress",
                source,
                destination
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # Show output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    
            if process.returncode == 0:
                rprint("\n[green]Sync completed successfully![/green]")
                return True
            else:
                rprint("\n[red]Error during sync process[/red]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error during sync: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        if not self.verify_paths():
            return

        while True:
            rprint("[magenta]=== LoRA Sync Tool ===[/magenta]")
            rprint("\n[cyan]Select sync mode:[/cyan]")
            rprint("[yellow]1. Sync single version[/yellow]")
            rprint("[yellow]2. Sync all versions of a model family[/yellow]")
            rprint("[cyan]Press Enter to exit[/cyan]")
            
            choice = Prompt.ask("\nEnter choice").strip()
            if not choice:
                rprint("[yellow]Exiting...[/yellow]")
                return
                
            families = self.list_model_families()
            if not families:
                continue
                
            family_num = Prompt.ask("\nEnter number to select model family (or press Enter to return)").strip()
            if not family_num:
                continue
                
            try:
                selected_family = families[int(family_num) - 1]
            except (ValueError, IndexError):
                rprint("[red]Invalid selection[/red]")
                continue
                
            if choice == "1":
                versions = self.list_versions(selected_family)
                if not versions:
                    continue
                    
                version_num = Prompt.ask("\nEnter number to select version (or press Enter to return)").strip()
                if not version_num:
                    continue
                    
                try:
                    selected_version = versions[int(version_num) - 1]
                    sync_path = f"{selected_family}/{selected_version}"
                except (ValueError, IndexError):
                    rprint("[red]Invalid selection[/red]")
                    continue
                    
            else:  # Sync entire family
                sync_path = selected_family
                
            self.sync_to_dropbox(sync_path)
            input("\nPress Enter to continue...")


class Tool(BaseTool):
    def __init__(self):
        super().__init__()
        self.sync_tool = LoraSync()
        
    def process(self):
        try:
            self.sync_tool.run()
        except Exception as e:
            print(f"Error: {str(e)}")
            input("\nPress Enter to continue...")