import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
import tiktoken
from datetime import datetime

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTuner'
        self.templates_path = self.simpletuner_path / 'prompts' / 'templates'
        self.panel_width = 40
        # Initialize GPT-4 tokenizer
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken"""
        return len(self.tokenizer.encode(text))

    def get_file_modified_time(self, file_path: Path) -> str:
        """Get formatted last modified time of file"""
        timestamp = datetime.fromtimestamp(file_path.stat().st_mtime)
        return timestamp.strftime("%Y-%m-%d %H:%M")

    def load_template_file(self, file_path: Path) -> Dict[str, int]:
        """Load template file and return dict of shortnames and token counts"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    name: self.count_tokens(prompt)
                    for name, prompt in data.items()
                }
        except Exception as e:
            self.console.print(f"[red]Error loading {file_path.name}: {str(e)}[/red]")
            return {}

    def get_template_files(self) -> List[Tuple[Path, Dict[str, int]]]:
        """Get all template files and their prompt contents"""
        if not self.templates_path.exists():
            self.console.print(f"[red]Templates directory not found: {self.templates_path}[/red]")
            return []

        template_files = []
        for file_path in sorted(self.templates_path.glob('*.json')):
            prompts = self.load_template_file(file_path)
            if prompts:
                template_files.append((file_path, prompts))
        return template_files

    def create_template_panel(self, file_path: Path, prompts: Dict[str, int], index: int) -> Panel:
        """Create a panel displaying template shortnames and token counts"""
        content_lines = []
        
        # Add prompt names and token counts
        for name, token_count in prompts.items():
            content_lines.append(f"[yellow]{name}[/yellow]: {token_count} tokens")
        
        # Add last modified time at the bottom
        last_modified = self.get_file_modified_time(file_path)
        content_lines.append(f"\n[dim]Last modified: {last_modified}[/dim]")
        
        content = "\n".join(content_lines)
        return Panel(
            content,
            title=f"[yellow]{index}.[/yellow] {file_path.stem}",
            border_style="blue",
            width=self.panel_width
        )

    def display_templates(self, template_files: List[Tuple[Path, Dict[str, int]]]) -> None:
        """Display template files in panels, 3 per row"""
        if not template_files:
            self.console.print("[red]No template files found[/red]")
            return

        self.console.print("[cyan]Templates[/cyan]")
        
        # Create panels in groups of 3
        current_row = []
        for idx, (file_path, prompts) in enumerate(template_files, 1):
            panel = self.create_template_panel(file_path, prompts, idx)
            current_row.append(panel)
            
            if len(current_row) == 3:
                self.console.print(Columns(current_row, equal=True, expand=True))
                current_row = []
        
        # Display any remaining panels
        if current_row:
            self.console.print(Columns(current_row, equal=True, expand=True))

    def save_prompts_to_config(self, template_file: Path) -> None:
        """Save selected prompts to config"""
        try:
            # Load the template file
            with open(template_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            # Get the config directory path
            config_dir = self.simpletuner_path / 'config'
            if not config_dir.exists():
                self.console.print(f"[red]Config directory not found: {config_dir}[/red]")
                return

            # Create backup of existing file if it exists
            output_file = config_dir / 'user_prompt_library.json'
            if output_file.exists():
                backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = config_dir / f'user_prompt_library.{backup_time}.json'
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2)

            # Save new prompts
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2)
            
            self.console.print(f"[green]Successfully saved prompts to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error saving prompts: {str(e)}[/red]")

    def run(self) -> None:
        """Main execution method"""
        self.console.print("[cyan]Loading tool: set_prompts[/cyan]")
        
        # Get and display templates
        template_files = self.get_template_files()
        self.display_templates(template_files)

        # Get user selection
        while True:
            choice = input("\nEnter number to select template: ").strip()
            
            if not choice:
                break

            try:
                idx = int(choice)
                if 1 <= idx <= len(template_files):
                    template_file, _ = template_files[idx - 1]
                    self.save_prompts_to_config(template_file)
                    break
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
                break