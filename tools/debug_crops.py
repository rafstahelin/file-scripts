import os
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

class Tool:
    def __init__(self):
        self.console = Console()
        self.config_path = Path('/workspace/SimpleTuner/config')
        self.base_path = Path('/workspace/SimpleTuner')
        
    def clear_screen(self):
        """Clear terminal screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def verify_paths(self) -> bool:
        """Verify that required paths exist."""
        missing = []
        for path in [self.config_path, self.base_path]:
            if not path.exists():
                missing.append(str(path))
        
        if missing:
            rprint("[red]Error: The following paths do not exist:[/red]")
            for path in missing:
                rprint(f"[red]- {path}[/red]")
            return False
            
        # Check if train.sh exists
        if not (self.base_path / 'train.sh').exists():
            rprint("[red]Error: train.sh not found in SimpleTuner directory[/red]")
            return False
            
        return True

    def show_progress(self, description: str, progress_task=None) -> None:
        """Show a progress bar with the given description."""
        if progress_task:
            progress_task.update(description=description)
        else:
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(complete_style="green"),
                TaskProgressColumn(),
                console=self.console,
                transient=True
            ) as progress:
                task = progress.add_task(description, total=100)
                while not progress.finished:
                    progress.update(task, advance=1)
                    import time
                    time.sleep(0.02)

    def list_tokens(self) -> List[str]:
        """List all configuration tokens."""
        try:
            tokens = set()
            for path in self.config_path.iterdir():
                if path.is_dir() and path.name != '.ipynb_checkpoints':
                    tokens.add(path.name.split('-')[0])
            
            if not tokens:
                rprint("[yellow]No configuration tokens found[/yellow]")
                return []
            
            # Create single panel with all tokens
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            ordered_tokens = sorted(list(tokens))
            for idx, token in enumerate(ordered_tokens, 1):
                table.add_row(f"[yellow]{idx}. {token}[/yellow]")
            
            # Create panel with title
            panel = Panel(table, title=f"[magenta]Available Tokens[/magenta]", 
                         border_style="blue", width=36)
            
            # Display with two empty panels for consistent layout
            panels = [
                panel,
                Panel("", border_style="blue", width=36),
                Panel("", border_style="blue", width=36)
            ]
            self.console.print(Columns(panels, equal=True, expand=True))
            
            return ordered_tokens
            
        except Exception as e:
            rprint(f"[red]Error scanning tokens: {str(e)}[/red]")
            return []

    def run_debug_crops(self, token: str) -> bool:
        """Run the debug crops command with the specified token."""
        try:
            # First clean images directory
            clean_cmd = "rm -rf images/*"
            
            # Debug command with environment variables
            debug_cmd = (
                "env SIMPLETUNER_DEBUG_IMAGE_PREP=true "
                "SIMPLETUNER_DISABLE_ACCELERATOR=true "
                f"ENV={token} bash train.sh"
            )
            
            # Display commands that will be run
            rprint("\n[cyan]Will execute the following commands:[/cyan]")
            rprint(f"[yellow]1. {clean_cmd}[/yellow]")
            rprint(f"[yellow]2. {debug_cmd}[/yellow]")
            
            # Confirm execution
            confirm = Prompt.ask(
                "\nProceed with debug crops?",
                choices=["y", "n"],
                default="n"
            )
            
            if confirm.lower() == 'y':
                # Change to SimpleTuner directory
                os.chdir(self.base_path)
                
                with Progress(
                    TextColumn("[bold blue]{task.description}"),
                    BarColumn(complete_style="green"),
                    TaskProgressColumn(),
                    console=self.console,
                    transient=True
                ) as progress:
                    # Clean images directory
                    task = progress.add_task("Cleaning images directory...", total=100)
                    process = subprocess.run(
                        clean_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    if process.returncode != 0:
                        rprint(f"[red]Error cleaning images directory: {process.stderr}[/red]")
                        return False
                        
                    progress.update(task, completed=100)
                    
                    # Run debug command
                    task = progress.add_task("Running debug crops...", total=None)
                    process = subprocess.Popen(
                        debug_cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        bufsize=1,
                        universal_newlines=True
                    )
                    
                    # Show output in real-time
                    rprint("\n[cyan]Debug Output:[/cyan]")
                    while True:
                        output = process.stdout.readline()
                        if output == '' and process.poll() is not None:
                            break
                        if output:
                            rprint(f"[white]{output.strip()}[/white]")
                    
                    # Get final return code
                    return_code = process.wait()
                    
                    if return_code == 0:
                        rprint("\n[green]Debug crops completed successfully![/green]")
                        rprint("[cyan]Check the 'images' directory for results.[/cyan]")
                        return True
                    else:
                        stderr = process.stderr.read()
                        rprint(f"\n[red]Error during debug crops: {stderr}[/red]")
                        return False
            else:
                rprint("[yellow]Operation cancelled[/yellow]")
                return False
                
        except Exception as e:
            rprint(f"[red]Error running debug crops: {str(e)}[/red]")
            return False

    def run(self):
        """Main execution method."""
        self.clear_screen()
        
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Debug Crops Tool ===[/magenta]\n")
        
        # List and select token
        rprint("[cyan]Available Configuration Tokens:[/cyan]")
        tokens = self.list_tokens()
        if not tokens:
            return
            
        token_num = Prompt.ask("\nEnter number to select token").strip()
        if not token_num:
            rprint("[red]Exited--no input given[/red]")
            return
            
        try:
            selected_token = tokens[int(token_num) - 1]
        except (ValueError, IndexError):
            rprint("[red]Invalid selection[/red]")
            return
            
        # Run debug crops with selected token
        self.run_debug_crops(selected_token)

if __name__ == "__main__":
    tool = Tool()
    tool.run()