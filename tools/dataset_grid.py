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
            # Use the first `_` or `-` as the delimiter to determine the base name
            if "_" in folder.name:
                base_name = folder.name.split('_', 1)[0]
            elif "-" in folder.name:
                base_name = folder.name.split('-', 1)[0]
            else:
                base_name = folder.name
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

    def list_config_families(self) -> List[str]:
        """List families (base names) grouped from configuration folders."""
        folders = [f for f in self.config_path.iterdir() 
                if f.is_dir() and f.name != 'templates' 
                and not f.name.startswith('.ipynb_checkpoints')]

        # Group folders by base name
        grouped = {}
        for folder in folders:
            # Use the first `_` or `-` as the delimiter to determine the base name
            if "_" in folder.name:
                base_name = folder.name.split('_', 1)[0]
            elif "-" in folder.name:
                base_name = folder.name.split('-', 1)[0]
            else:
                base_name = folder.name
            grouped.setdefault(base_name, []).append(folder.name)

        # Return sorted list of families
        return sorted(grouped.keys()), grouped

    def get_dataset_path(self, config_dir: Path) -> Optional[Path]:
        """Extract dataset path from multidatabackend.json."""
        backend_file = config_dir / "multidatabackend.json"
        try:
            with open(backend_file) as f:
                data = json.load(f)
                for item in data:
                    if isinstance(item, dict) and 'instance_data_dir' in item:
                        # Extract dataset path as-is
                        dataset_path = item['instance_data_dir'].split('/')[-1]
                        return self.datasets_path / dataset_path
        except Exception as e:
            self.console.print(f"[red]Error reading dataset path: {str(e)}[/red]")
        return None

    def create_grid(self, images: List[Path], output_path: Path, title: str) -> Optional[Image.Image]:
        """Create and save an image grid."""
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
            return None

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
        
        draw.text((grid.width // 2, title_height // 2), title,
                fill='black', font=font, anchor="mm")

        # Save high-resolution grid
        quality = 95
        while True:
            test_path = output_path.with_suffix('.tmp.jpg')
            grid.save(test_path, 'JPEG', quality=quality)
            if test_path.stat().st_size <= 15_000_000 or quality <= 30:
                test_path.rename(output_path)
                break
            quality -= 5

        return grid

    def process_single_config(self, config_dir: Path):
        dataset_dir = self.get_dataset_path(config_dir)
        if not dataset_dir:
            self.console.print("[red]Could not find dataset path in config[/red]")
            return

        if not dataset_dir.exists():
            self.console.print(f"[red]Dataset directory not found: {dataset_dir}[/red]")
            return

        # Collect all image files from the dataset directory
        images = list(dataset_dir.glob("*.jpg")) + \
                list(dataset_dir.glob("*.jpeg")) + \
                list(dataset_dir.glob("*.png"))

        if not images:
            self.console.print("[red]No images found in dataset directory[/red]")
            return

        # Construct output file names
        output_file = config_dir / f"{config_dir.name}-dataset_grid.jpg"
        low_res_file = config_dir / f"{config_dir.name}-dataset_grid_lores.jpg"
        title = f"{config_dir.name} - {dataset_dir.name}"

        self.console.print("[cyan]Creating dataset grid...[/cyan]")
        
        # Create and save the high-resolution grid
        grid_image = self.create_grid(images, output_file, title)
        
        # Save a lower-resolution version
        if grid_image:
            self.save_low_res_version(grid_image, low_res_file)

        self.console.print(f"[cyan]Grid saved to: {output_file}[/cyan]")
        self.console.print(f"[cyan]Low-res grid saved to: {low_res_file}[/cyan]")

    def save_low_res_version(self, image: Image.Image, output_path: Path):
        """Save a lower-resolution version of an image with specific size constraints."""
        max_longest_side = 8192
        max_shortest_side = 4096

        width, height = image.size

        # Determine scaling factor to satisfy both constraints
        scaling_factor = min(max_longest_side / max(width, height), max_shortest_side / min(width, height))

        # Resize only if scaling is necessary
        if scaling_factor < 1.0:
            new_width = int(width * scaling_factor)
            new_height = int(height * scaling_factor)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save the resized image
        image.save(output_path, 'JPEG', quality=95)

    def run(self):
        # Step 1: List families
        families, grouped_configs = self.list_config_families()
        if not families:
            self.console.print("[red]No configuration families found[/red]")
            return

        self.console.print("\n[bold yellow]Available Families[/bold yellow]")
        for idx, family in enumerate(families, start=1):
            self.console.print(f"[yellow]{idx}.[/yellow] {family}")

        # Step 2: Prompt user to select a family
        family_num = Prompt.ask("Select a family number", choices=[str(i) for i in range(1, len(families) + 1)])
        selected_family = families[int(family_num) - 1]

        # Step 3: Show configurations within the selected family
        configs_in_family = sorted(grouped_configs[selected_family])
        self.console.print(f"\n[bold yellow]Configurations in {selected_family}[/bold yellow]")
        for idx, config in enumerate(configs_in_family, start=1):
            self.console.print(f"[yellow]{idx}.[/yellow] {config}")

        # Step 4: Prompt user to select a configuration
        config_num = Prompt.ask("Enter number to select config", choices=[str(i) for i in range(1, len(configs_in_family) + 1)])
        
        try:
            selected_config = configs_in_family[int(config_num) - 1]
            config_dir = self.config_path / selected_config
            self.process_single_config(config_dir)
            
        except (ValueError, IndexError):
            self.console.print("[red]Invalid selection[/red]")

class Tool:
    def __init__(self):
        self.tool = DatasetGridTool()
    
    def run(self):
        self.tool.run()

if __name__ == "__main__":
    tool = Tool()
    tool.run()
