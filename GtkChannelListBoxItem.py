from gi.repository import Gtk

class GtkChannelListBoxItem(Gtk.ListBoxRow):
    def __init__(self, channel):
        Gtk.ListBoxRow.__init__(self)
        self.channel = channel