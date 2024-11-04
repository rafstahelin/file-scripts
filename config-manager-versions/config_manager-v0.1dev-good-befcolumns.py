import os
import json
import shutil
import time
from typing import Tuple, Optional
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint
from rich.prompt import Prompt

class ConfigManager:
    def __init__(self):
        self.console = Console()
    
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

    def list_folders(self) -> list:
        folders = sorted(
            [f for f in Path().iterdir() if f.is_dir() and f.name not in ['lora', 'lokr', '.ipynb_checkpoints']],
            reverse=True
        )
        grouped_folders = sorted(folders, key=lambda x: x.stem.split('-')[0])
        
        rprint("[cyan]Existing folders:[/cyan]")
        for i, folder in enumerate(grouped_folders, 1):
            rprint(f"[yellow]{i}. {folder.name}[/yellow]")
        
        return [folder.name for folder in grouped_folders]
    
    def list_datasets(self) -> list:
        datasets_path = Path('../datasets')
        datasets = [
            folder.name for folder in sorted(datasets_path.iterdir())
            if folder.is_dir() and folder.name != '.ipynb_checkpoints'
        ]
        
        rprint("\n[cyan]Available datasets:[/cyan]")
        for i, dataset in enumerate(datasets, 1):
            rprint(f"[yellow]{i}. {dataset}[/yellow]")
        
        return datasets
    
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
            # For "lora" or "lokr" templates, replace placeholders with provided values
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

    def update_config_files(
        self, token_name: str, new_version: str, source_dir: str, dataset_dir: str, target_dir: str, old_version: Optional[str] = None
    ) -> None:
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

    def get_yes_no_input(self, prompt_text: str) -> str:
        """Prompt user with a yes or no question, expecting 'y' or 'n'."""
        while True:
            response = input(f"{prompt_text} [y/n]: ").strip().lower()
            if response in ('y', 'n'):
                return response
            else:
                rprint("[red]Invalid input. Please enter 'y' or 'n'.[/red]")

    def run(self):
        """Main execution method for the configuration management tool."""
        self.clear_screen()
        rprint("[magenta]=== Configuration Folder Management Tool ===[/magenta]")
        
        rprint("\n[cyan]Select source folder type:[/cyan]")
        rprint("[yellow]1. Use existing folder[/yellow]")
        rprint("[yellow]2. Use 'lora' template[/yellow]")
        rprint("[yellow]3. Use 'lokr' template[/yellow]")
        
        choice = Prompt.ask("Enter choice")
        
        if choice == '1':
            folders = self.list_folders()
            folder_num = int(Prompt.ask("Enter number to select source folder"))
            
            try:
                source_dir = folders[folder_num - 1]
            except IndexError:
                rprint("[red]Invalid selection. Please try again.[/red]")
                return
            
            token_name, old_version = self.parse_folder_name(source_dir)
            new_version = Prompt.ask("Enter new version number")
            
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
                dataset_num = int(Prompt.ask("Enter dataset number"))
                dataset_dir = datasets[dataset_num - 1]
        else:
            # For "lora" or "lokr" templates, no old_version is needed
            source_dir = 'lora' if choice == '2' else 'lokr'
            token_name = Prompt.ask("Enter new token name")
            new_version = Prompt.ask("Enter version number")
            
            datasets = self.list_datasets()
            dataset_num = int(Prompt.ask("Enter dataset number"))
            dataset_dir = datasets[dataset_num - 1]
            
            old_version = None  # No old version when using templates
        
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
