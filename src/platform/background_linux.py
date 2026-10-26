"""
Linux background implementation using freedesktop Background portal.
Wraps the original main.py implementation.
"""

from gi.repository import Gio, GLib

from . import BackgroundBackend


class LinuxBackground(BackgroundBackend):
    """Linux background using org.freedesktop.portal.Background"""

    def __init__(self, app_id: str, autostart_command: list[str]) -> None:
        self.app_id = app_id
        self.autostart_command = autostart_command

    def request_background(self, enabled: bool, autostart: bool, command: list[str]) -> None:
        options = {
            'reason': GLib.Variant('s', 'Keep the Suwayomi server running'),
            'background': GLib.Variant('b', enabled),
            'autostart': GLib.Variant('b', autostart),
            'commandline': GLib.Variant('as', command),
            'dbus-activatable': GLib.Variant('b', False),
        }

        def done(bus, result):
            try:
                bus.call_finish(result)
            except GLib.Error as e:
                print("Background portal request failed:", e.message)

        try:
            bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            bus.call(
                'org.freedesktop.portal.Desktop',
                '/org/freedesktop/portal/desktop',
                'org.freedesktop.portal.Background',
                'RequestBackground',
                GLib.Variant('(sa{sv})', ('', options)),
                None, Gio.DBusCallFlags.NONE, -1, None, done)
        except GLib.Error as e:
            print("Background portal unavailable:", e.message)