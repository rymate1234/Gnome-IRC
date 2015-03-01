# A tab completion entrybox - originally found on github,
# modified to remove dependency on Gtk EntryCompletion
# See https://gist.github.com/ssokolow/135673/ for original

from gi.repository import Gtk, Gio, Gdk

MOD_MASK = ( Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.MOD1_MASK |
Gdk.ModifierType.MOD4_MASK | Gdk.ModifierType.SHIFT_MASK )

class TabCompletionEntry(Gtk.Entry):
    def __init__(self, completion_getter):
        Gtk.Entry.__init__(self)

        self.completion_getter = completion_getter
        self.completed = False  # Used by "allow Tab-cycling after completion"
        self.completing = ''
        self.completion_prev = ""

        self.connect('changed', self.content_changed_cb)
        self.connect('key-press-event', self.entry_keypress_cb)
        self.connect('activate', self.activate_cb)

    def activate_cb(self, widget):
        if False:
            self.stop_emission('activate')

    def entry_keypress_cb(self, widget, event):
        text = self.get_text()
        prefix = text.split(" ")[-1]

        if event.keyval == Gdk.KEY_Tab and not event.state & MOD_MASK and (
                    not self.completed):

            if self.completing:
                liststore = self.completion_getter(self.completing_prefix)

                if len(liststore) < self.liststore_length:
                    old_text = self.completed_text
                    self.completed_text = liststore[0][self.liststore_length]
                    self.liststore_length = len(liststore)
                    self.set_text(text.replace(old_text, self.completed_text))
                    self.set_position(-1)
                    self.liststore_length += 1
                    return True

            liststore = self.completion_getter(prefix)

            if len(liststore) == 0:
                # Users can press Tab twice in this circumstance to confirm.
                self.completed = True
            if len(liststore) == 1:
                self.set_text(text.replace(prefix, liststore[0][0]))
                self.set_position(-1)
                self.completed = True
            else:
                self.completing = True
                self.completing_prefix = prefix
                self.liststore_length = len(liststore)
                self.completed_text = liststore[0][self.liststore_length]
                self.set_text(text.replace(prefix, self.completed_text))
                self.set_position(-1)
                self.liststore_length += 1
            return True
        else:
            # we're no longer completing
            self.completing = False
            return False

    def content_changed_cb(self, widget):
        self.completed = False

