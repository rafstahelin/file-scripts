from pathlib import Path
import subprocess
import os
import shutil
from rich.console import Console
from rich import print as rprint
from rich.progress import track

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.file_scripts_path = self.workspace_path / 'file-scripts'
        self.is_runpod = os.path.exists('/.dockerenv') or os.path.exists('/workspace/.runpod')
        rprint(f"[cyan]Environment:[/] {'[green]RunPod[/]' if self.is_runpod else '[yellow]WSL[/]'}")
        self.debug_mode = os.getenv('DEBUG', '').lower() == 'true'

    def _run_command(self, command, cwd=None, shell=True):
        """Execute a shell command and return the result."""
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
            if self.debug_mode:
                self.console.print(f"[yellow]Command failed: {command}[/]")
                self.console.print(f"[yellow]Error: {e.stderr}[/]")
            return False, f"Error: {e.stderr}"

    def setup_dependencies(self):
        """Install required Python packages."""
        self.console.print("\n[bold blue]Setting up dependencies...[/]")
        
        try:
            self.console.print("[cyan]Installing system packages...[/]")
            # Install jq system package first
            success, output = self._run_command("apt-get update && apt-get install -y jq")
            if not success:
                self.console.print(f"[red]Failed to install jq:[/]\n{output}")
                return False
            
            self.console.print("[cyan]Installing Python packages...[/]")
            dependencies = [
                "rich>=10.0.0",
                "requests>=2.25.1",
                "tqdm>=4.65.0",
                "safetensors",
                "tiktoken>=0.8.0",
                "regex>=2022.1.18"
            ]
            
            for dep in dependencies:
                self.console.print(f"[dim]Installing {dep}...[/]")
                success, output = self._run_command(f"python -m pip install '{dep}'")
                if not success:
                    self.console.print(f"[red]Failed to install {dep}:[/]")
                    self.console.print(f"[red]Error output:[/]\n{output}")
                    return False
                self.console.print(f"[green]✓[/] Installed {dep}")
        
            self.console.print("[green]✓[/] All dependencies installed")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error installing dependencies:[/]\n{str(e)}")
            return False

    def setup_rclone(self):
        """Configure rclone."""
        self.console.print("\n[bold blue]Configuring rclone...[/]")
        try:
            rclone_config_dir = Path(os.path.expanduser('~/.config/rclone'))
            rclone_config_dir.mkdir(parents=True, exist_ok=True)
            
            rclone_src = self.workspace_path / 'rclone.conf'
            rclone_dst = rclone_config_dir / 'rclone.conf'
            
            if not rclone_src.exists():
                self.console.print("[yellow]Warning: rclone.conf not found in workspace[/]")
                return True

            shutil.copy2(rclone_src, rclone_dst)
            self.console.print("[green]✓[/] Rclone configured successfully")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error configuring rclone:[/]\n{str(e)}")
            if self.debug_mode:
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/]")
            return False

    def setup_git_auth(self):
        """Configure Git authentication using a Personal Access Token (PAT)."""
        self.console.print("\n[bold blue]Configuring Git authentication...[/]")
        try:
            # Check if already configured
            git_credentials = Path.home() / '.git-credentials'
            if git_credentials.exists():
                self.console.print("[green]✓[/] Git credentials already configured")
                return True

            # Get PAT from environment variable
            pat = os.getenv('GITHUB_PAT')
            if not pat:
                self.console.print("[yellow]GITHUB_PAT not found in environment, skipping auth setup[/]")
                return True

            # Write credentials
            with git_credentials.open('w') as f:
                f.write(f"https://{pat}@github.com\n")
            
            # Set secure permissions
            git_credentials.chmod(0o600)

            # Enable credential helper
            success, _ = self._run_command('git config --global credential.helper store')
            if not success:
                self.console.print("[red]Failed to configure credential helper[/]")
                return False

            self.console.print("[green]✓[/] Git authentication configured successfully")
            return True

        except Exception as e:
            self.console.print(f"[red]Error configuring Git authentication:[/]\n{str(e)}")
            if self.debug_mode:
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/]")
            return False

    def setup_tools_shortcut(self):
        """Setup tools.py shortcut and navigation aliases."""
        self.console.print("\n[bold blue]Setting up shortcuts...[/]")
        
        try:
            bin_path = Path('/usr/local/bin')
            bin_path.mkdir(parents=True, exist_ok=True)
            
            tools_script = """#!/bin/bash
if [ -f "/workspace/file-scripts/tools.py" ]; then
    cd /workspace/file-scripts
    python tools.py
elif [ -f "./file-scripts/tools.py" ]; then
    cd ./file-scripts
    python tools.py
else
    echo "Error: Could not find tools.py"
    exit 1
fi"""
            tools_path = bin_path / 'tools'
            tools_path.write_text(tools_script)
            tools_path.chmod(0o755)
    
            bashrc_path = Path('/root/.bashrc')
            if bashrc_path.exists():
                navigation_aliases = """
# Tools shortcuts
alias tools='tools'

# Navigation shortcuts
alias config='cd /workspace/SimpleTuner/config'
alias data='cd /workspace/SimpleTuner/datasets'
alias out='cd /workspace/SimpleTuner/output'
alias flux='cd /workspace/StableSwarmUI/Models/loras/flux'
alias scripts='cd /workspace/file-scripts'
"""
                with bashrc_path.open('a') as f:
                    f.write(navigation_aliases)
    
            self.console.print("[green]✓[/] Shortcuts installed successfully")
            return True
    
        except Exception as e:
            self.console.print(f"[red]Error setting up shortcuts:[/]\n{str(e)}")
            return False

    def setup_wandb(self):
        """Configure Weights & Biases API token."""
        self.console.print("\n[bold blue]Setting up Weights & Biases...[/]")
        
        if not self.is_runpod:
            self.console.print("[yellow]Skipping WANDB setup in WSL environment[/]")
            return True
                
        try:
            wandb_key = os.getenv('WANDB_API_KEY')
            if not wandb_key:
                self.console.print("[yellow]WANDB API key not found in environment[/]")
                return True
    
            os.environ['WANDB_API_KEY'] = wandb_key
            success, _ = self._run_command('wandb login --relogin')
            
            self.console.print("[green]✓[/] WANDB configured successfully")
            return True
                    
        except Exception as e:
            self.console.print(f"[yellow]WANDB setup skipped: {str(e)}[/]")
            return True

    def run(self):
        """Main execution method."""
        self.console.print("[bold cyan]File-Scripts Setup Tool[/]")
        self.console.print("[dim]Version: 0.9.0[/]")
        
        steps = [
            (self.setup_dependencies, "Installing dependencies"),
            (self.setup_git_auth, "Configuring Git authentication"),
            (self.setup_rclone, "Configuring rclone"),
            (self.setup_tools_shortcut, "Setting up tools launcher"),
            (self.setup_wandb, "Configuring WANDB")
        ]
        
        success = True
        for step_func, step_name in track(steps, description="[cyan]Setting up environment...[/]"):
            if not step_func():
                self.console.print(f"\n[red]✗ Failed:[/] {step_name}")
                success = False
                continue
        
        status = "[green]✓ Setup completed successfully[/]" if success else "[yellow]⚠ Setup completed with warnings[/]"
        self.console.print(f"\n{status}")
        
        # Start tools.py
        if self.file_scripts_path.exists():
            os.chdir(str(self.file_scripts_path))
            subprocess.run(['python', 'tools.py'])

if __name__ == "__main__":
    tool = Tool()
    tool.run()