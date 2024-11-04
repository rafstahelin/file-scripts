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
        # Using absolute path to templates directory
        self.templates_path = Path('/workspace/SimpleTuner/config/templates')
        self.root_path = Path('/workspace/SimpleTuner/config')
        
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
        folders = [f for f in self.root_path.iterdir() if f.is_dir() and f.name not in ['templates', '.ipynb_checkpoints']]
        # Group folders by base name
        grouped = {}
        for folder in folders:
            base_name = folder.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(folder.name)
        # Prepare indices and folder list
        folder_indices = {}
        index = 1
        ordered_folders = []
        for base_name in sorted(grouped.keys()):
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            folder_indices[base_name] = {}
            for name in names_in_group:
                folder_indices[base_name][name] = index
                ordered_folders.append(name)
                index += 1
        # Create panels for each group
        panels = []
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            # Add column with max_width to control wrapping
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            for name in names_in_group:
                idx = folder_indices[base_name][name]
                table.add_row(f"[yellow]{idx}. {name}[/yellow]")
            panel = Panel(table, title=f"[magenta]{base_name}[/magenta]", border_style="blue", width=36)
            panels.append(panel)
        # Arrange panels into rows with three panels each, adding placeholder panels if needed
        panels_per_row = 3
        panel_rows = [panels[i:i + panels_per_row] for i in range(0, len(panels), panels_per_row)]
        # Add placeholder panels to the last row if necessary
        if panels and len(panel_rows[-1]) < panels_per_row:
            for _ in range(panels_per_row - len(panel_rows[-1])):
                panel_rows[-1].append(Panel("", border_style="blue", width=36))
        rprint("[cyan]Existing folders:[/cyan]")
        for row in panel_rows:
            self.console.print(Columns(row, equal=True, expand=True))
        return ordered_folders
        
    def list_templates(self) -> list:
        """List template folders from the templates directory."""
        if not self.templates_path.exists():
            rprint(f"[yellow]Warning: Templates directory {self.templates_path} not found.[/yellow]")
            return []

        templates = [f for f in self.templates_path.iterdir() if f.is_dir() and f.name != '.ipynb_checkpoints']
        
        # Group templates by base name
        grouped = {}
        for template in templates:
            base_name = template.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(template.name)

        # Prepare indices and template list
        template_indices = {}
        index = 1
        ordered_templates = []
        for base_name in sorted(grouped.keys()):
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            template_indices[base_name] = {}
            for name in names_in_group:
                template_indices[base_name][name] = index
                ordered_templates.append(name)
                index += 1

        # Create panels for each group
        panels = []
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            for name in names_in_group:
                idx = template_indices[base_name][name]
                table.add_row(f"[yellow]{idx}. {name}[/yellow]")
            panel = Panel(table, title=f"[magenta]{base_name}[/magenta]", border_style="blue", width=36)
            panels.append(panel)

        # Arrange panels into rows with three panels each
        panels_per_row = 3
        panel_rows = [panels[i:i + panels_per_row] for i in range(0, len(panels), panels_per_row)]
        if panels and len(panel_rows[-1]) < panels_per_row:
            for _ in range(panels_per_row - len(panel_rows[-1])):
                panel_rows[-1].append(Panel("", border_style="blue", width=36))

        rprint("\n[cyan]Available templates:[/cyan]")
        for row in panel_rows:
            self.console.print(Columns(row, equal=True, expand=True))
        
        return ordered_templates

    def list_datasets(self) -> list:
        datasets_path = self.root_path.parent / 'datasets'
        datasets = [folder.name for folder in datasets_path.iterdir() if folder.is_dir() and folder.name != '.ipynb_checkpoints']
        # Group datasets by base name
        grouped = {}
        for dataset in datasets:
            base_name = dataset.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(dataset)
        # Prepare indices and dataset list
        dataset_indices = {}
        index = 1
        ordered_datasets = []
        for base_name in sorted(grouped.keys()):
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            dataset_indices[base_name] = {}
            for name in names_in_group:
                dataset_indices[base_name][name] = index
                ordered_datasets.append(name)
                index += 1
        # Create panels for each group
        panels = []
        for base_name in sorted(grouped.keys()):
            table = Table(show_header=False, show_edge=False, box=None, padding=(0,1))
            table.add_column(justify="left", no_wrap=False, overflow='fold', max_width=30)
            names_in_group = sorted(grouped[base_name], key=lambda x: x.lower(), reverse=True)
            for name in names_in_group:
                idx = dataset_indices[base_name][name]
                table.add_row(f"[yellow]{idx}. {name}[/yellow]")
            panel = Panel(table, title=f"[magenta]{base_name}[/magenta]", border_style="blue", width=36)
            panels.append(panel)
        # Arrange panels into rows with three panels each
        panels_per_row = 3
        panel_rows = [panels[i:i + panels_per_row] for i in range(0, len(panels), panels_per_row)]
        if panels and len(panel_rows[-1]) < panels_per_row:
            for _ in range(panels_per_row - len(panel_rows[-1])):
                panel_rows[-1].append(Panel("", border_style="blue", width=36))
        rprint("\n[cyan]Available datasets:[/cyan]")
        for row in panel_rows:
            self.console.print(Columns(row, equal=True, expand=True))
        return ordered_datasets

    def parse_folder_name(self, folder: str) -> Tuple[str, str]:
        parts = folder.split('-', 1)
        return parts[0], parts[1] if len(parts) > 1 else ''

    def process_config_json(
        self, filepath: Path, token_name: str, new_version: str, old_version: Optional[str] = None
    ) -> None:
        """Process config.json to update paths with the correct new version or placeholders."""
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

    def process_user_prompt_library(
        self, filepath: Path, token_name: str, existing_token: Optional[str] = None
    ) -> None:
        """Update user_prompt_library.json, replacing tokens if they differ."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        updated_data = {}
        for key, value in data.items():
            if existing_token:
                # Replace the old token in the key and value with the new token, if different
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

    def process_multidatabackend(self, filepath: Path, token_name: str, dataset_name: str) -> None:
        """Update paths in multidatabackend.json with the new token and dataset names."""
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

    def update_config_files(self, token_name: str, new_version: str, source_dir: str, dataset_dir: str, target_dir: str, old_version: Optional[str] = None) -> None:
        """Update configuration files in the target directory with new token and version info."""
        config_path = Path(target_dir) / "config.json"
        if config_path.exists():
            self.process_config_json(config_path, token_name, new_version, old_version)

        prompt_path = Path(target_dir) / "user_prompt_library.json"
        if prompt_path.exists():
            self.process_user_prompt_library(prompt_path, token_name, existing_token=token_name if old_version else None)

        backend_path = Path(target_dir) / "multidatabackend.json"
        if backend_path.exists():
            self.process_multidatabackend(backend_path, token_name, dataset_dir)

    def run(self):
        """Main execution method for the configuration management tool."""
        self.clear_screen()
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
            folder_num_input = Prompt.ask("Enter number to select source folder").strip()
            if not folder_num_input:
                rprint("[red]Exited--no input given[/red]")
                return
            try:
                folder_num = int(folder_num_input)
                source_dir = folders[folder_num - 1]
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
                with open(f"{source_dir}/multidatabackend.json") as f:
                    data = json.load(f)
                    dataset_dir = next(
                        (obj['instance_data_dir'].split('/')[-1]
                         for obj in data if isinstance(obj, dict) and 'instance_data_dir' in obj),
                        None
                    )
                rprint(f"[green]Using existing dataset: {dataset_dir}[/green]")
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
                source_dir = str(self.templates_path / template_name)
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

        target_dir = f"{token_name}-{new_version}"

        rprint("\n[cyan]Processing with following parameters:[/cyan]")
        rprint(f"[yellow]Source Directory: {source_dir}[/yellow]")
        rprint(f"[yellow]Token Name: {token_name}[/yellow]")
        rprint(f"[yellow]New Version: {new_version}[/yellow]")
        rprint(f"[yellow]New Folder Name: {target_dir}[/yellow]")
        rprint(f"[yellow]Dataset: {dataset_dir}[/yellow]")

        proceed = self.get_yes_no_input("\nProceed?")
        if proceed != 'y':
            rprint("[red]\nOperation cancelled.[/red]")
            return

        rprint("\n[cyan]Copying files...[/cyan]")
        self.show_rainbow_progress("Copying")
        shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)

        rprint("\n[cyan]Updating configuration files...[/cyan]")
        self.show_rainbow_progress("Updating")
        self.update_config_files(token_name, new_version, source_dir, dataset_dir, target_dir, old_version)

        rprint("\n[green]Operation completed successfully![/green]")
        rprint(f"\n[cyan]Created new configuration in: {target_dir}[/cyan]")

if __name__ == "__main__":
    manager = ConfigManager()
    manager.run()