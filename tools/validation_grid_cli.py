# Script to create a validation grid from model output images
# Run with: python script.py --model <model_name> --version <version_number>
# Expects images in: /workspace/SimpleTuner/output/<model>/<version>/validation_images/
# Saves grid to: /workspace/SimpleTuner/config/<model>-<version>/

import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import sys
import re

class ValidationGridTool:
    def __init__(self):
        # Grid layout parameters
        self.top_margin = 240
        self.padding = 40
        self.title_height = 240
        self.image_title_height = 60
        self.main_title_font_size = 144
        self.image_title_font_size = 48

    def parse_image_info(self, filename: str):
        """Parse step number, concept, and resolution from filename."""
        pattern = r'step_(\d+)_(.+?)_(\d+)x(\d+)\.png'
        match = re.match(pattern, filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")
            
        step = int(match.group(1))
        concept = match.group(2)
        width = int(match.group(3))
        height = int(match.group(4))
        return step, concept, (width, height)

    def group_images(self, images: list):
        """Group images by step and concept, excluding step_0."""
        groups = {}
        
        for img_path in images:
            try:
                step, concept, _ = self.parse_image_info(img_path.name)
                if step == 0:  # Skip step_0 images
                    continue
                    
                if step not in groups:
                    groups[step] = {}
                groups[step][concept] = img_path
            except ValueError:
                continue
                
        return dict(sorted(groups.items(), reverse=True))

    def calculate_grid_dimensions(self, grouped_images):
        if not grouped_images:
            raise ValueError("No valid images found for grid creation")
            
        all_concepts = list(dict.fromkeys(
            concept for step_images in grouped_images.values() 
            for concept in step_images.keys()
        ))
        
        steps = list(grouped_images.keys())
        
        first_image = next(iter(next(iter(grouped_images.values())).values()))
        sample_img = Image.open(first_image)
        base_size = sample_img.size
        
        return all_concepts, steps, base_size

    def create_grid(self, images, model, version):
        try:
            grouped_images = self.group_images(images)
            concepts, steps, (base_width, base_height) = self.calculate_grid_dimensions(grouped_images)
            
            n_cols = len(concepts)
            n_rows = len(steps)
            
            total_width = (base_width + self.padding) * n_cols + self.padding
            total_height = (
                self.top_margin +
                self.title_height +
                (base_height + self.image_title_height + self.padding) * n_rows +
                self.padding
            )
            
            grid_image = Image.new('RGB', (total_width, total_height), 'black')
            draw = ImageDraw.Draw(grid_image)
            
            try:
                main_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                   self.main_title_font_size)
                image_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                    self.image_title_font_size)
            except Exception:
                main_title_font = ImageFont.load_default()
                image_title_font = ImageFont.load_default()
            
            main_title = f"{model}-{version} Validation Grid"
            title_bbox = draw.textbbox((0, 0), main_title, font=main_title_font)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, self.padding), main_title, font=main_title_font, fill='white')
            
            start_y = self.top_margin + self.title_height
            for row, step in enumerate(steps):
                y = start_y + row * (base_height + self.image_title_height + self.padding)
                
                for col, concept in enumerate(concepts):
                    if concept in grouped_images[step]:
                        x = col * (base_width + self.padding) + self.padding
                        img_path = grouped_images[step][concept]
                        
                        title = f"Step {step} - {concept}"
                        title_bbox = draw.textbbox((0, 0), title, font=image_title_font)
                        title_width = title_bbox[2] - title_bbox[0]
                        title_x = x + (base_width - title_width) // 2
                        draw.text((title_x, y), title, font=image_title_font, fill='white')
                        
                        with Image.open(img_path) as img:
                            grid_image.paste(img, (x, y + self.image_title_height))
            
            return grid_image
            
        except Exception as e:
            print(f"Error creating grid: {str(e)}")
            return None

    def save_grid(self, grid_image: Image.Image, model: str, version: str, config_path: Path) -> bool:
        try:
            save_dir = config_path / f"{model}-{version}"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = save_dir / f"{model}-{version}-validation-grid.jpg"
            grid_image.save(output_path, 'JPEG', quality=95)
            
            print(f"Grid saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error saving grid: {str(e)}")
            return False

def create_validation_grid(workspace_path: str, model: str, version: str):
    workspace_path = Path(workspace_path)
    output_base = workspace_path / 'output'
    config_path = workspace_path / 'config'
    
    # Construct validation images path
    validation_path = output_base / model / version / 'validation_images'
    if not validation_path.exists():
        print(f"Error: Validation path not found: {validation_path}")
        return False
        
    images = list(validation_path.glob('*.png'))
    if not images:
        print("No validation images found.")
        return False
        
    print(f"Found {len(images)} validation images")
    
    tool = ValidationGridTool()
    grid_image = tool.create_grid(images, model, version)
    if grid_image:
        return tool.save_grid(grid_image, model, version, config_path)
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create validation grid')
    parser.add_argument('--model', required=True, help='Model name (e.g., amelia)')
    parser.add_argument('--version', required=True, help='Model version')
    
    args = parser.parse_args()
    
    success = create_validation_grid('/workspace/SimpleTuner', args.model, args.version)
    if not success:
        sys.exit(1)