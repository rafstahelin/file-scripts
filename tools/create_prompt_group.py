import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.panel import Panel
from datetime import datetime
from collections import defaultdict

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTuner'
        self.templates_path = self.simpletuner_path / 'prompts' / 'templates'
        self.all_prompts: List[Tuple[str, str, Path, datetime]] = []  # (name, prompt, source_file, modified_date)
        self.selected_prompts: Dict[str, str] = {}

    def get_file_modified_time(self, file_path: Path) -> datetime:
        """Get last modified time of file as datetime object"""
        return datetime.fromtimestamp(file_path.stat().st_mtime)

    def load_all_prompts(self) -> None:
        """Load all prompts from all JSON files in templates directory"""
        if not self.templates_path.exists():
            self.console.print(f"[red]Templates directory not found: {self.templates_path}[/red]")
            return

        for file_path in self.templates_path.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompts = json.load(f)
                    modified_time = self.get_file_modified_time(file_path)
                    # Store each prompt with its source file and modification time
                    for name, prompt in prompts.items():
                        self.all_prompts.append((name, prompt, file_path, modified_time))
                        
                # Sort by modification time, newest first
                self.all_prompts.sort(key=lambda x: x[3], reverse=True)
                        
            except Exception as e:
                self.console.print(f"[red]Error loading {file_path.name}: {str(e)}[/red]")

    def display_prompts(self) -> None:
        """Display all available prompts in full-width panels, grouped by file and date"""
        if not self.all_prompts:
            self.console.print("[red]No prompts found[/red]")
            return

        self.console.print("\n[cyan]Available Prompts:[/cyan]")
        
        current_date = None
        current_file = None
        
        for idx, (name, prompt, source_file, modified_time) in enumerate(self.all_prompts, 1):
            # Format date string
            date_str = modified_time.strftime("%Y-%m-%d %H:%M")
            
            # If we're starting a new date/file group, print the header
            if date_str != current_date or source_file != current_file:
                self.console.print(f"\n[dim]{date_str} - {source_file.name}[/dim]")
                current_date = date_str
                current_file = source_file
            
            panel = Panel(
                prompt,  # Just display the prompt text
                title=f"[yellow]{idx}.[/yellow] {name}",  # Number and shortname in title
                border_style="blue",
                width=120
            )
            self.console.print(panel)

    def save_prompt_group(self, filename: str) -> None:
        """Save selected prompts to a new template file"""
        if not filename.endswith('.json'):
            filename += '.json'
        
        output_path = self.templates_path / filename
        
        try:
            # Create templates directory if it doesn't exist
            self.templates_path.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.selected_prompts, f, indent=4)
            
            self.console.print(f"[green]Successfully saved prompt group to {output_path}[/green]")
        
        except Exception as e:
            self.console.print(f"[red]Error saving prompt group: {str(e)}[/red]")

    def run(self) -> None:
        """Main execution method"""
        self.console.print("[cyan]Loading tool: create_prompt_group[/cyan]")
        
        # Load all available prompts
        self.load_all_prompts()
        
        # Main selection loop
        while True:
            self.display_prompts()
            
            # Show currently selected prompts
            if self.selected_prompts:
                self.console.print("\n[cyan]Selected Prompts:[/cyan]")
                for name in self.selected_prompts:
                    self.console.print(f"- {name}")
            
            choice = input("\nEnter number to select prompt (or press Enter to finish): ").strip()
            
            if not choice:
                if not self.selected_prompts:
                    self.console.print("[yellow]No prompts selected. Exiting...[/yellow]")
                    return
                break
                
            try:
                idx = int(choice)
                if 1 <= idx <= len(self.all_prompts):
                    # Get the prompt at the selected index
                    name, prompt, _, _ = self.all_prompts[idx - 1]
                    self.selected_prompts[name] = prompt
                    self.console.print(f"[green]Added prompt: {name}[/green]")
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
        
        # Get filename for the new template
        filename = input("\nEnter filename for the prompt group (without .json): ").strip()
        if filename:
            self.save_prompt_group(filename)