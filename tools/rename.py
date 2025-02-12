from pathlib import Path
import json
import shutil
import re
from typing import List, Dict, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table
import os

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.config_path = self.workspace_path / 'SimpleTuner/config'
        self.output_path = self.workspace_path / 'SimpleTuner/output'
        self.lora_path = self.workspace_path / 'ComfyUI/models/loras/flux'
        
    def verify_paths(self) -> bool:
        """Verify all required paths exist."""
        required_paths = {
            'workspace': self.workspace_path,
            'config': self.config_path,
            'output': self.output_path,
            'lora': self.lora_path
        }
        
        missing = []
        for name, path in required_paths.items():
            if not path.exists():
                missing.append(f"{name}: {path}")
                
        if missing:
            self.console.print("[red]Error: The following required paths do not exist:[/red]")
            for path in missing:
                self.console.print(f"[red]- {path}[/red]")
            return False
            
        return True

    def validate_pattern(self, pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate a pattern meets required format."""
        if not pattern:
            return False, "Pattern cannot be empty"
            
        # Pattern should have either hyphens or underscores, not both
        if '-' in pattern and '_' in pattern:
            return False, "Pattern cannot contain both hyphens and underscores"
            
        # Basic pattern validation (prefix-number or prefix_number)
        pattern_regex = r'^[a-zA-Z]+[-_]\d+$'
        if not re.match(pattern_regex, pattern):
            return False, "Pattern must be in format: prefix-number or prefix_number"
            
        return True, None

    def validate_pattern_pair(self, old_pattern: str, new_pattern: str) -> Tuple[bool, Optional[str]]:
        """Validate old and new patterns are compatible."""
        # Get prefixes
        old_prefix = old_pattern.split('-')[0]
        new_prefix = new_pattern.split('_')[0]
        
        if old_prefix != new_prefix:
            return False, f"Prefixes must match: {old_prefix} ≠ {new_prefix}"
            
        if '-' not in old_pattern:
            return False, "Old pattern must use hyphens"
            
        if '_' not in new_pattern:
            return False, "New pattern must use underscores"
            
        return True, None

    def backup_file(self, file_path: Path) -> Optional[Path]:
        """Create backup of a file before modification."""
        try:
            backup_path = file_path.with_suffix(file_path.suffix + '.bak')
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to create backup of {file_path}: {str(e)}[/yellow]")
            return None

    def update_json_file(self, file_path: Path, old_pattern: str, new_pattern: str, dry_run: bool = False) -> bool:
        """Update pattern references in JSON config files."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            modified = False
            
            def replace_in_value(value: any) -> any:
                if isinstance(value, str):
                    if old_pattern in value:
                        return value.replace(old_pattern, new_pattern)
                elif isinstance(value, dict):
                    return {k: replace_in_value(v) for k, v in value.items()}
                elif isinstance(value, list):
                    return [replace_in_value(item) for item in value]
                return value
                
            new_data = replace_in_value(data)
            
            if new_data != data and not dry_run:
                backup = self.backup_file(file_path)
                with open(file_path, 'w') as f:
                    json.dump(new_data, f, indent=2)
                self.console.print(f"[green]Updated {file_path}[/green]")
                modified = True
                
            return modified
            
        except Exception as e:
            self.console.print(f"[red]Error processing {file_path}: {str(e)}[/red]")
            return False

    def should_skip_path(self, path: Path) -> bool:
        """Determine if a path should be skipped during processing."""
        skip_patterns = [
            '.ipynb_checkpoints',
            '__pycache__',
            '.git'
        ]
        return any(pattern in str(path) for pattern in skip_patterns)

    def process_directory(self, 
                         base_path: Path,
                         old_pattern: str, 
                         new_pattern: str,
                         dry_run: bool = False) -> List[Tuple[Path, Path]]:
        """Process a directory tree for renames."""
        renames = []
        
        try:
            # Extract prefix and version numbers
            old_prefix, old_version = old_pattern.split('-')
            new_prefix, new_version = new_pattern.split('_')
            
            # Collect all paths that need renaming
            for path in base_path.rglob('*'):
                if self.should_skip_path(path):
                    continue
                    
                path_str = str(path)
                new_path_str = path_str
                
                # Handle different path patterns
                if 'ComfyUI/models/loras/flux' in path_str:
                    # Handle version number in directory structure
                    new_path_str = re.sub(
                        f"{old_prefix}/{old_version}",
                        f"{new_prefix}/{new_version}",
                        new_path_str
                    )
                
                # Handle the main pattern replacement
                if old_pattern in new_path_str:
                    new_path_str = new_path_str.replace(old_pattern, new_pattern)
                    
                if new_path_str != path_str:
                    renames.append((path, Path(new_path_str)))
            
            # Sort by depth (deepest first) to handle nested paths correctly
            renames.sort(key=lambda x: len(str(x[0]).split(os.sep)), reverse=True)
            
            if not dry_run:
                # Execute renames
                for old_path, new_path in renames:
                    try:
                        new_path.parent.mkdir(parents=True, exist_ok=True)
                        old_path.rename(new_path)
                        self.console.print(f"[green]Renamed: {old_path} → {new_path}[/green]")
                    except Exception as e:
                        self.console.print(f"[red]Error renaming {old_path}: {str(e)}[/red]")
                        
        except Exception as e:
            self.console.print(f"[red]Error processing directory {base_path}: {str(e)}[/red]")
            
        return renames

    def run(self):
        """Main execution method."""
        self.console.print("[cyan]Loading tool: rename[/cyan]")
        
        if not self.verify_paths():
            return

        # Get patterns
        old_pattern = self.console.input("\nEnter old pattern (e.g., amelia-0002): ").strip()
        if not old_pattern:
            self.console.print("[yellow]Operation cancelled.[/yellow]")
            return
            
        new_pattern = self.console.input("\nEnter new pattern (e.g., amelia_002): ").strip()
        if not new_pattern:
            self.console.print("[yellow]Operation cancelled.[/yellow]")
            return

        # Validate patterns
        valid, error = self.validate_pattern(old_pattern)
        if not valid:
            self.console.print(f"[red]Invalid old pattern: {error}[/red]")
            return
            
        valid, error = self.validate_pattern(new_pattern)
        if not valid:
            self.console.print(f"[red]Invalid new pattern: {error}[/red]")
            return
            
        valid, error = self.validate_pattern_pair(old_pattern, new_pattern)
        if not valid:
            self.console.print(f"[red]Invalid pattern combination: {error}[/red]")
            return

        # Show plan
        paths_to_process = [
            self.config_path,
            self.output_path,
            self.lora_path
        ]
        
        self.console.print("\n[cyan]Will process the following paths:[/cyan]")
        for path in paths_to_process:
            self.console.print(f"[yellow]- {path}[/yellow]")

        # Dry run first
        self.console.print("\n[cyan]Performing dry run...[/cyan]")
        total_renames = []
        
        for path in paths_to_process:
            renames = self.process_directory(path, old_pattern, new_pattern, dry_run=True)
            total_renames.extend(renames)
            
        if not total_renames:
            self.console.print("[yellow]No files found matching the pattern.[/yellow]")
            return

        # Show summary
        table = Table(
            title="Planned Renames",
            show_header=True,
            padding=(0,2),
            show_edge=True,
            expand=True
        )
        table.add_column("From", style="cyan", no_wrap=True, overflow="fold")
        table.add_column("To", style="green", no_wrap=True, overflow="fold")
        
        for old_path, new_path in total_renames:
            table.add_row(str(old_path), str(new_path))
            
        self.console.print(table)

        # Confirm
        if not Confirm.ask("\nProceed with renaming?"):
            self.console.print("[yellow]Operation cancelled.[/yellow]")
            return

        # Execute renames with progress tracking
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn()
        ) as progress:
            task = progress.add_task("Processing files...", total=len(total_renames))
            
            for path in paths_to_process:
                self.process_directory(path, old_pattern, new_pattern)
                
                # Update any JSON configs in this path
                for config_file in path.rglob('*.json'):
                    self.update_json_file(config_file, old_pattern, new_pattern)
                    
                progress.update(task, advance=1)

        self.console.print("[green]✓ Rename operation completed successfully![/green]")

if __name__ == "__main__":
    tool = Tool()
    tool.run()