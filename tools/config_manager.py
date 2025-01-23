import os
import json
import shutil
import time
import sys
import tty
import termios
from contextlib import contextmanager
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
from rich import print as rprint

import tiktoken

###############################################
# Part 1: ConfigManager (from the third snippet)
###############################################

class ConfigManager:
    def __init__(self):
        self.console = Console()
        self.templates_path = Path('/workspace/SimpleTuner/config/templates')
        self.root_path = Path('/workspace/SimpleTuner/config')
        
    def verify_paths(self) -> bool:
        required_paths = {
            'config': self.root_path,
            'templates': self.templates_path,
            'datasets': self.root_path.parent / 'datasets'
        }
        
        missing = []
        for name, path in required_paths.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
                
        if missing:
            rprint("[red]Error: The following required paths do not exist:[/red]")
            for path in missing:
                rprint(f"[red]- {path}[/red]")
            return False
            
        return True
        
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def show_rainbow_progress(self, description: str) -> None:
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
                time.sleep(0.02)

    def getch(self):
        if sys.platform.startswith('win'):
            import msvcrt
            return msvcrt.getch().decode('utf-8')
        else:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch

    def get_yes_no_input(self, prompt_text: str) -> str:
        print(f"{prompt_text} [y/n]: ", end='', flush=True)
        while True:
            ch = self.getch()
            if ch.lower() in ('y', 'n'):
                print(ch)
                return ch.lower()
            else:
                print("\n[red]Invalid input. Please enter 'y' or 'n'.[/red]")
                print(f"{prompt_text} [y/n]: ", end='', flush=True)

    def list_folders(self) -> list:
        folders = [f for f in self.root_path.iterdir() 
                   if f.is_dir() and f.name not in ['templates', '.ipynb_checkpoints']]
        
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
        
    def list_templates(self) -> list:
        if not self.templates_path.exists():
            rprint(f"[yellow]Warning: Templates directory {self.templates_path} not found.[/yellow]")
            return []

        templates = [f for f in self.templates_path.iterdir() 
                     if f.is_dir() and f.name != '.ipynb_checkpoints']
        
        grouped = {}
        ordered_templates = []
        index = 1
        
        for template in templates:
            base_name = template.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(template.name)
            ordered_templates.append(template.name)

        panels = []
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
            for name in names_in_group:
                table.add_row(f"[yellow]{index}. {name}[/yellow]")
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
        
        return ordered_templates

    def list_datasets(self) -> list:
        datasets_path = self.root_path.parent / 'datasets'
        if not datasets_path.exists():
            rprint(f"[yellow]Warning: Datasets directory {datasets_path} not found.[/yellow]")
            return []
            
        datasets = [folder.name for folder in datasets_path.iterdir() 
                    if folder.is_dir() and folder.name != '.ipynb_checkpoints']
        
        grouped = {}
        ordered_datasets = []
        index = 1
        
        for dataset in sorted(datasets):
            base_name = dataset.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(dataset)
            ordered_datasets.append(dataset)
    
        panels = []
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            
            names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
            for name in names_in_group:
                table.add_row(f"[yellow]{index}. {name}[/yellow]")
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
        
        return ordered_datasets

    def parse_folder_name(self, folder: str) -> Tuple[str, str]:
        parts = folder.split('-', 1)
        return parts[0], parts[1] if len(parts) > 1 else ''

    def process_config_json(self, filepath: Path, token_name: str, new_version: str, old_version: Optional[str] = None) -> None:
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            if old_version:
                content = content.replace(f"{token_name}-{old_version}", f"{token_name}-{new_version}")
                content = content.replace(f"{token_name}/{old_version}", f"{token_name}/{new_version}")
            else:
                replacements = {
                    '__TOKEN_NAME__': token_name,
                    '__TOKEN_NAME_VERSION__': f"{token_name}-{new_version}",
                    '__VERSION_NUMBER__': new_version,
                }
                for old, new in replacements.items():
                    content = content.replace(old, new)

            with open(filepath, 'w') as f:
                f.write(content)
                
        except Exception as e:
            rprint(f"[red]Error processing config.json: {str(e)}[/red]")

    def process_user_prompt_library(self, filepath: Path, token_name: str, existing_token: Optional[str] = None) -> None:
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

    def process_multidatabackend(self, filepath: Path, token_name: str, dataset_name: str) -> None:
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            cache_dir_name = f"{token_name}-{dataset_name}"
            for item in data:
                if isinstance(item, dict):
                    if 'instance_data_dir' in item:
                        item['instance_data_dir'] = f"datasets/{dataset_name}"
                    if 'cache_dir_vae' in item:
                        item['cache_dir_vae'] = f"cache/vae/{cache_dir_name}/{item.get('id', '')}"
                    elif item.get('id') == 'text_embeds':
                        item['cache_dir'] = f"cache/text/{cache_dir_name}"
                        item.pop('instance_data_dir', None)
                        item.pop('cache_dir_vae', None)

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            rprint(f"[red]Error processing multidatabackend.json: {str(e)}[/red]")

    def update_config_files(self, token_name: str, new_version: str, source_dir: str, 
                            dataset_dir: str, target_dir: str, old_version: Optional[str] = None) -> None:
        try:
            target_path = Path(target_dir)
            
            config_path = target_path / "config.json"
            if config_path.exists():
                self.process_config_json(config_path, token_name, new_version, old_version)

            prompt_path = target_path / "user_prompt_library.json"
            if prompt_path.exists():
                self.process_user_prompt_library(
                    prompt_path, 
                    token_name,
                    existing_token=token_name if old_version else None
                )

            backend_path = target_path / "multidatabackend.json"
            if backend_path.exists():
                self.process_multidatabackend(backend_path, token_name, dataset_dir)
                
        except Exception as e:
            rprint(f"[red]Error updating configuration files: {str(e)}[/red]")

    def run(self) -> Optional[Path]:
        self.clear_screen()
        
        if not self.verify_paths():
            return None
            
        rprint("[magenta]=== Configuration Folder Management Tool ===[/magenta]")

        rprint("\n[cyan]Select source type:[/cyan]")
        rprint("[yellow]1. Use existing folder[/yellow]")
        rprint("[yellow]2. Use template[/yellow]")

        choice = Prompt.ask("Enter choice").strip()
        if not choice:
            rprint("[red]Exited--no input given[/red]")
            return None

        if choice == '1':
            folders = self.list_folders()
            if not folders:
                rprint("[red]No existing folders found.[/red]")
                return None
                
            folder_num_input = Prompt.ask("Enter number to select source folder").strip()
            if not folder_num_input:
                rprint("[red]Exited--no input given[/red]")
                return None
                
            try:
                folder_num = int(folder_num_input)
                source_dir = folders[folder_num - 1]
                source_path = self.root_path / source_dir
                rprint(f"[cyan]Using source path: {source_path}[/cyan]")
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return None

            token_name, old_version = self.parse_folder_name(source_dir)
            new_version = Prompt.ask("Enter new version number").strip()
            if not new_version:
                rprint("[red]Exited--no input given[/red]")
                return None

            proceed = self.get_yes_no_input("Use same dataset?")
            if proceed == 'y':
                backend_file = source_path / "multidatabackend.json"
                try:
                    with open(backend_file) as f:
                        data = json.load(f)
                        dataset_dir = next(
                            (obj['instance_data_dir'].split('/')[-1]
                             for obj in data if isinstance(obj, dict) and 'instance_data_dir' in obj),
                            None
                        )
                    if dataset_dir:
                        rprint(f"[green]Using existing dataset: {dataset_dir}[/green]")
                    else:
                        raise ValueError("No dataset found in configuration")
                except Exception as e:
                    rprint(f"[red]Error reading dataset from configuration: {str(e)}[/red]")
                    datasets = self.list_datasets()
                    dataset_num_input = Prompt.ask("Enter dataset number").strip()
                    if not dataset_num_input:
                        rprint("[red]Exited--no input given[/red]")
                        return None
                    try:
                        dataset_num = int(dataset_num_input)
                        dataset_dir = datasets[dataset_num - 1]
                    except (IndexError, ValueError):
                        rprint("[red]Invalid selection. Please try again.[/red]")
                        return None
            else:
                datasets = self.list_datasets()
                dataset_num_input = Prompt.ask("Enter dataset number").strip()
                if not dataset_num_input:
                    rprint("[red]Exited--no input given[/red]")
                    return None
                try:
                    dataset_num = int(dataset_num_input)
                    dataset_dir = datasets[dataset_num - 1]
                except (IndexError, ValueError):
                    rprint("[red]Invalid selection. Please try again.[/red]")
                    return None

        elif choice == '2':
            templates = self.list_templates()
            if not templates:
                rprint("[red]No templates found in config/templates directory. Exiting.[/red]")
                return None
                
            template_num_input = Prompt.ask("Enter template number").strip()
            if not template_num_input:
                rprint("[red]Exited--no input given[/red]")
                return None
                
            try:
                template_num = int(template_num_input)
                template_name = templates[template_num - 1]
                source_path = self.templates_path / template_name
                rprint(f"[cyan]Using template path: {source_path}[/cyan]")
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return None

            token_name = Prompt.ask("Enter new token name").strip()
            if not token_name:
                rprint("[red]Exited--no input given[/red]")
                return None
                
            new_version = Prompt.ask("Enter version number").strip()
            if not new_version:
                rprint("[red]Exited--no input given[/red]")
                return None

            datasets = self.list_datasets()
            dataset_num_input = Prompt.ask("Enter dataset number").strip()
            if not dataset_num_input:
                rprint("[red]Exited--no input given[/red]")
                return None
                
            try:
                dataset_num = int(dataset_num_input)
                dataset_dir = datasets[dataset_num - 1]
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return None

            old_version = None
        else:
            rprint("[red]Invalid choice. Exiting.[/red]")
            return None

        target_dir = self.root_path / f"{token_name}-{new_version}"

        rprint("\n[cyan]Processing with following parameters:[/cyan]")
        rprint(f"[yellow]Source Directory: {source_path}[/yellow]")
        rprint(f"[yellow]Token Name: {token_name}[/yellow]")
        rprint(f"[yellow]New Version: {new_version}[/yellow]")
        rprint(f"[yellow]Target Directory: {target_dir}[/yellow]")
        rprint(f"[yellow]Dataset: {dataset_dir}[/yellow]")

        proceed = self.get_yes_no_input("\nProceed?")
        if proceed != 'y':
            rprint("[red]\nOperation cancelled.[/red]")
            return None

        try:
            rprint("\n[cyan]Copying files...[/cyan]")
            self.show_rainbow_progress("Copying")
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source_path, target_dir, dirs_exist_ok=True)

            rprint("\n[cyan]Updating configuration files...[/cyan]")
            self.show_rainbow_progress("Updating")
            self.update_config_files(
                token_name, 
                new_version, 
                str(source_path), 
                dataset_dir, 
                str(target_dir), 
                old_version
            )

            rprint("\n[green]Operation completed successfully![/green]")
            rprint(f"\n[cyan]Created new configuration in: {target_dir}[/cyan]")
            
            return target_dir

        except Exception as e:
            rprint(f"[red]Error during operation: {str(e)}[/red]")
            return None


