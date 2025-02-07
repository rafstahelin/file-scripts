from pathlib import Path
import subprocess
import os
import asyncio
from rich.console import Console
from typing import Union

class MinimalSetup:
    def __init__(self):
        self.console = Console()
        self.workspace_path = Path('/workspace')
        self.file_scripts_path = self.workspace_path / 'file-scripts'
        self.is_runpod = os.path.exists('/.dockerenv') or os.path.exists('/workspace/.runpod')

    async def run_command(self, command: str) -> bool:
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            self.console.print(f"[yellow]Command failed: {command}[/yellow]\n{str(e)}")
            return False

    async def install_dependencies(self) -> bool:
        """Install core dependencies"""
        try:
            # System dependencies (jq for JSON processing)
            if self.is_runpod:
                system_commands = [
                    "apt-get update",
                    "apt-get install -y jq",
                ]
                for cmd in system_commands:
                    if not await self.run_command(cmd):
                        return False

            # Python dependencies
            python_deps = [
                "rich>=10.0.0",
                "requests>=2.25.1",
                "tqdm>=4.65.0",
                "safetensors[numpy]",  # Numpy backend instead of torch
                "tiktoken>=0.8.0",
                "regex>=2022.1.18"
            ]
            
            tasks = [self.run_command(f"python -m pip install '{dep}'") 
                    for dep in python_deps]
            results = await asyncio.gather(*tasks)
            return all(results)
            
        except Exception as e:
            self.console.print(f"[red]Error installing dependencies: {str(e)}[/red]")
            return False

    async def setup_shortcuts(self) -> bool:
        """Create essential shortcuts and aliases"""
        try:
            # Create tools launcher
            bin_path = Path('/usr/local/bin')
            bin_path.mkdir(parents=True, exist_ok=True)
            
            tools_script = """#!/bin/bash
cd /workspace/file-scripts 2>/dev/null || cd ./file-scripts 2>/dev/null
if [ -f "tools.py" ]; then
    python tools.py
else
    echo "Error: tools.py not found"
    exit 1
fi
"""
            tools_path = bin_path / 'tools'
            tools_path.write_text(tools_script)
            tools_path.chmod(0o755)
            
            # Setup aliases
            bashrc = Path('/root/.bashrc')
            if bashrc.exists():
                # Read existing content to avoid duplicates
                current_content = bashrc.read_text()
                
                # Only add if not already present
                if '# Tools shortcuts' not in current_content:
                    aliases = """
# Tools shortcuts
alias tools='tools'
alias config='cd /workspace/SimpleTuner/config'
alias data='cd /workspace/SimpleTuner/datasets'
alias out='cd /workspace/SimpleTuner/output'
alias flux='cd /workspace/StableSwarmUI/Models/loras/flux'
alias scripts='cd /workspace/file-scripts'

# JSON processing shortcuts
alias fix-config='find . -type f -name "config.json" -exec sh -c '\''
    jq ".[\"--validation_steps\"] = (\"validation_steps/ BS\" | tonumber)" "{}" > "{}.tmp" && 
    mv "{}.tmp" "{}"
'\'' \;'

# Quick edit shortcuts
alias edit-config='python /workspace/file-scripts/tools.py set_config'
alias edit-prompts='python /workspace/file-scripts/tools.py set_prompts'
"""
                    with bashrc.open('a') as f:
                        f.write(aliases)

                    # Try to source bashrc
                    await self.run_command('source ~/.bashrc')
                    
            return True

        except Exception as e:
            self.console.print(f"[red]Error setting up shortcuts: {str(e)}[/red]")
            return False

    async def ensure_paths(self) -> bool:
        """Ensure essential directories exist"""
        try:
            paths = {
                'config': self.workspace_path / 'SimpleTuner/config',
                'datasets': self.workspace_path / 'SimpleTuner/datasets',
                'scripts': self.file_scripts_path
            }
            
            for path in paths.values():
                path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            self.console.print(f"[red]Error creating directories: {str(e)}[/red]")
            return False

    async def run(self) -> bool:
        """Main setup execution"""
        self.console.print("[cyan]Starting minimal setup...[/cyan]")
        
        # Create paths first
        if not await self.ensure_paths():
            return False
        
        # Run core setup tasks in parallel
        tasks = [
            self.install_dependencies(),
            self.setup_shortcuts()
        ]
        
        results = await asyncio.gather(*tasks)
        success = all(results)
        
        if success:
            self.console.print("\n[green]✓[/] Setup completed successfully")
            self.console.print("\n[cyan]Quick reference:[/cyan]")
            self.console.print("• Use 'tools' command to launch tools menu")
            self.console.print("• Navigation: config, data, out, flux, scripts")
            self.console.print("• Quick edits: edit-config, edit-prompts")
            self.console.print("• JSON tools: fix-config")
        else:
            self.console.print("\n[red]✗[/] Setup failed")
            
        return success

if __name__ == "__main__":
    setup = MinimalSetup()
    asyncio.run(setup.run())