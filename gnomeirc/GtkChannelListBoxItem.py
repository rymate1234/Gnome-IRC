from gi.repository import Gtk, Gio

# various guff for the listbox of channels

class GtkChannelListBoxItem(Gtk.ListBoxRow):
    def __init__(self, channel):
        Gtk.ListBoxRow.__init__(self)
        self.channel = channel

class GtkChannelCloseButton(Gtk.Button):
    def __init__(self, channel):
        Gtk.Button.__init__(self)
        icon = Gio.ThemedIcon(name="window-close-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        self.add(image)
        self.channel = channel