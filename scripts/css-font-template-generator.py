import os
import re
import argparse
from urllib.parse import quote
from pathlib import Path

# Canonical variant mapping
VARIANT_PATTERNS = [
    (r'(extra|ultra)light(italic)?$', '200'),
    (r'extrabold(italic)?$', '800'),
    (r'(hairline|thin)(italic)?$', '100'),
    (r'light(italic)?$', '300'),
    (r'medium(italic)?$', '500'),
    (r'(semi|demi)bold(italic)?$', '600'),
    (r'(?<!extra)(?<!semi)(?<!demi)bold(italic)?$', '700'),
    (r'(extra|ultra)?(black|heavy|super)(italic)?$', '900'),
    (r'italic$', '400'),
    (r'(book|regular|roman)$', '400'),
]

EXT_PRIORITY = ['woff2', 'woff', 'otf', 'ttf']

FORMAT_TYPES = {
    'woff2': 'woff2',
    'woff': 'woff',
    'otf': 'opentype',
    'ttf': 'truetype'
}

WIDTH_MAPPING = {
    'ultracondensed': '50%',
    'extracondensed': '62.5%',
    'compressed': '75%',
    'condensed': '75%',
    'narrow': '85%',
    'extraexpanded': '150%',
    'ultraexpanded': '200%',
    'extended': '125%',
    'expanded': '125%',
}

def get_variant(file_name):
    # Initial normalization
    normalized = re.sub(
        r'[-_\s]',
        '',
        Path(file_name).stem.lower()
    )

    # Default values
    weight, style = ('400', 'normal')
    stretch = 'normal'

    # 1. Identify Stretch (Width) - Check longest patterns first to avoid partial matches
    # (e.g., 'extracondensed' should match 'extracondensed' before 'condensed')
    for key in sorted(WIDTH_MAPPING.keys(), key=len, reverse=True):
        if key in normalized:
            stretch = WIDTH_MAPPING[key]
            # Remove it so it doesn't interfere with weight detection
            normalized = normalized.replace(key, '')
            break

    # 2. Identify Weight/Style
    for pattern, weight in VARIANT_PATTERNS:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if match:
            # Dynamically determine style based on whether 'italic' was part of the match
            style = 'italic' if 'italic' in match.group(0).lower() else 'normal'
            return (weight, style, stretch)

    return (weight, style, stretch)


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
                
                # Prevent duplicate overwrites if multiple files match the same weight/style
                if fmt not in font_variants[variant_key]:
                    font_variants[variant_key][fmt] = file_url_path

        for variant, sources in font_variants.items():
            font_weight, font_style, font_stretch = variant

            src_lines = []
            for fmt in EXT_PRIORITY:
                if fmt in sources:
                    fmt_type = FORMAT_TYPES.get(fmt, 'unknown')
                    src_lines.append(f"url('{sources[fmt]}') format('{fmt_type}')")

            if not src_lines:
                continue

            joined_src_lines = ',\n       '.join(src_lines)

            display_family = font_family_name.replace('-', ' ')

            block = f"""@font-face {{
  font-family: '{display_family}';
  src: {joined_src_lines};
  font-weight: {font_weight};
  font-style: {font_style};
  font-stretch: {font_stretch};
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
