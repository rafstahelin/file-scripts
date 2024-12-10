from pathlib import Path
import subprocess
import os
import shutil
from rich.console import Console
from rich.prompt import Confirm
from rich import print as rprint
from rich.progress import track

class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.file_scripts_path = self.workspace_path / 'file-scripts'
        self.is_runpod = self._check_is_runpod()
        rprint(f"[cyan]Environment:[/] {'[green]RunPod[/]' if self.is_runpod else '[yellow]WSL[/]'}")
        self.debug_mode = os.getenv('DEBUG', '').lower() == 'true'

    def _check_is_runpod(self):
        is_container = os.path.exists('/.dockerenv')
        is_runpod = os.path.exists('/workspace/.runpod')
        return is_runpod or is_container

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

    def _safe_remove(self, path: Path):
        """Safely remove a file or directory with proper error handling."""
        try:
            if not path.exists():
                return True

            if self.debug_mode:
                self.console.print(f"[dim]Attempting to remove: {path}[/]")

            if path.is_file():
                path.unlink(missing_ok=True)
            elif path.is_dir():
                # Remove contents first
                for item in path.glob('*'):
                    self._safe_remove(item)
                # Then remove the directory
                try:
                    path.rmdir()
                except OSError:
                    # If rmdir fails, try force remove with shutil
                    shutil.rmtree(path, ignore_errors=True)
            return True
        except Exception as e:
            if self.debug_mode:
                self.console.print(f"[yellow]Warning: Failed to remove {path}: {str(e)}[/]")
            return False

    def cleanup_structure(self):
        """Clean up workspace directory structure with improved handling."""
        self.console.print("\n[bold blue]Cleaning directory structure...[/]")
        
        try:
            cleanup_patterns = [
                '**/__pycache__',
                '**/*.pyc',
                '**/.DS_Store',
                '**/Thumbs.db',
                '**/.ipynb_checkpoints',
                # Add patterns for pip installation artifacts
                '**/=*.0',
                '**/=*.1'
            ]
            
            total_cleaned = 0
            failed_paths = []
            
            for pattern in cleanup_patterns:
                if self.debug_mode:
                    self.console.print(f"[dim]Scanning for pattern: {pattern}[/]")
                
                # Use rglob to handle nested paths
                for item in self.file_scripts_path.rglob(pattern.replace('**/', '')):
                    if self._safe_remove(item):
                        total_cleaned += 1
                    else:
                        failed_paths.append(str(item))

            # Clean up pip installation artifacts directly
            pip_artifacts = ['=10.0.0', '=2.25.1', '=4.65.0']
            for artifact in pip_artifacts:
                artifact_path = self.file_scripts_path / artifact
                if artifact_path.exists():
                    if self._safe_remove(artifact_path):
                        total_cleaned += 1
                    else:
                        failed_paths.append(str(artifact_path))

            # Report results
            if total_cleaned > 0:
                self.console.print(f"[green]✓[/] Cleaned {total_cleaned} items")
            
            if failed_paths:
                self.console.print("[yellow]Warning: Some items could not be removed:[/]")
                for path in failed_paths[:5]:
                    self.console.print(f"[yellow]  - {path}[/]")
                if len(failed_paths) > 5:
                    self.console.print(f"[yellow]  ... and {len(failed_paths) - 5} more[/]")
                return True
            
            self.console.print("[green]✓[/] Directory structure cleaned successfully")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error during cleanup:[/]\n{str(e)}")
            if self.debug_mode:
                import traceback
                self.console.print(f"[dim]{traceback.format_exc()}[/]")
            return False

    def setup_dependencies(self):
        """Install required Python packages."""
        self.console.print("\n[bold blue]Setting up dependencies...[/]")
        
        try:
            # First verify if safetensors is already installed
            success, output = self._run_command("pip show safetensors")
            if success:
                self.console.print("[green]✓[/] safetensors already installed")
            else:
                # Install safetensors if not present
                success, output = self._run_command("pip install safetensors")
                if not success:
                    self.console.print("[red]Failed to install safetensors:[/]\n{output}")
                    return False
                self.console.print("[green]✓[/] safetensors installed")

            # Install other dependencies with proper version specifiers
            other_deps = [
                "rich>=10.0.0",
                "requests>=2.25.1",
                "tqdm>=4.65.0"
            ]
            
            for dep in other_deps:
                # Use pip install without creating version files
                success, output = self._run_command(f"python -m pip install '{dep}'")
                if not success:
                    self.console.print(f"[red]Failed to install {dep}:[/]\n{output}")
                    return False
                if self.debug_mode:
                    self.console.print(f"[dim]Installed {dep}[/]")
        
            self.console.print("[green]✓[/] All dependencies installed")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error installing dependencies:[/]\n{str(e)}")
            return False

    def setup_rclone(self):
        """Configure rclone if config file is present."""
        self.console.print("\n[bold blue]Configuring rclone...[/]")
        try:
            rclone_config_dir = Path(os.path.expanduser('~/.config/rclone'))
            os.makedirs(rclone_config_dir, exist_ok=True)
            
            rclone_src = self.workspace_path / 'rclone.conf'
            rclone_dst = rclone_config_dir / 'rclone.conf'
            
            if not rclone_src.exists():
                self.console.print("[yellow]Warning: rclone.conf not found in workspace[/]")
                return True

            shutil.copy2(rclone_src, rclone_dst)
            self.console.print("[green]✓[/] Configured rclone")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error configuring rclone:[/]\n{str(e)}")
            return False

    def check_git_credentials(self):
        """Check and setup git credentials if needed."""
        try:
            netrc_path = Path(os.path.expanduser("~/.netrc"))
            
            # Check if .netrc exists and has correct permissions
            if not netrc_path.exists():
                self.console.print("[yellow]Warning: .netrc file not found, creating...[/]")
                with open(netrc_path, 'w') as f:
                    f.write("""machine github.com
login rafstahelin
password your_pat_token""")
                os.chmod(netrc_path, 0o600)
                self.console.print("[green]✓[/] .netrc file created with secure permissions")
            
            # Check permissions
            current_perms = os.stat(netrc_path).st_mode & 0o777
            if current_perms != 0o600:
                self.console.print("[yellow]Warning: .netrc file has incorrect permissions, fixing...[/]")
                os.chmod(netrc_path, 0o600)
                self.console.print("[green]✓[/] .netrc permissions corrected")
                
            # Check git config
            success, name = self._run_command('git config --get user.name')
            success2, email = self._run_command('git config --get user.email')
            
            if not success or not success2:
                self.console.print("[yellow]Git user not configured, setting up...[/]")
                self._run_command('git config --global user.name "rafstahelin"')
                self._run_command('git config --global user.email "raf@raf.studio"')
                self.console.print("[green]✓[/] Git configuration completed")
                
            return True
                
        except Exception as e:
            if self.debug_mode:
                self.console.print(f"[red]Error setting up git credentials: {str(e)}[/]")
            return False

    def sync_git_repo(self):
        """Check git repository status and report differences."""
        self.console.print("\n[bold blue]Checking git repository status...[/]")
        
        # Check git credentials first
        if not self.check_git_credentials():
            self.console.print("[yellow]Warning: Git credentials setup failed, some operations may be limited[/]")
        
        # Check if repo exists locally
        if not self.file_scripts_path.exists():
            self.console.print("[yellow]Repository not found. Cloning...[/]")
            success, output = self._run_command(
                "git clone https://github.com/rafstahelin/file-scripts.git /workspace/file-scripts"
            )
            if not success:
                self.console.print(f"[red]Failed to clone repository:[/]\n{output}")
                return False

        # Get current branch
        success, current_branch = self._run_command("git rev-parse --abbrev-ref HEAD")
        if not success:
            self.console.print("[red]Failed to get current branch[/]")
            return False
        
        self.console.print(f"[green]Current branch:[/] {current_branch.strip()}")

        # Fetch to update remote refs (without merging)
        success, _ = self._run_command("git fetch --all --quiet")
        if not success:
            self.console.print("[yellow]Warning: Failed to fetch from remote[/]")
        
        # Check for unpushed commits
        success, unpushed = self._run_command("git log @{u}..HEAD --oneline")
        if success and unpushed.strip():
            self.console.print("\n[yellow]Unpushed commits:[/]")
            for line in unpushed.strip().split('\n'):
                self.console.print(f"  {line}")
        
        # Check for unstaged changes
        success, unstaged = self._run_command("git diff --name-status")
        if success and unstaged.strip():
            self.console.print("\n[yellow]Unstaged changes:[/]")
            for line in unstaged.strip().split('\n'):
                self.console.print(f"  {line}")
        
        # Check for staged changes
        success, staged = self._run_command("git diff --staged --name-status")
        if success and staged.strip():
            self.console.print("\n[yellow]Staged changes:[/]")
            for line in staged.strip().split('\n'):
                self.console.print(f"  {line}")
        
        # Check for untracked files
        success, untracked = self._run_command("git ls-files --others --exclude-standard")
        if success and untracked.strip():
            self.console.print("\n[yellow]Untracked files:[/]")
            for line in untracked.strip().split('\n'):
                self.console.print(f"  {line}")

        # Compare with dev branch without merging
        success, diff_dev = self._run_command("git rev-list --left-right --count origin/dev...HEAD")
        if success:
            behind, ahead = map(int, diff_dev.strip().split())
            if behind > 0:
                self.console.print(f"\n[yellow]Your branch is behind dev by {behind} commit(s)[/]")
            if ahead > 0:
                self.console.print(f"[green]Your branch is ahead of dev by {ahead} commit(s)[/]")
        
        self.console.print("\n[green]✓[/] Git status check completed")
        return True

    def setup_tools_shortcut(self):
        """Setup tools.py shortcut and navigation aliases that persist in network volume."""
        self.console.print("\n[bold blue]Setting up shortcuts...[/]")
        
        try:
            # Create shortcuts in /usr/local/bin
            bin_path = Path('/usr/local/bin')
            bin_path.mkdir(parents=True, exist_ok=True)
            
            # Setup the tools launcher
            tools_script = """#!/bin/bash
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
            tools_path = bin_path / 'tools'
            if tools_path.exists():
                tools_path.unlink()
            tools_path.write_text(tools_script)
            tools_path.chmod(0o755)
    
            # Setup navigation aliases in persistent bashrc with correct paths
            bashrc_path = Path('/root/.bashrc')
            if bashrc_path.exists():
                # Read current content
                current_content = bashrc_path.read_text()
                
                # Remove old shortcuts section if it exists
                if '# Tools shortcuts' in current_content:
                    lines = current_content.split('\n')
                    new_lines = []
                    skip_mode = False
                    
                    for line in lines:
                        if '# Tools shortcuts' in line:
                            skip_mode = True
                            continue
                        if skip_mode and line.strip() == '':
                            skip_mode = False
                            continue
                        if not skip_mode:
                            new_lines.append(line)
                    
                    current_content = '\n'.join(new_lines)
                
                # Define navigation shortcuts with correct paths
                navigation_aliases = """
    # Tools shortcuts
    alias tools='tools'
    
    # Navigation shortcuts for workspace paths
    alias config='cd /workspace/SimpleTuner/config'
    alias data='cd /workspace/SimpleTuner/datasets'
    alias out='cd /workspace/SimpleTuner/output'
    alias flux='cd /workspace/StableSwarmUI/Models/loras/flux'
    alias scripts='cd /workspace/file-scripts'
    """
                # Write the updated content back
                with bashrc_path.open('w') as f:
                    f.write(current_content.rstrip() + '\n' + navigation_aliases)
    
                # Try to reload bashrc
                success, output = self._run_command('source ~/.bashrc')
                if not success:
                    self.console.print("[yellow]Warning: Could not automatically reload bashrc[/]")
                    self.console.print("[yellow]Please run 'source ~/.bashrc' manually[/]")
    
            self.console.print("[green]✓[/] Shortcuts installed successfully")
            self.console.print("[dim]Note: Shortcuts are installed in the network volume and will persist across sessions[/]")
            
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
                self.console.print("[yellow]Skipping WANDB setup - add WANDB_API_KEY to your environment if needed[/]")
                return True
    
            os.environ['WANDB_API_KEY'] = wandb_key
            
            success, output = self._run_command('wandb login --relogin')
            if not success:
                self.console.print("[yellow]WANDB login failed, but continuing...[/]")
                self.console.print("[yellow]You can set up WANDB manually later if needed[/]")
                return True
    
            self.console.print("[green]✓[/] WANDB configured successfully")
            return True
                    
        except Exception as e:
            self.console.print(f"[yellow]WANDB setup skipped: {str(e)}[/]")
            self.console.print("[yellow]You can set up WANDB manually later if needed[/]")
            return True
    
    def run(self):
        """Main execution method."""
        self.console.print("[bold cyan]File-Scripts Setup Tool[/]")
        self.console.print("[dim]Version: 0.8.0[/]")  # Updated version number
        
        steps = [
            (self.cleanup_structure, "Cleaning directory structure"),
            (self.setup_dependencies, "Installing dependencies"),
            (self.setup_rclone, "Configuring rclone"),
            (self.sync_git_repo, "Checking git repository"),
            (self.setup_tools_shortcut, "Setting up tools launcher"),
            (self.setup_wandb, "Configuring WANDB")
        ]
        
        success = True
        for step_func, step_name in track(steps, description="[cyan]Setting up environment...[/]"):
            if not step_func():
                self.console.print(f"\n[red]✗ Failed:[/] {step_name}")
                success = False
                if not Confirm.ask("[yellow]Continue with remaining steps?[/]"):
                    break
        
        status = "[green]✓ Setup completed successfully[/]" if success else "[yellow]⚠ Setup completed with warnings[/]"
        self.console.print(f"\n{status}")
        
        if Confirm.ask("\nReturn to main menu?"):
            return

if __name__ == "__main__":
    tool = Tool()
    tool.run()
                