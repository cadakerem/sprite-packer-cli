import os
from PIL import Image, ImageDraw

def create_mock_png(path, size, color, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = Image.new('RGBA', size, color)
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), text, fill="black")
    img.save(path)

if __name__ == "__main__":
    examples_dir = "examples/input"
    
    # Create simple PNG files for testing
    create_mock_png(f"{examples_dir}/hero_run_1.png", (64, 64), "red", "H1")
    create_mock_png(f"{examples_dir}/hero_run_2.png", (64, 64), "red", "H2")
    create_mock_png(f"{examples_dir}/hero_run_3.png", (64, 64), "red", "H3")
    
    create_mock_png(f"{examples_dir}/zombie_walk_1.png", (32, 64), "green", "Z1")
    create_mock_png(f"{examples_dir}/zombie_walk_2.png", (32, 64), "green", "Z2")
    
    # Empty PNGs for edge cases? No, let's keep it simple first
    # Maybe add some subfolders if recursive testing is needed later
    
    print(f"Mock PNG files created in {examples_dir}")
