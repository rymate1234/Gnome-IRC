#!/usr/bin/env python2
from distutils.core import setup

__author__ = 'rymate1234'

setup(name='Gnome IRC',
      version='1.0',
      description='IRC Client for the GNOME Desktop',
      author='rymate1234',
      author_email='ryan.murthick@rymate.co.uk',
      url='https://github.com/rymate1234/Gnome-IRC',
      packages=['gnomeirc'],
      data_files=[('share/gnome-irc/data/',
                   ['data/channel.glade', 'data/main_view.glade', 'data/server.glade']),
                  ('share/pixmaps', ['data/gnome-irc.png']),
                  ('share/applications', ['data/gnomeirc.desktop'])],
      scripts=['gnome-irc'],
)