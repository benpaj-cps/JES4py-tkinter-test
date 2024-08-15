#!/usr/bin/env python3

import sys, time, atexit
import tkinter as tk
from PIL import ImageTk
from multiprocessing import Process, Pipe
from queue import Empty, Full
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
        self.app = ShowApp(self.pipe)
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
        self.root = tk.Tk()
        self.pipe = pipe
        stopEvent = Event()
        self.showThread = Thread(target=self.showImages, args=(stopEvent,), daemon=True)
        self.showThread.start()
        # atexit.register(self.stopBackground, stopEvent, self.showThread)
        self.root.protocol("WM_DELETE_WINDOW", self.onWindowClosed)
        self.root.bind('<<ListenerExit>>', self.onListenerExit)
        self.root.mainloop()
        # del self.root
        # exit()
        # self.showThread.join()

    def showImages(self, event):
        logger('Show thread has started')
        self.canvas = tk.Canvas(self.root)
        self.canvas.pack()
        imageID = None
        while not event.is_set():
            logger('Getting potential image...')
            try:
                picture = self.pipe.recv()
            except EOFError | OSError:
                self.root.event_generate('<<ListenerExit>>', when='head')
                logger(f"showImages (thread {self.showThread.ident}): at end of function")
                return
            logger('Possible image found on queue...')
            logger(f'  Type: {type(picture)}')
            logger(f'  Value: {picture}')
            if isinstance(picture, str) and picture == self.EXIT_CODE:
                logger('not an image - exit code')
                self.root.event_generate('<<ListenerExit>>', when='head')
                
                # while self.pipe.poll() == True:
                    # _ = self.pipe.recv()
                # self.pipe.close()
                # self.root.event_generate('<<ListenerExit>>')
                logger(f"showImages (thread {self.showThread.ident}): at end of function")
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
                pass
        # return None
        # exit()

    def __notifyExit(self):
        """Safely stop communication with main process
        """
        
        # Tell main process that this subprocess is unusable
        self.pipe.send(self.NOTIFY_EXIT)

        # Safety interval, to handle the edge case of the main process
        # not seeing the above message in time to stop sending images
        time.sleep(0.001)

        # If the main process tried to send anything, it would block
        # until the message was consumed (by this subprocess).
        # while self.pipe.poll():
            # _ = self.pipe.recv()   
        
        self.pipe.close()

    def stopBackground(self, event, thread):
        """Handle Python exiting"""
        logger(f"stopBackground: threading.enumerate(): {enumerate()}")
        logger(f'stopBackground: threading.current_thread: {current_thread()}')
        self.showThread.join(timeout=1)
        
        if self.showThread.is_alive():
            raise RuntimeError(f"Listener thread for show() failed to quit")
        elif self.showThread.is_alive() == False:
            logger(f'stopBackground: Listener thread for show ({self.showThread}) has stopped')
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
        del self.showThread
        logger(f"onListenerExit: 2nd threading.enumerate(): {enumerate()}")

        # if self.showThread.is_alive():
        #     self.showThread.join(timeout=1)
        
        # if self.showThread.is_alive():
        #     raise RuntimeError(f"Listener thread for show() failed to quit")
        # elif self.showThread.is_alive() == False:
        #     logger(f'stopBackground: Listener thread for show ({self.showThread}) has stopped')
        # exit()
