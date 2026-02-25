import os
import re
import shutil
import argparse
from urllib.parse import quote
from pathlib import Path

# Variant patterns to match styles
VARIANT_MAP = {
    'BlackItalic': ('900', 'italic'),
    'Black': ('900', 'normal'),
    'SuperItalic': ('900', 'italic'),
    'Super': ('900', 'normal'),
    'BoldItalic': ('700', 'italic'),
    'Bold': ('700', 'normal'),
    'Italic': ('400', 'italic'),
    'Regular': ('400', 'normal'),
    'LightItalic': ('300', 'italic'),
    'Light': ('300', 'normal'),
    'MediumItalic': ('500', 'italic'),
    'Medium': ('500', 'normal'),
    'SemiBoldItalic': ('600', 'italic'),
    'SemiBold': ('600', 'normal'),
    'ExtraBoldItalic': ('800', 'italic'),
    'ExtraBold': ('800', 'normal'),
    'ExtraLightItalic': ('200', 'italic'),
    'ExtraLight': ('200', 'normal'),
    'UltraLightItalic': ('200', 'italic'),
    'UltraLight': ('200', 'normal'),
    'ThinItalic': ('100', 'italic'),
    'Thin': ('100', 'normal'),
    'HairlineItalic': ('100', 'italic'),
    'Hairline': ('100', 'normal'),
}

EXT_PRIORITY = ['woff2', 'woff', 'otf', 'ttf']


def get_variant(file_name):
    name_stem = Path(file_name).stem.lower()
    
    # Remove separators for consistent matching
    name_stem = re.sub(r'[-_ ]', '', name_stem)

    for key in sorted(VARIANT_MAP.keys(), key=len, reverse=True):
        if name_stem.endswith(key.lower()):
            return key

    return 'Regular'


def scan_fonts(input_dir):
    css_blocks = []
    
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"❌ Input directory not found: {input_path}")
        return []

    # Input directory is already normalized by normalise-fonts.py
    for font_family_dir in sorted(os.listdir(input_path)):
        family_path = input_path / font_family_dir
        if not family_path.is_dir():
            continue

        font_family_name = font_family_dir.strip()
        print(f"📁 Processing font family: {font_family_name}")

        font_variants = {}

        for fmt in EXT_PRIORITY:
            format_dir = family_path / fmt
            if not format_dir.is_dir():
                continue

            for file in sorted(os.listdir(format_dir)):
                if not file.lower().endswith(f".{fmt}"):
                    continue

                variant_key = get_variant(file)
                if variant_key not in font_variants:
                    font_variants[variant_key] = {}

                # Use relative path for portability. Files and folders are already normalized.
                file_url_path = f"../fonts/{font_family_dir}/{fmt}/{quote(file)}"
                font_variants[variant_key][fmt] = file_url_path

        for variant, sources in font_variants.items():
            font_weight, font_style = VARIANT_MAP.get(variant, ('normal', 'normal'))

            src_lines = []
            for fmt in EXT_PRIORITY:
                if fmt in sources:
                    fmt_type = {
                        'woff2': 'woff2',
                        'woff': 'woff',
                        'otf': 'opentype',
                        'ttf': 'truetype'
                    }.get(fmt, 'unknown')
                    src_lines.append(f"url('{sources[fmt]}') format('{fmt_type}')")

            if not src_lines:
                continue

            joined_src_lines = ',\n       '.join(src_lines)

            # We use the variant name as the font-family label in CSS for better precision,
            # but the user might want the family name. Let's use the folder name for family.
            # Convert hyphenated name back to Title Case for font-family if desired, 
            # but usually the folder name reflects the family.
            display_family = font_family_name.replace('-', ' ').title()

            block = f"""@font-face {{
  font-family: '{display_family}';
  src: {joined_src_lines};
  font-weight: {font_weight};
  font-style: {font_style};
  font-display: swap;
}}"""
            css_blocks.append(block)

    return css_blocks


def main():
    parser = argparse.ArgumentParser(description="Generate CSS font template from a directory of fonts.")
    parser.add_argument("--input", required=True, help="Input directory containing font families (should be normalized).")
    parser.add_argument("--output", required=True, help="Output directory for CSS.")
    parser.add_argument("--filename", default="brand-fonts.css", help="Generated CSS filename (default: brand-fonts.css).")
    
    args = parser.parse_args()
    
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    css_blocks = scan_fonts(args.input)

    output_file = output_path / args.filename
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(css_blocks))

    print(f"✅ CSS font template generated: {output_file}")

if __name__ == '__main__':
    main()
