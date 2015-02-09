#!/usr/bin/python

from twisted.internet import gtk3reactor

from ChannelDialog import ChannelDialog
from GtkChannelListBoxItem import GtkChannelListBoxItem


gtk3reactor.install()

from twisted.internet import reactor

from gi.repository import Gtk
import time, os
from ConnectDialog import ConnectDialog

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import protocol

if os.path.dirname(os.path.realpath(__file__)).startswith("/usr/local/"):
    DATADIR = "/usr/local/share/gnome-irc/"
elif os.path.dirname(os.path.realpath(__file__)).startswith("/usr/"):
    DATADIR = "/usr/share/gnome-irc/"
else:
    DATADIR = ""

class Client(irc.IRCClient):

    def __init__(self):
        self.channels = {}
        self.selected = ""

    def _get_nickname(self):
        return self.factory.username

    def _get_password(self):
        return self.factory.password

    nickname = property(_get_nickname)
    password = property(_get_password)

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

        # get some stuff
        self.parent = self.factory.parent
        self.msg_entry = self.parent.message_entry

        self.addChannel("Server")

        self.log("[Connected established at %s]" %
                 time.asctime(time.localtime(time.time())), "Server")

    def on_join_clicked(self, widget):
        dialog = ChannelDialog(self.parent)
        dialog.connect('response', self.dialog_response_join)
        dialog.show()

    def dialog_response_join(self, dialog, response):

        if response == Gtk.ResponseType.OK:
            channel = dialog.channel.get_text()

            dialog.destroy()

            self.join(channel)

        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLost(self, reason)
        self.log("[Disconnected at %s]" %
                 time.asctime(time.localtime(time.time())), "Server")

    # callbacks for events
    def keypress(self, widget, event):
        if event.keyval == 65293:
            self.msg(self.selected, widget.get_text())
            self.log("<%s> %s" % (self.nickname, widget.get_text()), self.selected)
            widget.set_text("")
            return True
        return False

    def channel_selected(self, widget, selected):
        self.selected = selected.channel
        self.parent.messages_view.set_buffer(self.channels[selected.channel])

    def signedOn(self):
        """Called when bot has succesfully signed on to server."""
        self.log("Successfuly connected!", "Server")

        self.msg_entry.connect("key-press-event", self.keypress)
        self.parent.chan_list.connect("row-selected", self.channel_selected)

        button = Gtk.Button("Join Channel")
        button.connect("clicked", self.on_join_clicked)
        self.parent.hb.pack_end(button)
        self.parent.show_all()

        self.join(self.factory.channel)

    def joined(self, channel):
        self.addChannel(channel)
        self.selected = channel
        self.log("[You have joined %s]" % channel, channel)

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        if not any(channel in s for s in self.channels):
            self.addChannel(channel) # multiple channels for znc

        user = user.split('!', 1)[0]
        self.log("<%s> %s" % (user, msg), channel)

    def action(self, user, channel, msg):
        """This will get called when the bot sees someone do an action."""
        user = user.split('!', 1)[0]
        self.log("* %s %s" % (user, msg), channel)

    # irc callbacks

    def irc_NICK(self, prefix, params):
        """Called when an IRC user changes their nickname."""
        old_nick = prefix.split('!')[0]
        new_nick = params[0]
        self.log("%s is now known as %s" % (old_nick, new_nick), self.selected)


    # For fun, override the method that determines how a nickname is changed on
    # collisions. The default method appends an underscore.
    def alterCollidedNick(self, nickname):
        """
        Generate an altered version of a nickname that caused a collision in an
        effort to create an unused related name for subsequent registration.
        """
        return nickname + '_'

    def log(self, message, channel):
        end_iter = self.channels[channel].get_end_iter()
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.channels[channel].insert(end_iter, '%s %s\n' % (timestamp, message))

    def addChannel(self, channel):
        row = GtkChannelListBoxItem(channel)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=50)
        row.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)

        label1 = Gtk.Label(channel, xalign=0)
        label2 = Gtk.Label("Some more info text here", xalign=0)
        vbox.pack_start(label1, True, True, 0)
        #vbox.pack_start(label2, True, True, 0)

        button = Gtk.Button("Close")
        button.props.valign = Gtk.Align.CENTER
        hbox.pack_start(button, False, True, 0)
        row.show_all()
        self.parent.chan_list.add(row)
        self.channels[channel] = Gtk.TextBuffer.new(None)

class IRCFactory(protocol.ClientFactory):
    """A factory for Clients.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = Client

    def __init__(self, username, channel, password, messages_buffer, chan_list, parent):
        self.channel = channel
        self.username = username
        self.password = password
        self.chan_list = chan_list
        self.messages_buffer = messages_buffer
        self.parent = parent

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, show an error."""
        end_iter = self.messages_buffer.get_end_iter()
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.messages_buffer.insert(end_iter, '%s Connection lost! Reason: %s\n' % (timestamp, reason))
        # connector.connect()

    def clientConnectionFailed(self, connector, reason):
        end_iter = self.messages_buffer.get_end_iter()
        timestamp = time.strftime("[%H:%M:%S]", time.localtime(time.time()))
        self.messages_buffer.insert(end_iter, '%s Connection failed! Reason: %s\n' % (timestamp, reason))
        reactor.stop()


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Gnome IRC")
        self.set_border_width(10)
        self.set_default_size(800, 600)

        self.hb = Gtk.HeaderBar()
        self.hb.set_show_close_button(True)
        self.hb.props.title = "Gnome IRC"
        self.set_titlebar(self.hb)

        button = Gtk.Button("Quick Connect")
        button.connect("clicked", self.on_connect_clicked)
        self.hb.pack_start(button)

        builder = Gtk.Builder()
        builder.add_from_file(DATADIR + "data/main_view.glade")
        self.message_entry = builder.get_object("message_entry")
        self.messages_view = builder.get_object("messages")
        self.ircview = builder.get_object("ircviewpane")
        self.chan_list = builder.get_object("channel_list")

        self.add(self.ircview)
        self.connect("delete_event", self.on_quit)
        self.connect("delete_event", self.on_quit)

    def on_connect_clicked(self, widget):
        dialog = ConnectDialog(self)
        dialog.connect('response', self.dialog_response_cb)
        dialog.show()

    def dialog_response_cb(self, dialog, response):

        if response == Gtk.ResponseType.OK:
            server = dialog.address_entry.get_text()
            port = int(dialog.port_entry.get_text())
            nickname = dialog.nick_entry.get_text()
            password = dialog.password.get_text()
            channel = dialog.channel.get_text()

            dialog.destroy()

            factory = IRCFactory(nickname, channel, password,
                                 self.messages_view.get_buffer(),
                                 self.chan_list, self)

            # connect factory to this host and port
            reactor.connectTCP(server, port, factory)

        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def on_quit(self, *args):
        #Gtk.main_quit()
        reactor.stop()


win = MainWindow()
win.set_wmclass ("Gnome IRC", "Gnome IRC")
win.set_title ("Gnome IRC")
win.show_all()
reactor.run()