"""
GTK4 implementations of libadwaita widgets.
These provide the same API as Adw widgets but using vanilla GTK4.
"""

from gi.repository import Gtk, GLib, GObject, Gio, Gdk, Pango, Graphene


# ============================================================================
# GType Registration Helpers
# ============================================================================

def register_adw_type(cls, adw_name):
    """Register a compat class with the Adw GType name."""
    # The Adw GType names are typically like "AdwApplicationWindow"
    # We register our class with that name so .ui files work
    try:
        GObject.type_register(cls)
        # Also register with the Adw name
        gtype_name = f"Adw{adw_name}"
        GObject.type_register(cls, gtype_name)
    except Exception:
        pass  # Ignore registration errors


# ============================================================================
# Style Manager (simplified)
# ============================================================================

class ColorScheme:
    DEFAULT = 0
    PREFER_LIGHT = 1
    PREFER_DARK = 2
    FORCE_LIGHT = 3
    FORCE_DARK = 4


class StyleManager(GObject.Object):
    """Simplified StyleManager that uses GTK settings."""

    __gtype_name__ = 'KaoriStyleManager'

    color_scheme = GObject.Property(type=int, default=ColorScheme.DEFAULT)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._settings = Gtk.Settings.get_default()
        self._apply_color_scheme()

        if self._settings:
            self._settings.connect('notify::gtk-application-prefer-dark-theme',
                                   self._on_theme_changed)

    def _on_theme_changed(self, settings, pspec):
        self._apply_color_scheme()

    def _apply_color_scheme(self):
        if not self._settings:
            return
        scheme = self.props.color_scheme
        if scheme == ColorScheme.FORCE_DARK or scheme == ColorScheme.PREFER_DARK:
            self._settings.props.gtk_application_prefer_dark_theme = True
        elif scheme == ColorScheme.FORCE_LIGHT or scheme == ColorScheme.PREFER_LIGHT:
            self._settings.props.gtk_application_prefer_dark_theme = False

    @classmethod
    def get_default(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ============================================================================
# Application & ApplicationWindow
# ============================================================================

class Application(Gtk.Application):
    """Compatible with Adw.Application."""
    pass


class ApplicationWindow(Gtk.ApplicationWindow):
    """Compatible with Adw.ApplicationWindow."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add a default header bar if not set
        if not self.get_titlebar():
            header = HeaderBar()
            self.set_titlebar(header)


# ============================================================================
# Navigation View & Page
# ============================================================================

class NavigationPage(Gtk.Box):
    """Compatible with Adw.NavigationPage."""

    __gtype_name__ = 'KaoriNavigationPage'

    title = GObject.Property(type=str, default='')
    tag = GObject.Property(type=GObject.TYPE_PYOBJECT, default=None)

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._child = None

    def set_child(self, child):
        if self._child:
            self.remove(self._child)
        self._child = child
        if child:
            self.append(child)

    def get_child(self):
        return self._child


class NavigationView(Gtk.Box):
    """Compatible with Adw.NavigationView."""

    __gtype_name__ = 'KaoriNavigationView'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_transition_duration(300)
        self._stack.set_vexpand(True)
        self._stack.set_hexpand(True)
        self.append(self._stack)
        self._pages = []
        self._current_page = None

    def push(self, page: NavigationPage):
        """Push a page onto the navigation stack."""
        if page not in self._pages:
            self._pages.append(page)
            self._stack.add_named(page, str(id(page)))
        self._stack.set_visible_child(page)
        self._current_page = page

    def push_by_tag(self, tag):
        """Push a page by its tag."""
        for page in self._pages:
            if page.props.tag == tag:
                self.push(page)
                break

    def pop(self):
        """Pop the current page."""
        if len(self._pages) > 1:
            self._pages.pop()
            page = self._pages[-1]
            self._stack.set_visible_child(page)
            self._current_page = page

    def get_visible_page(self):
        return self._current_page

    def get_pages(self):
        return self._pages


# ============================================================================
# Toolbar View & Header Bar
# ============================================================================

class HeaderBar(Gtk.HeaderBar):
    """Compatible with Adw.HeaderBar."""
    pass


class ToolbarView(Gtk.Box):
    """Compatible with Adw.ToolbarView."""

    __gtype_name__ = 'KaoriToolbarView'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._top_bars = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._content = None
        self._bottom_bars = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        self.append(self._top_bars)
        self._content_box = Gtk.Box()
        self._content_box.set_vexpand(True)
        self._content_box.set_hexpand(True)
        self.append(self._content_box)
        self.append(self._bottom_bars)

    def add_top_bar(self, bar: Gtk.Widget):
        self._top_bars.append(bar)

    def add_bottom_bar(self, bar: Gtk.Widget):
        self._bottom_bars.append(bar)

    def set_content(self, content: Gtk.Widget):
        if self._content:
            self._content_box.remove(self._content)
        self._content = content
        if content:
            self._content_box.append(content)

    def get_content(self):
        return self._content


# ============================================================================
# View Stack & View Switcher
# ============================================================================

class ViewStackPage(Gtk.Box):
    """Compatible with Adw.ViewStackPage."""

    __gtype_name__ = 'KaoriViewStackPage'

    name = GObject.Property(type=str, default='')
    title = GObject.Property(type=str, default='')
    icon = GObject.Property(type=str, default='')
    needs_attention = GObject.Property(type=bool, default=False)
    use_underline = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._child = None

    def set_child(self, child):
        if self._child:
            self.remove(self._child)
        self._child = child
        if child:
            self.append(child)

    def get_child(self):
        return self._child


class ViewStack(Gtk.Stack):
    """Compatible with Adw.ViewStack."""

    __gtype_name__ = 'KaoriViewStack'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.set_transition_duration(300)

    def add_named(self, child: ViewStackPage, name: str):
        self.add_child(child, name)
        if child.props.title:
            child.set_name(name)


class ViewSwitcher(Gtk.Box):
    """Compatible with Adw.ViewSwitcher."""

    __gtype_name__ = 'KaoriViewSwitcher'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self._stack = None
        self._buttons = {}
        self.add_css_class('view-switcher')

    def set_stack(self, stack: ViewStack):
        self._stack = stack
        self._rebuild_buttons()
        if stack:
            stack.connect('notify::visible-child-name', self._on_page_changed)

    def _rebuild_buttons(self):
        for btn in self._buttons.values():
            self.remove(btn)
        self._buttons.clear()

        if not self._stack:
            return

        for page in self._stack.get_children():
            if isinstance(page, ViewStackPage):
                btn = Gtk.ToggleButton(label=page.props.title or page.props.name)
                btn.add_css_class('view-switcher-button')
                if page.props.icon:
                    img = Gtk.Image.new_from_icon_name(page.props.icon)
                    btn.set_child(img)
                btn.connect('toggled', self._on_button_toggled, page.props.name)
                self._buttons[page.props.name] = btn
                self.append(btn)

    def _on_button_toggled(self, btn, name):
        if btn.get_active():
            self._stack.set_visible_child_name(name)

    def _on_page_changed(self, stack, pspec):
        name = stack.get_visible_child_name()
        for btn_name, btn in self._buttons.items():
            btn.set_active(btn_name == name)


class ViewSwitcherBar(Gtk.Box):
    """Compatible with Adw.ViewSwitcherBar."""

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self._switcher = ViewSwitcher()
        self.append(self._switcher)
        self.add_css_class('view-switcher-bar')

    def set_stack(self, stack: ViewStack):
        self._switcher.set_stack(stack)


# ============================================================================
# Clamp
# ============================================================================

class Clamp(Gtk.Box):
    """Compatible with Adw.Clamp."""

    __gtype_name__ = 'KaoriClamp'

    maximum_size = GObject.Property(type=int, default=600)
    tightening_threshold = GObject.Property(type=int, default=100)

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._child = None
        self._center_box = Gtk.CenterBox()
        self._center_box.set_hexpand(True)
        self._center_box.set_vexpand(False)
        self.append(self._center_box)

    def set_child(self, child):
        if self._child:
            self._center_box.remove(self._child)
        self._child = child
        if child:
            self._center_box.set_center_widget(child)

    def get_child(self):
        return self._child


# ============================================================================
# Status Page
# ============================================================================

class StatusPage(Gtk.Box):
    """Compatible with Adw.StatusPage."""

    __gtype_name__ = 'KaoriStatusPage'

    title = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')
    icon_name = GObject.Property(type=str, default='')
    paintable = GObject.Property(type=Gdk.Paintable, default=None)
    child = GObject.Property(type=Gtk.Widget, default=None)

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)
        self.set_spacing(16)
        self.add_css_class('status-page')

        self._icon = Gtk.Image()
        self._icon.add_css_class('status-page-icon')
        self.append(self._icon)

        self._title = Gtk.Label()
        self._title.add_css_class('status-page-title')
        self._title.add_css_class('title-1')
        self.append(self._title)

        self._description = Gtk.Label()
        self._description.add_css_class('status-page-description')
        self._description.set_wrap(True)
        self._description.set_max_width_chars(50)
        self._description.set_justify(Gtk.Justification.CENTER)
        self.append(self._description)

        self._child_widget = None

        self.connect('notify::title', self._update_title)
        self.connect('notify::description', self._update_description)
        self.connect('notify::icon-name', self._update_icon)
        self.connect('notify::paintable', self._update_paintable)
        self.connect('notify::child', self._update_child)

    def _update_title(self, *args):
        self._title.set_text(self.props.title)

    def _update_description(self, *args):
        self._description.set_text(self.props.description)

    def _update_icon(self, *args):
        if self.props.icon_name:
            self._icon.set_from_icon_name(self.props.icon_name)
            self._icon.set_visible(True)
        else:
            self._icon.set_visible(False)

    def _update_paintable(self, *args):
        if self.props.paintable:
            self._icon.set_paintable(self.props.paintable)
            self._icon.set_visible(True)
        elif not self.props.icon_name:
            self._icon.set_visible(False)

    def _update_child(self, *args):
        if self._child_widget:
            self.remove(self._child_widget)
        self._child_widget = self.props.child
        if self._child_widget:
            self.append(self._child_widget)


# ============================================================================
# Preferences Widgets
# ============================================================================

class PreferencesDialog(Gtk.Dialog):
    """Compatible with Adw.PreferencesDialog."""

    __gtype_name__ = 'KaoriPreferencesDialog'

    def __init__(self, **kwargs):
        kwargs.setdefault('modal', True)
        kwargs.setdefault('use_header_bar', True)
        super().__init__(**kwargs)
        self.add_css_class('preferences-dialog')
        self.set_default_size(600, 500)

        content_area = self.get_content_area()
        content_area.set_orientation(Gtk.Orientation.VERTICAL)
        content_area.set_spacing(0)

        # Use a stack for pages
        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._stack.set_hexpand(True)
        content_area.append(self._stack)

        self._pages = []

    def add(self, page: 'PreferencesPage'):
        self._pages.append(page)
        self._stack.add_named(page, page.props.name or str(len(self._pages)))

    def remove(self, page: 'PreferencesPage'):
        if page in self._pages:
            self._pages.remove(page)
            self._stack.remove(page)


class PreferencesPage(Gtk.Box):
    """Compatible with Adw.PreferencesPage."""

    __gtype_name__ = 'KaoriPreferencesPage'

    title = GObject.Property(type=str, default='')
    name = GObject.Property(type=str, default='')
    icon_name = GObject.Property(type=str, default='')

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.add_css_class('preferences-page')
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self._groups = []

    def add(self, group: 'PreferencesGroup'):
        self._groups.append(group)
        self.append(group)

    def remove(self, group: 'PreferencesGroup'):
        if group in self._groups:
            self._groups.remove(group)
            self.remove(group)


class PreferencesGroup(Gtk.Box):
    """Compatible with Adw.PreferencesGroup."""

    __gtype_name__ = 'KaoriPreferencesGroup'

    title = GObject.Property(type=str, default='')
    description = GObject.Property(type=str, default='')
    header_suffix = GObject.Property(type=Gtk.Widget, default=None)

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self.add_css_class('preferences-group')
        self.set_spacing(0)

        self._header = None
        self._rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._rows_box.add_css_class('preferences-group-rows')
        self.append(self._rows_box)

        self.connect('notify::title', self._update_header)
        self.connect('notify::description', self._update_header)
        self.connect('notify::header-suffix', self._update_header)

    def _update_header(self, *args):
        if self.props.title or self.props.description:
            if not self._header:
                self._header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                self._header.add_css_class('preferences-group-header')
                self.insert_child_after(self._header, None)

            # Clear header
            for child in list(self._header.get_children()):
                self._header.remove(child)

            if self.props.title:
                title_label = Gtk.Label(label=self.props.title)
                title_label.add_css_class('preferences-group-title')
                title_label.set_xalign(0)
                title_label.set_hexpand(True)
                self._header.append(title_label)

            if self.props.description:
                desc_label = Gtk.Label(label=self.props.description)
                desc_label.add_css_class('preferences-group-description')
                desc_label.set_xalign(0)
                desc_label.set_wrap(True)
                self._header.append(desc_label)

            if self.props.header_suffix:
                self._header.append(self.props.header_suffix)
        elif self._header:
            self.remove(self._header)
            self._header = None

    def add(self, row: 'ActionRow'):
        self._rows_box.append(row)

    def remove(self, row: 'ActionRow'):
        self._rows_box.remove(row)


class ActionRow(Gtk.ListBoxRow):
    """Compatible with Adw.ActionRow."""

    __gtype_name__ = 'KaoriActionRow'

    title = GObject.Property(type=str, default='')
    subtitle = GObject.Property(type=str, default='')
    activatable = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_css_class('action-row')
        self.set_activatable(self.props.activatable)
        self.set_selectable(True)

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._box.set_spacing(12)
        self._box.set_margin_start(16)
        self._box.set_margin_end(16)
        self._box.set_margin_top(12)
        self._box.set_margin_bottom(12)
        self.set_child(self._box)

        self._prefix = None
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._content_box.set_hexpand(True)
        self._content_box.set_valign(Gtk.Align.CENTER)
        self._content_box.set_spacing(4)
        self._box.append(self._content_box)

        self._title_label = Gtk.Label()
        self._title_label.add_css_class('action-row-title')
        self._title_label.set_xalign(0)
        self._title_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._content_box.append(self._title_label)

        self._subtitle_label = Gtk.Label()
        self._subtitle_label.add_css_class('action-row-subtitle')
        self._subtitle_label.set_xalign(0)
        self._subtitle_label.set_ellipsize(Pango.EllipsizeMode.END)
        self._subtitle_label.set_visible(False)
        self._content_box.append(self._subtitle_label)

        self._suffix_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._suffix_box.set_spacing(6)
        self._box.append(self._suffix_box)

        self.connect('notify::title', self._update_title)
        self.connect('notify::subtitle', self._update_subtitle)
        self.connect('notify::activatable', self._update_activatable)

    def _update_title(self, *args):
        self._title_label.set_text(self.props.title)

    def _update_subtitle(self, *args):
        self._subtitle_label.set_text(self.props.subtitle)
        self._subtitle_label.set_visible(bool(self.props.subtitle))

    def _update_activatable(self, *args):
        self.set_activatable(self.props.activatable)

    def add_prefix(self, widget: Gtk.Widget):
        if self._prefix:
            self._box.remove(self._prefix)
        self._prefix = widget
        self._box.insert_child_after(widget, None)

    def add_suffix(self, widget: Gtk.Widget):
        self._suffix_box.append(widget)

    def remove_suffix(self, widget: Gtk.Widget):
        self._suffix_box.remove(widget)


class EntryRow(ActionRow):
    """Compatible with Adw.EntryRow."""

    __gtype_name__ = 'KaoriEntryRow'

    text = GObject.Property(type=str, default='')
    placeholder_text = GObject.Property(type=str, default='')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._entry = Gtk.Entry()
        self._entry.set_hexpand(True)
        self._entry.set_halign(Gtk.Align.END)
        self._entry.set_max_width_chars(30)
        self.add_suffix(self._entry)

        self._entry.connect('changed', self._on_entry_changed)
        self.connect('notify::text', self._update_entry)
        self.connect('notify::placeholder-text', self._update_placeholder)

    def _on_entry_changed(self, entry):
        self.props.text = entry.get_text()

    def _update_entry(self, *args):
        self._entry.set_text(self.props.text)

    def _update_placeholder(self, *args):
        self._entry.set_placeholder_text(self.props.placeholder_text)


class ComboRow(ActionRow):
    """Compatible with Adw.ComboRow."""

    __gtype_name__ = 'KaoriComboRow'

    model = GObject.Property(type=GObject.TYPE_PYOBJECT, default=None)
    selected = GObject.Property(type=int, default=0)
    selected_item = GObject.Property(type=GObject.TYPE_PYOBJECT, default=None)
    use_subtitle = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._combo = Gtk.ComboBox()
        self._combo.set_hexpand(False)
        self._combo.set_halign(Gtk.Align.END)
        self.add_suffix(self._combo)

        self._combo.connect('changed', self._on_combo_changed)
        self.connect('notify::model', self._update_model)
        self.connect('notify::selected', self._update_selected)
        self.connect('notify::selected-item', self._update_selected_item)

    def _on_combo_changed(self, combo):
        self.props.selected = combo.get_active()
        if self.props.model:
            active = combo.get_active()
            if active >= 0 and active < len(self.props.model):
                self.props.selected_item = self.props.model[active]

    def _update_model(self, *args):
        model = self.props.model
        if model:
            string_model = Gtk.StringList()
            for item in model:
                if isinstance(item, str):
                    string_model.append(item)
                else:
                    string_model.append(str(item))
            self._combo.set_model(string_model)

    def _update_selected(self, *args):
        self._combo.set_active(self.props.selected)

    def _update_selected_item(self, *args):
        if self.props.selected_item and self.props.model:
            try:
                idx = self.props.model.index(self.props.selected_item)
                self._combo.set_active(idx)
            except ValueError:
                pass


class SwitchRow(ActionRow):
    """Compatible with Adw.SwitchRow."""

    __gtype_name__ = 'KaoriSwitchRow'

    active = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._switch = Gtk.Switch()
        self._switch.set_valign(Gtk.Align.CENTER)
        self.add_suffix(self._switch)

        self._switch.connect('notify::active', self._on_switch_changed)
        self.connect('notify::active', self._update_switch)

    def _on_switch_changed(self, switch, pspec):
        self.props.active = switch.get_active()

    def _update_switch(self, *args):
        self._switch.set_active(self.props.active)


class SpinRow(ActionRow):
    """Compatible with Adw.SpinRow."""

    __gtype_name__ = 'KaoriSpinRow'

    adjustment = GObject.Property(type=Gtk.Adjustment, default=None)
    numeric = GObject.Property(type=bool, default=True)
    clamp = GObject.Property(type=bool, default=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        adj = self.props.adjustment or Gtk.Adjustment(value=0, lower=0, upper=100, step_increment=1)
        self._spin = Gtk.SpinButton.new(adj, 1.0, 0)
        self._spin.set_hexpand(False)
        self._spin.set_halign(Gtk.Align.END)
        self._spin.set_numeric(self.props.numeric)
        self.add_suffix(self._spin)

        self.connect('notify::adjustment', self._update_adjustment)

    def _update_adjustment(self, *args):
        if self.props.adjustment:
            self._spin.set_adjustment(self.props.adjustment)


# ============================================================================
# Dialogs
# ============================================================================

class Dialog(Gtk.Dialog):
    """Compatible with Adw.Dialog."""

    __gtype_name__ = 'KaoriDialog'

    def __init__(self, **kwargs):
        kwargs.setdefault('modal', True)
        kwargs.setdefault('use_header_bar', True)
        super().__init__(**kwargs)
        self.add_css_class('dialog')
        self.set_default_size(400, 300)


class MessageDialog(Gtk.MessageDialog):
    """Compatible with Adw.MessageDialog."""

    __gtype_name__ = 'KaoriMessageDialog'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_css_class('message-dialog')


# ============================================================================
# Toast Overlay
# ============================================================================

class Toast(Gtk.Widget):
    """Compatible with Adw.Toast."""

    __gtype_name__ = 'KaoriToast'

    title = GObject.Property(type=str, default='')
    timeout = GObject.Property(type=int, default=3)
    use_markup = GObject.Property(type=bool, default=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_css_class('toast')

        self._revealer = Gtk.Revealer()
        self._revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        self._revealer.set_transition_duration(250)
        self._revealer.set_reveal_child(True)

        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._box.add_css_class('toast-box')
        self._box.set_margin_top(8)
        self._box.set_margin_bottom(8)
        self._box.set_margin_start(12)
        self._box.set_margin_end(12)
        self._box.set_spacing(12)
        self._revealer.set_child(self._box)
        self.set_child(self._revealer)

        self._label = Gtk.Label()
        self._label.set_wrap(True)
        self._label.set_use_markup(self.props.use_markup)
        self._box.append(self._label)

        self._button = None

        self.connect('notify::title', self._update_title)
        self.connect('notify::use-markup', self._update_markup)

    def _update_title(self, *args):
        self._label.set_text(self.props.title)

    def _update_markup(self, *args):
        self._label.set_use_markup(self.props.use_markup)

    def set_button(self, label, callback):
        if self._button:
            self._box.remove(self._button)
        self._button = Gtk.Button(label=label)
        self._button.add_css_class('toast-button')
        self._button.connect('clicked', lambda b: callback())
        self._box.append(self._button)


class ToastOverlay(Gtk.Overlay):
    """Compatible with Adw.ToastOverlay."""

    __gtype_name__ = 'KaoriToastOverlay'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._toasts = []
        self._toast_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self._toast_box.set_valign(Gtk.Align.END)
        self._toast_box.set_halign(Gtk.Align.CENTER)
        self._toast_box.set_margin_bottom(48)
        self._toast_box.set_spacing(8)
        self.add_overlay(self._toast_box)

    def add_toast(self, toast: Toast):
        self._toasts.append(toast)
        self._toast_box.append(toast)

        # Auto-dismiss after timeout
        if toast.props.timeout > 0:
            GLib.timeout_add_seconds(toast.props.timeout, self._dismiss_toast, toast)

    def _dismiss_toast(self, toast):
        if toast in self._toasts:
            self._toasts.remove(toast)
        if toast.get_parent():
            toast.get_parent().remove(toast)
        return GLib.SOURCE_REMOVE


# ============================================================================
# About Dialog
# ============================================================================

class AboutDialog(Gtk.AboutDialog):
    """Compatible with Adw.AboutDialog."""
    pass


# ============================================================================
# Carousel
# ============================================================================

class Carousel(Gtk.Box):
    """Compatible with Adw.Carousel."""

    __gtype_name__ = 'KaoriCarousel'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self._scrolled = Gtk.ScrolledWindow()
        self._scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self._scrolled.set_kinetic_scrolling(True)
        self._scrolled.set_hscrollbar_policy(Gtk.PolicyType.NEVER)
        self._scrolled.set_vexpand(True)
        self._scrolled.set_hexpand(True)

        self._inner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._inner_box.set_spacing(16)
        self._scrolled.set_child(self._inner_box)
        self.append(self._scrolled)

        self._pages = []

    def append(self, page: Gtk.Widget):
        self._pages.append(page)
        self._inner_box.append(page)

    def remove(self, page: Gtk.Widget):
        if page in self._pages:
            self._pages.remove(page)
            self._inner_box.remove(page)

    def get_n_pages(self):
        return len(self._pages)

    def get_page(self, index):
        if 0 <= index < len(self._pages):
            return self._pages[index]
        return None


class CarouselIndicatorDots(Gtk.Box):
    """Compatible with Adw.CarouselIndicatorDots."""

    __gtype_name__ = 'KaoriCarouselIndicatorDots'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self.set_halign(Gtk.Align.CENTER)
        self.set_spacing(8)
        self._carousel = None
        self._dots = []

    def set_carousel(self, carousel: Carousel):
        self._carousel = carousel
        self._rebuild_dots()
        if carousel:
            carousel.connect('notify::children', lambda *a: self._rebuild_dots())

    def _rebuild_dots(self):
        for dot in self._dots:
            self.remove(dot)
        self._dots.clear()

        if not self._carousel:
            return

        n_pages = self._carousel.get_n_pages()
        for i in range(n_pages):
            dot = Gtk.Button()
            dot.add_css_class('carousel-indicator-dot')
            dot.set_size_request(8, 8)
            dot.connect('clicked', lambda b, idx=i: self._on_dot_clicked(idx))
            self.append(dot)
            self._dots.append(dot)

        self._update_active(0)

    def _on_dot_clicked(self, index):
        # Carousel doesn't have built-in page switching, so we scroll
        if self._carousel and self._carousel._scrolled:
            page = self._carousel.get_page(index)
            if page:
                # Scroll to page
                pass

    def _update_active(self, index):
        for i, dot in enumerate(self._dots):
            dot.add_css_class('active') if i == index else dot.remove_css_class('active')


# ============================================================================
# Breakpoint Bin
# ============================================================================

class BreakpointBin(Gtk.Box):
    """Compatible with Adw.BreakpointBin."""

    __gtype_name__ = 'KaoriBreakpointBin'

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, **kwargs)
        self._breakpoints = []
        self._child = None

    def set_child(self, child):
        if self._child:
            self.remove(self._child)
        self._child = child
        if child:
            self.append(child)

    def get_child(self):
        return self._child

    def add_breakpoint(self, breakpoint: 'Breakpoint'):
        self._breakpoints.append(breakpoint)


class Breakpoint(GObject.Object):
    """Compatible with Adw.Breakpoint."""

    __gtype_name__ = 'KaoriBreakpoint'

    condition = GObject.Property(type=str, default='')
    name = GObject.Property(type=str, default='')


# ============================================================================
# WrapBox
# ============================================================================

class WrapBox(Gtk.FlowBox):
    """Compatible with Adw.WrapBox."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_max_children_per_line(0)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.add_css_class('wrap-box')


# ============================================================================
# Other widgets (minimal implementations)
# ============================================================================

class Avatar(Gtk.Image):
    """Compatible with Adw.Avatar."""
    pass


class Squeezer(Gtk.Box):
    """Compatible with Adw.Squeezer."""

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self.add_css_class('squeezer')


class Leaflet(Gtk.Box):
    """Compatible with Adw.Leaflet."""

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)


