from gi.repository import Gtk


class ChannelDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Join Channel", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK), use_header_bar=1)

        builder = Gtk.Builder()
        builder.add_from_file("channel.glade")
        self.channel = builder.get_object("channel")
        self.get_content_area().add(builder.get_object("ChannelForm"))
