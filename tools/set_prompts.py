import os
import json
import time
from pathlib import Path
from typing import Dict, List, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
from rich import print as rprint

import tiktoken

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTuner'
        self.templates_path = self.simpletuner_path / 'prompts' / 'templates'
        self.config_path = self.simpletuner_path / 'config'   # Root path for configs
        self.panel_width = 40
        # Initialize GPT-4 tokenizer
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.target_config_dir: Path = None

    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
        
    def list_folders(self) -> List[str]:
        """List folders in the config directory, similar to ConfigManager.list_folders."""
        self.clear_screen()
        rprint("[magenta]=== Select a Configuration Folder ===[/magenta]\n")
        
        # Folders to list: all directories under config_path except 'templates' and '.ipynb_checkpoints'
        folders = [
            f for f in self.config_path.iterdir() 
            if f.is_dir() and f.name not in ['templates', '.ipynb_checkpoints']
        ]
        
        if not folders:
            rprint("[red]No configuration folders found.[/red]")
            return []
        
        grouped = {}
        ordered_folders = []
        panels = []
        index = 1
        
        for folder in folders:
            base_name = folder.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(folder.name)
        
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
            for name in names_in_group:
                table.add_row(f"[yellow]{index}. {name}[/yellow]")
                ordered_folders.append(name)
                index += 1

            panel = Panel(table, title=f"[magenta]{base_name}[/magenta]", 
                          border_style="blue", width=36)
            panels.append(panel)
        
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))
            
        return ordered_folders

    def select_target_directory(self) -> bool:
        """Prompt the user to select a target configuration directory."""
        folders = self.list_folders()
        if not folders:
            return False
        
        folder_num_input = Prompt.ask("Enter number to select target folder").strip()
        if not folder_num_input:
            rprint("[red]Exited--no input given[/red]")
            return False

        try:
            folder_num = int(folder_num_input)
            selected_dir_name = folders[folder_num - 1]
            self.target_config_dir = self.config_path / selected_dir_name
            rprint(f"[cyan]Using target configuration directory: {self.target_config_dir}[/cyan]")
            return True
        except (IndexError, ValueError):
            rprint("[red]Invalid selection. Please try again.[/red]")
            return False

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer.encode(text))

    def get_file_modified_time(self, file_path: Path) -> str:
        timestamp = file_path.stat().st_mtime
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp))

    def load_template_file(self, file_path: Path) -> Dict[str, int]:
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
        content_lines = []
        for name, token_count in prompts.items():
            content_lines.append(f"[yellow]{name}[/yellow]: {token_count} tokens")
        
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
        if not template_files:
            self.console.print("[red]No template files found[/red]")
            return

        self.console.print("[cyan]Templates[/cyan]")
        
        current_row = []
        for idx, (file_path, prompts) in enumerate(template_files, 1):
            panel = self.create_template_panel(file_path, prompts, idx)
            current_row.append(panel)
            
            if len(current_row) == 3:
                self.console.print(Columns(current_row, equal=True, expand=True))
                current_row = []
        
        if current_row:
            self.console.print(Columns(current_row, equal=True, expand=True))

    def process_user_prompt_library(self, filepath: Path, token_name: str, existing_token: str = None) -> None:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            updated_data = {}
            for key, value in data.items():
                if existing_token:
                    new_key = key.replace(existing_token, token_name) if existing_token != token_name else key
                    updated_data[new_key] = (
                        value.replace(existing_token, token_name) if existing_token != token_name else value
                    )
                else:
                    new_key = key.replace('__TOKEN_NAME__', token_name).replace('_TOKEN_NAME_', token_name)
                    updated_data[new_key] = value.replace('__TOKEN_NAME__', token_name).replace('_TOKEN_NAME_', token_name)

            with open(filepath, 'w') as f:
                json.dump(updated_data, f, indent=2)
                
        except Exception as e:
            rprint(f"[red]Error processing user_prompt_library.json: {str(e)}[/red]")

    def save_prompts_to_config(self, template_file: Path) -> None:
        if not self.target_config_dir:
            self.console.print("[red]No target config directory selected.[/red]")
            return

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            
            config_dir = self.target_config_dir
            if not config_dir.exists():
                self.console.print(f"[red]Config directory not found: {config_dir}[/red]")
                return

            output_file = config_dir / 'user_prompt_library.json'

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(prompts, f, indent=2)
            
            # If token name is derivable from the folder name, process it
            token_name = os.path.basename(config_dir).split('-')[0]
            self.process_user_prompt_library(output_file, token_name, None)

            self.console.print(f"[green]Successfully saved prompts to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error saving prompts: {str(e)}[/red]")

    def run(self) -> None:
        self.console.print("[cyan]Loading Prompts Tool[/cyan]")
        
        # Select target config directory first
        if not self.select_target_directory():
            return

        template_files = self.get_template_files()
        if not template_files:
            return
        self.display_templates(template_files)

        choice = Prompt.ask("\nEnter number to select template (or press Enter to skip)", default="")
        if not choice:
            return

        try:
            idx = int(choice)
            if 1 <= idx <= len(template_files):
                template_file, _ = template_files[idx - 1]
                self.save_prompts_to_config(template_file)
            else:
                self.console.print("[red]Invalid selection. Please try again.[/red]")
        except ValueError:
            self.console.print("[red]Please enter a valid number.[/red]")
        except Exception as e:
            self.console.print(f"[red]Error: {str(e)}[/red]")