class Flap(Gtk.Box):
    """Compatible with Adw.Flap."""

    def __init__(self, **kwargs):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, **kwargs)
        self._content = None
        self._flap = None

    def set_content(self, content):
        if self._content:
            self.remove(self._content)
        self._content = content
        if content:
            self.append(content)

    def set_flap(self, flap):
        if self._flap:
            self.remove(self._flap)
        self._flap = flap
        if flap:
            self.insert_child_after(flap, None)


class WindowTitle(Gtk.Label):
    """Compatible with Adw.WindowTitle."""
    pass


# Export all
__all__ = [
    'Application', 'ApplicationWindow', 'NavigationView', 'NavigationPage',
    'ToolbarView', 'HeaderBar', 'ViewStack', 'ViewStackPage', 'ViewSwitcher',
    'ViewSwitcherBar', 'Clamp', 'StatusPage', 'PreferencesDialog', 'PreferencesPage',
    'PreferencesGroup', 'ActionRow', 'EntryRow', 'ComboRow', 'SwitchRow', 'SpinRow',
    'Dialog', 'MessageDialog', 'ToastOverlay', 'Toast', 'AboutDialog', 'Carousel',
    'CarouselIndicatorDots', 'BreakpointBin', 'Breakpoint', 'WrapBox', 'Avatar',
    'Squeezer', 'Leaflet', 'Flap', 'WindowTitle', 'StyleManager', 'ColorScheme'
]


