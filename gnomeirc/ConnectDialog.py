from gi.repository import Gtk


class ConnectDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Connect to a Server", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK), use_header_bar=1)

        builder = Gtk.Builder()
        builder.add_from_file("data/server.glade")
        self.address_entry = builder.get_object("address")
        self.port_entry = builder.get_object("port")
        self.nick_entry = builder.get_object("username")
        self.password = builder.get_object("password")
        self.channel = builder.get_object("channel")
        self.get_content_area().add(builder.get_object("ServerForm"))
