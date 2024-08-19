#!/usr/bin/env python3

import os, sys
from multiprocessing import Process
from threading import *
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageOps

# Method from https://tkdocs.com/tutorial/grid.html

'''
class ExploreProcess(Process)
    __init__

    run

    exit

    listen
'''
        
'''
class Cursor
    __init__
        initialize
        create bitmaps for cursor

    drawCursor
        position cursor
        save image under cursor
        draw cursor bitmap

    undrawPreviousCursor
        reset image under last cursor position

    drawCrosshairs
        display cursor

    clearBackupBitmap
        clear bitmap buffer
'''

class ExploreApp():
    def __init__(self, imagePath, imageTitle, pipe=None) -> None:
        self.pipe = pipe
        self.imagePath = imagePath
        self.imageTitle = imageTitle

        self.root = tk.Tk()

        self.initContentFrame()
        self.initInfoBar()
        self.initImageCanvas()

        self.root.mainloop()
        
    def loadImage(self):
        self.image = ImageTk.PhotoImage(file=self.imagePath)

    def initContentFrame(self):
        self.frame = ttk.Frame(self.root)
        self.frame.grid(sticky=tk.NSEW)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, minsize=0, weight=1)
        self.frame.rowconfigure(0, minsize=66, weight=0)
        self.frame.rowconfigure(1, weight=1)

    def initInfoBar(self):
        # define fonts
        self.smallFont = font.Font(font='TkDefaultFont').copy()
        self.smallFont.config(size=10, weight=font.NORMAL)

        self.largeFont = font.Font(font='TkDefaultFont').copy()
        self.largeFont.config(size=12, weight=font.NORMAL)

        self.iconFont = font.Font(font='TkIconFont').copy()
        self.iconFont.config(size=12, weight=font.BOLD)

        # main bar at top
        self.infoBar = ttk.Frame(self.frame)
        
        # navigation
        self.navBar = ttk.Frame(self.infoBar)

        # x text
        self.xText = ttk.Label(self.navBar, text='X:', font=self.smallFont)
        # y: text
        self.yText = ttk.Label(self.navBar, text='Y:', font=self.smallFont)

        # x input field
        self.xInput = ttk.Entry(self.navBar, width=6, font=self.smallFont)
        # y input field
        self.yInput = ttk.Entry(self.navBar, width=6, font=self.smallFont)


        # Icons made by Freepik from www.flaticon.com; Modified by Gahngnin Kim
        self.rightArrowImagePath = os.path.join(sys.path[0], 'images', 'Right2.png')
        self.leftArrowImagePath = os.path.join(sys.path[0], 'images', 'Left2.png')

        self.rightArrowIcon = ImageTk.PhotoImage(file=self.rightArrowImagePath)
        self.leftArrowIcon = ImageTk.PhotoImage(file=self.leftArrowImagePath)
        
        # x/y increment/decrement
        self.xIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon)
        self.xDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon)
        self.yIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon)
        self.yDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon) 

        # color display
        self.colorBar = ttk.Frame(self.infoBar, height=50)
        # rgb text
        self.rgbText = ttk.Label(self.colorBar, text="R: 0 G: 0 B: 0", font=self.largeFont)
        # color at location text
        self.colorAtText = ttk.Label(self.colorBar, text="Color at location: ", font=self.largeFont)
        # color patch
        self.colorPatch = tk.Canvas(self.colorBar, background="black", width=24, height=24)
        
        # Arrange items on info bar
        self.infoBar.grid(row=0, sticky=tk.N, padx=10)
        self.navBar.grid(row=0, sticky=tk.N, pady=3)
        
        self.xText.grid(row=0, column=0)
        self.xDecrementButton.grid(row=0, column=1)
        self.xInput.grid(row=0, column=2)
        self.xIncrementButton.grid(row=0, column=3, padx=(0, 5))
        # self.xIncrementButton.grid()
        
        self.yText.grid(row=0, column=4, padx=(5, 0))
        self.yDecrementButton.grid(row=0, column=5)
        self.yInput.grid(row=0, column=6)
        self.yIncrementButton.grid(row=0, column=7)
        
        self.colorBar.grid(row=1, sticky=tk.N, pady=3)
        self.rgbText.grid(row=0, column=0)
        self.colorAtText.grid(row=0, column=1)
        self.colorPatch.grid(row=0, column=2)

    def initImageCanvas(self):
        self.image = ImageTk.PhotoImage(file=self.imagePath)

        # Containing frame
        self.imageFrame = ttk.Frame(self.frame)
        self.imageFrame.grid(row=1, column=0, sticky=tk.NSEW)

        # canvas for displaying image
        self.imageCanvas = tk.Canvas(self.imageFrame, width=self.image.width(), height=self.image.height())
        self.imageCanvas.config(scrollregion=(0, 0, self.image.width(), self.image.height()))
        
        self.imageCanvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        
        # self.imageCanvas.grid(row=1, sticky=tk.NW)
        
        
        # scrollbars on sides, see https://tkdocs.com/shipman/connecting-scrollbars.html
        self.xScrollbar = ttk.Scrollbar(self.imageFrame, orient=tk.HORIZONTAL, command=self.imageCanvas.xview)
        self.yScrollbar = ttk.Scrollbar(self.imageFrame, orient=tk.VERTICAL, command=self.imageCanvas.yview)
        
        self.imageCanvas.config(xscrollcommand=self.xScrollbar.set)
        self.imageCanvas.config(yscrollcommand=self.yScrollbar.set)

        self.imageCanvas.grid(row=0, column=0, sticky=tk.NW)
        
        self.xScrollbar.grid(row=1, column=0, sticky=tk.EW)
        self.yScrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        self.imageCanvas.columnconfigure(0, weight=1)
        self.imageCanvas.rowconfigure(0, weight=1)
        self.imageFrame.columnconfigure(0, weight=1)
        self.imageFrame.rowconfigure(0, weight=1)
    
    def initZoomMenu(self):
        # zoom menu item
        # menu entries
        pass

'''class MainWindow

    __init__
        load image
        init ui

    InitUI
        size window to fit within display
        call setup functions

    setupZoomMenu
        create menu for zoom setting
    
    setupColorInfoDisplay
        create top navigation display with color info

    setupImageDisplay
        create panel for showing image

    clipOnBoundary
        clamp x and y to image bounds

    updateColorInfo
        update bitmap representing current pixel under cursor

    updateView
        apply zoom, display image

    drawCrosshairs
        show pixel cursor
    
    onFocus
        update image panel focus

    onZoom
        set zoom level

    ImageCtrl_OnNavBtn
        handle pixel inc/decrement

    ImageCtrl_OnEnter
        apply assigned x,y from text fields

    ImageCtrl_OnMouseClick
        select pixel on mouse click
'''

'''
main
    interpret commands, run app
'''

def main(argv):

    usage = "usage: {} file [title]".format(argv[0])
    # Get image file name and optional image title from command line
    if len(argv) == 2:
        filename = title = argv[1]
    elif len(argv) == 3:
        filename = argv[1]
        title = argv[2]
    else:
        print(usage)
        exit(1)

    if not os.path.isfile(filename):
        print("{} does not exist or is not a file".format(filename))
        print(usage)
        exit(1)

    app = ExploreApp(imagePath=filename, imageTitle=title)
    

if __name__ == '__main__':
    main(sys.argv)