# ============================================================================
# Register classes with Adw GType names for .ui file compatibility
# ============================================================================

# Only register if Adw is not available (Windows)
if not HAS_ADW:
    register_adw_type(Application, 'Application')
    register_adw_type(ApplicationWindow, 'ApplicationWindow')
    register_adw_type(NavigationView, 'NavigationView')
    register_adw_type(NavigationPage, 'NavigationPage')
    register_adw_type(ToolbarView, 'ToolbarView')
    register_adw_type(HeaderBar, 'HeaderBar')
    register_adw_type(ViewStack, 'ViewStack')
    register_adw_type(ViewStackPage, 'ViewStackPage')
    register_adw_type(ViewSwitcher, 'ViewSwitcher')
    register_adw_type(ViewSwitcherBar, 'ViewSwitcherBar')
    register_adw_type(Clamp, 'Clamp')
    register_adw_type(StatusPage, 'StatusPage')
    register_adw_type(PreferencesDialog, 'PreferencesDialog')
    register_adw_type(PreferencesPage, 'PreferencesPage')
    register_adw_type(PreferencesGroup, 'PreferencesGroup')
    register_adw_type(ActionRow, 'ActionRow')
    register_adw_type(EntryRow, 'EntryRow')
    register_adw_type(ComboRow, 'ComboRow')
    register_adw_type(SwitchRow, 'SwitchRow')
    register_adw_type(SpinRow, 'SpinRow')
    register_adw_type(Dialog, 'Dialog')
    register_adw_type(MessageDialog, 'MessageDialog')
    register_adw_type(ToastOverlay, 'ToastOverlay')
    register_adw_type(Toast, 'Toast')
    register_adw_type(AboutDialog, 'AboutDialog')
    register_adw_type(Carousel, 'Carousel')
    register_adw_type(CarouselIndicatorDots, 'CarouselIndicatorDots')
    register_adw_type(BreakpointBin, 'BreakpointBin')
    register_adw_type(Breakpoint, 'Breakpoint')
    register_adw_type(WrapBox, 'WrapBox')
    register_adw_type(Avatar, 'Avatar')
    register_adw_type(Squeezer, 'Squeezer')
    register_adw_type(Leaflet, 'Leaflet')
    register_adw_type(Flap, 'Flap')
    register_adw_type(WindowTitle, 'WindowTitle')
    register_adw_type(StyleManager, 'StyleManager')