# WordPress CSS Colour Theme Variable Generator

A robust Ansible-driven workflow to generate and deploy CSS custom properties (variables) to WordPress themes from structured color data.

## Features

- 🚀 **JSON-First Workflow**: Define brand colors in structured JSON files.
- 🎨 **Multi-Format Support**: Define colors in **HEX**, **RGB**, or **HSL**. The generator automatically derives all other formats.
- 🛠️ **Professional Python Generator**: A modular, typed Python script handles color mathematics and CSS formatting.
- 📦 **Automated Deployment**: Ansible captures generated CSS and uploads it directly to your remote WordPress servers—no local temporary files needed.
- ⚖️ **Flexible Aliasing**: Create base variables (e.g., `--prefix-color: #hex`) referencing any format, with optional redundancy removal.

---

## Prerequisites

- **Local**: Python 3.x and Ansible installed.
- **Remote**: SSH access to your WordPress server(s).

---

## Setup & Configuration

### 1. Project Setup
Rename the example configuration files and add your specific server details:

```bash
cp config/vars.yml.example config/vars.yml
cp hosts.ini.example hosts.ini
```

### 2. Configure project variables
Edit `config/vars.yml` to define your theme paths and generation preferences:

```yaml
# WordPress Paths
wp_path: "public_html"      # Relative path to WP root from SSH home
theme_name: "my-theme"      # Your child theme directory name
theme_path: "{{ wp_path }}/wp-content/themes/{{ theme_name }}"

# CSS Generation Logic
css_variable_formats: "hex,rgb,h,s,l" # Which formats to generate per color
css_default_target: "hex"             # Format used for the base alias (--prefix-name)
css_exclude_target_format: true       # Hide redundant variables (e.g. no --prefix-name-hex)

# Internal Paths
remote_css_dir: "{{ theme_path }}/css"
local_json_dir: "{{ playbook_dir }}/config"
python_script_path: "{{ playbook_dir }}/scripts/colour-theme.py"
```

---

## Defining Color Data

Create `.json` files in your `config/` directory. You can provide colors in whichever format you have available:

```json
[
    {
        "color": {
            "prefix": "brand",
            "name": "Primary Red",
            "hex": "#FF0000"
        }
    },
    {
        "color": {
            "prefix": "brand",
            "name": "Action Green",
            "rgb": "0, 255, 0"
        }
    },
    {
        "color": {
            "prefix": "brand",
            "name": "Sky Blue",
            "hsl": "210, 100%, 50%"
        }
    }
]
```

*The generator will automatically output HEX, RGB, and HSL variables for **all** entries, regardless of how they were defined in the JSON.*

---

## Usage

Run the Ansible playbook to process all JSON files and upload the results:

```bash
ansible-playbook -i hosts.ini playbook.yml
```

### How it works
1. **Find**: Ansible identifies all `.json` files in your `config/` directory.
2. **Generate**: The Python script is called locally. It prints the generated CSS to `stdout`.
3. **Capture**: Ansible captures this output directly into a variable.
4. **Deploy**: The content is sent to the remote server and saved as a `.css` file in your theme's CSS directory.

---

## Maintenance

### Adding New Formats
Supported format tokens for `css_variable_formats`:
- `hex`: Standard hex code (`#FFFFFF`)
- `hex-r`, `hex-g`, `hex-b`: Individual hex components.
- `rgb`: Comma-separated RGB (`255, 255, 255`)
- `r`, `g`, `b`: Individual RGB components.
- `hsl`: CSS HSL syntax (`0 0% 100%`)
- `h`, `s`, `l`: Individual HSL components.

### Python script CLI
You can also run the generator manually for local testing:
```bash
python3 scripts/colour-theme.py --input config/brand-colors.json --formats hex,rgb
```
