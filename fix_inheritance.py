#!/usr/bin/env python3
"""Fix class inheritances from Adw.X to compat.X"""

import re
from pathlib import Path

# Mapping of Adw class names to compat equivalents
INHERITANCE_MAP = {
    'Adw.NavigationPage': 'NavigationPage',
    'Adw.ApplicationWindow': 'ApplicationWindow',
    'Adw.BreakpointBin': 'BreakpointBin',
    'Adw.Dialog': 'Dialog',
    'Adw.Bin': 'Box',  # Adw.Bin -> Gtk.Box (compat doesn't have Bin, use Box)
    'Adw.PreferencesDialog': 'PreferencesDialog',
}

# Files that need fixing (from grep output)
FILES_TO_FIX = [
    'src/widgets/containers/manga_grid.py',
    'src/widgets/download/dialog.py',
    'src/widgets/download/page.py',
    'src/widgets/extension/dialog.py',
    'src/widgets/extension/extensions.py',
    'src/widgets/history/page.py',
    'src/widgets/home/page.py',
    'src/widgets/library/category_edit.py',
    'src/widgets/library/category_manager.py',
    'src/widgets/library/category_panel.py',
    'src/widgets/library/page.py',
    'src/widgets/manga/page.py',
    'src/widgets/preferences/extension_stores.py',
    'src/widgets/preferences/preferences.py',
    'src/widgets/reader/base.py',
    'src/widgets/reader/dialog.py',
    'src/widgets/reader/page.py',
    'src/widgets/search/page.py',
    'src/widgets/setup.py',
    'src/widgets/source/filter.py',
    'src/widgets/source/page.py',
    'src/widgets/source/sources.py',
    'src/widgets/updates/page.py',
]

def fix_file(filepath: Path):
    content = filepath.read_text(encoding='utf-8')
    original = content

    for adw_class, compat_class in INHERITANCE_MAP.items():
        # Fix class inheritance: class ClassName(Adw.X):
        pattern = rf'(class\s+\w+\s*\()\s*{re.escape(adw_class)}\s*\)'
        content = re.sub(pattern, rf'\1{compat_class})', content)

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        print(f"Fixed: {filepath}")
        return True
    else:
        print(f"No change: {filepath}")
        return False

def main():
    base = Path('D:/Descargas/Kaori')
    fixed = 0
    for rel_path in FILES_TO_FIX:
        filepath = base / rel_path
        if filepath.exists():
            if fix_file(filepath):
                fixed += 1
        else:
            print(f"NOT FOUND: {rel_path}")
    print(f"\nTotal fixed: {fixed}")

if __name__ == '__main__':
    main()