#!/usr/bin/env python3

"""
show.py - script program to implement the "show" and "repaint" functionality
            in JES for the JES4py package

Written: 2020-07-22 Jonathan Senning <jonathan.senning@gordon.edu>

The "show()" function in JES will open a new window and display the image
associated with the given Picture object in the window.  The window is
static and does not provide for user interaction.  When the "repaint()"
function is called, however, the contents of the window are refreshed so
that any changes to the displayed Picture (the image itself or the picture's
title) are displayed.  Thus, repaint() can be used to produce simple
animations.

The jes4py.Picture module defines the Picture class, which has show() and
repaint() methods.  The show() method saves the Picture object's image to a
temporary JPEG file and starts a subprocess to run this program.  It passes
the name of the temporary file and the Picture object's title to the script
on the command line.  This program then opens a window, displays the
image, and waits for input on stdin (standard input).

The repaint() method overwrites the temporary JPEG file with the current
image associated with the Picture object and then writes a line to the
subprocess' stdin consisting of the JPEG filename and the title string.

Upon receving input from stdin, this program resets the window title and
redisplays the contents of the image file.

This program will terminate if it is sent the single line message "exit".

Implementation note: The thread portion of this program is based on the
first example at https://wiki.wxpython.org/LongRunningTasks.  The pickling
method is based on that shown in
https://www.imagetracking.org.uk/2018/03/piping-numpy-arrays-to-other-processes-in-python/
"""

import wx
import sys, os
import pickle
from threading import *
from jes4py import *

class MessageEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data"""
    def __init__(self, data):
        """Initializer for MessageEvent class

        Parameters
        ----------
        data : (can be any type, but will be a string in this program)
            the message contents
        """
        wx.PyEvent.__init__(self)
        self.SetEventType(wx.ID_ANY)
        self.data = data

# Thread class that executes processing
class Listener(Thread):
    """Listener Thread Class"""
    def __init__(self, notifyWindow):
        """Initializer for Listener Thread Class

        Parameters
        ----------
        notifyWindow : wx.Frame
            the window to notify when a message is received
        """
        Thread.__init__(self)
        self.notifyWindow = notifyWindow
        self.start()

    def run(self):
        """Run Listener thread"""
        while True:
            data = sys.stdin.buffer.read(1)
            if data == Picture.show_control_exit:
                wx.PostEvent(self.notifyWindow, MessageEvent(None))
                return
            elif data == Picture.show_control_data:
                try:
                    data = sys.stdin.buffer.read(8)
                    dataLen = int.from_bytes(data, byteorder='big')
                    pkg = sys.stdin.buffer.read(dataLen)
                    wx.PostEvent(self.notifyWindow, MessageEvent(pkg))
                except RuntimeError:
                    return
            else:
                # unrecognised control code
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
        filename : str
            the name of an image file containing the image to display
        title : str
            the title string for the window
        """
        super(MainWindow, self).__init__(parent=parent)
        self.Connect(-1, -1, wx.ID_ANY, self.OnMessage)
        self.worker = Listener(self)
        self.panel = None

    def OnMessage(self, event):
        """Handle received message

        Parameters
        ----------
        event : wx.Event
            the event object
        """
        if event.data is None:
            # all done
            self.Close()
        else:
            picture = pickle.loads(event.data)
            if self.panel is None:
                self.panel = wx.Panel(parent=self)
                self.showPicture(picture)
                self.sizer = wx.BoxSizer(wx.VERTICAL)
                self.sizer.Add(self.panel, 0, wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.ALL, 0)
                self.SetSizerAndFit(self.sizer)
                #imageSize = (picture.getWidth(), picture.getHeight())
                #self.SetClientSize(imageSize)
                self.Refresh()
            else:
                self.showPicture(picture)

    def showPicture(self, picture):
        image = picture.getWxImage()
        imageSize = image.GetSize()
        #print(f'Showing {picture.getTitle()} with size {imageSize}')
        bmp = wx.Bitmap(image, wx.BITMAP_TYPE_ANY)
        self.SetTitle(picture.getTitle())
        self.bitmap = wx.StaticBitmap(parent=self.panel, size=imageSize, bitmap=bmp)
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
    main(sys.argv)
