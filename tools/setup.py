"""
Environment Setup Tool
---------------------
• Git Repository Management:
  - Syncs file-scripts to latest dev branch
  - Handles merge conflicts and issues
  - Reports sync status

• Tools Launcher Setup:
  - Creates 'tools' command for quick access
  - Can be run from any directory
  - Automatic path detection

• WANDB Configuration (RunPod only):
  - Sets up WANDB API token
  - Tests connection
  - Handles authentication issues

Usage:
    Menu option: 'setup' or shortcut: 'st'
"""

from pathlib import Path
import subprocess
import os
from rich.console import Console
from rich.prompt import Confirm
from rich import print as rprint

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.file_scripts_path = self.workspace_path / 'file-scripts'
        self.is_runpod = self._check_is_runpod()
        print(f"Running in {'RunPod' if self.is_runpod else 'WSL'} environment")  # Debug print

    def _check_is_runpod(self):
        """Check if running in RunPod environment."""
        # Check for both RunPod and general container environment
        is_container = os.path.exists('/.dockerenv')
        is_runpod = os.path.exists('/workspace/.runpod')
        
        if is_runpod:
            return True  # Specifically RunPod
        elif is_container:
            return True  # Other container (treat same as RunPod)
        else:
            return False  # WSL/local environment

    def _run_command(self, command, cwd=None, shell=True):
        """Run shell command and handle errors."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.file_scripts_path,
                capture_output=True,
                text=True,
                check=True,
                shell=shell
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    def _run_git_command(self, command, cwd=None):
        """Run git command and handle errors."""
        return self._run_command(command, cwd)

    def cleanup_structure(self):
        """Clean up file-scripts directory structure."""
        print("Starting cleanup_structure...")  # Debug print
        self.console.print("\n[bold blue]Cleaning up directory structure...[/]")
        
        try:
            # Remove unnecessary files
            files_to_remove = [
                'CURSOR.rules',
                'paths.json',
                'requirements.txt'
            ]
            
            for file in files_to_remove:
                file_path = self.file_scripts_path / file
                if file_path.exists():
                    file_path.unlink()
                    self.console.print(f"[green]✓ Removed {file}[/]")

            print("Cleanup completed successfully")  # Debug print
            return True

        except Exception as e:
            print(f"Cleanup error: {str(e)}")  # Debug print
            self.console.print(f"[red]Error cleaning up structure:[/]\n{str(e)}")
            return False

    def setup_tools_shortcut(self):
        """Setup tools.py shortcut command."""
        print("Starting setup_tools_shortcut...")  # Debug print
        self.console.print("\n[bold blue]Setting up tools launcher shortcut...[/]")
        
        try:
            # Use /usr/local/bin for the shortcut
            bin_path = '/usr/local/bin'
            shortcut_path = f'{bin_path}/tools'
            
            print(f"Using bin path: {bin_path}")  # Debug print
            print(f"Shortcut path: {shortcut_path}")  # Debug print

            # Ensure bin directory exists
            os.makedirs(bin_path, exist_ok=True)

            # Remove any existing shortcuts
            if os.path.exists(shortcut_path):
                print(f"Removing existing shortcut at {shortcut_path}")
                os.remove(shortcut_path)

            # Create shortcut script
            script_content = """#!/bin/bash

# Find the tools.py script
if [ -f "/workspace/file-scripts/tools.py" ]; then
    cd /workspace/file-scripts
    python tools.py
elif [ -f "./file-scripts/tools.py" ]; then
    cd ./file-scripts
    python tools.py
else
    echo "Error: Could not find tools.py. Are you in the workspace directory?"
    exit 1