###########################################
# Part 2: Set Prompts Tool (from the first snippet)
###########################################

class PromptsTool:
    def __init__(self, target_config_dir: Path):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.simpletuner_path = self.workspace_path / 'SimpleTuner'
        self.templates_path = self.simpletuner_path / 'prompts' / 'templates'
        self.panel_width = 40
        # Initialize GPT-4 tokenizer
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.target_config_dir = target_config_dir

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

    def process_user_prompt_library(self, filepath: Path, token_name: str, existing_token: Optional[str] = None) -> None:
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
            
            if os.path.isdir(config_dir):
                token_name = os.path.basename(config_dir).split('-')[0]
                self.process_user_prompt_library(output_file, token_name, None)


            self.console.print(f"[green]Successfully saved prompts to {output_file}[/green]")

        except Exception as e:
            self.console.print(f"[red]Error saving prompts: {str(e)}[/red]")

    def run(self) -> None:
        self.console.print("[cyan]Loading tool: set_prompts[/cyan]")
        
        template_files = self.get_template_files()
        if not template_files:
            return
        self.display_templates(template_files)

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


###############################################
# Part 3: Set Config Tool (from the second snippet)
###############################################

@contextmanager
def raw_mode(file):
    if os.name == 'nt':
        yield
    else:
        old_attrs = termios.tcgetattr(file.fileno())
        new_attrs = old_attrs[:]
        new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
        try:
            termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
            yield
        finally:
            termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)

