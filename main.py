from twisted.internet import gtk3reactor
from gnomeirc.MainWindow import MainWindow

gtk3reactor.install()

from twisted.internet import reactor


if __name__ == "__main__":
    win = MainWindow()
    win.set_wmclass ("Gnome IRC", "Gnome IRC")
    win.set_title ("Gnome IRC")
    win.show_all()
    reactor.run()