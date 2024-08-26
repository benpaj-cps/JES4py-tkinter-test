#!/usr/bin/env python3

"""
show.py - script program to implement the "show" and "repaint" functionality
            in JES for the JES4py package

Written: 2020-07-22 Jonathan Senning <jonathan.senning@gordon.edu>
Revised: 2020-09-02 Jonathan Senning <jonathan.senning@gordon.edu>
- received pickled picture objects rather than filename, no need to read files

Revised: 2022-08-16 by Dr. Senning 
- initial Tkinter port
Modified 2024-08-26 Benjamin Pajunen <benjamin.pajunen@gordon.edu>
- changed to run as a Process instance using multiprocessing module
- moved image display updates to main thread event handler

The "show()" function in JES will open a new window and display the image
associated with the given Picture object in the window.  The window is
static and does not provide for user interaction.  When the "repaint()"
function is called, however, the contents of the window are refreshed so
that any changes to the displayed Picture (the image itself or the picture's
title) are displayed.  Thus, repaint() can be used to produce simple
animations.

The jes4py.Picture module defines the Picture class, which has show() and
repaint() methods.  The show() method causes this script to be run in a
subprocess and uses a pipe to send a pickled picture object to the subprocess.
The repaint() method checks to make sure a subprocess for this picture object
is currently running and then sends the pickled updated picture object.

Implementation note: The thread portion of this program is based on the
first example at https://wiki.wxpython.org/LongRunningTasks.
"""

import tkinter as tk
from PIL import ImageTk
from multiprocessing import Process
from queue import Queue
from threading import Thread

class ShowProcess(Process):
    """Process wrapper for ShowApp"""
    def __init__(self, pipe):
        """Initializer for ShowProcess class
        
        Parameters
        ----------
        pipe : multiprocessing.Connection
            one end of a pipe which connects to the main process
        """
        Process.__init__(self)
        self.pipe = pipe
        self.start()

    def run(self):
        """Run "show" process"""
        # Run GUI window
        self.app = ShowApp(self.pipe)

        # Application has finished
        del self.app
        exit()
    
    def exit(self):
        """Signal the process to exit"""
        self.pipe.send(ShowApp.EXIT_CODE)


class ShowApp():
    """App class for show program
    """
    EXIT_CODE = bytes([0])

    def __init__(self, pipe):
        """Initializer for ShowApp class
        
        Parameters
        ----------
        pipe : multiprocessing.Connection
            one end of a pipe which connects to the main process
        """
        # Record connection to main process
        self.pipe = pipe
        
        # Create GUI application root window
        self.root = tk.Tk()
        
        # Register callback for when the window is closed by user
        self.root.protocol('WM_DELETE_WINDOW', self.onWindowClosed)
        
        # Register callbacks for custom events used by listener
        self.root.bind('<<ListenerExit>>', self.onListenerExit)
        self.root.bind('<<ImageQueued>>', self.showImage)
        
        # Create canvas for displaying image
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()
        
        # Create threadsafe queue for images to be displayed
        self.imageQueue = Queue()

        # Used to display the eventual image item on the canvas
        self.image = None
        self.imageID = None
        
        # Create and run listener thread
        self.listenerThread = Thread(target=self.listen, daemon=True)
        self.listenerThread.start()            

        # Ensure window displays on top (Windows platforms)
        self.root.iconify()
        self.root.update()
        self.root.deiconify()

        # Enter GUI event loop
        self.root.mainloop()

    def listen(self):
        """Run listener thread"""
        
        # Wait for an image to be sent from main process
        picture = self.pipe.recv()
        
        while picture != self.EXIT_CODE:
            # Should be an image, add to queue
            self.imageQueue.put_nowait(picture)

            # Tell the Tk window to display the next image in queue
            # by adding a custom event to the bottom of the stack
            self.root.event_generate('<<ImageQueued>>', when='tail')
            
            try:
                # Wait for next image
                picture = self.pipe.recv()
            except EOFError:
                # Main process has closed pipe
                break
            except BrokenPipeError or OSError:
                # Problem with pipe, cannot receive images
                break

        # No more images to receive; signal process to exit:
        self.root.event_generate('<<ListenerExit>>', when='head')
        

    def showImage(self, *args):
        """Display an image from this subprocess's queue"""
        picture = self.imageQueue.get()

        try:
            self.root.title(picture.getTitle())
            self.image = ImageTk.PhotoImage(picture.getImage())
            self.canvas.config(width=picture.getWidth(),
                               height=picture.getHeight())        
            if self.imageID is None:
                self.imageID = self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
            else:
                self.canvas.itemconfig(self.imageID, image=self.image)
                self.canvas.lift(self.imageID)
        except AttributeError:
            print("Attempted to show a non-image")
            pass
    
    def onWindowClosed(self):
        """Handle GUI window close event"""
        # Request exit signal from main process
        self.pipe.send(self.EXIT_CODE)
    
    def onListenerExit(self, *args):
        """Handle request from listener to exit process"""
        # End the app window
        self.root.destroy()

        # Make sure the Tcl interpreter quits
        self.root.quit()
        
        del self.root, self.canvas
        del self.listenerThread
