#!/usr/bin/python2
from twisted.internet import gtk3reactor
from gnomeirc import Utils

from gnomeirc.ChannelDialog import ChannelDialog
from gnomeirc.GtkChannelListBoxItem import GtkChannelListBoxItem, GtkChannelCloseButton

from twisted.internet import defer
from gnomeirc.TabCompletionEntry import TabCompletionEntry
from gnomeirc.UserList import UserList

gtk3reactor.install()

from twisted.internet import reactor

from gi.repository import Gtk, Gio, Gdk
import time, os
from gnomeirc.ConnectDialog import ConnectDialog

# twisted imports
from twisted.words.protocols import irc
from twisted.internet import protocol

if os.path.dirname(os.path.realpath(__file__)).startswith("/usr/local/"):
    DATADIR = "/usr/local/share/gnome-irc/"
elif os.path.dirname(os.path.realpath(__file__)).startswith("/usr/"):
    DATADIR = "/usr/share/gnome-irc/"
else:
    DATADIR = ""

css = """
#toolbar-gnomeirc {
    border-radius: 0;
}

"""

class Client(irc.IRCClient):

    def __init__(self, *args, **kwargs):
        self._namescallback = {}
        self._whoiscallback = {}
        self.channels = {}
        self.channel_users = {}
        self.chan_list_items = {}
        self.selected = ""

    def _get_nickname(self):
        return self.factory.username

    def _get_password(self):
        return self.factory.password

    nickname = property(_get_nickname)
    password = property(_get_password)
    versionName = "GnomeIRC Alpha"

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)

        builder = Gtk.Builder()
        builder.add_from_file(DATADIR + "data/main_view.glade")
        self.message_entry_container = builder.get_object("message_entry_container")
        self.messages_view = builder.get_object("messages")
        self.messages_scroll = builder.get_object("messages_scroll")
        self.ircview = builder.get_object("ircviewpane")
        self.chan_list = builder.get_object("channel_list")

        self.message_entry = TabCompletionEntry(self.update_completion)
        self.message_entry_container.add(self.message_entry)

        # get some stuff
        self.parent = self.factory.parent

        self.parent.addTab(self.ircview, self.factory.server_name, self)

        self.addChannel(self.factory.server_name)

        self.log("[Connected established at %s]" %
                 time.asctime(time.localtime(time.time())), self.factory.server_name)


    def signedOn(self):
        """Called when the client has succesfully signed on to server."""
        self.log("Successfuly connected!", self.factory.server_name)

        self.message_entry.connect("key-press-event", self.keypress)
        self.chan_list.connect("row-selected", self.channel_selected)
        self.messages_view.connect('size-allocate', self.on_new_line)

        self.join(self.factory.channel)

    def receivedMOTD(self, motd):
        """Called when the client gets the motd"""
        self.log("Server MOTD is: ", self.factory.server_name)
        self.log("\n".join(motd), self.factory.server_name)

    def show_users(self):
        users = self.channel_users[self.selected]
        users.get_users().sort()
        self.users_popover = Gtk.Popover().new(self.parent.users_button)
        self.users_popover.set_border_width(6);
        self.users_popover.set_position(Gtk.PositionType.TOP)
        self.users_popover.set_modal(True)
        self.users_popover.set_vexpand(False)
        self.users_popover.connect("closed", self.users_list_closed)
        self.users_popover.set_size_request(160,300)
        self.populate_users_menu(users)
        self.users_popover.add(self.users_list_container)
        self.users_popover.show_all()

    def populate_users_menu(self, users):
        self.users_list_add("Operators", True)
        ops = [user for user in users if user.startswith("@")]
        for s in ops:
            self.users_list_add(s)

        self.users_list_add("Voiced", True)
        voiced = [user for user in users if user.startswith("+")]
        for s in voiced:
            self.users_list_add(s)

        self.users_list_add("Users", True)
        users = [user for user in users if not(user.startswith("+") or user.startswith("@"))]
        for s in users:
            self.users_list_add(s)

    def users_list_add(self, user, bold=False):
        row = Gtk.ListBoxRow()
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)

        if bold:
            label1 = Gtk.Label()
            label1.set_markup("<b>" + user + "</b>")
        else:
            label1 = Gtk.Label(user, xalign=0)
        vbox.pack_start(label1, True, True, 0)

        row.show_all()
        self.users_list.add(row)

    def users_list_closed(self, *args):
        self.users_popover.remove(self.users_list)
        self.users_list.destroy()
        del self.users_list
        self.users_popover.destroy()
        del self.users_popover

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
                 time.asctime(time.localtime(time.time())), self.factory.server_name)

    # callbacks for events
    def keypress(self, widget, event):
        adj = self.messages_scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())
        if event.keyval == Gdk.KEY_Return:
            self.handle_message(widget.get_text())
            widget.set_text("")
            return True
        if event.keyval == Gdk.KEY_Tab:
            return True
        return False

    def handle_message(self, message):
        if message.startswith("/"):
            cmd_args = message.split(" ")
            if cmd_args[0] == "/me":
                message = message.replace("/me ", "")
                self.describe(self.selected, message)
                self.log("* %s %s" % (self.nickname, message), self.selected)
            elif cmd_args[0] == "/join":
                channel = message.replace("/join ", "")
                self.join(channel)
        else:
            self.msg(self.selected, message)
            self.log("<%s> %s" % (self.nickname, message), self.selected)


    def channel_selected(self, widget, selected):
        self.selected = selected.channel
        self.messages_view.set_buffer(self.channels[selected.channel])

    def update_completion(self, prefix):
        user_store = Gtk.ListStore(str)

        if self.selected == "":
            user_store.append([""])
            return user_store

        for user in self.channel_users[self.selected].get_raw_users():
            if user.startswith(prefix):
                user_store.append([user])

        return user_store

    def joined(self, channel):
        self.addChannel(channel)
        self.selected = channel
        self.channel_users[channel] = UserList()
        self.log("[You have joined %s]" % channel, channel)

    def on_new_line(self, widget, event, data=None):
        adj = self.messages_scroll.get_vadjustment()
        adj.set_value(adj.get_upper() - adj.get_page_size())

    def privmsg(self, user, channel, msg):
        """This will get called when the bot receives a message."""
        if not any(channel in s for s in self.channels):
            self.addChannel(channel)  # multiple messages_scrollchannels for znc

        if channel == self.selected:
            adj = self.messages_scroll.get_vadjustment()
            adj.set_value(adj.get_upper() - adj.get_page_size())

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
        for channel, users in self.channel_users.iteritems():
            if users.has_user(old_nick):
                self.log("%s is now known as %s" % (old_nick, new_nick), channel)
                users.change_user(old_nick, new_nick)
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
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.add(hbox)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        hbox.pack_start(vbox, True, True, 0)

        label1 = Gtk.Label(channel, xalign=0)
        vbox.pack_start(label1, True, False, 0)

        button = GtkChannelCloseButton(channel)

        button.props.valign = Gtk.Align.CENTER
        button.connect("clicked", self.on_close_clicked)

        hbox.pack_start(button, False, False, 0)
        row.show_all()
        self.chan_list.add(row)
        self.channels[channel] = Gtk.TextBuffer.new(None)
        self.chan_list_items[channel] = row
        self.chan_list.select_row(row)

    def on_close_clicked(self, widget):
        chan_list_item = self.chan_list_items[widget.channel]
        prev_chan_list_item = self.chan_list.get_row_at_index(chan_list_item.get_index() - 1)
        self.chan_list.remove(chan_list_item)
        self.part(widget.channel)
        self.chan_list.show_all()
        self.selected = ""
        self.chan_list.select_row(prev_chan_list_item)


    # Names command - used for the users list
    def names(self, channel):
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._namescallback:
            self._namescallback[channel] = ([], [])

        self._namescallback[channel][0].append(d)
        self.sendLine("NAMES %s" % channel)
        return d

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2]
        nicklist = params[3].split(' ')

        if channel not in self._namescallback:
            self.channel_users[channel].add_users(nicklist)
            return

        n = self._namescallback[channel][1]
        n += nicklist

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1]
        if channel not in self._namescallback:
            return

        callbacks, namelist = self._namescallback[channel]

        for cb in callbacks:
            cb.callback(namelist)

        del self._namescallback[channel]

    # handling for the WHOIS command
    def performWhois(self, username):
        username = username.lower()
        d = defer.Deferred()
        if username not in self._whoiscallback:
            self._whoiscallback[username] = ([], [])

        self._whoiscallback[username][0].append(d)
        self.whois(username)
        return d

    def irc_RPL_WHOISCHANNELS(self, prefix, params):
        nickname = params[1].lower()
        callbacks, namelist = self._whoiscallback[nickname]

        n = self._whoiscallback[nickname][1]
        n += params

        for cb in callbacks:
            cb.callback(namelist)

        del self._whoiscallback[nickname]

