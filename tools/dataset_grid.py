import os
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.prompt import Prompt
from PIL import Image
import json
import math

class DatasetGridTool:
    def __init__(self):
        self.console = Console()
        self.config_path = Path('/workspace/SimpleTuner/config')
        self.datasets_path = Path('/workspace/SimpleTuner/datasets')

    def list_config_folders(self) -> List[str]:
        """List configuration folders grouped by base name."""
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
            
            # Add "process all" option for each group
            content.append(f"[yellow]{index}.[/yellow] all")
            ordered_folders.append(f"{base_name}:all")
            index += 1
            
            # Add individual folders
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
        """Extract dataset path from multidatabackend.json."""
        backend_file = config_dir / "multidatabackend.json"
        try:
            with open(backend_file) as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict) and 'instance_data_dir' in item:
                        dataset_path = item['instance_data_dir'].split('/')[-1]
                        return self.datasets_path / dataset_path
        except Exception as e:
            self.console.print(f"[red]Error reading dataset path: {str(e)}[/red]")
        return None

    def create_grid(self, images: List[Path], output_path: Path, title: str):
        """Create and save image grid."""
        pil_images = []
        for img_path in images:
            try:
                img = Image.open(img_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                pil_images.append(img)
            except Exception as e:
                self.console.print(f"[red]Error loading {img_path}: {str(e)}[/red]")

        if not pil_images:
            return

        n = len(pil_images)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        cell_width = 512
        cell_height = 512
        title_height = 60

        grid = Image.new('RGB', 
                        (cols * cell_width, rows * cell_height + title_height),
                        'white')

        for idx, img in enumerate(pil_images):
            row = idx // cols
            col = idx % cols
            img.thumbnail((cell_width, cell_height), Image.Resampling.LANCZOS)
            
            x = col * cell_width
            y = row * cell_height + title_height
            grid.paste(img, (x, y))

        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(grid)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        draw.text((grid.width//2, title_height//2), title, 
                  fill='black', font=font, anchor="mm")

        quality = 95
        while True:
            test_path = output_path.with_suffix('.tmp.jpg')
            grid.save(test_path, 'JPEG', quality=quality)
            if test_path.stat().st_size <= 15_000_000 or quality <= 30:
                test_path.rename(output_path)
                break
            quality -= 5

    def process_single_config(self, config_dir):
        dataset_dir = self.get_dataset_path(config_dir)
        if not dataset_dir:
            self.console.print("[red]Could not find dataset path in config[/red]")
            return

        if not dataset_dir.exists():
            self.console.print(f"[red]Dataset directory not found: {dataset_dir}[/red]")
            return

        images = list(dataset_dir.glob("*.jpg")) + \
                list(dataset_dir.glob("*.jpeg")) + \
                list(dataset_dir.glob("*.png"))

        if not images:
            self.console.print("[red]No images found in dataset directory[/red]")
            return

        output_file = config_dir / f"{config_dir.name}-dataset-grid.jpg"
        title = f"{config_dir.name} - {dataset_dir.name}"
        
        self.console.print("[cyan]Creating dataset grid...[/cyan]")
        self.create_grid(images, output_file, title)
        self.console.print(f"[cyan]Grid saved to: {output_file}[/cyan]")

    def run(self):
        config_folders = self.list_config_folders()
        if not config_folders:
            self.console.print("[red]No configuration folders found[/red]")
            return

        from rich.prompt import Prompt  # Change back to regular Prompt
        folder_num = Prompt.ask("Enter number to select config").strip()
        if not folder_num:
            return


        try:
            selected = config_folders[int(folder_num) - 1]
            
            # Handle "all" selection for a group
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
                
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")
            return

class Tool:
    def __init__(self):
        self.tool = DatasetGridTool()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()
