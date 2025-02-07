from pathlib import Path
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns

class Tool:
    def __init__(self):
        self.console = Console()
        self.simpletuner_path = Path('/workspace/SimpleTuner')
        self.config_path = self.simpletuner_path / 'config'

    def _scan_configs(self):
        """Scan for available training configurations"""
        configs = {}
        skip_dirs = {'templates'}

        for config_dir in self.config_path.iterdir():
            if config_dir.is_dir() and config_dir.name not in skip_dirs:
                if any((config_dir / f"config{ext}").exists() for ext in ['.json', '.toml', '.env']):
                    # Use both '-' and '_' as delimiters to find the base name
                    base_name = config_dir.name.split('_')[0].split('-')[0]

                    if base_name not in configs:
                        configs[base_name] = []

                    configs[base_name].append(config_dir.name)

        # Sort configurations within each group
        return {k: sorted(v) for k, v in sorted(configs.items())}


    def _create_config_panel(self, base_name, configs, start_number):
        """Create a panel for a group of configs"""
        lines = []
        config_map = {}
        
        for idx, config in enumerate(configs, start_number):
            lines.append(f"[yellow]{idx}.[/yellow] {config}")
            config_map[idx] = config

        panel = Panel(
            "\n".join(lines),
            title=f"[yellow]{base_name}[/yellow]",
            border_style="blue",
            width=40
        )
        
        return panel, config_map

    def _display_configs(self, config_groups):
        """Display available configurations"""
        # Removed loading message as it's handled by tools.py
        print()  # Just keep a blank line for spacing
        
        all_config_maps = {}
        start_number = 1
        panels = []
        
        for base_name, configs in config_groups.items():
            panel, config_map = self._create_config_panel(base_name, configs, start_number)
            panels.append(panel)
            all_config_maps.update(config_map)
            start_number += len(configs)
    
        # Display panels in rows of 3
        for i in range(0, len(panels), 3):
            row_panels = panels[i:min(i + 3, len(panels))]
            self.console.print(Columns(row_panels, equal=True, expand=True))
    
        return all_config_maps

    def _launch_training(self, config_name):
        """Launch SimpleTuner training"""
        try:
            os.chdir(self.simpletuner_path)
            env = os.environ.copy()
            env['ENV'] = config_name
            
            # Add three blank lines before starting training
            print("\n\n\n")
            
            # Activate venv and run training
            activate_cmd = f"source .venv/bin/activate && ENV={config_name} bash train.sh"
            process = subprocess.Popen(
                activate_cmd,
                env=env,
                shell=True,
                executable='/bin/bash'
            )
            
            try:
                process.wait()  # Wait for the training to complete
            except KeyboardInterrupt:
                process.terminate()
                raise
                
        except Exception as e:
            self.console.print(f"\n[red]Error: {e}[/red]")
            return False
            
        return True

    def run(self):
        try:
            if not self.simpletuner_path.exists():
                self.console.print("[red]Error: SimpleTuner directory not found![/red]")
                return
                
            if not (self.simpletuner_path / 'train.sh').exists():
                self.console.print("[red]Error: train.sh not found![/red]")
                return
            
            config_groups = self._scan_configs()
            if not config_groups:
                self.console.print("[red]No configurations found![/red]")
                return

            config_map = self._display_configs(config_groups)
            
            while True:
                choice = input("\nEnter number to select config:   ")
                if not choice.strip():
                    return
                        
                try:
                    choice_num = int(choice)
                    if choice_num in config_map:
                        config = config_map[choice_num]
                        self._launch_training(config)
                        break
                    else:
                        self.console.print("[red]Invalid selection![/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number![/red]")
                    
        except KeyboardInterrupt:
            self.console.print("\n[cyan]Training tool closed[/cyan]")