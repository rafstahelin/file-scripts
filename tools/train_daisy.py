from pathlib import Path
import os
import subprocess
import json
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from datetime import datetime

class Logger:
    
    def __init__(self, filter_path, config_path, backend_path, log_path, mode):

        self.filter_path = filter_path
        self.config_path = config_path
        self.backend_path = backend_path
        self.log_path = log_path
        self.mode = mode

        self.filter_data = self.load_json(self.filter_path)
        self.config_data = self.load_json(self.config_path)
        self.backend_data = self.load_json(self.backend_path)

    def load_json(self, path):
        with open(path, "r") as file:
            return json.load(file)

    def extract_data(self):
        
        extracted = {}
        for key in self.filter_data.get("config.json", []):
            prefixed_key = f"--{key}"
            if prefixed_key in self.config_data:
                extracted[key] = self.config_data[prefixed_key]

        backend_keys = self.filter_data.get("multidatabackend.json", {})
        for dimension, keys in backend_keys.items():
            for entry in self.backend_data:
                if entry.get("id") == dimension:
                    extracted[dimension] = {
                        key: entry.get(key, "N/A") for key in keys
                    }
        return extracted

    def write_log(self, data, start_time, end_time):

        extracted_data = self.extract_data()

        config_json_string = json.dumps(self.config_data, indent=4)
        backend_json_string = json.dumps(self.backend_data, indent=4)

        max_key_length = max(len(key.replace('_', ' ').title()) for key in extracted_data)

        if data:
            log_content = f"{data}\n"
            log_content += f"{'=' * 50}\n"
        else:
            log_content = f"{'=' * 50}\n"

        log_content += f"Start Time: {start_time}\n"
        log_content += f"End Time: {end_time}\n"

        for key, value in extracted_data.items():
            formatted_key = key.replace('_', ' ').title().ljust(max_key_length + 2)
            log_content += f"{formatted_key}: {value}\n"

        # log_content += f"{'-' * 50}\n"

        # log_content += "Config JSON:\n" + config_json_string + "\n\n"
        # log_content += "Multidatabackend JSON:\n" + backend_json_string + "\n"

        log_content += f"{'=' * 50}\n"

        # mode = "a" if os.path.exists(self.log_path) else "w"
        mode = self.mode
        with open(self.log_path, mode) as log_file:
            log_file.write(log_content)

