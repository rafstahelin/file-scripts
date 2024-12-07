import os
import sys
from pathlib import Path
import traceback
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.prompt import Prompt

class ValidationGridTool:
    def __init__(self):
        self.console = Console()
        self.debug = True
        
        try:
            # Verify workspace path
            self.workspace_path = Path('/workspace/SimpleTuner')
            self.log(f"Workspace path: {self.workspace_path}")
            if not self.workspace_path.exists():
                raise ValueError(f"Workspace path does not exist: {self.workspace_path}")
            
            # Verify other paths
            self.output_path = self.workspace_path / 'output'
            self.config_path = self.workspace_path / 'config'
            
            self.log(f"Output path: {self.output_path}")
            self.log(f"Config path: {self.config_path}")
            
            if not self.output_path.exists():
                raise ValueError(f"Output path does not exist: {self.output_path}")
            if not self.config_path.exists():
                raise ValueError(f"Config path does not exist: {self.config_path}")
            
            # Grid layout parameters
            self.top_margin = 240  # Tripled from original
            self.padding = 40
            self.title_height = 240  # Tripled for main title area
            self.image_title_height = 60
            
            # Separate font sizes for main title and image titles
            self.main_title_font_size = 144  # Tripled for main title
            self.image_title_font_size = 48  # Original size for image titles
            
        except Exception as e:
            self.log(f"Error during initialization: {str(e)}")
            self.log(traceback.format_exc())
            raise

    def log(self, message: str):
        """Debug logging function"""
        if self.debug:
            self.console.print(f"[cyan]DEBUG: {message}[/cyan]")

    def verify_dependencies(self) -> bool:
        """Verify all required dependencies are available"""
        try:
            try:
                from PIL import Image, ImageDraw, ImageFont
                self.log("PIL/Pillow available")
            except ImportError:
                self.console.print("[red]Error: PIL/Pillow not installed[/red]")
                return False
            return True
        except Exception as e:
            self.log(f"Error in verify_dependencies: {str(e)}")
            self.log(traceback.format_exc())
            return False

    def parse_image_info(self, filename: str) -> Tuple[int, str, Tuple[int, int]]:
        """Parse step number, concept, and resolution from filename."""
        pattern = r'step_(\d+)_(.+?)_(\d+)x(\d+)\.png'
        import re
        match = re.match(pattern, filename)
        if not match:
            raise ValueError(f"Invalid filename format: {filename}")
            
        step = int(match.group(1))
        concept = match.group(2)
        width = int(match.group(3))
        height = int(match.group(4))
        return step, concept, (width, height)

    def group_images(self, images: List[Path]) -> Dict[int, Dict[str, Path]]:
        """Group images by step and concept, excluding step_0."""
        groups: Dict[int, Dict[str, Path]] = {}
        
        for img_path in images:
            try:
                step, concept, _ = self.parse_image_info(img_path.name)
                if step == 0:  # Skip step_0 images
                    continue
                    
                if step not in groups:
                    groups[step] = {}
                groups[step][concept] = img_path
            except ValueError as e:
                self.log(f"Warning: Skipping {img_path.name} - {str(e)}")
                
        return dict(sorted(groups.items(), reverse=True))

    def calculate_grid_dimensions(self, grouped_images: Dict[int, Dict[str, Path]]) -> Tuple[List[str], List[int], Tuple[int, int]]:
        """Calculate grid dimensions and get unique concepts and steps."""
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

    def scan_model_versions(self, model_name: str) -> list:
        """Scan for model versions in both output and config directories."""
        versions = set()
        
        # Check output directory
        output_model_path = self.output_path / model_name
        self.log(f"Scanning output path for versions: {output_model_path}")
        
        if output_model_path.exists():
            output_versions = [p.name for p in output_model_path.iterdir() 
                             if p.is_dir() and p.name != '.ipynb_checkpoints']
            versions.update(output_versions)
            self.log(f"Found versions in output: {output_versions}")
        
        # Check config directory for [model]-[version] format
        self.log(f"Scanning config path for versions: {self.config_path}")
        config_versions = [
            p.name.split('-')[-1] for p in self.config_path.iterdir()
            if p.is_dir() and p.name.startswith(f"{model_name}-")
        ]
        versions.update(config_versions)
        self.log(f"Found versions in config: {config_versions}")
        
        # Sort versions
        version_list = sorted(versions, key=lambda x: str(x))
        self.log(f"Combined unique versions: {version_list}")
        return version_list

    def create_grid(self, images: List[Path], model: str, version: str) -> Optional[Image.Image]:
        """Create a grid of validation images with enhanced titles."""
        try:
            # Group and organize images
            self.log("Grouping images by step and concept...")
            grouped_images = self.group_images(images)
            concepts, steps, (base_width, base_height) = self.calculate_grid_dimensions(grouped_images)
            
            self.log(f"Found {len(concepts)} concepts and {len(steps)} steps")
            self.log(f"Base image size: {base_width}x{base_height}")
            
            # Calculate grid dimensions with new margins
            n_cols = len(concepts)
            n_rows = len(steps)
            
            # Calculate total dimensions with updated spacing
            total_width = (base_width + self.padding) * n_cols + self.padding
            total_height = (
                self.top_margin +  # Top margin
                self.title_height +  # Main title
                (base_height + self.image_title_height + self.padding) * n_rows +  # Images with titles
                self.padding  # Bottom padding
            )
            
            self.log(f"Creating grid image of size {total_width}x{total_height}")
            
            # Create base image
            grid_image = Image.new('RGB', (total_width, total_height), 'black')
            draw = ImageDraw.Draw(grid_image)
            
            # Load fonts with different sizes
            try:
                main_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                   self.main_title_font_size)
                image_title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                    self.image_title_font_size)
                self.log("Loaded DejaVuSans-Bold fonts")
            except Exception as e:
                self.log(f"Font loading error: {str(e)}")
                self.log("Falling back to default font")
                main_title_font = ImageFont.load_default()
                image_title_font = ImageFont.load_default()
            
            # Draw main title near top edge with larger font
            main_title = f"{model}-{version} Validation Grid"
            title_bbox = draw.textbbox((0, 0), main_title, font=main_title_font)
            title_x = (total_width - (title_bbox[2] - title_bbox[0])) // 2
            draw.text((title_x, self.padding), main_title, font=main_title_font, fill='white')
            
            # Place images with their titles using smaller font
            start_y = self.top_margin + self.title_height
            for row, step in enumerate(steps):
                y = start_y + row * (base_height + self.image_title_height + self.padding)
                
                for col, concept in enumerate(concepts):
                    if concept in grouped_images[step]:
                        x = col * (base_width + self.padding) + self.padding
                        img_path = grouped_images[step][concept]
                        
                        # Draw image title with original smaller font
                        title = f"Step {step} - {concept}"
                        title_bbox = draw.textbbox((0, 0), title, font=image_title_font)
                        title_width = title_bbox[2] - title_bbox[0]
                        title_x = x + (base_width - title_width) // 2
                        draw.text((title_x, y), title, font=image_title_font, fill='white')
                        
                        self.log(f"Processing image: {img_path}")
                        # Open and paste image below its title
                        with Image.open(img_path) as img:
                            grid_image.paste(img, (x, y + self.image_title_height))
            
            self.log("Grid creation completed successfully")
            return grid_image
            
        except Exception as e:
            self.log(f"Error creating grid: {str(e)}")
            self.log(traceback.format_exc())
            return None

    def save_grid(self, grid_image: Image.Image, model: str, version: str) -> bool:
        """Save the grid image to the config directory."""
        try:
            save_dir = self.config_path / f"{model}-{version}"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = save_dir / f"{model}-{version}-validation-grid.jpg"
            grid_image.save(output_path, 'JPEG', quality=95)
            
            self.console.print(f"[green]Grid saved successfully to: {output_path}[/green]")
            return True
            
        except Exception as e:
            self.log(f"Error saving grid: {str(e)}")
            self.log(traceback.format_exc())
            return False

    def run(self):
        """Main execution method with enhanced error handling"""
        try:
            self.log("Starting validation grid tool...")
            
            # Scan for models in output directory
            self.log("Scanning for models...")
            models = [p.name for p in self.output_path.iterdir() 
                     if p.is_dir() and p.name != '.ipynb_checkpoints']
            
            if not models:
                self.console.print("[red]No models found.[/red]")
                return
            
            self.log(f"Found models: {models}")
            
            # Display models
            for idx, model in enumerate(models, 1):
                self.console.print(f"[yellow]{idx}. {model}[/yellow]")
            
            # Get model selection
            try:
                model_idx = int(Prompt.ask("Select model number", default="1")) - 1
                if not (0 <= model_idx < len(models)):
                    self.console.print("[red]Invalid selection.[/red]")
                    return
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
                return
            
            selected_model = models[model_idx]
            self.log(f"Selected model: {selected_model}")
            
            # Get versions for selected model
            versions = self.scan_model_versions(selected_model)
            
            if not versions:
                self.console.print("[red]No versions found for selected model.[/red]")
                return
            
            self.log(f"Available versions for {selected_model}: {versions}")
            
            # Display versions
            self.console.print("\n[cyan]Available versions:[/cyan]")
            for idx, version in enumerate(versions, 1):
                config_path = self.config_path / f"{selected_model}-{version}"
                output_path = self.output_path / selected_model / version
                
                status = []
                if config_path.exists():
                    status.append("config")
                if output_path.exists():
                    status.append("output")
                
                status_str = f"[dim]({', '.join(status)})[/dim]" if status else ""
                self.console.print(f"[yellow]{idx}. Version {version} {status_str}[/yellow]")
            
            # Get version selection
            try:
                version_idx = int(Prompt.ask("\nSelect version number", default="1")) - 1
                if not (0 <= version_idx < len(versions)):
                    self.console.print("[red]Invalid version selection.[/red]")
                    return
            except ValueError:
                self.console.print("[red]Invalid input. Please enter a number.[/red]")
                return
            
            selected_version = versions[version_idx]
            self.log(f"Selected version: {selected_version}")
            
            # Verify validation images path
            validation_path = self.output_path / selected_model / selected_version / 'validation_images'
            self.log(f"Checking validation images path: {validation_path}")
            
            if not validation_path.exists():
                self.console.print(f"[red]No validation images found at: {validation_path}[/red]")
                return
            
            images = list(validation_path.glob('*.png'))
            self.log(f"Found {len(images)} validation images")
            
            if not images:
                self.console.print("[red]No validation images found.[/red]")
                return
            
            # Create and save grid
            self.log("Found validation images, proceeding with grid creation")
            grid_image = self.create_grid(images, selected_model, selected_version)
            
            if grid_image:
                self.log("Grid created successfully, saving...")
                if self.save_grid(grid_image, selected_model, selected_version):
                    self.console.print("[green]Grid created and saved successfully![/green]")
                else:
                    self.console.print("[red]Error saving grid image.[/red]")
            else:
                self.console.print("[red]Error creating validation grid.[/red]")
            
        except Exception as e:
            self.log(f"Error in run method: {str(e)}")
            self.log(traceback.format_exc())
            self.console.print("[red]An error occurred. Check the debug output above for details.[/red]")

class Tool:
    def __init__(self):
        try:
            self.console = Console()
            self.console.print("[cyan]Initializing Validation Grid Tool...[/cyan]")
            self.tool = ValidationGridTool()
        except Exception as e:
            self.console.print(f"[red]Error initializing tool: {str(e)}[/red]")
            raise
    
    def run(self):
        try:
            self.tool.run()
        except Exception as e:
            self.console.print(f"[red]Error running tool: {str(e)}[/red]")
            self.console.print("Press Enter to continue...")
            input()

if __name__ == "__main__":
    tool = Tool()
    tool.run()