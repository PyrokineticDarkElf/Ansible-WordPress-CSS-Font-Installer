import csv
import os
from pathlib import Path
from colorsys import rgb_to_hls

# Directories
base_dir = Path(__file__).parent
input_dir = base_dir / "input"
output_dir = base_dir / "output"
conf_path = base_dir / ".conf"
output_dir.mkdir(parents=True, exist_ok=True)

# Read config
default_target = None
config_options = set()

print(f"🔍 Looking for config file at: {conf_path}")
if conf_path.exists():
    print("📄 Config file found, reading...")
    with open(conf_path) as conf_file:
        for line_num, line in enumerate(conf_file, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            
            # Remove everything after # (inline comments)
            if '#' in stripped:
                stripped = stripped.split('#')[0].strip()
            
            if not stripped:  # Check again after removing inline comments
                continue
                
            if stripped.lower().startswith("default:"):
                default_target = stripped.split(":", 1)[1].strip()
            else:
                config_options.add(stripped.lower())
else:
    print("❌ No config file found, using defaults")
    # No config file — enable everything except default alias
    config_options = {
        "hex", "hex-r", "hex-g", "hex-b",
        "rgb", "r", "g", "b",
        "hsl", "h", "s", "l",
    }

def hex_to_rgb(hex_color):
    hex_color = hex_color.strip().lstrip('#')
    r, g, b = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    return r, g, b, hex_color.upper()

def rgb_to_hsl(r, g, b):
    r_f, g_f, b_f = r / 255, g / 255, b / 255
    h, l, s = rgb_to_hls(r_f, g_f, b_f)
    return round(h * 360), round(s * 100), round(l * 100)

def process_csv_file(csv_path):
    output_lines = []
    
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            prefix = row['prefix'].strip()
            name_raw = row['colour name'].strip()
            name = name_raw.lower().replace(' ', '-')
            hex_val = row['colour hex'].strip()
            
            r, g, b, hex_full = hex_to_rgb(hex_val)
            h, s, l = rgb_to_hsl(r, g, b)
            
            var_base = f"--{prefix}-{name}"
            
            # Add comment section header
            output_lines.append(f"  /* {name_raw} */")
            
            # Add default alias if default_target is set
            if default_target:
                default_line = f"  {var_base}: var({var_base}-{default_target});"
                output_lines.append(default_line)
            
            if "hex" in config_options:
                output_lines.append(f"  {var_base}-hex: #{hex_full};")
            if "hex-r" in config_options:
                output_lines.append(f"  {var_base}-hex-r: {hex_full[0:2]};")
            if "hex-g" in config_options:
                output_lines.append(f"  {var_base}-hex-g: {hex_full[2:4]};")
            if "hex-b" in config_options:
                output_lines.append(f"  {var_base}-hex-b: {hex_full[4:6]};")
            
            if "rgb" in config_options:
                output_lines.append(f"  {var_base}-rgb: {r}, {g}, {b};")
            if "r" in config_options:
                output_lines.append(f"  {var_base}-r: {r};")
            if "g" in config_options:
                output_lines.append(f"  {var_base}-g: {g};")
            if "b" in config_options:
                output_lines.append(f"  {var_base}-b: {b};")
            
            if "hsl" in config_options:
                output_lines.append(f"  {var_base}-hsl: {h} {s}% {l}%;")
            if "h" in config_options:
                output_lines.append(f"  {var_base}-h: {h};")
            if "s" in config_options:
                output_lines.append(f"  {var_base}-s: {s}%;")
            if "l" in config_options:
                output_lines.append(f"  {var_base}-l: {l}%;")
            
            output_lines.append("")  # space between blocks
    
    return '\n'.join(output_lines)

def main():
    csv_files = list(input_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in input/")
        return
    
    for csv_file in csv_files:
        css_output = process_csv_file(csv_file)
        out_file = output_dir / f"{csv_file.stem}.css"
        
        with open(out_file, "w") as f:
            f.write(f":root {{\n{css_output}}}\n")
        
        print(f"✅ Generated: {out_file.name}")

if __name__ == "__main__":
    main()