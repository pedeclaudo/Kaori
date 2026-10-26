import asyncio
import os
import sys
import time

import gi

gi.require_version('Gtk', '4.0')
# gi.require_version('Adw', '1')  # Removed for Windows port
from gi.events import GLibEventLoopPolicy

asyncio.set_event_loop_policy(GLibEventLoopPolicy())

from gi.repository import Gio, GLib, Gtk, Gdk
from gql.transport.exceptions import TransportError

from .constants import NAME, DONATE_URL, set_version
from .integrations import Suwayomi
from .server import LocalServer
from .widgets import KaoriWindow, build_shortcuts
from .widgets.preferences import KaoriPreferences
from .widgets.setup import SetupWindow

from .platform import Entry, Tray, get_autostart_backend, get_background_backend

APPLICATION_ID = 'io.github.riyaniii.Kaori'

READY_TIMEOUT = 90
POLL_INTERVAL = 0.5
AUTOSTART_COMMAND = ['kaori', '--background']


def run_until_done(coro, timeout: float) -> None:
    task = asyncio.ensure_future(coro)
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while not task.done() and time.monotonic() < deadline:
        if not context.iteration(False):
            time.sleep(0.01)
    if not task.done():
        task.cancel()


class KaoriApplication(Gtk.Application):

    def __init__(self, version: str) -> None:
        super().__init__(application_id=APPLICATION_ID,
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
                         resource_base_path='/io/github/riyaniii/Kaori')
        self.version = version
        self.settings = Gio.Settings(schema_id=APPLICATION_ID)
        self.suwayomi = Suwayomi()
        self.server = LocalServer()
        self.tray = None
        self.background_start = False
        self.background_held = False

        self.add_main_option('background', 0, GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE,
                             'Start the server without opening a window', None)
        self.connect('handle-local-options', self.on_handle_local_options)
        self.settings.connect('changed::run-in-background',
                              lambda *args: self.apply_background_settings())
        self.settings.connect('changed::run-on-startup',
                              lambda *args: self.apply_background_settings())
        self.suwayomi.connect('notify::downloader-state',
                              lambda *args: self.refresh_tray())
        self.suwayomi.download_queue.connect('items-changed',
                                             lambda *args: self.refresh_tray())

        # Platform-specific backends
        self.autostart_backend = get_autostart_backend()(APPLICATION_ID, NAME)
        self.background_backend = get_background_backend()(APPLICATION_ID, AUTOSTART_COMMAND)

        self.create_action('quit', lambda *args: self.quit(), ['<control>q'])

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        self.load_theme()

    def load_theme(self) -> None:
        """Load the application CSS theme."""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource('/io/github/riyaniii/Kaori/theme.css')
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.create_action('preferences', self.on_preferences_action, ['<control>comma'])
        self.create_action('shortcuts', self.on_shortcuts_action,
                           ['<control>question', '<control>slash'])
        self.create_action('about', self.on_about_action)
        self.create_action('change_instance', self.on_change_instance_action)

    def do_activate(self) -> None:
        background_start, self.background_start = self.background_start, False

        if win := self.props.active_window:
            win.present()
            return

        mode = self.settings.get_string('suwayomi-mode')
        if mode not in ('local', 'remote'):
            self.show_setup_window()
            return

        hidden = (background_start
                  and sys.platform == 'linux'
                  and mode == 'local'
                  and self.settings.get_boolean('run-in-background'))

        self.hold()
        asyncio.create_task(self.launch_or_setup(
            mode, self.settings.get_string('suwayomi-url'), not hidden))

    def do_shutdown(self) -> None:
        run_until_done(self.suwayomi.close(), 5)
        self.set_tray(False)
        self.server.stop()
        Gtk.Application.do_shutdown(self)

    def on_handle_local_options(self, app, options) -> int:
        if options.contains('background'):
            self.background_start = True
        return -1

    def failure_message(self, mode: str) -> str:
        if mode == 'local' and self.server.log_path:
            return f"Couldn't start the local server. See the log:\n{self.server.log_path}"
        if mode == 'local':
            return "Couldn't start the local server. Check the logs and try again."
        return "Couldn't connect. Check the address and try again."

    async def launch_or_setup(self, mode: str, url: str, show_window: bool = True) -> None:
        try:
            if not await self.launch(mode, url, show_window):
                self.show_setup_window(error=self.failure_message(mode))
        except Exception as e:
            print(f'[kaori] failed to start: {e!r}')
            self.server.stop()
            self.show_setup_window(error=f"Failed to start: {e}")
        finally:
            self.release()

    async def launch(self, mode: str, url: str, show_window: bool = True) -> bool:
        local = mode == 'local'
        if local and not self.server.running:
            self.server.start()
        await self.suwayomi.reconnect(self.server.url if local else url)

        if not await self.wait_for_server():
            await self.suwayomi.disconnect()
            self.server.stop()
            return False

        self.settings.set_string('suwayomi-mode', mode)
        self.settings.set_string('suwayomi-url', '' if local else url)
        if show_window:
            KaoriWindow(application=self).present()
        self.apply_background_settings()
        return True

    async def wait_for_server(self) -> bool:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + READY_TIMEOUT
        while loop.time() < deadline:
            if self.server.exited:
                print('[kaori] server exited early')
                print('[kaori] ---- server.log (tail) ----')
                print(self.server.log_tail())
                print('[kaori] ----------------------------')
                return False
            try:
                if await self.suwayomi.getServerSettings():
                    return True
            except (TransportError, OSError, TimeoutError):
                pass
            await asyncio.sleep(POLL_INTERVAL)
        print(f'[kaori] server did not become ready within {READY_TIMEOUT}s')
        return False

    def set_background_hold(self, held: bool) -> None:
        if held and not self.background_held:
            self.hold()
        elif not held and self.background_held:
            self.release()
        self.background_held = held

    def set_tray(self, shown: bool) -> None:
        if Tray is None:
            return
        if shown and not self.tray:
            self.tray = Tray(APPLICATION_ID, NAME, self.tray_entries())
        elif not shown and self.tray:
            self.tray.close()
            self.tray = None

    def refresh_tray(self) -> None:
        if self.tray:
            self.tray.set_entries(self.tray_entries())

    def downloads_label(self) -> str:
        count = self.suwayomi.download_queue.get_n_items()
        if not count:
            return 'Downloads'
        if self.suwayomi.downloader_state == 'STARTED':
            return f'Downloads ({count})'
        return f'Downloads ({count}, paused)'

    def tray_entries(self) -> list:
        count = self.suwayomi.download_queue.get_n_items()
        running = self.suwayomi.downloader_state == 'STARTED'
        downloads = Entry(
            self.downloads_label(),
            children=[
                Entry('Pause Downloads' if running else 'Resume Downloads',
                      self.toggle_downloads, running or count > 0),
                Entry('Clear Download Queue', self.clear_downloads, count > 0),
            ],
        )
        return [
            Entry('Open Kaori', self.activate),
            Entry(separator=True),
            downloads,
            Entry(separator=True),
            Entry('Open Web Interface', self.open_web_interface),
            Entry(separator=True),
            Entry('Quit', self.quit),
        ]

    def toggle_downloads(self) -> None:
        if self.suwayomi.downloader_state == 'STARTED':
            asyncio.create_task(self.suwayomi.stopDownloader())
        else:
            asyncio.create_task(self.suwayomi.startDownloader())

    def clear_downloads(self) -> None:
        asyncio.create_task(self.suwayomi.clearDownloader())

    def open_web_interface(self) -> None:
        Gio.AppInfo.launch_default_for_uri(self.suwayomi.url, None)

    def apply_background_settings(self) -> None:
        local = self.settings.get_string('suwayomi-mode') == 'local'
        background = local and self.settings.get_boolean('run-in-background')
        autostart = background and self.settings.get_boolean('run-on-startup')

        self.set_background_hold(background)
        self.set_tray(background)
        if background:
            self.suwayomi.startPolling()

        # Use platform abstraction for autostart
        self.autostart_backend.set_autostart(autostart, AUTOSTART_COMMAND)
        # Use platform abstraction for background
        self.background_backend.request_background(background, autostart, AUTOSTART_COMMAND)

    def show_setup_window(self, error: str | None = None) -> None:
        SetupWindow(application=self, error=error).present()

    def on_change_instance_action(self, *args) -> None:
        self.server.stop()
        self.set_background_hold(False)
        self.set_tray(False)
        if win := self.props.active_window:
            for dialog in list(win.get_dialogs()):
                dialog.force_close()
            win.close()
        self.show_setup_window()

    def on_about_action(self, *args) -> None:
        dialog = Gtk.AboutDialog(
            program_name=NAME,
            logo_icon_name=APPLICATION_ID,
            version=self.version,
            authors=['Riyan Parvez (rini)'],
            artists=['Riyan Parvez (rini)'],
            copyright='© 2026 Riyan Parvez',
            comments='A beautiful manga reader for Suwayomi',
            license_type=Gtk.License.GPL_3_0,
            website='https://github.com/riyaniii/Kaori',
            website_label='GitHub Repository',
        )
        # Add link to Buy Me a Coffee
        dialog.add_credit_section("CI added by", ["Oween Unda", "Jaish Khan"])
        dialog.present(self.props.active_window)

    def on_preferences_action(self, *args) -> None:
        KaoriPreferences().present(self.props.active_window)

    def on_shortcuts_action(self, *args) -> None:
        build_shortcuts().present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None, parameter_type=None) -> None:
        action = Gio.SimpleAction.new(name, parameter_type)
        action.connect('activate', callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f'app.{name}', shortcuts)


def main(version: str) -> int:
    set_version(version)
    return KaoriApplication(version).run(sys.argv)