class IRCFactory(protocol.ClientFactory):
    """A factory for Clients.

    A new protocol instance will be created each time we connect to the server.
    """

    # the class of the protocol to build when new connection is made
    protocol = Client

    def __init__(self, username, channel, password, server_name, parent):
        self.channel = channel
        self.username = username
        self.password = password
        self.server_name = server_name
        self.parent = parent

    def clientConnectionLost(self, connector, reason):
        """If we get disconnected, show an error."""
        self.showError('Connection lost! Reason: %s\n' % (reason))
        # connector.connect()

    def clientConnectionFailed(self, connector, reason):
        self.showError('Connection failed! Reason: %s\n' % (reason))
        # reactor.stop()

    def showError(self, error):
        dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR,
            Gtk.ButtonsType.OK, "Error with connection")
        dialog.format_secondary_text(
            error)
        dialog.show()


class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Gnome IRC")
        self.clients = {}
        self.set_default_size(1024, 600)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


        if Utils.isGnome():
            # we're in gnome, so use the gnome UI
            self.hb = Gtk.HeaderBar()
            self.hb.set_show_close_button(True)
            self.hb.props.title = "Gnome IRC"
            self.set_titlebar(self.hb)

            self.server_tabs = Gtk.Notebook.new()
            self.add(self.server_tabs)

        else:
            # not gnome, use the header bar as a toolbar
            layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.add(layout)

            self.hb = Gtk.HeaderBar()
            self.hb.set_name("toolbar-gnomeirc")

            layout.pack_start(self.hb, False, True, 0)

            self.server_tabs = Gtk.Notebook.new()
            layout.pack_start(self.server_tabs, True, True, 0)

        # add the buttons to the toolbar
        self.connect_button = Gtk.Button("Quick Connect")
        self.connect_button.connect("clicked", self.on_connect_clicked)
        self.hb.pack_start(self.connect_button)

        # Join Channel Button
        button = Gtk.Button()

        icon = Gio.ThemedIcon(name="list-add")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button.add(image)

        button.connect("clicked", self.on_join_clicked)

        # Users list button
        button2 = Gtk.Button()

        icon = Gio.ThemedIcon(name="avatar-default-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        button2.add(image)

        self.users_button = button2

        button2.connect("clicked", self.on_users_clicked)

        self.hb.pack_end(button)
        self.hb.pack_end(button2)
        self.show_all()

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
            server_name = dialog.server_name.get_text()

            dialog.destroy()

            factory = IRCFactory(nickname, channel, password, server_name, self)

            # connect factory to this host and port
            reactor.connectTCP(server, port, factory)

            # disable the button once connected, at least until we have a proper multiple server implementation
            # self.connect_button.set_sensitive(False);
            # self.connect_button.set_label("Connected to " + server);
            win.show_all()

        elif response == Gtk.ResponseType.CANCEL:
            dialog.destroy()

    def addTab(self, widget, server, client):
        self.server_tabs.append_page(widget, Gtk.Label(server))
        self.clients[server] = client
        self.show_all()


    def on_join_clicked(self, widget):
        if not self.clients:
            return

        current_client = self.clients[self.get_current_page()]

        dialog = ChannelDialog(self)
        dialog.connect('response', current_client.dialog_response_join)
        dialog.show()


    def on_users_clicked(self, widget):
        if not self.clients:
            return

        current_client = self.clients[self.get_current_page()]

        if not hasattr(current_client, "users_popover"):
            builder = Gtk.Builder()
            builder.add_from_file(DATADIR + "data/users_list.glade")
            current_client.users_list = builder.get_object("users_list")
            current_client.users_list_container = builder.get_object("users_list_container")
            #current_client.names(current_client.selected).addCallback(current_client.got_users)
            current_client.show_users()

    def get_current_page(self):
        page_num = self.server_tabs.get_current_page()
        page_widget = self.server_tabs.get_nth_page(page_num)
        page_name = self.server_tabs.get_tab_label_text(page_widget)
        return page_name

    def on_quit(self, *args):
        #Gtk.main_quit()
        reactor.stop()


win = MainWindow()
win.set_wmclass ("Gnome IRC", "Gnome IRC")
win.set_title ("Gnome IRC")
win.show_all()
reactor.run()