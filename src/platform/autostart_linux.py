"""
Linux autostart implementation using freedesktop .desktop files.
Wraps the original main.py implementation.
"""

import os
from pathlib import Path

from gi.repository import GLib

from . import AutostartBackend


class LinuxAutostart(AutostartBackend):
    """Linux autostart using .desktop files in ~/.config/autostart/"""

    def __init__(self, app_id: str, app_name: str) -> None:
        self.app_id = app_id
        self.app_name = app_name
        self.desktop_path = Path(GLib.get_user_config_dir()) / 'autostart' / f'{app_id}.desktop'

    def set_autostart(self, enabled: bool, command: list[str]) -> None:
        if enabled:
            self.desktop_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.desktop_path, 'w') as f:
                f.write('[Desktop Entry]\n'
                        'Type=Application\n'
                        f'Name={self.app_name}\n'
                        f'Exec={" ".join(command)}\n'
                        'X-GNOME-Autostart-enabled=true\n')
        elif self.desktop_path.exists():
            self.desktop_path.unlink()

    def is_autostart_enabled(self) -> bool:
        return self.desktop_path.exists()