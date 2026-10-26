#!/usr/bin/env python3
"""
Script to convert .blp files from Adw widgets to compat (Gtk) equivalents.
This allows the blueprint compiler to generate .ui files that work with the compat layer.
"""

import re
import sys
from pathlib import Path

# Mapping of Adw widget names to compat equivalents
WIDGET_MAPPING = {
    'Adw.ApplicationWindow': 'ApplicationWindow',
    'Adw.NavigationView': 'NavigationView',
    'Adw.NavigationPage': 'NavigationPage',
    'Adw.ToolbarView': 'ToolbarView',
    'Adw.HeaderBar': 'HeaderBar',
    'Adw.ViewStack': 'ViewStack',
    'Adw.ViewStackPage': 'ViewStackPage',
    'Adw.ViewSwitcher': 'ViewSwitcher',
    'Adw.ViewSwitcherBar': 'ViewSwitcherBar',
    'Adw.Clamp': 'Clamp',
    'Adw.StatusPage': 'StatusPage',
    'Adw.PreferencesDialog': 'PreferencesDialog',
    'Adw.PreferencesPage': 'PreferencesPage',
    'Adw.PreferencesGroup': 'PreferencesGroup',
    'Adw.ActionRow': 'ActionRow',
    'Adw.EntryRow': 'EntryRow',
    'Adw.ComboRow': 'ComboRow',
    'Adw.SwitchRow': 'SwitchRow',
    'Adw.SpinRow': 'SpinRow',
    'Adw.Dialog': 'Dialog',
    'Adw.MessageDialog': 'MessageDialog',
    'Adw.ToastOverlay': 'ToastOverlay',
    'Adw.Toast': 'Toast',
    'Adw.AboutDialog': 'AboutDialog',
    'Adw.Carousel': 'Carousel',
    'Adw.CarouselIndicatorDots': 'CarouselIndicatorDots',
    'Adw.BreakpointBin': 'BreakpointBin',
    'Adw.Breakpoint': 'Breakpoint',
    'Adw.WrapBox': 'WrapBox',
    'Adw.Avatar': 'Avatar',
    'Adw.Squeezer': 'Squeezer',
    'Adw.Leaflet': 'Leaflet',
    'Adw.Flap': 'Flap',
    'Adw.WindowTitle': 'WindowTitle',
    'Adw.Bin': 'Box',  # Adw.Bin is a simple container, use Box
    'Adw.ComboBox': 'ComboBox',
    'Adw.Switch': 'Switch',
    'Adw.SpinButton': 'SpinButton',
    'Adw.Entry': 'Entry',
    'Adw.Label': 'Label',
    'Adw.Button': 'Button',
    'Adw.Image': 'Image',
    'Adw.Separator': 'Separator',
    'Adw.ScrolledWindow': 'ScrolledWindow',
    'Adw.Box': 'Box',
    'Adw.CenterBox': 'CenterBox',
    'Adw.Overlay': 'Overlay',
    'Adw.Revealer': 'Revealer',
    'Adw.Expander': 'Expander',
    'Adw.Stack': 'Stack',
    'Adw.StackPage': 'StackPage',
    'Adw.StackSwitcher': 'StackSwitcher',
}

# For template declarations, we need to map parent classes
TEMPLATE_MAPPING = {
    'Adw.ApplicationWindow': 'ApplicationWindow',
    'Adw.Dialog': 'Dialog',
    'Adw.NavigationPage': 'NavigationPage',
    'Adw.PreferencesDialog': 'PreferencesDialog',
    'Adw.PreferencesPage': 'PreferencesPage',
    'Adw.PreferencesGroup': 'PreferencesGroup',
    'Adw.StatusPage': 'StatusPage',
}

def convert_blp_file(filepath: Path) -> str:
    """Convert a single .blp file."""
    content = filepath.read_text(encoding='utf-8')
    original = content

    # Handle template declarations: template $Name : Adw.Widget {
    for adw_widget, compat_widget in TEMPLATE_MAPPING.items():
        pattern = rf'(template\s+\$\w+\s*:\s*){re.escape(adw_widget)}(\s*{{)'
        content = re.sub(pattern, rf'\1{compat_widget}\2', content)

    # Handle widget declarations: Adw.Widget name { ... }
    for adw_widget, compat_widget in WIDGET_MAPPING.items():
        # Match "Adw.WidgetName identifier {" or "Adw.WidgetName {"
        pattern = rf'\b{re.escape(adw_widget)}\b(\s+\$\w+)?\s*{{'
        content = re.sub(pattern, f'{compat_widget}\\1 {{', content)

    # Handle styles references: styles ["class-name"] -> keep as is (CSS classes unchanged)
    # The styles are CSS classes, not widget types

    return content


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_blp.py <file_or_directory> [output_directory]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else input_path

    if input_path.is_file():
        files = [input_path]
    else:
        files = list(input_path.rglob('*.blp'))

    for filepath in files:
        print(f"Converting {filepath}...")
        content = convert_blp_file(filepath)

        if output_path.is_dir():
            out_file = output_path / filepath.relative_to(input_path)
        else:
            out_file = output_path

        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(content, encoding='utf-8')
        print(f"  -> {out_file}")

    print(f"\nConverted {len(files)} files.")


if __name__ == '__main__':
    main()