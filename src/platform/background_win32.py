"""
Windows background implementation.
Windows doesn't have a direct equivalent to freedesktop Background portal.
This is a no-op implementation - the app just stays running normally.
"""

from . import BackgroundBackend


class Win32Background(BackgroundBackend):
    """Windows background - no special handling needed."""

    def __init__(self, app_id: str, autostart_command: list[str]) -> None:
        self.app_id = app_id
        self.autostart_command = autostart_command

    def request_background(self, enabled: bool, autostart: bool, command: list[str]) -> None:
        # Windows doesn't have a background portal.
        # The app just keeps running if the main loop is active.
        # For "run in background" behavior on Windows, we'd typically:
        # 1. Minimize to tray (handled by tray backend)
        # 2. Keep the main loop running (handled by GTK main loop)
        pass