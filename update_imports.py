#!/usr/bin/env python3
"""
Script to update Python files to use the compat layer instead of direct Adw imports.
"""

import re
from pathlib import Path

def update_file(filepath: Path) -> bool:
    """Update a single Python file to use compat layer."""
    content = filepath.read_text(encoding='utf-8')
    original = content

    # Replace imports
    # Pattern: from gi.repository import ..., Adw, ...
    content = re.sub(
        r'(from gi\.repository import\s+)([^,\n]*?),\s*Adw\s*,\s*',
        r'\1\2, ',
        content
    )
    content = re.sub(
        r'(from gi\.repository import\s+)([^,\n]*?)\s*,\s*Adw$',
        r'\1\2',
        content
    )
    content = re.sub(
        r'(from gi\.repository import\s+)Adw\s*,\s*',
        r'\1',
        content
    )
    content = re.sub(
        r'(from gi\.repository import\s+)Adw$',
        r'\1Gtk',
        content
    )

    # If after removing Adw there's nothing left, add Gtk
    content = re.sub(
        r'from gi\.repository import\s+\n',
        'from gi.repository import Gtk\n',
        content
    )

    # Replace Adw.Widget with compat.Widget in class inheritance and instantiation
    # This is more complex - we'll just add the compat import
    if 'Adw.' in content and 'from ..compat import' not in content:
        # Add compat import after other imports
        import_pattern = r'(from gi\.repository import [^\n]+\n)'
        matches = list(re.finditer(import_pattern, content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + 'from ..compat import ApplicationWindow, NavigationView, NavigationPage, ToolbarView, HeaderBar, ViewStack, ViewStackPage, ViewSwitcher, ViewSwitcherBar, Clamp, StatusPage, PreferencesDialog, PreferencesPage, PreferencesGroup, ActionRow, EntryRow, ComboRow, SwitchRow, SpinRow, Dialog, MessageDialog, ToastOverlay, Toast, AboutDialog, Carousel, CarouselIndicatorDots, BreakpointBin, Breakpoint, WrapBox, Avatar, Squeezer, Leaflet, Flap, WindowTitle, StyleManager, ColorScheme\n' + content[insert_pos:]

    if content != original:
        filepath.write_text(content, encoding='utf-8')
        return True
    return False

def main():
    widgets_dir = Path('src/widgets')
    files = list(widgets_dir.rglob('*.py'))
    updated = 0
    for filepath in files:
        if update_file(filepath):
            print(f"Updated {filepath}")
            updated += 1
    print(f"\nUpdated {updated} files.")

if __name__ == '__main__':
    main()