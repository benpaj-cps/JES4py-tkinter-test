#!/usr/bin/env python3

import sys, pickle, atexit
import tkinter as tk
from PIL import ImageTk
from multiprocessing import Process, SimpleQueue
from queue import Empty, Full
from threading import Thread, Event

def logger(message, logging=True):
    if logging:
        f = open('MULTITEST.log', 'a')
        f.write(message + '\n')
        f.close()

class ShowProcess(Process):
    def __init__(self, imageQueue):
        Process.__init__(self)
        self.imageQueue = imageQueue
        self.start()
    
    def run(self):
        self.app = ShowApp(self.imageQueue)
    
    def exit(self):
        """Signal the process to exit
        
        Sends the exit signal to the image queue, which is monitored
        by the subprocess's listener thread. The listener should then signal
        the subprocess's main thread to exit.
        """
        self.imageQueue.put(ShowApp.EXIT_CODE)


class ShowApp():
    EXIT_CODE = 'exit'

    def __init__(self, imageQueue):
        self.root = tk.Tk()
        self.imageQueue = imageQueue
        stopEvent = Event()
        self.showThread = Thread(target=self.showImages, args=(stopEvent,), daemon=True)
        self.showThread.start()
        atexit.register(self.stopBackground, stopEvent, self.showThread)
        self.root.protocol("WM_DELETE_WINDOW", self.onWindowClosed)
        self.root.bind('<<ListenerExit>>', self.onListenerExit)
        self.root.mainloop()

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
            if isinstance(picture, str) and picture == self.EXIT_CODE:
                logger('not an image - exit code')
                self.root.event_generate('<<ListenerExit>>')
                #self.root.destroy()
                return
            try:
                logger('must be an image')
                self.root.title(picture.getTitle())
                image = ImageTk.PhotoImage(picture.getImage())
                self.canvas.config(width=picture.getWidth(),
                                   height=picture.getHeight())        
                if imageID is None:
                    logger('showing a new image')
                    imageID = self.canvas.create_image(0, 0, anchor=tk.NW,
                                                       image=image)
                else:
                    logger('repainting exisiting image')
                    self.canvas.itemconfig(imageID, image=image)
            except AttributeError:
                logger('Attribute Error encountered')
                #pass

    def stopBackground(self, event, thread):
        """Handle Python exiting"""
        event.set()
        self.imageQueue.put(self.EXIT_CODE)
        logger('stopBackground: Exit')
        # exit()
    
    def onWindowClosed(self):
        """Handle GUI window close event"""
        logger('windowClosed')
        self.imageQueue.put(self.EXIT_CODE)  # Signal stop to showImage thread
        # self.showThread.join()
        #self.listenThread.join()
        #self.listenThread._stop()
        # exit()
    
    def onListenerExit(self, *args):
        """Handle request from listener to exit process"""
        self.root.quit()
        exit()
