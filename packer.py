import argparse
import os
import json
import fnmatch
import re
import sys
from pathlib import Path
from collections import defaultdict
from PIL import Image

def get_image_files(input_dir, filter_pattern=None):
    input_path = Path(input_dir)
    all_pngs = [p for p in input_path.iterdir() if p.is_file() and p.suffix.lower() == '.png']
    
    if filter_pattern:
        # Case sensitive fnmatch
        filtered = [p for p in all_pngs if fnmatch.fnmatchcase(p.name, filter_pattern)]
        return filtered
    return all_pngs

def get_prefix(filename):
    stem = Path(filename).stem
    # Remove trailing digits and optional separator (_, -)
    prefix = re.sub(r'[-_]?\d+$', '', stem)
    return prefix

class MaxRectsPacker:
    def __init__(self, max_width, max_height=8192):
        self.max_width = max_width
        self.max_height = max_height
        self.free_rects = [(0, 0, max_width, max_height)]
        
    def pack(self, width, height):
        best_node = None
        best_short_fit = float('inf')
        best_long_fit = float('inf')
        
        for r in self.free_rects:
            rx, ry, rw, rh = r
            if rw >= width and rh >= height:
                leftover_w = rw - width
                leftover_h = rh - height
                short_fit = min(leftover_w, leftover_h)
                long_fit = max(leftover_w, leftover_h)
                
                if short_fit < best_short_fit or (short_fit == best_short_fit and long_fit < best_long_fit):
                    best_node = (rx, ry, width, height)
                    best_short_fit = short_fit
                    best_long_fit = long_fit
                    
        if best_node is None:
            return None
            
        self._split_free_node(best_node)
        self._prune_free_rects()
        return best_node

    def _split_free_node(self, node):
        nx, ny, nw, nh = node
        new_free_rects = []
        for r in self.free_rects:
            rx, ry, rw, rh = r
            if nx < rx + rw and nx + nw > rx and ny < ry + rh and ny + nh > ry:
                if ny > ry:
                    new_free_rects.append((rx, ry, rw, ny - ry))
                if ny + nh < ry + rh:
                    new_free_rects.append((rx, ny + nh, rw, (ry + rh) - (ny + nh)))
                if nx > rx:
                    new_free_rects.append((rx, ry, nx - rx, rh))
                if nx + nw < rx + rw:
                    new_free_rects.append((nx + nw, ry, (rx + rw) - (nx + nw), rh))
            else:
                new_free_rects.append(r)
        self.free_rects = new_free_rects

    def _prune_free_rects(self):
        to_remove = set()
        for i, r1 in enumerate(self.free_rects):
            x1, y1, w1, h1 = r1
            for j, r2 in enumerate(self.free_rects):
                if i != j and j not in to_remove:
                    x2, y2, w2, h2 = r2
                    if x2 <= x1 and y2 <= y1 and x2 + w2 >= x1 + w1 and y2 + h2 >= y1 + h1:
                        to_remove.add(i)
                        break
        self.free_rects = [r for i, r in enumerate(self.free_rects) if i not in to_remove]

def maxrects_pack(images, max_width=1024, max_height=8192):
    # Sort images by area descending or max side descending for best packing efficiency
    images.sort(key=lambda img: max(img[1].size[0], img[1].size[1]), reverse=True)
    
    packer = MaxRectsPacker(max_width, max_height)
    frames = {}
    actual_width = 0
    actual_height = 0
    
    skipped_any = False
    for filename, img in images:
        w, h = img.size
        node = packer.pack(w, h)
        if node is None:
            print(f"Uyarı: '{filename}' görseli sığmadığı için atlandı (Maksimum boyutları aşıyor).")
            skipped_any = True
            continue
        
        x, y, w, h = node
        frames[filename] = node
        actual_width = max(actual_width, x + w)
        actual_height = max(actual_height, y + h)
        
    return actual_width, actual_height, frames, skipped_any

def process_images_and_save(image_paths, output_image_path, output_json_path, max_width, max_height):
    if not image_paths:
        print("Hata: Eşleşen dosya bulunamadı.")
        return False
        
    images = []
    for p in image_paths:
        try:
            with Image.open(p) as img:
                images.append((p.name, img.convert("RGBA")))
        except Exception as e:
            print(f"Error loading {p}: {e}")
            
    if not images:
        print("Hata: Geçerli görsel bulunamadı.")
        return False
        
    try:
        width, height, frames_info, skipped = maxrects_pack(images, max_width, max_height)
        if not frames_info:
            print("Hata: Hiçbir görsel paketlenemedi (hepsi çok büyük).")
            return False
    except Exception as e:
        print(f"Hata paketleme sırasında: {e}")
        return False
    
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
        spritesheet.paste(img, (x, y), img)
        
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
    os.makedirs(os.path.dirname(output_image_path) or '.', exist_ok=True)
    spritesheet.save(output_image_path)
    
    os.makedirs(os.path.dirname(output_json_path) or '.', exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4)
        
    print(f"Spritesheet created successfully: {output_image_path} ({width}x{height})")
    print(f"JSON data created successfully: {output_json_path}")
    return True

