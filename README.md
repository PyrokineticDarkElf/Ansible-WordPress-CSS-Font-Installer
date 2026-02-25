# 🖋️ WordPress CSS Font Installer (Ansible)

A powerful Ansible playbook designed to automate the entire workflow of preparing, converting, and installing custom fonts into a WordPress theme. It handles font normalization, conversion to modern web formats (`.woff2`), CSS `@font-face` generation, and remote deployment.

## 🚀 Key Features

-   **Font Normalization**: Automatically cleans up font filenames and folder structures (removing spaces, lowercase naming).
-   **Automated Conversion**: Uses CloudConvert to convert your raw font files into optimized `.woff2` files for better web performance.
-   **CSS Generation**: Dynamically creates a `brand-fonts.css` (or custom-named) file with all necessary `@font-face` declarations.
-   **Remote Deployment**: Securely uploads converted fonts and the generated CSS file to your WordPress theme via SSH.
-   **Preflight Checks**: Verifies your WordPress installation, remote paths, and WP-CLI availability before starting.

---

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed on your local machine:

1.  **Ansible**: `brew install ansible` (macOS) or equivalent.
2.  **Python 3**: For running the font processing scripts.
3.  **SSH Access**: SSH access to your WordPress server with an authorized key.
4.  **CloudConvert API Key**: Sign up at [cloudconvert.com](https://cloudconvert.com/) to get your API key for font conversions.

---

## 📂 Project Structure

```text
.
├── config/
│   └── vars.yml          # Core configuration and API keys
├── fonts/               # 📥 Place your raw font files here
├── scripts/             # Python helper scripts for font processing
├── tasks/               # Modular Ansible task definitions
├── hosts.ini            # Server inventory
└── playbook.yml         # Main entry point
```

---

## ⚙️ Configuration

### 1. Setup Inventory
Copy the example host file and update it with your server details:
```bash
cp hosts.ini.example hosts.ini
```
Edit `hosts.ini`:
```ini
[wordpress_servers]
your_server ansible_host=123.456.78.90 ansible_user=username
```

### 2. Configure Variables
Copy the example variables file and fill in your specific paths and API keys:
```bash
cp config/vars.yml.example config/vars.yml
```

**Key variables to update in `config/vars.yml`:**
- `cloudconvert_api_key`: Your API key from CloudConvert.
- `wp_path`: Relative path to your WordPress root (e.g., `public_html`).
- `theme_name`: The directory name of your active child theme.
- `css_filename`: Desired name for the generated CSS file (default: `brand-fonts.css`).

### 3. Add Your Fonts
Place all your font files (OTF, TTF, etc.) inside the `fonts/` directory. You can organize them into subfolders (e.g., `fonts/Inter/`, `fonts/Montserrat/`).

---

## 🏃 Usage

Once configured, run the playbook using the following command:

```bash
ansible-playbook -i hosts.ini playbook.yml
```

### What happens next?
1.  **Preflight**: Checks local dependencies and remote WordPress directory.
2.  **Conversion**: Raw fonts are converted to `.woff2` and stored locally in `temp/`.
3.  **Normalization**: Filenames are cleaned (e.g., `My Font Bold.ttf` ➔ `my-font-bold.woff2`).
4.  **CSS Generation**: A CSS template is created mapping all normalized fonts.
5.  **Deployment**: Converted fonts are uploaded to `wp-content/themes/your-theme/fonts/` and the CSS is uploaded to `wp-content/themes/your-theme/css/`.
