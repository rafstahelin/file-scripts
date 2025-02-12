from pathlib import Path
import subprocess
import os
import shutil
from rich.console import Console
from rich.progress import track


class Tool:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.is_runpod = self._check_is_runpod()

    def _check_is_runpod(self):
        is_container = os.path.exists('/.dockerenv')
        is_runpod = os.path.exists('/workspace/.runpod')
        return is_runpod or is_container

    def _run_command(self, command, cwd=None, shell=True):
        """Execute a shell command and return the result."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or self.workspace_path,
                capture_output=True,
                text=True,
                check=True,
                shell=shell
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Error: {e.stderr}"

    def setup_rclone_bisync(self):
        """Set up Rclone Bisync alias and ensure rclone is configured."""
        self.console.print("\n[bold blue]Setting up Rclone Bisync...[/]")
        try:
            # Ensure rclone.conf exists
            rclone_config_dir = Path(os.path.expanduser('~/.config/rclone'))
            os.makedirs(rclone_config_dir, exist_ok=True)
            rclone_src = self.workspace_path / 'rclone.conf'
            rclone_dst = rclone_config_dir / 'rclone.conf'

            if not rclone_src.exists():
                self.console.print("[yellow]Warning: rclone.conf not found in workspace[/]")
                return True

            shutil.copy2(rclone_src, rclone_dst)
            self.console.print("[green]✓[/] Rclone configuration file copied")

            # Add alias for bisync
            bashrc_path = Path('/root/.bashrc')
            alias_command = (
                "alias sync='rclone bisync /workspace/ComfyUI/user/default/workflows "
                "dbx:/studio/ai/libs/comfy-data/comfyui-default/workflows --progress'"
            )

            if bashrc_path.exists():
                with bashrc_path.open('a') as f:
                    f.write(f"\n# Rclone Bisync Alias\n{alias_command}\n")
                self.console.print("[green]✓[/] Added 'sync' alias to .bashrc")
            else:
                self.console.print("[yellow]Warning: .bashrc not found, alias not added[/]")

            # Reload .bashrc
            success, output = self._run_command('source ~/.bashrc')
            if not success:
                self.console.print("[yellow]Warning: Could not automatically reload .bashrc[/]")
                self.console.print("[yellow]Please run 'source ~/.bashrc' manually[/]")

            return True

        except Exception as e:
            self.console.print(f"[red]Error setting up Rclone Bisync:[/]\n{str(e)}")
            return False

    def run(self):
        """Main execution method."""
        self.console.print("[bold cyan]RunPod Setup Tool[/]")
        steps = [
            (self.setup_rclone_bisync, "Setting up Rclone Bisync"),
        ]

        success = True
        for step_func, step_name in track(steps, description="[cyan]Setting up environment...[/]"):
            if not step_func():
                self.console.print(f"\n[red]✗ Failed:[/] {step_name}")
                success = False

        status = "[green]✓ Setup completed successfully[/]" if success else "[yellow]⚠ Setup completed with warnings[/]"
        self.console.print(f"\n{status}")


if __name__ == "__main__":
    tool = Tool()
    tool.run()