class ParameterLibrary:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
        self.library_path = self.base_path / 'config' / 'set_config_lib.json'
        self.parameters: Dict[str, Dict] = {}
        self.load_parameter_library()
    
    def load_parameter_library(self) -> None:
        try:
            if not self.library_path.exists():
                raise FileNotFoundError(f"Parameter library not found: {self.library_path}")
            with open(self.library_path) as f:
                raw_data = json.load(f)
                if not isinstance(raw_data, dict):
                    raise ValueError("Invalid parameter library format")
                self.parameters = raw_data
        except Exception as e:
            raise RuntimeError(f"Failed to load parameter library: {str(e)}")
    
    def get_parameter_definition(self, param_key: str) -> Dict:
        key = param_key.lstrip('-')
        for category, params in self.parameters.items():
            if key in params:
                return params[key]
            if f"--{key}" in params:
                return params[f"--{key}"]
        raise KeyError(f"Parameter not found in library: {param_key}")

class ParameterSelector:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent if '__file__' in globals() else Path('.')
        self.selection_path = self.base_path / 'config' / 'set_config_params.txt'
        self.selected_params: List[str] = []
        self.load_parameter_selection()
    
    def load_parameter_selection(self) -> None:
        try:
            if not self.selection_path.exists():
                raise FileNotFoundError(f"Parameter selection file not found: {self.selection_path}")
            with open(self.selection_path) as f:
                self.selected_params = [line.strip() for line in f if line.strip()]
        except Exception as e:
            raise RuntimeError(f"Failed to load parameter selection: {str(e)}")

