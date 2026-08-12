# Sprite Packer CLI 🎮

A professional command-line tool for Game Developers (especially tailored for MonoGame/XNA ecosystem) to pack scattered PNG frames into a single, highly optimized Sprite Sheet. 

It utilizes the advanced **MaxRects Bin-Packing Algorithm** to ensure zero wasted space and outputs a TexturePacker-compatible JSON format.

## ✨ Features

- **Advanced Bin-Packing:** Uses the industry-standard MaxRects algorithm (Best Short Side Fit) for maximum space optimization compared to basic shelf packing.
- **Auto-Grouping (`--auto-group`):** Automatically detects sprite prefixes (e.g., `hero_run_1.png` and `zombie_walk_1.png`) and groups them into separate sprite sheets (`spritesheet_hero_run.png`, `spritesheet_zombie_walk.png`) on the fly.
- **Smart Filtering (`--filter`):** Safely filter specific files using glob patterns (e.g., `--filter "zombie_*.png"`) with built-in case-sensitivity and OS-agnostic protection.
- **MonoGame Ready:** Directly exports TexturePacker JSON (Array format), easily readable by MonoGame.Extended or custom content pipelines.

## 🚀 Installation & Setup

Ensure you have Python 3.x installed. Then install the required dependencies:

```bash
pip install -r requirements.txt
```

## 💻 Usage

```bash
python packer.py <input_dir> <output_image> <output_json> [options]
```

### 1. Basic Packing
Packs all PNGs in the `input` directory and creates `spritesheet.png` and `spritesheet.json`.
```bash
python packer.py ./examples/input ./examples/output/spritesheet.png ./examples/output/spritesheet.json
```

### 2. Auto-Grouping (`--auto-group`)
Groups files by their prefixes (ignores trailing numbers and underscores) and outputs multiple sprite sheets.
```bash
python packer.py ./examples/input ./examples/output/spritesheet.png ./examples/output/spritesheet.json --auto-group
```
*(E.g., Generates `spritesheet_hero_run.png` and `spritesheet_zombie_walk.png`)*

### 3. Smart Filtering (`--filter`)
Pack only specific sprites using a glob pattern. 
> ⚠️ **Note:** Always wrap your filter in quotes to prevent unwanted terminal shell expansion!
```bash
python packer.py ./examples/input ./examples/output/spritesheet.png ./examples/output/spritesheet.json --filter "zombie_*.png"
```

## 🛠️ Architecture & Under the Hood
- **Language:** Python 3
- **Image Processing:** `Pillow` (PIL)
- **Algorithm:** 2D MaxRects Bin-Packing (Splits free rectangles dynamically as images are placed, keeping the canvas as small as possible).
