import os
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
import json
import random

class DatasetCaptionsTool:
    def __init__(self):
        self.console = Console()
        self.config_path = Path('/workspace/SimpleTuner/config')
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')
        self.console.print(f"[cyan]Initialized with config path: {self.config_path}[/cyan]")
        self.console.print(f"[cyan]Datasets path: {self.datasets_path}[/cyan]")

    def list_config_folders(self) -> List[str]:
        folders = [f for f in self.config_path.iterdir() 
                  if f.is_dir() and f.name != 'templates' 
                  and not f.name.startswith('.ipynb_checkpoints')]
        
        grouped = {}
        ordered_folders = []
        panels = []
        index = 1
        
        for folder in folders:
            base_name = folder.name.split('-', 1)[0]
            grouped.setdefault(base_name, []).append(folder.name)
            
        for base_name in sorted(grouped.keys()):
            content = []
            names_in_group = sorted(grouped[base_name], key=str.lower, reverse=True)
            
            content.append(f"[yellow]{index}.[/yellow] all")
            ordered_folders.append(f"{base_name}:all")
            index += 1
            
            for name in names_in_group:
                content.append(f"[yellow]{index}.[/yellow] {name}")
                ordered_folders.append(name)
                index += 1
                
            panel = Panel(
                "\n".join(content),
                title=f"[yellow]{base_name}[/yellow]",
                border_style="blue",
                width=40
            )
            panels.append(panel)
        
        for i in range(0, len(panels), 3):
            row_panels = panels[i:i + 3]
            self.console.print(Columns(row_panels, equal=True, expand=True))
            
        return ordered_folders

    def get_dataset_path(self, config_dir: Path) -> Optional[Path]:
        backend_file = config_dir / "multidatabackend.json"
        self.console.print(f"[yellow]Looking for backend file: {backend_file}[/yellow]")
        
        if not backend_file.exists():
            self.console.print(f"[red]Backend file not found: {backend_file}[/red]")
            return None
            
        try:
            with open(backend_file) as f:
                self.console.print("[green]Successfully opened backend file[/green]")
                data = json.load(f)
                self.console.print(f"[yellow]Backend data structure: {type(data)}[/yellow]")
                
                for item in data:
                    self.console.print(f"[yellow]Processing item: {item}[/yellow]")
                    if isinstance(item, dict) and 'instance_data_dir' in item:
                        dataset_path = item['instance_data_dir'].split('/')[-1]
                        full_path = self.datasets_path / dataset_path
                        self.console.print(f"[green]Found dataset path: {full_path}[/green]")
                        return full_path
                
                self.console.print("[red]No valid instance_data_dir found in backend file[/red]")
                return None
        except Exception as e:
            self.console.print(f"[red]Error reading backend file: {str(e)}[/red]")
            return None

    def process_captions(self, dataset_dir: Path, output_file: Path):
        self.console.print(f"[cyan]Processing captions from: {dataset_dir}[/cyan]")
        
        if not dataset_dir.exists():
            self.console.print(f"[red]Dataset directory does not exist: {dataset_dir}[/red]")
            return
            
        caption_files = list(dataset_dir.glob("*.txt"))
        self.console.print(f"[yellow]Found {len(caption_files)} caption files[/yellow]")
        
        if not caption_files:
            self.console.print("[red]No caption files found in dataset directory[/red]")
            return

        selected_files = random.sample(caption_files, min(10, len(caption_files)))
        self.console.print(f"[green]Selected {len(selected_files)} random files[/green]")
        
        captions = []
        for file in selected_files:
            try:
                self.console.print(f"[yellow]Reading caption from: {file.name}[/yellow]")
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        captions.append(f"# Caption from {file.name}\n{content}\n")
                        self.console.print(f"[green]Successfully read caption from {file.name}[/green]")
                    else:
                        self.console.print(f"[red]Empty caption file: {file.name}[/red]")
            except Exception as e:
                self.console.print(f"[red]Error reading {file}: {str(e)}[/red]")

        if captions:
            try:
                self.console.print(f"[yellow]Saving {len(captions)} captions to: {output_file}[/yellow]")
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write("\n".join(captions))
                self.console.print(f"[green]Successfully saved captions to: {output_file}[/green]")
            except Exception as e:
                self.console.print(f"[red]Error saving captions: {str(e)}[/red]")
        else:
            self.console.print("[red]No valid captions found to save[/red]")

    def process_single_config(self, config_dir):
        self.console.print(f"[cyan]Processing config directory: {config_dir}[/cyan]")
        
        if not config_dir.exists():
            self.console.print(f"[red]Config directory does not exist: {config_dir}[/red]")
            return
            
        dataset_dir = self.get_dataset_path(config_dir)
        if not dataset_dir:
            self.console.print("[red]Could not find dataset path in config[/red]")
            return

        output_file = config_dir / f"{config_dir.name}-captions.txt"
        self.console.print("[cyan]Processing captions...[/cyan]")
        self.process_captions(dataset_dir, output_file)

    def run(self):
        while True:
            config_folders = self.list_config_folders()
            if not config_folders:
                self.console.print("[red]No configuration folders found[/red]")
                return

            folder_num = Prompt.ask("Enter number or ENTER to exit").strip()
            if not folder_num:
                return

            try:
                selected = config_folders[int(folder_num) - 1]
                
                if ":all" in selected:
                    base_name = selected.split(":")[0]
                    group_configs = [f for f in config_folders 
                                   if f.startswith(base_name) and ":all" not in f]
                    
                    for config in group_configs:
                        self.console.print(f"[cyan]Processing {config}...[/cyan]")
                        config_dir = self.config_path / config
                        self.process_single_config(config_dir)
                else:
                    config_dir = self.config_path / selected
                    self.process_single_config(config_dir)
                
                self.console.print("\n[green]Processing complete. Returning to config selection...[/green]\n")
                    
            except (ValueError, IndexError):
                self.console.print("[red]Invalid selection[/red]")
                continue

class Tool:
    def __init__(self):
        self.tool = DatasetCaptionsTool()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()
