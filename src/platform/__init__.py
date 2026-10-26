"""
Platform abstraction layer for Kaori.
Provides cross-platform implementations for system tray, autostart, etc.
"""

import sys
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TrayEntry:
    """Platform-agnostic tray menu entry."""
    label: str = ''
    callback: Callable | None = None
    enabled: bool = True
    separator: bool = False
    children: list = field(default_factory=list)


class TrayBackend(ABC):
    """Abstract base for system tray implementations."""

    @abstractmethod
    def __init__(self, icon: str, title: str, entries: list[TrayEntry]) -> None:
        pass

    @abstractmethod
    def set_entries(self, entries: list[TrayEntry]) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def start(self) -> None:
        """Start the tray (no-op for Linux, required for Windows)."""
        pass


class AutostartBackend(ABC):
    """Abstract base for autostart implementations."""

    @abstractmethod
    def set_autostart(self, enabled: bool, command: list[str]) -> None:
        pass

    @abstractmethod
    def is_autostart_enabled(self) -> bool:
        pass


class BackgroundBackend(ABC):
    """Abstract base for background execution (keeping app alive)."""

    @abstractmethod
    def request_background(self, enabled: bool, autostart: bool, command: list[str]) -> None:
        pass


def get_tray_backend() -> type[TrayBackend]:
    """Get the appropriate tray backend for the current platform."""
    if sys.platform == 'win32':
        from .tray_win32 import Win32Tray
        return Win32Tray
    else:
        from .tray_linux import LinuxTray
        return LinuxTray


def get_autostart_backend() -> type[AutostartBackend]:
    """Get the appropriate autostart backend for the current platform."""
    if sys.platform == 'win32':
        from .autostart_win32 import Win32Autostart
        return Win32Autostart
    else:
        from .autostart_linux import LinuxAutostart
        return LinuxAutostart


def get_background_backend() -> type[BackgroundBackend]:
    """Get the appropriate background backend for the current platform."""
    if sys.platform == 'win32':
        from .background_win32 import Win32Background
        return Win32Background
    else:
        from .background_linux import LinuxBackground
        return LinuxBackground


# Re-export for backward compatibility
Entry = TrayEntry
Tray = get_tray_backend()