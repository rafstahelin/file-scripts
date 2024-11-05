import os
import json
import shutil
import time
import sys
import tty
import termios
from typing import Tuple, Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import print as rprint
from rich.prompt import Prompt

class ConfigManager:
    def __init__(self):
        self.console = Console()
        self.templates_path = Path('/workspace/SimpleTuner/config/templates')
        self.root_path = Path('/workspace/SimpleTuner/config')
        
    def verify_paths(self) -> bool:
        """Verify that all required paths exist."""
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
        """Clear terminal screen."""
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
        """Read a single character from the console without requiring Enter."""
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
        """Prompt user with a yes or no question, expecting 'y' or 'n' without requiring Enter."""
        print(f"{prompt_text} [y/n]: ", end='', flush=True)
        while True:
            ch = self.getch()
            if ch.lower() in ('y', 'n'):
                print(ch)  # Echo the character
                return ch.lower()
            else:
                print("\n[red]Invalid input. Please enter 'y' or 'n'.[/red]")
                print(f"{prompt_text} [y/n]: ", end='', flush=True)

    def list_folders(self) -> list:
        """List all configuration folders."""
        folders = [f for f in self.root_path.iterdir() 
                  if f.is_dir() and f.name not in ['templates', '.ipynb_checkpoints']]
        
        # Group folders by base name
        grouped = {}
        ordered_folders = []
        for folder in folders:
            base_name = folder.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(folder.name)
            ordered_folders.append(folder.name)
            
        # Create panels for each group
        panels = []
        index = 1
        
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
            
        # Arrange panels into rows with three panels each
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))
            
        return ordered_folders
        
    def list_templates(self) -> list:
        """List template folders from the templates directory."""
        if not self.templates_path.exists():
            rprint(f"[yellow]Warning: Templates directory {self.templates_path} not found.[/yellow]")
            return []

        templates = [f for f in self.templates_path.iterdir() 
                    if f.is_dir() and f.name != '.ipynb_checkpoints']
        
        # Group templates by base name
        grouped = {}
        ordered_templates = []
        index = 1
        
        for template in templates:
            base_name = template.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(template.name)
            ordered_templates.append(template.name)

        # Create panels for each group
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

        # Display panels in rows
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))
        
        return ordered_templates

    def list_datasets(self) -> list:
        """List available datasets."""
        datasets_path = self.root_path.parent / 'datasets'
        if not datasets_path.exists():
            rprint(f"[yellow]Warning: Datasets directory {datasets_path} not found.[/yellow]")
            return []
            
        datasets = [folder.name for folder in datasets_path.iterdir() 
                   if folder.is_dir() and folder.name != '.ipynb_checkpoints']
        
        # Group datasets by base name
        grouped = {}
        ordered_datasets = []
        index = 1
        
        for dataset in datasets:
            base_name = dataset.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(dataset)
            ordered_datasets.append(dataset)

        # Create panels for each group
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

        # Display panels
        panels_per_row = 3
        for i in range(0, len(panels), panels_per_row):
            row_panels = panels[i:i + panels_per_row]
            while len(row_panels) < panels_per_row:
                row_panels.append(Panel("", border_style="blue", width=36))
            self.console.print(Columns(row_panels, equal=True, expand=True))
            
        return ordered_datasets

    def parse_folder_name(self, folder: str) -> Tuple[str, str]:
        """Parse a folder name into token and version components."""
        parts = folder.split('-', 1)
        return parts[0], parts[1] if len(parts) > 1 else ''

    def process_config_json(
        self, filepath: Path, token_name: str, new_version: str, old_version: Optional[str] = None
    ) -> None:
        """Process config.json to update paths with the correct new version or placeholders."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()

            if old_version:
                # When using an existing folder, replace old version with new version
                content = content.replace(f"{token_name}-{old_version}", f"{token_name}-{new_version}")
                content = content.replace(f"{token_name}/{old_version}", f"{token_name}/{new_version}")
            else:
                # For template configs, replace placeholders with provided values
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

    def process_user_prompt_library(
        self, filepath: Path, token_name: str, existing_token: Optional[str] = None
    ) -> None:
        """Update user_prompt_library.json, replacing tokens if they differ."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            updated_data = {}
            for key, value in data.items():
                if existing_token:
                    # Replace the old token in the key and value with the new token
                    new_key = key.replace(existing_token, token_name) if existing_token != token_name else key
                    updated_data[new_key] = (
                        value.replace(existing_token, token_name) if existing_token != token_name else value
                    )
                else:
                    # Replace placeholders with the new token name
                    new_key = key.replace('__TOKEN_NAME__', token_name).replace('_TOKEN_NAME_', token_name)
                    updated_data[new_key] = value.replace('__TOKEN_NAME__', token_name).replace('_TOKEN_NAME_', token_name)

            with open(filepath, 'w') as f:
                json.dump(updated_data, f, indent=2)
                
        except Exception as e:
            rprint(f"[red]Error processing user_prompt_library.json: {str(e)}[/red]")

    def process_multidatabackend(self, filepath: Path, token_name: str, dataset_name: str) -> None:
        """Update paths in multidatabackend.json with the new token and dataset names."""
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

    def update_config_files(
        self, token_name: str, new_version: str, source_dir: str, 
        dataset_dir: str, target_dir: str, old_version: Optional[str] = None
    ) -> None:
        """Update all configuration files in the target directory."""
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

    def run(self):
        """Main execution method for the configuration management tool."""
        self.clear_screen()
        
        # Verify paths before proceeding
        if not self.verify_paths():
            return
            
        rprint("[magenta]=== Configuration Folder Management Tool ===[/magenta]")

        rprint("\n[cyan]Select source type:[/cyan]")
        rprint("[yellow]1. Use existing folder[/yellow]")
        rprint("[yellow]2. Use template[/yellow]")

        choice = Prompt.ask("Enter choice").strip()
        if not choice:
            rprint("[red]Exited--no input given[/red]")
            return

        if choice == '1':
            folders = self.list_folders()
            if not folders:
                rprint("[red]No existing folders found.[/red]")
                return
                
            folder_num_input = Prompt.ask("Enter number to select source folder").strip()
            if not folder_num_input:
                rprint("[red]Exited--no input given[/red]")
                return
                
            try:
                folder_num = int(folder_num_input)
                source_dir = folders[folder_num - 1]
                # Create full absolute source path
                source_path = self.root_path / source_dir
                rprint(f"[cyan]Using source path: {source_path}[/cyan]")
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return

            token_name, old_version = self.parse_folder_name(source_dir)
            new_version = Prompt.ask("Enter new version number").strip()
            if not new_version:
                rprint("[red]Exited--no input given[/red]")
                return

            proceed = self.get_yes_no_input("Use same dataset?")
            if proceed == 'y':
                # Use absolute path when reading the backend file
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
                        return
                    try:
                        dataset_num = int(dataset_num_input)
                        dataset_dir = datasets[dataset_num - 1]
                    except (IndexError, ValueError):
                        rprint("[red]Invalid selection. Please try again.[/red]")
                        return
            else:
                datasets = self.list_datasets()
                dataset_num_input = Prompt.ask("Enter dataset number").strip()
                if not dataset_num_input:
                    rprint("[red]Exited--no input given[/red]")
                    return
                try:
                    dataset_num = int(dataset_num_input)
                    dataset_dir = datasets[dataset_num - 1]
                except (IndexError, ValueError):
                    rprint("[red]Invalid selection. Please try again.[/red]")
                    return

        elif choice == '2':
            templates = self.list_templates()
            if not templates:
                rprint("[red]No templates found in config/templates directory. Exiting.[/red]")
                return
                
            template_num_input = Prompt.ask("Enter template number").strip()
            if not template_num_input:
                rprint("[red]Exited--no input given[/red]")
                return
                
            try:
                template_num = int(template_num_input)
                template_name = templates[template_num - 1]
                # Create full absolute source path for template
                source_path = self.templates_path / template_name
                rprint(f"[cyan]Using template path: {source_path}[/cyan]")
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return

            token_name = Prompt.ask("Enter new token name").strip()
            if not token_name:
                rprint("[red]Exited--no input given[/red]")
                return
                
            new_version = Prompt.ask("Enter version number").strip()
            if not new_version:
                rprint("[red]Exited--no input given[/red]")
                return

            datasets = self.list_datasets()
            dataset_num_input = Prompt.ask("Enter dataset number").strip()
            if not dataset_num_input:
                rprint("[red]Exited--no input given[/red]")
                return
                
            try:
                dataset_num = int(dataset_num_input)
                dataset_dir = datasets[dataset_num - 1]
            except (IndexError, ValueError):
                rprint("[red]Invalid selection. Please try again.[/red]")
                return

            old_version = None  # No old version when using templates
        else:
            rprint("[red]Invalid choice. Exiting.[/red]")
            return

        # Always use absolute paths for target directory
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
            return

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
        except Exception as e:
            rprint(f"[red]Error during operation: {str(e)}[/red]")


# Add Tool class for compatibility with tools.py
class Tool:
    """Wrapper class to make ConfigManager compatible with the tools interface."""
    def __init__(self):
        self.manager = ConfigManager()
        
    def run(self):
        """Main execution method that delegates to ConfigManager."""
        self.manager.run()


if __name__ == "__main__":
    tool = Tool()
    tool.run()