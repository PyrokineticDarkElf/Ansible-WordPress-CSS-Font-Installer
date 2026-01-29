#!/usr/bin/env python3
"""
Generate CSS custom properties from structured JSON color definitions.
Supports HEX, RGB, and HSL input formats and derives all other formats.
"""

import json
import sys
import argparse
import re
from pathlib import Path
from colorsys import rgb_to_hls, hls_to_rgb
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ColorEntry:
    """Represents a single color definition before formatting."""
    prefix: str
    name: str
    source_value: str
    source_type: str  # 'hex', 'rgb', or 'hsl'
    name_slug: str

    @property
    def var_base(self) -> str:
        return f"--{self.prefix}-{self.name_slug}"


class ColorProcessor:
    """Handles color conversion and CSS variable generation."""

    def __init__(self, requested_formats: List[str], default_format: Optional[str] = None):
        self.requested_formats = requested_formats
        self.default_format = default_format

    @staticmethod
    def parse_numeric_string(value: str) -> List[float]:
        """Parse strings like '255, 0, 0' or '240 100% 50%' into a list of floats."""
        # Remove common CSS syntax noise
        clean = re.sub(r'[a-zA-Z()]+', '', value)
        # Split by comma or space
        parts = re.split(r'[,\s]+', clean.strip())
        # Filter out empty and strip percent signs
        floats = []
        for p in parts:
            if not p:
                continue
            try:
                floats.append(float(p.rstrip('%')))
            except ValueError:
                continue
        return floats

    @staticmethod
    def hex_to_rgb(hex_val: str) -> Tuple[int, int, int]:
        """Convert hex string to RGB tuple."""
        clean_hex = hex_val.strip().lstrip('#')
        if len(clean_hex) == 3:
            clean_hex = ''.join([c * 2 for c in clean_hex])
        
        if len(clean_hex) != 6:
            raise ValueError(f"Invalid hex color length: {hex_val}")
            
        r, g, b = (int(clean_hex[i:i+2], 16) for i in (0, 2, 4))
        return r, g, b

    def normalize_to_rgb(self, entry: ColorEntry) -> Tuple[int, int, int]:
        """Convert any supported input format to a standard 0-255 RGB tuple."""
        if entry.source_type == "hex":
            return self.hex_to_rgb(entry.source_value)
        
        vals = self.parse_numeric_string(entry.source_value)
        if len(vals) < 3:
            raise ValueError(f"Insufficient color components for {entry.source_type}: {entry.source_value}")

        if entry.source_type == "rgb":
            return round(vals[0]), round(vals[1]), round(vals[2])
        
        if entry.source_type == "hsl":
            # hms_to_rgb expects 0.0-1.0. Input h is 0-360, s/l are 0-100
            h, s, l = vals[0] / 360.0, vals[1] / 100.0, vals[2] / 100.0
            r_f, g_f, b_f = hls_to_rgb(h, l, s)
            return round(r_f * 255), round(g_f * 255), round(b_f * 255)
        
        raise ValueError(f"Unsupported source type: {entry.source_type}")

    def generate_format_map(self, entry: ColorEntry) -> Dict[str, str]:
        """Normalize input and generate all available CSS format strings."""
        r, g, b = self.normalize_to_rgb(entry)
        
        # Ensure bounds
        r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
        
        hex_full = f"{r:02X}{g:02X}{b:02X}"
        h_comp, l_comp, s_comp = rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        h, s, l = round(h_comp * 360), round(s_comp * 100), round(l_comp * 100)

        return {
            "hex": f"#{hex_full}",
            "hex-r": hex_full[0:2],
            "hex-g": hex_full[2:4],
            "hex-b": hex_full[4:6],
            "rgb": f"{r}, {g}, {b}",
            "r": str(r),
            "g": str(g),
            "b": str(b),
            "hsl": f"{h} {s}% {l}%",
            "h": str(h),
            "s": f"{s}%",
            "l": f"{l}%"
        }

    def generate_css_block(self, entry: ColorEntry) -> List[str]:
        """Generate a CSS block for a single color entry."""
        try:
            format_map = self.generate_format_map(entry)
        except (ValueError, IndexError, ZeroDivisionError) as e:
            print(f"⚠️  Skipping '{entry.name}': {e}", file=sys.stderr)
            return []

        lines = [f"  /* {entry.name} */"]
        
        # Add base alias if requested
        if self.default_format and self.default_format in format_map:
            lines.append(f"  {entry.var_base}: {format_map[self.default_format]};")

        # Add requested formats
        for fmt in self.requested_formats:
            if fmt in format_map:
                lines.append(f"  {entry.var_base}-{fmt}: {format_map[fmt]};")
        
        lines.append("")  # Spacing
        return lines


class DataExporter:
    """Handles loading JSON data and ensuring it matches the expected structure."""

    @staticmethod
    def load_json(path: Path) -> List[ColorEntry]:
        """Load and normalize color data from a JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError("Root JSON element must be a list.")

        entries = []
        for i, item in enumerate(data):
            try:
                color_data = item.get("color", {})
                prefix = color_data.get("prefix", "theme").strip()
                name = color_data.get("name", "unnamed").strip()
                
                # Intelligent Source Detection
                source_value = None
                source_type = None
                
                # Check for available format keys
                for key in ["hex", "rgb", "hsl"]:
                    if key in color_data and color_data[key]:
                        source_value = str(color_data[key])
                        source_type = key
                        break
                
                if not source_type:
                    print(f"⚠️  No valid color code (hex, rgb, hsl) found at index {i}", file=sys.stderr)
                    continue

                entries.append(ColorEntry(
                    prefix=prefix,
                    name=name,
                    source_value=source_value,
                    source_type=source_type,
                    name_slug=name.lower().replace(' ', '-')
                ))
            except Exception as e:
                print(f"⚠️  Skipping malformed item at index {i}: {e}", file=sys.stderr)
        
        return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Input JSON file or directory")
    parser.add_argument("--formats", help="Comma-separated CSS formats (e.g., hex,rgb,hsl)")
    parser.add_argument("--default-format", help="Base alias target (e.g., hex)")
    parser.add_argument("--exclude-default", action="store_true", 
                        help="Don't generate redundant variable for the default format")
    
    args = parser.parse_args()
    
    # 1. Setup Input Files
    input_path = Path(args.input)
    if input_path.is_file():
        files = [input_path]
    elif input_path.is_dir():
        files = sorted(list(input_path.glob("*.json")))
        if not files:
            print(f"❌ No JSON files found in {input_path}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"❌ Input path does not exist: {input_path}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup Processing Options
    if args.formats:
        formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    else:
        # Defaults if none provided
        formats = ["hex", "hex-r", "hex-g", "hex-b", "rgb", "r", "g", "b", "hsl", "h", "s", "l"]

    default_format = args.default_format.lower() if args.default_format else None
    
    if args.exclude_default and default_format and default_format in formats:
        formats.remove(default_format)

    processor = ColorProcessor(formats, default_format)

    # 3. Process Files
    for json_file in files:
        try:
            color_entries = DataExporter.load_json(json_file)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Error loading {json_file.name}: {e}", file=sys.stderr)
            continue

        css_lines = []
        for entry in color_entries:
            css_lines.extend(processor.generate_css_block(entry))

        # Output to stdout
        if css_lines:
            output = ":root {\n" + "\n".join(css_lines) + "}"
            print(output)
            print(f"✅ Generated from: {json_file.name}", file=sys.stderr)


if __name__ == "__main__":
    main()