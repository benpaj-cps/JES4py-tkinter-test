#!/usr/bin/env python3

import sys, time, atexit
import tkinter as tk
from PIL import ImageTk
from multiprocessing import Process, Pipe
from queue import Queue
from threading import Thread, Event, enumerate, current_thread

def logger(message, logging=True):
    if logging:
        f = open('MULTITEST.log', 'a')
        f.write(time.ctime() + ': ' + message + '\n')
        f.close()

class ShowProcess(Process):
    def __init__(self, pipe):
        Process.__init__(self)
        self.pipe = pipe
        self.start()

    def run(self):
        logger(f"run(): Process {self.pid} has started")
        
        # Run GUI window
        self.app = ShowApp(self.pipe)

        # Application has finished
        del self.app

        logger(f"run(): Process {self.pid} is exiting")
        exit()
    
    def exit(self):
        """Signal the process to exit
        
        Sends the exit signal to the image queue, which is monitored
        by the subprocess's listener thread. The listener should then signal
        the subprocess's main thread to exit.
        """
        # self.imageQueue.put(ShowApp.EXIT_CODE)
        self.pipe.send(ShowApp.NOTIFY_EXIT)


class ShowApp():
    EXIT_CODE = 'exit'
    NOTIFY_EXIT = bytes([0])

    def __init__(self, pipe):
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

        # Enter GUI event loop
        # self.root.iconify()
        # self.root.update()
        # self.root.deiconify()
        self.root.mainloop()

    def listen(self):
        logger('Show listener has started')
        # self.canvas = tk.Canvas(self.root)
        # self.canvas.pack()
        # imageID = None
        
        # Wait for an image to be sent from main process
        picture = self.pipe.recv()
        
        while picture != self.EXIT_CODE:
            # Should be an image, add to queue
            self.imageQueue.put_nowait(picture)

            # Tell the GUI to display the next image in queue
            # by adding an custom Tk event to the bottom of the stack
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
        
        logger(f"showImages (thread {self.listenerThread.ident}): at end of function")
        return

    def showImage(self, *args):
        logger('Getting item from image queue')      
        picture = self.imageQueue.get()

        try:
            logger(f'must be an image: {picture}')
            self.root.title(picture.getTitle())
            self.image = ImageTk.PhotoImage(picture.getImage())
            self.canvas.config(width=picture.getWidth(),
                               height=picture.getHeight())        
            if self.imageID is None:
                logger(f'showing a new image: {self.image}')
                self.imageID = self.canvas.create_image(0, 0, image=self.image, anchor=tk.NW)
            else:
                logger(f'repainting exisiting image (id: {self.imageID})')
                self.canvas.itemconfig(self.imageID, image=self.image)
                self.canvas.lift(self.imageID)
        except AttributeError:
            logger('Attribute Error encountered')
            pass

    def __notifyExit(self):
        """Safely stop communication with main process
        """
        
        # Tell main process that this subprocess is unusable
        self.pipe.send(self.NOTIFY_EXIT)

        # Safety interval, to handle the edge case of the main process
        # not seeing the above message in time to stop sending images
        # time.sleep(0.001)

        # If the main process tried to send anything, it would block
        # until the message was consumed (by this subprocess).
        # while self.pipe.poll():
            # _ = self.pipe.recv()   
        
        # self.pipe.close()

    def stopBackground(self, event, thread):
        """Handle Python exiting"""
        logger(f"stopBackground: threading.enumerate(): {enumerate()}")
        logger(f'stopBackground: threading.current_thread: {current_thread()}')
        self.listenerThread.join(timeout=1)
        
        if self.listenerThread.is_alive():
            raise RuntimeError(f"Listener thread for show() failed to quit")
        elif self.listenerThread.is_alive() == False:
            logger(f'stopBackground: Listener thread for show ({self.listenerThread}) has stopped')
        # exit()
    
    def onWindowClosed(self):
        """Handle GUI window close event"""
        logger('windowClosed')
        # Notify main process that subprocess is no longer usable
        # self.commandPipe.send(ShowApp.NOTIFY_EXIT)
        # self.root.destroy()
        self.__notifyExit()
        # self.showThread.join()
        # exit()
    
    def onListenerExit(self, *args):
        """Handle request from listener to exit process"""
        # logger(f'onListenerExit')
        logger(f'onListenerExit: current thread is {current_thread()}')
        # self.__notifyExit()
        # logger('notify complete')
        self.root.destroy()
        self.root.quit()
        del self.root, self.canvas
        # self.showThread.join()
        logger(f"onListenerExit: threading.enumerate(): {enumerate()}")
        del self.listenerThread
        logger(f"onListenerExit: 2nd threading.enumerate(): {enumerate()}")

        # if self.showThread.is_alive():
        #     self.showThread.join(timeout=1)
        
        # if self.showThread.is_alive():
        #     raise RuntimeError(f"Listener thread for show() failed to quit")
        # elif self.showThread.is_alive() == False:
        #     logger(f'stopBackground: Listener thread for show ({self.showThread}) has stopped')
        # exit()
