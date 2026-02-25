import os
import argparse
import cloudconvert
import ssl
from pathlib import Path

# Workaround for macOS SSL certificate verification issues
if hasattr(ssl, '_create_unverified_context'):
    ssl._create_default_https_context = ssl._create_unverified_context

# Configuration
EXT_PRIORITY = ['otf', 'ttf', 'woff', 'woff2']
TARGET_FORMATS = ['otf', 'ttf', 'woff', 'woff2']

def get_font_variants(family_path):
    """
    Scans a font family directory and returns a dictionary of variants and their available formats.
    Structure: { 'VariantName': { 'format': 'path/to/file' } }
    """
    variants = {}
    for fmt in EXT_PRIORITY:
        fmt_dir = family_path / fmt
        if not fmt_dir.exists() or not fmt_dir.is_dir():
            continue
        
        for file in fmt_dir.glob(f"*.{fmt}"):
            variant_name = file.stem
            if variant_name not in variants:
                variants[variant_name] = {}
            variants[variant_name][fmt] = file
            
    return variants

def convert_fonts(api_key, input_dir, output_dir):
    input_path = Path(input_dir)
    output_base_path = Path(output_dir)
    
    if not api_key:
        print("❌ Error: CloudConvert API key is required.")
        return

    cloudconvert.configure(api_key=api_key)

    for family_dir in input_path.iterdir():
        if not family_dir.is_dir():
            continue
            
        print(f"📁 Processing font family: {family_dir.name}")
        family_variants = get_font_variants(family_dir)
        
        for variant, existing_fmts in family_variants.items():
            missing_fmts = [f for f in TARGET_FORMATS if f not in existing_fmts]
            
            if not missing_fmts:
                print(f"  ✅ Variant '{variant}' already has all formats.")
                # Even if all exist, we should ensure they are in the output directory if needed
                # But the instructions imply the script generates what's missing.
                # Let's copy existing ones to output if they aren't already there?
                # Actually, the instructions say "Save the converted font files to the output folder".
                # I'll ensure all formats (existing and new) end up in the output folder.
                pass
            else:
                print(f"  🔄 Variant '{variant}' is missing: {', '.join(missing_fmts)}")
                
                # Determine source format based on preference
                source_fmt = None
                for p in EXT_PRIORITY:
                    if p in existing_fmts:
                        source_fmt = p
                        break
                
                if not source_fmt:
                    print(f"  ⚠️ No source format found for variant '{variant}'. Skipping.")
                    continue
                
                source_file = existing_fmts[source_fmt]
                print(f"  🚀 Converting from {source_fmt} using CloudConvert...")
                
                try:
                    # Sanitize variant name for use in task identifiers
                    safe_variant = variant.replace(" ", "-")
                    import_task_name = f"import-{safe_variant}"
                    
                    tasks = {
                        import_task_name: {
                            "operation": "import/upload"
                        }
                    }
                    
                    convert_task_names = []
                    for fmt in missing_fmts:
                        task_name = f"convert-{safe_variant}-{fmt}"
                        tasks[task_name] = {
                            "operation": "convert",
                            "input": import_task_name,
                            "output_format": fmt
                        }
                        convert_task_names.append(task_name)
                    
                    for task_name in convert_task_names:
                        fmt = task_name.split("-")[-1]
                        tasks[f"export-{safe_variant}-{fmt}"] = {
                            "operation": "export/url",
                            "input": task_name
                        }

                    # Create Job (v2 syntax uses dict for tasks)
                    job = cloudconvert.Job.create(payload={"tasks": tasks})
                    
                    # Upload file
                    upload_task = next(t for t in job['tasks'] if t['name'] == import_task_name)
                    cloudconvert.Task.upload(file_name=str(source_file), task=upload_task)
                    
                    # Wait for job to finish
                    job = cloudconvert.Job.wait(job['id'])
                    
                    # Download converted files
                    for task in job['tasks']:
                        if task['operation'] == 'export/url' and task['status'] == 'finished':
                            # Determine format from task name
                            fmt = task['name'].split("-")[-1]
                            export_url = task['result']['files'][0]['url']
                            
                            dest_dir = output_base_path / family_dir.name / fmt
                            dest_dir.mkdir(parents=True, exist_ok=True)
                            dest_file = dest_dir / f"{variant}.{fmt}"
                            
                            cloudconvert.download(export_url, str(dest_file))
                            print(f"    ✨ Downloaded: {dest_file}")

                except Exception as e:
                    print(f"  ❌ Error converting variant '{variant}': {str(e)}")

            # Copy existing formats to output directory as well
            for fmt, path in existing_fmts.items():
                dest_dir = output_base_path / family_dir.name / fmt
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / f"{variant}.{fmt}"
                if not dest_file.exists():
                    import shutil
                    shutil.copy2(path, dest_file)
                    print(f"    📂 Copied existing: {dest_file}")

def main():
    parser = argparse.ArgumentParser(description="Convert font files to multiple formats using CloudConvert.")
    parser.add_argument("--input", required=True, help="Input directory containing font families.")
    parser.add_argument("--output", required=True, help="Output directory for all font formats.")
    parser.add_argument("--api-key", required=True, help="CloudConvert API Key.")
    
    args = parser.parse_args()
    
    convert_fonts(args.api_key, args.input, args.output)

if __name__ == "__main__":
    main()