class ConfigEditor:
    def __init__(self, target_config_dir: Path):
        self.console = Console()
        self.library = ParameterLibrary()
        self.selector = ParameterSelector()
        self.parameters: Dict[str, Dict] = {}
        self.current_config: Optional[str] = None
        self.current_parameter: Optional[str] = None
        self.status_message: str = ""
        self.target_config_dir = target_config_dir
        self.initialize_parameters()
    
    def initialize_parameters(self) -> None:
        for idx, param_key in enumerate(self.selector.selected_params, 1):
            try:
                param_def = self.library.get_parameter_definition(param_key)
                is_choice, param_type = self.determine_parameter_type(param_def)
                
                self.parameters[str(idx)] = {
                    "name": param_key,
                    "value": "",
                    "is_choice": is_choice or param_type == 'bool',
                    "type": param_type,
                    "options": self.get_parameter_options(param_def, param_type),
                    "config_key": f"--{param_key}" if not param_key.startswith('--') else param_key
                }
            except KeyError as e:
                self.console.print(f"[yellow]Warning: {str(e)}[/yellow]")
    
    def determine_parameter_type(self, param_def: Dict) -> Tuple[bool, str]:
        if isinstance(param_def, dict):
            if any(isinstance(x, bool) for x in param_def.values()):
                return True, 'bool'
            elif any(isinstance(x, float) for x in param_def.values()):
                return False, 'float'
            elif any(isinstance(x, int) for x in param_def.values()):
                return False, 'int'
            return False, 'string'
        elif isinstance(param_def, list):
            if all(isinstance(x, bool) for x in param_def):
                return True, 'bool'
            elif all(isinstance(x, (int, float)) for x in param_def):
                return False, 'float' if any(isinstance(x, float) for x in param_def) else 'int'
            return True, 'choice'
        return False, 'string'
    
    def get_parameter_options(self, param_def: Union[Dict, List], param_type: str) -> List:
        if param_type == 'bool':
            return ['true', 'false']
        if isinstance(param_def, list):
            return param_def
        return []
    
    def parse_number_format(self, value: str) -> str:
        try:
            value = value.strip().lower()
            parts = value.split()
            if len(parts) == 2:
                try:
                    base = float(parts[0])
                    exp = int(parts[1])
                    return f"{base}e-{exp}"
                except ValueError:
                    raise ValueError("Invalid scientific notation format")
            
            try:
                float(value)
                return value
            except ValueError:
                raise ValueError("Invalid number format")
                
        except ValueError as e:
            raise ValueError(str(e))

    def make_parameters_panel(self) -> Panel:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Parameter", style="cyan", width=30)
        table.add_column("Value", style="white", width=20)
        table.add_column("Parameter", style="cyan", width=30)
        table.add_column("Value", style="white", width=20)
        
        params = list(self.parameters.items())
        mid_point = (len(params) + 1) // 2  # Split parameters into two groups

        # Iterate over the full range of parameters, splitting into left and right columns
        for i in range(len(params)):
            left = params[i] if i < mid_point else None
            right = params[i + mid_point] if i + mid_point < len(params) else None
            
            if left and right:
                table.add_row(
                    f"[yellow]{left[0]}[/yellow] [cyan]{left[1]['name']}[/cyan]", 
                    str(left[1]['value']) if left[1]['value'] else "",
                    f"[yellow]{right[0]}[/yellow] [cyan]{right[1]['name']}[/cyan]", 
                    str(right[1]['value']) if right[1]['value'] else ""
                )
            elif left:
                table.add_row(
                    f"[yellow]{left[0]}[/yellow] [cyan]{left[1]['name']}[/cyan]", 
                    str(left[1]['value']) if left[1]['value'] else "",
                    "", ""
                )

        return Panel(
            table,
            title=f"[gold1]Parameter Settings - {self.current_config}[/gold1]",
            border_style="blue",
            padding=(1, 1)
        )


    def handle_save_and_rename(self, config_path: Path) -> None:
        self.console.print("\nSave changes? (Enter=Yes, Esc=No): ", end="")
        save_confirmed = False
        
        with raw_mode(sys.stdin):
            key = sys.stdin.read(1)
            if key == '\r' or key == '\n':
                self.console.print("Yes")
                self.save_changes(config_path)
                save_confirmed = True
            elif key == '\x1b':
                self.console.print("No")
                self.console.print("[yellow]Changes discarded.[/yellow]")
    
        if save_confirmed:
            self.console.print("\nRename config? (Space=Yes, Enter=No): ", end="")
            with raw_mode(sys.stdin):
                key = sys.stdin.read(1)
                if key == ' ':
                    self.console.print("Yes")
                    self.handle_rename(config_path)
                elif key == '\r':
                    self.console.print("No")

    def make_options_panel(self) -> Panel:
        content = ""
        
        if not self.current_parameter:
            content = "Select parameter to edit:"
        else:
            param = self.parameters[self.current_parameter]
            if param['is_choice']:
                options = [f"[yellow]{i}[/yellow] {option}" 
                          for i, option in enumerate(param['options'], 1)]
                content = "\n".join([
                    f"Select value for {param['name']}:",
                    *options
                ])
            else:
                type_hints = {
                    'float': "Enter number (format: 1.5e-4 or 1.5 4)",
                    'int': "Enter whole number",
                    'bool': "Enter true or false",
                    'string': "Enter value"
                }
                content = f"Enter value for {param['name']}:"
                if param['type'] in type_hints:
                    content += f"\n{type_hints[param['type']]}"
        
        return Panel(
            content,
            title="[gold1]Parameter Options[/gold1]",
            border_style="blue",
            padding=(1, 1)
        )

    def update_display(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')
        from rich.layout import Layout
        layout = Layout()
        layout.split_column(
            Layout(self.make_parameters_panel(), size=12),
            Layout(self.make_options_panel())
        )
        self.console.print(layout)
        if self.status_message:
            self.console.print(f"[red]{self.status_message}[/red]")
            self.status_message = ""

    def handle_parameter_input(self, value: str, immediate: bool = False) -> bool:
        if not value:
            return True
                
        param = self.parameters[self.current_parameter]
        
        try:
            if param['is_choice']:
                if immediate:
                    try:
                        idx = int(value) - 1
                        if 0 <= idx < len(param['options']):
                            param['value'] = str(param['options'][idx])
                            self.current_parameter = None
                            self.console.print(f"\nSelected: {param['value']}")
                            return True
                    except ValueError:
                        pass
                    return False
                
                idx = int(value) - 1
                if 0 <= idx < len(param['options']):
                    param['value'] = str(param['options'][idx])
                    return True
                else:
                    raise ValueError("Invalid option selection")
            elif param['type'] == 'float':
                parsed_value = self.parse_number_format(value)
                param['value'] = parsed_value
                self.console.print(f"\nEntered: {param['value']}")
            elif param['type'] == 'int':
                param['value'] = str(int(value))
                self.console.print(f"\nEntered: {param['value']}")
            else:
                param['value'] = str(value)
                self.console.print(f"\nEntered: {param['value']}")
            
            return True
            
        except ValueError as e:
            self.status_message = str(e)
            return False

    def edit_config(self, config_path: Path) -> None:
        self.current_config = config_path.parent.name
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                for param in self.parameters.values():
                    config_key = param['config_key']
                    key_without_dashes = config_key.lstrip('-')
                    
                    value = None
                    if config_key in config:
                        value = config[config_key]
                    elif key_without_dashes in config:
                        value = config[key_without_dashes]
                    
                    if value is not None:
                        if isinstance(value, bool):
                            param['value'] = str(value).lower()
                        elif isinstance(value, float):
                            if abs(value) < 0.01 or abs(value) >= 1000:
                                param['value'] = f"{value:.2e}"
                            else:
                                param['value'] = str(value)
                        else:
                            param['value'] = str(value)
                    
        except Exception as e:
            self.console.print(f"[red]Error loading config: {str(e)}[/red]")
            return

        self.update_display()

        with raw_mode(sys.stdin):
            while True:
                if not self.current_parameter:
                    key = sys.stdin.read(1)
                    if key in ('\r', '\n'):
                        break
                    elif key in self.parameters:
                        self.current_parameter = key
                        self.console.print(f"\nSelected parameter: {self.parameters[key]['name']}")
                        self.update_display()
                        
                        if self.parameters[key]['is_choice']:
                            while True:
                                choice = sys.stdin.read(1)
                                if choice in ('\r', '\n'):
                                    self.current_parameter = None
                                    break
                                if self.handle_parameter_input(choice, immediate=True):
                                    break
                            self.update_display()
                else:
                    value = self.console.input("\nEnter value: ").strip()
                    if self.handle_parameter_input(value):
                        self.current_parameter = None
                        self.update_display()

        self.handle_save_and_rename(config_path)

    def save_changes(self, config_path: Path) -> None:
        if not config_path.exists():
            self.console.print(f"[red]Config file not found: {config_path}[/red]")
            return

        try:
            with open(config_path, 'r') as f:
                try:
                    config = json.load(f)
                except json.JSONDecodeError:
                    self.console.print(f"[red]Invalid JSON format in file: {config_path}[/red]")
                    return

            for param in self.parameters.values():
                if 'config_key' not in param:
                    self.console.print(f"[yellow]Skipping parameter with missing config_key: {param}[/yellow]")
                    continue
                try:
                    if param['type'] == 'float':
                        config[param['config_key']] = float(param['value'])
                    elif param['type'] == 'int':
                        config[param['config_key']] = int(param['value'])
                    elif param['type'] == 'bool':
                        config[param['config_key']] = param['value'].lower() == 'true'
                    else:
                        config[param['config_key']] = param['value']
                except ValueError:
                    self.console.print(f"[red]Invalid value for {param['config_key']}: {param['value']}[/red]")

            try:
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=4)
                self.console.print("[green]Config saved successfully![/green]")
            except OSError as e:
                self.console.print(f"[red]Failed to save config: {str(e)}[/red]")

        except Exception as e:
            self.console.print(f"[red]Error saving config: {str(e)}[/red]")

    def handle_rename(self, config_path: Path) -> None:
        current_name = config_path.parent.name
        self.console.print(f"\nCurrent name: {current_name}")
        
        new_name = self.console.input("Enter new name: ").strip()

        if new_name and new_name != current_name:
            if self.validate_new_name(new_name):
                try:
                    old_folder = config_path.parent
                    new_folder = old_folder.parent / new_name

                    if new_folder.exists():
                        self.console.print(f"[red]Error: Folder '{new_name}' already exists.[/red]")
                        return

                    old_folder.rename(new_folder)
                    self.console.print(f"[green]Successfully renamed folder to '{new_name}'.[/green]")

                    config_file = new_folder / 'config.json'
                    self.edit_config_family(new_name, config_file)

                except Exception as e:
                    self.console.print(f"[red]Error during rename operation: {str(e)}[/red]")
            else:
                self.console.print("[red]Invalid name format or name already exists.[/red]")

    def edit_config_family(self, new_folder_name: str, config_path: Path):
        try:
            name, version = new_folder_name.split('-')
        except ValueError:
            raise ValueError("Invalid folder name format. Expected format: 'name-version'")

        try:
            with open(config_path, 'r') as file:
                config = json.load(file)
        except FileNotFoundError:
            print(f"Config file not found at: {config_path}")
            return
        except json.JSONDecodeError:
            print(f"Failed to parse config file. Ensure it's valid JSON: {config_path}")
            return

        config["--instance_prompt"] = name
        config["--user_prompt_library"] = f"config/{new_folder_name}/user_prompt_library.json"
        config["--data_backend_config"] = f"config/{new_folder_name}/multidatabackend.json"
        config["--output_dir"] = f"output/{name}/{version}"

        try:
            with open(config_path, 'w') as file:
                json.dump(config, file, indent=4)
            print(f"Config updated successfully: {config_path}")
        except Exception as e:
            print(f"Failed to save updated config: {e}")

    def validate_new_name(self, new_name: str) -> bool:
        if not all(c.isalnum() or c in '-_' for c in new_name):
            return False
        
        new_path = Path(self.current_config).parent.parent / new_name
        if new_path.exists():
            return False
            
        parts = new_name.split('-')
        if len(parts) != 2:
            return False
            
        return True


###########################################
# MasterTool: Orchestrate all steps
###########################################

class Tool:
    def __init__(self):
        self.console = Console()

    def run(self):
        # Step 1: Run ConfigManager to create new environment
        mgr = ConfigManager()
        new_config_path = mgr.run()
        if not new_config_path:
            return  # Could not create config

        # Step 2: Run Set Prompts Tool to select and set user prompts
        prompts_tool = PromptsTool(new_config_path)
        prompts_tool.run()

        # Step 3 & 4: Run Config Editor (Set Config Tool) to handle renaming and final editing
        # The ConfigEditor expects a config.json in new_config_path
        config_file = new_config_path / 'config.json'
        if not config_file.exists():
            self.console.print("[red]Config file not found for editing.[/red]")
            return

        editor = ConfigEditor(new_config_path)
        editor.edit_config(config_file)
        # After editing and optional renaming, user can finalize their configuration parameters.

        self.console.print("[green]All steps completed successfully![/green]")


if __name__ == "__main__":
    tool = MasterTool()
    tool.run()