class Tool:
    def __init__(self):
        self.console = Console()
        self.simpletuner_path = Path('/workspace/SimpleTuner')
        self.filter_file = Path('/workspace/file-scripts/config/filter_params.json')
        self.config_path = self.simpletuner_path / 'config'

    def list_folders(self):
        skip_dirs = {'templates', '.ipynb_checkpoints'}
        folders = [f.name for f in self.config_path.iterdir() if f.is_dir() and f.name not in skip_dirs]

        if not folders:
            self.console.print("[red]No configuration folders found.[/red]")
            return []

        folders = sorted(folders, key=str.lower)

        if len(folders) <= 5:
            for i, folder in enumerate(folders, 1):
                self.console.print(f"[yellow]{i}. {folder}[/yellow]")
        else:
            left_column = []
            right_column = []
            for i, folder in enumerate(folders, 1):
                line = f"[yellow]{i}. {folder}[/yellow]"
                if i <= 5:
                    left_column.append(line)
                else:
                    right_column.append(line)
            
            left_panel = Panel("\n".join(left_column), border_style="blue", width=36)
            right_panel = Panel("\n".join(right_column), border_style="blue", width=36)
            
            self.console.print(Columns([left_panel, right_panel], equal=True, expand=True))

        return folders

    def _load_config_data(self, config_name):
        config_dir = self.config_path / config_name
        config_file = config_dir / "config.json"
        config_data = {}        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config_data = json.load(f)
        return config_data

    def _load_config_log(self, config_name):
        config_dir = self.config_path / config_name
        config_file = config_dir / f"{config_name}.log"
        config_data = ""
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = f.read()
        return config_data

    def _save_config_data(self, config_name, new_data):
        config_dir = self.config_path / config_name
        config_file = config_dir / "config.json"
        if not config_dir.exists():
            self.console.print("[red]Config directory does not exist.[/red]")
            return False
        try:
            with open(config_file, 'w') as f:
                json.dump(new_data, f, indent=4)
            self.console.print(f"[green]Config data saved successfully to:[/green] {config_file}")
            return True
        except Exception as e:
            self.console.print(f"[red]Failed to save config data:[/red] {e}")
            return False


    def _launch_training(self, config_name, daisy_chained_config):

        config_data = self._load_config_data(config_name)

        start_time = datetime.now()

        iteration_hash = int(start_time.timestamp() * 1000)

        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

        config_data['--instance_prompt'] = f"{config_data['--instance_prompt']}:{iteration_hash}"

        self._save_config_data(config_name, config_data)

        self.console.print(f"[cyan]Training started at:[/cyan] {start_time}")

        try:
            os.chdir(self.simpletuner_path)
            env = os.environ.copy()
            env['ENV'] = config_name

            print("\n\n\n")  
            activate_cmd = f"source .venv/bin/activate && ENV={config_name} bash train.sh"
            process = subprocess.Popen(
                activate_cmd,
                env=env,
                shell=True,
                executable='/bin/bash'
            )
            
            try:
                process.wait() 
            except KeyboardInterrupt:
                process.terminate()
                raise
                
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            return False

        end_time = datetime.now()

        # config_data = self._load_config_data(config_name)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")

        # self._save_config_data(config_name, config_data)

        if not daisy_chained_config:
            filter_path = self.filter_file
            config_path = self.config_path / config_name / "config.json"
            backend_path = self.config_path / config_name / "multidatabackend.json"
            log_path = self.config_path / config_name / f"{config_name}.log"

            logger = Logger(filter_path, config_path, backend_path, log_path, "w")
            logger.write_log(None, start_time_str, end_time_str)
        
        else: 
            log_data = self._load_config_log(daisy_chained_config)
            filter_path = self.filter_file
            config_path = self.config_path / config_name / "config.json"
            backend_path = self.config_path / config_name / "multidatabackend.json"
            log_path = self.config_path / config_name / f"{config_name}.log"

            logger = Logger(filter_path, config_path, backend_path, log_path, "a")
            logger.write_log(log_data, start_time_str, end_time_str)


        self.console.print(f"[cyan]Training finished at:[/cyan] {end_time}")
        self.console.print(f"[green]Total training time:[/green] {end_time - start_time}")
        
        return True

    def run(self):
        try:
            self.console.print("[magenta]=== Simple Tuner Trainer Tool ===[/magenta]")

            if not self.simpletuner_path.exists():
                self.console.print("[red]Error: SimpleTuner directory not found![/red]")
                return
                
            if not (self.simpletuner_path / 'train.sh').exists():
                self.console.print("[red]Error: train.sh not found![/red]")
                return

            folders = self.list_folders()

            if not folders:
                return
            
            # Create a simple map: index -> folder name
            config_map = {i+1: folders[i] for i in range(len(folders))}
            
            while True:
                choice = input("\nEnter number to select config:   ")
                if not choice.strip():
                    return
                        
                try:
                    choice_num = int(choice)
                    if choice_num in config_map:
                        config = config_map[choice_num]
                        self.console.print(f"[green]Config selected:[/green] {config}")

                        # Ask if it's daisy chained
                        daisy_choice = input("\nIs it daisy chained? (y/n):   ").strip().lower()

                        if daisy_choice == 'y':
                            
                            self.console.print("\n[cyan]Select daisy chained config:[/cyan]")

                            self.list_folders()
                            
                            while True:
                                daisy_choice = input("Enter number to select daisy chained config:   ")
                                try:
                                    daisy_choice_num = int(daisy_choice)
                                    if daisy_choice_num in config_map:
                                        daisy_chained_config = config_map[daisy_choice_num]
                                        self.console.print(f"[green]Daisy chained config selected:[/green] {daisy_chained_config}")
                                        break
                                    else:
                                        self.console.print("[red]Invalid selection![/red]")
                                except ValueError:
                                    self.console.print("[red]Please enter a valid number![/red]")
                        else:
                            daisy_chained_config = None

                        # Launch training
                        self._launch_training(config, daisy_chained_config)
                        break
                    else:
                        self.console.print("[red]Invalid selection![/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number![/red]")
                    
        except KeyboardInterrupt:
            self.console.print("\n[cyan]Training tool closed[/cyan]")


if __name__ == "__main__":
    tool = Tool()
    tool.run()
