import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from datetime import datetime
import shutil
import traceback
from rich.text import Text
import time
import textwrap

def log_message(msg, error=False):
    """Write to log file with enhanced error information"""
    log_path = Path('/workspace/file-scripts/set_prompts.log')
    timestamp = datetime.now().isoformat()
    log_message = f"{timestamp} - {'ERROR' if error else 'INFO'}: {msg}\n"
    if error:
        log_message += f"{traceback.format_exc()}\n"
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a') as f:
            f.write(log_message)
    except Exception as e:
        print(f"Failed to write to log: {e}")

class SetPromptsUI:
    def __init__(self):
        self.console = Console()
        self.base_path = Path('/workspace/SimpleTuner/config')
        self.prompts_path = Path('/workspace/SimpleTuner/prompts')
        self.templates_path = self.prompts_path / 'templates'
        self.libraries_path = self.prompts_path / 'libraries'
        self.prompt_library = 'user_prompt_library.json'

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def wrap_panel_text(self, text: str, width: int) -> List[str]:
        """Wrap text for panel display with proper indentation"""
        wrapper = textwrap.TextWrapper(
            width=width,
            initial_indent='',
            subsequent_indent='    ',  # Add indentation for wrapped lines
            break_long_words=False,
            break_on_hyphens=False
        )
        return wrapper.wrap(text)

    def get_sorted_prompt_files(self, path: Path) -> Dict[str, Dict]:
        """Get prompt files sorted by last modified time"""
        files = {}
        if path.exists():
            # Get all JSON files with modification times
            json_files = [(f, f.stat().st_mtime) for f in path.glob('*.json')]
            # Sort by modification time, newest first
            sorted_files = sorted(json_files, key=lambda x: x[1], reverse=True)
            
            for file_path, _ in sorted_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files[file_path.stem] = json.load(f)
                except Exception as e:
                    log_message(f"Error loading file {file_path}: {str(e)}", error=True)
        return files

    def create_prompt_panel(self, content: List[str], title: str) -> Panel:
        """Create a panel with consistent formatting"""
        # Get terminal width and adjust panel width
        terminal_width = os.get_terminal_size().columns
        panel_width = min(terminal_width - 4, 100)  # Max width of 100, with padding
        
        return Panel(
            "\n".join(content),
            title=title,
            border_style="blue",
            width=panel_width,
            padding=(1, 2),  # Add consistent padding
            expand=False  # Prevent panel from expanding beyond width
        )

    def extract_family_name(self, config_path: Path) -> str:
        """Extract the family name from a config path"""
        base_name = config_path.parent.name
        return base_name.split('-')[0] if '-' in base_name else base_name

    def group_configs_by_family(self, configs: List[Path]) -> Dict[str, List[Path]]:
        """Group configs by their family name"""
        families = {}
        for config in configs:
            if "templates" in str(config.parent):
                continue
            family = self.extract_family_name(config)
            if family not in families:
                families[family] = []
            families[family].append(config)
        
        # Sort configs within each family by modification time
        for family in families:
            families[family].sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return families

    def create_family_panel(self, family_name: str, configs: List[Path], start_idx: int) -> Panel:
        """Create a panel for a family of configs"""
        content = []
        current_idx = start_idx
        
        for config in configs:
            env_name = config.parent.name
            content.append(f"[yellow]{current_idx}.[/yellow] {env_name}")
            current_idx += 1
        
        # Get terminal width and adjust panel width
        terminal_width = os.get_terminal_size().columns
        panel_width = min(terminal_width // 3 - 4, 60)  # Divide by 3 for three columns
        
        return Panel(
            "\n".join(content),
            title=f"[yellow]{family_name.upper()}[/yellow]",
            border_style="blue",
            width=panel_width
        )

    def display_configs(self, configs: List[Path]) -> List[Path]:
        """Display configs grouped by family and return flattened config list"""
        self.console.print("\n\n\n")  # Add 3 lines before section
        families = self.group_configs_by_family(configs)
        current_idx = 1
        panels = []
        all_configs = []
        
        for family_name, family_configs in sorted(families.items()):
            panel = self.create_family_panel(family_name, family_configs, current_idx)
            panels.append(panel)
            all_configs.extend(family_configs)
            current_idx += len(family_configs)
            
            if len(panels) == 3:
                self.console.print(Columns(panels, equal=True, expand=True))
                panels = []
        
        if panels:
            self.console.print(Columns(panels, equal=True, expand=True))
            
        self.console.print("\n\n\n")  # Add 3 lines after section
        return all_configs

    def display_prompt_files(self, title: str, prompt_files: Dict[str, Dict], start_index: int) -> List[Tuple[str, Dict]]:
        """Display prompt files in panels with full content"""
        log_message(f"Displaying {title} with {len(prompt_files)} files starting at index {start_index}")
        
        # Get terminal width
        terminal_width = os.get_terminal_size().columns
        panel_width = terminal_width - 4  # Account for borders
        
        # Add 3 lines before title
        self.console.print("\n\n\n")
        self.console.print(f"[cyan]{title}[/cyan]")
        # Add 3 lines after title
        self.console.print("\n\n\n")
        
        all_prompts = []
        current_index = start_index
    
        try:
            if not isinstance(prompt_files, dict):
                log_message(f"Error: prompt_files is not a dictionary. Got {type(prompt_files)}")
                return []
    
            for filename, prompts in prompt_files.items():
                log_message(f"Processing {filename}")
                content = []
                
                for prompt_name, prompt_text in prompts.items():
                    # Format the prompt name with proper coloring
                    parts = prompt_name.split('_')
                    formatted_parts = []
                    
                    for part in parts:
                        if part == 'token':
                            formatted_parts.append(f"[magenta]{part}[/magenta]")
                        else:
                            formatted_parts.append(f"[yellow]{part}[/yellow]")
                    
                    formatted_name = "_".join(formatted_parts)
                    
                    # Create the prompt line and wrap it
                    prompt_line = f"{formatted_name}: {prompt_text}"
                    wrapped_lines = self.wrap_panel_text(prompt_line, panel_width-4)
                    content.extend(wrapped_lines)
                    content.append("")  # Add blank line between prompts
    
                panel = self.create_prompt_panel(
                    content,
                    f"[yellow]{current_index}.[/yellow] {filename}"
                )
                self.console.print(panel)
                all_prompts.append((filename, prompts))
                current_index += 1
    
        except Exception as e:
            log_message(f"Error in display_prompt_files: {str(e)}", error=True)
            raise
    
        return all_prompts

    def run(self):
        try:
            self.console.print("[cyan]Loading tool: set_prompts[/cyan]\n")

            # Get and validate config files
            if not self.base_path.exists():
                raise FileNotFoundError(f"Config directory not found: {self.base_path}")
            
            configs = list(self.base_path.glob("**/config.json"))
            configs = [c for c in configs if "templates" not in str(c)]
            
            if not configs:
                raise FileNotFoundError("No config files found")

            # Display configs and get selection
            log_message("Found config files")
            all_configs = self.display_configs(configs)

            while True:
                try:
                    self.console.print("\nSelect config number (or press Ctrl+C to exit): ")
                    config_input = input().strip()
                    if not config_input:
                        continue
                    config_num = int(config_input)
                    if 1 <= config_num <= len(all_configs):
                        break
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number.[/red]")

            selected_config = all_configs[config_num - 1]
            self.clear_screen()

            # Load prompts
            templates = self.get_sorted_prompt_files(self.templates_path)
            libraries = self.get_sorted_prompt_files(self.libraries_path)

            if not templates and not libraries:
                raise FileNotFoundError("No prompts found in templates or libraries")

            # Display prompts
            template_prompts = []
            if templates:
                log_message(f"Displaying {len(templates)} templates...")
                template_prompts = self.display_prompt_files("Templates", templates, 1)
                log_message(f"Displayed {len(template_prompts)} template sets")

            library_prompts = []
            if libraries:
                log_message(f"Displaying {len(libraries)} libraries...")
                library_prompts = self.display_prompt_files("Libraries", libraries, len(template_prompts) + 1)
                log_message(f"Displayed {len(library_prompts)} library sets")

            # Add a small pause to ensure display is visible
            time.sleep(0.5)

            all_prompts = template_prompts + library_prompts
            
            # Get prompt selection
            while True:
                try:
                    self.console.print("\nSelect prompt set number (or press Ctrl+C to exit): ")
                    prompt_input = input().strip()
                    if not prompt_input:
                        continue
                    prompt_num = int(prompt_input)
                    if 1 <= prompt_num <= len(all_prompts):
                        break
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number.[/red]")

            # Process selection and save
            filename, prompts = all_prompts[prompt_num - 1]
            is_template = prompt_num <= len(template_prompts)

            if is_template:
                base_name = selected_config.parent.name.split('-')[0]
                processed_prompts = {
                    k.replace('token', base_name): v.replace('token', base_name)
                    for k, v in prompts.items()
                }
            else:
                processed_prompts = prompts

            # Backup and save
            library_path = selected_config.parent / self.prompt_library
            if library_path.exists():
                backup_path = library_path.with_suffix('.json.bak')
                shutil.copy2(library_path, backup_path)
                log_message(f"Created backup at {backup_path}")

            with open(library_path, 'w', encoding='utf-8') as f:
                json.dump(processed_prompts, f, indent=2)
            log_message(f"Saved prompt library to {library_path}")
            self.console.print(f"[green]Successfully updated {self.prompt_library}[/green]")

        except Exception as e:
            log_message(str(e), error=True)
            self.console.print(f"[red]Error: {str(e)}[/red]")
            self.console.print("[red]Check the log file for details: /workspace/file-scripts/set_prompts.log[/red]")

class Tool:
    def __init__(self):
        self.ui = SetPromptsUI()

    def run(self):
        self.ui.run()

if __name__ == "__main__":
    try:
        tool = Tool()
        tool.run()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        traceback.print_exc()