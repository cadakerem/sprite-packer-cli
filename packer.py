import argparse
import os
import json
from pathlib import Path
from PIL import Image

def get_image_files(input_dir):
    input_path = Path(input_dir)
    return list(input_path.glob('*.png'))

def shelf_pack(images, max_width=1024):
    """
    Very basic shelf packing algorithm.
    images: list of tuples (filename, PIL.Image)
    Returns: (width, height, frames_dict) where frames_dict maps filename to (x, y, w, h)
    """
    frames = {}
    current_x = 0
    current_y = 0
    row_height = 0
    max_w = 0
    
    # Sort images by height descending for a slightly better shelf pack
    images.sort(key=lambda img: img[1].size[1], reverse=True)
    
    for filename, img in images:
        w, h = img.size
        
        # Check if we need to wrap to the next row
        if current_x + w > max_width and current_x > 0:
            current_x = 0
            current_y += row_height
            row_height = 0
            
        frames[filename] = (current_x, current_y, w, h)
        
        current_x += w
        row_height = max(row_height, h)
        max_w = max(max_w, current_x)
        
    total_height = current_y + row_height
    return max_w, total_height, frames

def generate_spritesheet(input_dir, output_image_path, output_json_path, max_width=1024):
    image_paths = get_image_files(input_dir)
    if not image_paths:
        print("Hata: Eşleşen dosya bulunamadı.")
        return
        
    images = []
    for p in image_paths:
        try:
            img = Image.open(p)
            images.append((p.name, img))
        except Exception as e:
            print(f"Error loading {p}: {e}")
            
    if not images:
        return
        
    width, height, frames_info = shelf_pack(images, max_width)
    
    # Create the output image
    spritesheet = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    
    # TexturePacker JSON Array Format
    json_data = {
        "frames": [],
        "meta": {
            "app": "Sprite Packer CLI",
            "version": "1.0",
            "image": os.path.basename(output_image_path),
            "format": "RGBA8888",
            "size": {"w": width, "h": height},
            "scale": "1"
        }
    }
    
    for filename, img in images:
        x, y, w, h = frames_info[filename]
        spritesheet.paste(img, (x, y))
        
        frame_data = {
            "filename": filename,
            "frame": {"x": x, "y": y, "w": w, "h": h},
            "rotated": False,
            "trimmed": False,
            "spriteSourceSize": {"x": 0, "y": 0, "w": w, "h": h},
            "sourceSize": {"w": w, "h": h}
        }
        json_data["frames"].append(frame_data)
        
    # Save files
    os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
    spritesheet.save(output_image_path)
    
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4)
        
    print(f"Spritesheet created successfully: {output_image_path} ({width}x{height})")
    print(f"JSON data created successfully: {output_json_path}")

def main():
    parser = argparse.ArgumentParser(description="Sprite Sheet Packer CLI")
    parser.add_argument("input_dir", help="Directory containing input PNG files")
    parser.add_argument("output_image", help="Output spritesheet image path (e.g., output.png)")
    parser.add_argument("output_json", help="Output JSON data path (e.g., output.json)")
    parser.add_argument("--max-width", type=int, default=1024, help="Maximum width of the spritesheet")
    
    args = parser.parse_args()
    
    generate_spritesheet(args.input_dir, args.output_image, args.output_json, args.max_width)

if __name__ == "__main__":
    main()
