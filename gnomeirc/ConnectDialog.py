import os
import platform
from gi.repository import Gtk
from gnomeirc import Utils

if os.path.dirname(os.path.realpath(__file__)).startswith("/usr/local/"):
    DATADIR = "/usr/local/share/gnome-irc/"
elif os.path.dirname(os.path.realpath(__file__)).startswith("/usr/"):
    DATADIR = "/usr/share/gnome-irc/"
else:
    DATADIR = ""

if Utils.isGnome():
    HEADER_BARS = 1
else:
    HEADER_BARS = 0


class ConnectDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Connect to a Server", parent, 0,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OK, Gtk.ResponseType.OK), use_header_bar=HEADER_BARS)

        builder = Gtk.Builder()
        builder.add_from_file(DATADIR + "data/server.glade")
        self.address_entry = builder.get_object("address")
        self.server_name = builder.get_object("server_name")
        self.port_entry = builder.get_object("port")
        self.nick_entry = builder.get_object("username")
        self.password = builder.get_object("password")
        self.channel = builder.get_object("channel")
        self.get_content_area().add(builder.get_object("ServerForm"))
