#!/usr/bin/env python3

import sys, pickle, atexit
import socket
import tkinter as tk
from PIL import ImageTk
from queue import Queue
from threading import Thread, Event

def logger(message, logging=False):
    if logging:
        f = open('SOCKETTEST.log', 'a')
        f.write(message + '\n')
        f.close()

class App():
    EXIT_CODE = b'\x00'
    PICTURE_CODE = b'\x01'
    ExitCode = 'exit'

    def __init__(self):
        self.root = tk.Tk()
        self.imageQueue = Queue()
        stopEvent = Event()
        self.showThread = Thread(target=self.showImages, args=(stopEvent,), daemon=True)
        self.showThread.start()
        self.listenThread = Thread(target=self.listener, args=(stopEvent,), daemon=True)
        self.listenThread.start()
        atexit.register(self.stopBackground, stopEvent, self.showThread)
        atexit.register(self.stopBackground, stopEvent, self.listenThread)
        self.root.protocol("WM_DELETE_WINDOW", self.windowClosed)
        self.root.mainloop()

    def listener(self, event):
        # Open socket on unused port 
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 0))
        port = self.sock.getsockname()[1]
        logger(f'Port will be {port}')

        # Write port on stdout - should be read via pipes by parent process
        logger('About to write port to stdout')
        print(port)
        sys.stdout.flush()
        logger('finished writing port')

        # Ready start work...  Listen for connections
        backlog = 5
        self.sock.listen()#backlog)

        logger('About to accept on socket')
        self.client, address = self.sock.accept()
        logger('About to start main loop')
        while not event.is_set():
            logger('Waiting to receive message...')
            opCode = self.client.recv(1)
            logger(f'Just read something: {opCode}')
            if len(opCode) == 0 or opCode == self.EXIT_CODE:
                logger('Exiting')
                self.imageQueue.put('exit')
                self.client.close()
                return
                #exit()
            elif opCode == self.PICTURE_CODE:
                logger('Getting a picture')
                data = sys.stdin.buffer.read(8)
                dataLen = int.from_bytes(data, byteorder='big')
                logger(f'I need to read {dataLen} bytes')
                pkg = sys.stdin.buffer.read(dataLen)
                logger(f'I just read {len(pkg)} bytes')
                picture = pickle.loads(pkg)
                self.imageQueue.put(picture)
                logger('Image was put into queue')
            else:
                logger('Unknown opCode')

    def showImages(self, event):
        logger('Show thread has started')
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()
        imageID = None
        while not event.is_set():
            picture = self.imageQueue.get()
            logger('Possible image found on queue...')
            logger(f'  Type: {type(picture)}')
            logger(f'  Value: {picture}')
            if isinstance(picture, str) and picture == self.ExitCode:
                logger('not an image - exit code')
                #self.root.destroy()
                return

class MainWindow(wx.Frame):
    """Window class for show program
    """

    def __init__(self, parent):
        """Initializer for MainWindow

        Parameters
        ----------
        parent : wxFrame
            the parent frame
        """
        super(MainWindow, self).__init__(parent=parent)

        # Set up listener for data coming in over pipe
        self.Connect(-1, -1, wx.ID_ANY, self.OnMessage)
        self.worker = Listener(self)

        # Create panel for displayed window
        self.panel = wx.Panel(parent=self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.ALL, 0)
        self.SetSizerAndFit(self.sizer)

    def OnMessage(self, event):
        """Handle received message

        Parameters
        ----------
        event : wx.Event
            the event object

        event.data is either None (to indicate request to terminate program)
        or a pickled Picture object
        """
        if event.data is None:
            # all done
            self.Close()
        else:
            # unpickle data and update displayed image
            picture = pickle.loads(event.data)
            self.updateBitmap(picture)

    def updateBitmap(self, picture):
        """Update bitmap of displayed image

        Parameters
        ----------
        picture : Picture object
            picture to display
        """
        image = picture.getWxImage()
        imageSize = image.GetSize()
        bmp = wx.Bitmap(image)
        self.SetTitle(picture.getTitle())
        self.bitmap = wx.StaticBitmap(parent=self.panel, size=imageSize, \
                                        bitmap=bmp)
        self.SetClientSize(imageSize)
        self.Refresh()

# ===========================================================================
# Main program
# ===========================================================================

def main(argv):
    app = wx.App(False)
    frame = MainWindow(parent=None)
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    app = App()
