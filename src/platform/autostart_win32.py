"""
Windows autostart implementation using Registry (Run key).
"""

import sys
import subprocess
from pathlib import Path

from . import AutostartBackend


class Win32Autostart(AutostartBackend):
    """Windows autostart using HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"""

    def __init__(self, app_id: str, app_name: str) -> None:
        self.app_id = app_id
        self.app_name = app_name
        self.reg_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.reg_value = app_id

    def _get_python_exe(self) -> str:
        """Get the Python executable path."""
        return sys.executable

    def _get_script_path(self) -> str:
        """Get the main script path."""
        # Try to find kaori entry point
        base_dir = Path(__file__).parent.parent.parent
        # In installed version, it would be in the package
        return str(base_dir / 'kaori')

    def _build_command(self, command: list[str]) -> str:
        """Build the full command string for Registry."""
        # command is like ['kaori', '--background']
        # We need to convert to full Windows command
        python_exe = self._get_python_exe()
        if command[0] == 'kaori':
            # Running as module
            return f'"{python_exe}" -m kaori {" ".join(command[1:])}'
        return " ".join(command)

    def set_autostart(self, enabled: bool, command: list[str]) -> None:
        cmd_str = self._build_command(command)
        try:
            if enabled:
                # Add to registry
                subprocess.run([
                    'reg', 'add',
                    f'HKCU\\{self.reg_key}',
                    '/v', self.reg_value,
                    '/t', 'REG_SZ',
                    '/d', cmd_str,
                    '/f'
                ], check=True, capture_output=True)
            else:
                # Remove from registry
                subprocess.run([
                    'reg', 'delete',
                    f'HKCU\\{self.reg_key}',
                    '/v', self.reg_value,
                    '/f'
                ], check=True, capture_output=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            print(f"Autostart registry operation failed: {e}")

    def is_autostart_enabled(self) -> bool:
        try:
            result = subprocess.run([
                'reg', 'query',
                f'HKCU\\{self.reg_key}',
                '/v', self.reg_value
            ], capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False