fi
"""
            print(f"Creating new shortcut at {shortcut_path}")  # Debug print
            
            # Write script and set permissions
            with open(shortcut_path, 'w') as f:
                f.write(script_content)
            os.chmod(shortcut_path, 0o755)

            # Update .bashrc
            bashrc_path = '/root/.bashrc'  # Using root's .bashrc since we're in container
            print(f"Updating bashrc at {bashrc_path}")  # Debug print
            
            if os.path.exists(bashrc_path):
                with open(bashrc_path, 'r') as f:
                    bashrc_content = f.read()

                updates_needed = []
                if 'alias tools=' not in bashrc_content:
                    updates_needed.append('\n# Tools launcher shortcut\n'
                                       'alias tools=\'tools\'\n')

                if updates_needed:
                    with open(bashrc_path, 'a') as f:
                        for update in updates_needed:
                            f.write(update)

            print("Tools shortcut setup completed successfully")  # Debug print
            self.console.print("[green]✓ Tools launcher shortcut 'tools' installed successfully[/]")
            self.console.print("[yellow]Note: You'll need to restart your terminal or run 'source ~/.bashrc' to use the shortcut[/]")
            return True

        except Exception as e:
            print(f"Setup tools shortcut error: {str(e)}")  # Debug print
            self.console.print(f"[red]Error setting up tools launcher shortcut:[/]\n{str(e)}")
            return False

    def sync_git_repo(self):
        """Synchronize git repository with dev branch."""
        print("Starting sync_git_repo...")  # Debug print
        self.console.print("\n[bold blue]Syncing git repository...[/]")
        
        # Check if repo exists
        if not self.file_scripts_path.exists():
            print("Repository not found, attempting to clone...")  # Debug print
            self.console.print("[yellow]Repository not found. Cloning...[/]")
            success, output = self._run_git_command(
                "git clone https://github.com/rafstahelin/file-scripts.git /workspace/file-scripts"
            )
            if not success:
                print(f"Clone failed: {output}")  # Debug print
                self.console.print(f"[red]Failed to clone repository:[/]\n{output}")
                return False
        
        # Sync repository
        commands = [
            "git fetch --all --prune",
            "git checkout dev",
            "git pull origin dev"
        ]
        
        for cmd in commands:
            print(f"Running git command: {cmd}")  # Debug print
            success, output = self._run_git_command(cmd)
            if not success:
                print(f"Git command failed: {output}")  # Debug print
                self.console.print(f"[red]Failed to execute '{cmd}':[/]\n{output}")
                return False
            
        print("Git sync completed successfully")  # Debug print
        self.console.print("[green]✓ Git repository synced successfully[/]")
        return True

    def setup_wandb(self):
        """Configure Weights & Biases API token."""
        print("Starting setup_wandb...")  # Debug print
        self.console.print("\n[bold blue]Setting up Weights & Biases...[/]")
        
        if not self.is_runpod:
            print("Not in RunPod environment, skipping WANDB setup")  # Debug print
            self.console.print("[yellow]Skipping WANDB setup in WSL environment[/]")
            return True
            
        try:
            wandb_key = os.getenv('WANDB_API_KEY')
            if not wandb_key:
                print("WANDB_API_KEY not found in environment")  # Debug print
                self.console.print("[yellow]WANDB API key not found in environment variables[/]")
                self.console.print("[yellow]Skipping WANDB setup - add WANDB_API_KEY to your environment if needed[/]")
                return True  # Return True as this isn't a failure case
            
            # Configure WANDB only if key exists
            os.environ['WANDB_API_KEY'] = wandb_key
            
            # Test WANDB login
            print("Testing WANDB login...")  # Debug print
            result = subprocess.run(
                ['wandb', 'login', '--relogin'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("WANDB login successful")  # Debug print
                self.console.print("[green]✓ WANDB configured successfully[/]")
                return True
            else:
                print("WANDB login attempt failed, but continuing...")  # Debug print
                self.console.print("[yellow]WANDB login failed, but continuing...[/]")
                self.console.print("[yellow]You can set up WANDB manually later if needed[/]")
                return True  # Return True as this isn't a critical failure
                
        except Exception as e:
            print(f"WANDB setup error: {str(e)}")  # Debug print
            self.console.print(f"[yellow]WANDB setup skipped: {str(e)}[/]")
            self.console.print("[yellow]You can set up WANDB manually later if needed[/]")
            return True  # Return True as this isn't a critical failure

    def run(self):
        """Main tool execution flow."""
        print("====SETUP TOOL DEBUG====")  # Debug print
        print("Setup tool starting...")  # Debug print
        
        # Print the module's docstring as a header
        self.console.print(__doc__)
        
        steps = [
            (self.cleanup_structure, "Directory structure cleanup"),
            (self.sync_git_repo, "Git synchronization"),
            (self.setup_tools_shortcut, "Tools launcher setup"),
            (self.setup_wandb, "WANDB configuration")
        ]
        
        print("About to start steps...")  # Debug print
        print(f"Found {len(steps)} steps to execute")  # Debug print
        
        success = True
        for step_func, step_name in steps:
            print(f"Running step: {step_name}")  # Debug print
            if not step_func():
                self.console.print(f"\n[red]Failed at step: {step_name}[/]")
                success = False
                if not Confirm.ask("Continue with remaining steps?"):
                    break
        
        status = "[green]✓ Setup completed successfully[/]" if success else "[yellow]⚠ Setup completed with warnings[/]"
        self.console.print(f"\n{status}")
        
        print("Setup tool finished")  # Debug print
        
        if Confirm.ask("\nPress Enter to return to main menu"):
            return

if __name__ == "__main__":
    tool = Tool()
    tool.run()