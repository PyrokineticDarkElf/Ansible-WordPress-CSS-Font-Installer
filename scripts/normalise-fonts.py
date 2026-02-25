import os
import re
import argparse
from pathlib import Path

def slugify(text):
    """
    Sanitize text to be URL and filesystem safe.
    Replaces spaces and non-alphanumeric characters with hyphens.
    """
    # Replace anything that isn't a letter or number with a hyphen
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text)
    # Remove leading/trailing hyphens
    return slug.strip('-')

def normalise_fonts(target_dir):
    target_path = Path(target_dir)
    if not target_path.exists():
        print(f"❌ Target directory not found: {target_path}")
        return

    # First pass: Normalise folder names (font families)
    for family_dir in list(target_path.iterdir()):
        if not family_dir.is_dir():
            continue

        original_name = family_dir.name
        safe_family_name = slugify(original_name)
        
        new_family_path = target_path / safe_family_name
        
        if family_dir != new_family_path:
            # If target already exists, we might need to merge or handle it
            if new_family_path.exists():
                print(f"  ⚠️ Target folder {safe_family_name} already exists. Merging content...")
                # Simple move files logic for merging
                for fmt_dir in family_dir.iterdir():
                    if not fmt_dir.is_dir():
                        continue
                    new_fmt_dir = new_family_path / fmt_dir.name
                    new_fmt_dir.mkdir(parents=True, exist_ok=True)
                    for font_file in fmt_dir.iterdir():
                        os.rename(font_file, new_fmt_dir / font_file.name)
                family_dir.rmdir()
                # Use the new path for the next steps
                current_family_path = new_family_path
            else:
                os.rename(family_dir, new_family_path)
                current_family_path = new_family_path
            print(f"📁 Normalised folder: {original_name} → {safe_family_name}")
        else:
            current_family_path = family_dir

        # Second pass: Normalise filenames within each format directory
        for fmt_dir in current_family_path.iterdir():
            if not fmt_dir.is_dir():
                continue
            
            for font_file in list(fmt_dir.iterdir()):
                if font_file.is_dir():
                    continue
                
                original_filename = font_file.name
                stem = font_file.stem
                ext = font_file.suffix # Includes the dot
                
                safe_stem = slugify(stem)
                new_filename = f"{safe_stem}{ext.lower()}"
                
                new_file_path = fmt_dir / new_filename
                
                if font_file != new_file_path:
                    os.rename(font_file, new_file_path)
                    print(f"  📄 Normalised file: {original_filename} → {new_filename}")

def main():
    parser = argparse.ArgumentParser(description="Normalise font folder and file names.")
    parser.add_argument("--dir", required=True, help="Directory to normalise recursively.")
    
    args = parser.parse_args()
    
    print(f"🔍 Normalising fonts in: {args.dir}")
    normalise_fonts(args.dir)
    print("✅ Normalisation complete.")

if __name__ == "__main__":
    main()