def generate_grouped_outputs(image_paths, base_image_path, base_json_path, max_width, max_height):
    groups = defaultdict(list)
    for p in image_paths:
        groups[get_prefix(p.name)].append(p)
        
    if not groups:
        print("Hata: Eşleşen dosya bulunamadı.")
        return False
        
    misc_group = []
    final_groups = {}
    
    for prefix, paths in groups.items():
        if len(paths) == 1:
            misc_group.extend(paths)
        else:
            final_groups[prefix] = paths
            
    if misc_group:
        final_groups['misc'] = misc_group
        
    base_img_path = Path(base_image_path)
    base_js_path = Path(base_json_path)
    
    all_success = True
    for prefix, paths in final_groups.items():
        out_img = base_img_path.with_name(f"{base_img_path.stem}_{prefix}{base_img_path.suffix}")
        out_js = base_js_path.with_name(f"{base_js_path.stem}_{prefix}{base_js_path.suffix}")
        print(f"\nProcessing group: {prefix}")
        success = process_images_and_save(paths, str(out_img), str(out_js), max_width, max_height)
        if not success:
            all_success = False
            
    return all_success

def interactive_mode():
    print("="*50)
    print("🎮 Sprite Packer CLI - İnteraktif Mod 🎮")
    print("="*50)
    
    input_dir = input("1. Girdi Klasörü (Input Directory) [Varsayılan: ./input]: ").strip()
    if not input_dir:
        input_dir = "./input"
        
    output_image = input("2. Çıktı Görseli Yolu (Output Image) [Varsayılan: ./output/spritesheet.png]: ").strip()
    if not output_image:
        output_image = "./output/spritesheet.png"
        
    output_json = input("3. Çıktı JSON Yolu (Output JSON) [Varsayılan: ./output/spritesheet.json]: ").strip()
    if not output_json:
        output_json = "./output/spritesheet.json"
        
    max_width_str = input("4. Maksimum Genişlik (Max Width) [Varsayılan: 1024]: ").strip()
    max_width = int(max_width_str) if max_width_str.isdigit() else 1024
    
    max_height_str = input("4b. Maksimum Yükseklik (Max Height) [Varsayılan: 8192]: ").strip()
    max_height = int(max_height_str) if max_height_str.isdigit() else 8192
    
    auto_group_str = input("5. Akıllı Gruplama (Auto-Group) Aktif Edilsin mi? (y/n) [Varsayılan: n]: ").strip().lower()
    auto_group = auto_group_str == 'y'
    
    filter_pattern = None
    if not auto_group:
        filter_str = input("6. Filtre (Örn: zombie_*.png) [Boş bırakılabilir]: ").strip()
        if filter_str:
            filter_pattern = filter_str
            
    print("\nPaketleme işlemi başlatılıyor...\n" + "-"*50)
    
    image_paths = get_image_files(input_dir, filter_pattern)
    
    if not image_paths:
        print("Hata: Eşleşen dosya bulunamadı.")
        input("Çıkmak için Enter'a basın...")
        sys.exit(1)
        
    success = False
    if auto_group:
        success = generate_grouped_outputs(image_paths, output_image, output_json, max_width, max_height)
    else:
        success = process_images_and_save(image_paths, output_image, output_json, max_width, max_height)
        
    print("-" * 50)
    if success:
        print("İşlem tamamlandı!")
    else:
        print("İşlem hatalarla sonlandı!")
    input("Çıkmak için Enter'a basın...")

def main():
    # Eğer komut satırından hiçbir argüman verilmediyse (örneğin .exe'ye çift tıklandıysa)
    if len(sys.argv) == 1:
        interactive_mode()
        return

    parser = argparse.ArgumentParser(description="Sprite Sheet Packer CLI")
    parser.add_argument("input_dir", help="Directory containing input PNG files")
    parser.add_argument("output_image", help="Output spritesheet image path (e.g., output.png)")
    parser.add_argument("output_json", help="Output JSON data path (e.g., output.json)")
    parser.add_argument("--max-width", type=int, default=1024, help="Maximum width of the spritesheet")
    parser.add_argument("--max-height", type=int, default=8192, help="Maximum height of the spritesheet")
    parser.add_argument("--filter", type=str, default=None, help="Filter files using glob pattern (e.g. 'zombie_*.png')")
    parser.add_argument("--auto-group", action="store_true", help="Group files by prefix and create separate spritesheets")
    
    args = parser.parse_args()
    
    if args.filter and args.auto_group:
        print("Hata: --filter ve --auto-group aynı anda kullanılamaz.")
        sys.exit(1)
        
    image_paths = get_image_files(args.input_dir, args.filter)
    
    if not image_paths:
        print("Hata: Eşleşen dosya bulunamadı.")
        sys.exit(1)
        
    success = False
    if args.auto_group:
        success = generate_grouped_outputs(image_paths, args.output_image, args.output_json, args.max_width, args.max_height)
    else:
        success = process_images_and_save(image_paths, args.output_image, args.output_json, args.max_width, args.max_height)
        
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
