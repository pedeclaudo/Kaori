"""
Windows tray implementation using pystray.
Requires: pip install pystray pillow
"""

import threading
from typing import Any

from . import TrayEntry, TrayBackend


class Win32Tray(TrayBackend):
    """Windows system tray using pystray."""

    def __init__(self, icon: str, title: str, entries: list[TrayEntry]) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            raise RuntimeError(
                "pystray and pillow are required for Windows tray. "
                "Install with: pip install pystray pillow"
            )

        self.icon_name = icon
        self.title = title
        self._entries = entries
        self._pystray = None
        self._icon_image = self._create_default_icon()
        self._thread = None
        self._running = False
        self._build_menu()
        self.start()

    def _create_default_icon(self) -> Any:
        """Create a default icon if none provided."""
        from PIL import Image, ImageDraw
        # Create a simple 64x64 icon
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        # Draw a simple book/manga icon
        draw.rectangle([8, 12, 56, 52], outline=(100, 150, 255, 255), width=3)
        draw.rectangle([12, 16, 52, 48], fill=(100, 150, 255, 100))
        draw.line([20, 28, 44, 28], fill=(255, 255, 255, 200), width=2)
        draw.line([20, 34, 44, 34], fill=(255, 255, 255, 200), width=2)
        draw.line([20, 40, 36, 40], fill=(255, 255, 255, 150), width=2)
        return image

    def _build_menu(self) -> None:
        """Build pystray menu from entries."""
        import pystray
        self._menu_items = self._convert_entries(self._entries)
        self._menu = pystray.Menu(*self._menu_items)

    def _convert_entries(self, entries: list[TrayEntry]) -> list:
        """Convert TrayEntry list to pystray menu items."""
        import pystray
        items = []
        for entry in entries:
            if entry.separator:
                items.append(pystray.Menu.SEPARATOR)
            elif entry.children:
                submenu = self._convert_entries(entry.children)
                items.append(pystray.MenuItem(
                    entry.label,
                    pystray.Menu(*submenu),
                    enabled=entry.enabled
                ))
            else:
                items.append(pystray.MenuItem(
                    entry.label,
                    lambda _, cb=entry.callback: cb() if cb else None,
                    enabled=entry.enabled
                ))
        return items

    def set_entries(self, entries: list[TrayEntry]) -> None:
        """Update tray menu entries."""
        if entries == self._entries:
            return
        self._entries = entries
        self._build_menu()
        if self._pystray:
            self._pystray.menu = self._menu

    def _run_tray(self) -> None:
        """Run the tray icon in a separate thread."""
        import pystray
        self._pystray = pystray.Icon(
            name=self.icon_name,
            icon=self._icon_image,
            title=self.title,
            menu=self._menu
        )
        self._pystray.run()

    def start(self) -> None:
        """Start the tray (call after init if needed)."""
        if not self._running:
            self._running = True
            self._thread = threading.Thread(target=self._run_tray, daemon=True)
            self._thread.start()

    def close(self) -> None:
        """Close the tray icon."""
        self._running = False
        if self._pystray:
            self._pystray.stop()
        if self._thread:
            self._thread.join(timeout=2)