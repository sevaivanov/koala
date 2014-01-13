#!/usr/bin/python
from app.TkinterApp import TkinterApp
from app.KivyApp import KivyApp
from app.downloader import Youtube

from app.custom.Default import UI
from app.custom.Default import WINDOW_TITLE
from app.custom.Default import DEFAULT_DEST
from app.custom.Default import DEFAULT_UI
from app.custom.Default import HELP_MESSAGE
from app.custom.Default import LaunchOptions

from view.TkinterView import TkinterView
from view.KivyView import KivyView

import sys

PREFERRED_DEST = DEFAULT_DEST
PREFERRED_UI = DEFAULT_UI

def checkKoalaLaunchOptions(args):
    '''
    Here are the koala help options.
    $ ./KoalaBeatzHunter.py h?
    '''
    for arg in args:
        #Help
        if LaunchOptions.H[0] in arg:
            print HELP_MESSAGE
            exit(0)
        #Destination folder
        elif LaunchOptions.D[0] in arg:
            global PREFERRED_DEST
            PREFERRED_DEST = arg[len(LaunchOptions.D[0]):]
        #Tkinter
        elif LaunchOptions.T[0] in arg:
            global PREFERRED_UI
            PREFERRED_UI = UI.TKINTER
        #Kivy
        elif LaunchOptions.K[0] in arg:
            global PREFERRED_UI
            PREFERRED_UI = UI.KIVY
        #Wrong options
        else:
            print HELP_MESSAGE
            exit(0)

if __name__ == "__main__":
    checkKoalaLaunchOptions(sys.argv[1:])
    
    if PREFERRED_UI == UI.TKINTER:
        app = TkinterApp(WINDOW_TITLE, PREFERRED_DEST)
        view = TkinterView(app)
        app.setDownloaderView(view)
        view.root.mainloop()

    elif PREFERRED_UI == UI.KIVY:
        app = KivyApp()
        view = KivyView()
        app.setDownloaderView(view)
        app.setOutputFolder(PREFERRED_DEST)
        app.setYoutubeDownloader(Youtube.YouTube())
        app.run()
        app.root.mainloop()