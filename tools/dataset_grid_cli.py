# Script to create image grids from dataset directories, with recursive image search
# Run with: python script.py --config <config_name> or --config <base_name>:all

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
import json
import math

class DatasetGridTool:
    def __init__(self):
        self.cell_width = 512
        self.cell_height = 512
        self.title_height = 60
        self.font_size = 40

    def get_dataset_path(self, config_dir: Path, datasets_path: Path, workspace_path: Path) -> Path:
        """Parse multidatabackend.json to get instance_data_dir, excluding mask paths"""
        backend_file = config_dir / "multidatabackend.json"
        if not backend_file.exists():
            raise FileNotFoundError(f"multidatabackend.json not found in {config_dir}")
            
        try:
            with open(backend_file) as f:
                data = json.load(f)
                # Get first non-mask instance_data_dir
                for item in data:
                    if isinstance(item, dict) and 'instance_data_dir' in item:
                        path = item['instance_data_dir']
                        # Skip any path containing /msk/
                        if '/msk/' not in path:
                            return workspace_path / path
            raise FileNotFoundError(f"No valid image paths found in {backend_file}")
        except Exception as e:
            print(f"Error reading multidatabackend.json: {str(e)}")
            raise

    def find_images_recursively(self, directory: Path) -> list:
        """Find all images recursively, excluding /msk paths"""
        images = []
        for ext in ('*.jpg', '*.jpeg', '*.png'):
            for img_path in directory.rglob(ext):
                # Skip if path contains /msk/
                if '/msk/' not in str(img_path):
                    images.append(img_path)
        return sorted(images)  # Sort for consistent order

    def create_grid(self, images: list, output_path: Path, title: str):
        pil_images = []
        for img_path in images:
            try:
                img = Image.open(img_path)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                pil_images.append(img)
            except Exception as e:
                print(f"Error loading {img_path}: {str(e)}")
                continue

        if not pil_images:
            raise ValueError("No valid images could be loaded")

        n = len(pil_images)
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        grid = Image.new('RGB', 
                        (cols * self.cell_width, rows * self.cell_height + self.title_height),
                        'white')

        for idx, img in enumerate(pil_images):
            row = idx // cols
            col = idx % cols
            img.thumbnail((self.cell_width, self.cell_height), Image.Resampling.LANCZOS)
            
            x = col * self.cell_width
            y = row * self.cell_height + self.title_height
            grid.paste(img, (x, y))

        draw = ImageDraw.Draw(grid)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text((grid.width//2, self.title_height//2), title, 
                  fill='black', font=font, anchor="mm")

        quality = 95
        while True:
            test_path = output_path.with_suffix('.tmp.jpg')
            grid.save(test_path, 'JPEG', quality=quality)
            if test_path.stat().st_size <= 15_000_000 or quality <= 30:
                test_path.rename(output_path)
                break
            quality -= 5
            
        print(f"Grid saved to: {output_path}")
        return True

def create_dataset_grid(workspace_path: str, config_name: str):
    workspace_path = Path(workspace_path)
    config_path = workspace_path / 'config'
    datasets_path = workspace_path / 'datasets'
    
    if ':all' in config_name:
        base_name = config_name.split(':')[0]
        configs = [f.name for f in config_path.iterdir() 
                  if f.is_dir() and f.name.startswith(base_name) 
                  and not f.name.startswith('.ipynb_checkpoints')]
    else:
        configs = [config_name]
    
    tool = DatasetGridTool()
    success = True
    
    for config in configs:
        try:
            config_dir = config_path / config
            if not config_dir.exists() or not config_dir.is_dir():
                print(f"Config directory not found: {config_dir}")
                success = False
                continue
            
            # Try to get dataset path, first from json then direct path
            dataset_dir = tool.get_dataset_path(config_dir, datasets_path, workspace_path)
            if not dataset_dir.exists():
                print(f"Dataset directory not found: {dataset_dir}")
                success = False
                continue
            
            images = tool.find_images_recursively(dataset_dir)
            if not images:
                print(f"No images found in dataset directory: {dataset_dir}")
                success = False
                continue
            
            output_file = config_dir / f"{config}-dataset-grid.jpg"
            title = f"{config} - {dataset_dir.name}"
            
            print(f"Processing {config}...")
            print(f"Found {len(images)} images in {dataset_dir}")
            tool.create_grid(images, output_file, title)
            
        except Exception as e:
            print(f"Error processing {config}: {str(e)}")
            success = False
            
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create dataset grid')
    parser.add_argument('--config', required=True, help='Config name (e.g., amelia-v1) or base name with :all (e.g., amelia:all)')
    args = parser.parse_args()
    
    success = create_dataset_grid('/workspace/SimpleTuner', args.config)
    if not success:
        sys.exit(1)