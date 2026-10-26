"""
Compatibility layer for libadwaita widgets using vanilla GTK4.
This allows the existing code and blueprints to work without libadwaita.
"""

from gi.repository import Gtk, GLib, GObject, Gio, Adw as _Adw

# Check if libadwaita is available
try:
    _Adw.init()
    HAS_ADW = True
except Exception:
    HAS_ADW = False

# Re-export everything from Adw if available, otherwise provide Gtk equivalents
if HAS_ADW:
    from gi.repository import Adw
    # Use real Adw
    Application = Adw.Application
    ApplicationWindow = Adw.ApplicationWindow
    NavigationView = Adw.NavigationView
    NavigationPage = Adw.NavigationPage
    ToolbarView = Adw.ToolbarView
    HeaderBar = Adw.HeaderBar
    ViewStack = Adw.ViewStack
    ViewStackPage = Adw.ViewStackPage
    ViewSwitcher = Adw.ViewSwitcher
    ViewSwitcherBar = Adw.ViewSwitcherBar
    Clamp = Adw.Clamp
    StatusPage = Adw.StatusPage
    PreferencesDialog = Adw.PreferencesDialog
    PreferencesPage = Adw.PreferencesPage
    PreferencesGroup = Adw.PreferencesGroup
    ActionRow = Adw.ActionRow
    EntryRow = Adw.EntryRow
    ComboRow = Adw.ComboRow
    SwitchRow = Adw.SwitchRow
    SpinRow = Adw.SpinRow
    Dialog = Adw.Dialog
    MessageDialog = Adw.MessageDialog
    ToastOverlay = Adw.ToastOverlay
    Toast = Adw.Toast
    AboutDialog = Adw.AboutDialog
    Carousel = Adw.Carousel
    CarouselIndicatorDots = Adw.CarouselIndicatorDots
    BreakpointBin = Adw.BreakpointBin
    Breakpoint = Adw.Breakpoint
    WrapBox = Adw.WrapBox
    Avatar = Adw.Avatar
    Squeezer = Adw.Squeezer
    Leaflet = Adw.Leaflet
    Flap = Adw.Flap
    WindowTitle = Adw.WindowTitle
    StyleManager = Adw.StyleManager
    ColorScheme = Adw.ColorScheme
else:
    # Provide Gtk equivalents
    from .gtk_compat import (
        Application, ApplicationWindow, NavigationView, NavigationPage,
        ToolbarView, HeaderBar, ViewStack, ViewStackPage, ViewSwitcher,
        ViewSwitcherBar, Clamp, StatusPage, PreferencesDialog, PreferencesPage,
        PreferencesGroup, ActionRow, EntryRow, ComboRow, SwitchRow, SpinRow,
        Dialog, MessageDialog, ToastOverlay, Toast, AboutDialog, Carousel,
        CarouselIndicatorDots, BreakpointBin, Breakpoint, WrapBox, Avatar,
        Squeezer, Leaflet, Flap, WindowTitle, StyleManager, ColorScheme
    )

# Export all
__all__ = [
    'Application', 'ApplicationWindow', 'NavigationView', 'NavigationPage',
    'ToolbarView', 'HeaderBar', 'ViewStack', 'ViewStackPage', 'ViewSwitcher',
    'ViewSwitcherBar', 'Clamp', 'StatusPage', 'PreferencesDialog', 'PreferencesPage',
    'PreferencesGroup', 'ActionRow', 'EntryRow', 'ComboRow', 'SwitchRow', 'SpinRow',
    'Dialog', 'MessageDialog', 'ToastOverlay', 'Toast', 'AboutDialog', 'Carousel',
    'CarouselIndicatorDots', 'BreakpointBin', 'Breakpoint', 'WrapBox', 'Avatar',
    'Squeezer', 'Leaflet', 'Flap', 'WindowTitle', 'StyleManager', 'ColorScheme',
    'HAS_ADW'
]