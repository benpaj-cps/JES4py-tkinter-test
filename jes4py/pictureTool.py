#!/usr/bin/env python3

import os, sys
from multiprocessing import Process
from threading import *
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageOps
from jes4py import Config

# Method from https://tkdocs.com/tutorial/grid.html

class ExploreProcess(Process):
    def __init__(self, pipe, imagePath, imageTitle=None):
        Process.__init__(self)
        self.pipe = pipe
        self.imagePath = imagePath
        self.imageTitle = imageTitle if imageTitle else 'Picture'
        self.app = None
        self.start()
    
    def run(self):
        self.app = ExploreApp(self.imagePath, self.imageTitle)
        
        del self.app

        self.pipe.send(ExploreApp.EXIT_CODE)
        self.pipe.recv()
        
        exit()
        
    def exit(self):
        self.terminate()
        self.pipe.send(ExploreApp.EXIT_CODE)
        self.pipe.recv()

class ExploreApp():
    EXIT_CODE = bytes([0])
    CURSOR_RADIUS = 7

    def __init__(self, imagePath, imageTitle):
        self.imagePath = imagePath
        self.imageTitle = imageTitle
        self.root = tk.Tk()
        self.root.bind('<<Quit>>', self.doQuit)
        
        self.cursorX = 0
        self.cursorY = 0

        self.xInputVar = tk.StringVar()
        self.xInputVar.set('0')
        self.yInputVar = tk.StringVar()
        self.yInputVar.set('0')

        self.initContentFrame()
        self.initInfoBar()
        self.initImageCanvas()
        self.initCursor()
        
        self.initZoomMenu()
        
        self.root.mainloop()
    
    def requestQuit(self):
        self.root.event_generate('<<Quit>>', when='head')
        
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

        self.xValidateCommand = self.navBar.register(self.validateXInput)
        self.yValidateCommand = self.navBar.register(self.validateYInput)

        # x input field
        self.xInput = ttk.Entry(
             self.navBar, name='x_input',
             width=6, font=self.smallFont,
             textvariable=self.xInputVar, validate='focus',
             validatecommand=(self.xValidateCommand, '%P'))
        # x input field
        self.yInput = ttk.Entry(
             self.navBar, name='y_input',
             width=6, font=self.smallFont,
             textvariable=self.yInputVar, validate='focus',
             validatecommand=(self.yValidateCommand, '%P'))

        self.xInput.bind('<uparrow>', self.onXIncrement)
        self.xInput.bind('<downarrow>', self.onXDecrement)
        self.xInput.bind('<Return>', self.validateXInput)

        self.yInput.bind('<uparrow>', self.onYIncrement)
        self.yInput.bind('<downarrow>', self.onYDecrement)
        self.yInput.bind('<Return>', self.validateYInput)

        # Icons made by Freepik from www.flaticon.com; Modified by Gahngnin Kim
        self.rightArrowImagePath = os.path.join(Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Right2.png')
        self.leftArrowImagePath = os.path.join(Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Left2.png')

        self.rightArrowIcon = ImageTk.PhotoImage(file=self.rightArrowImagePath)
        self.leftArrowIcon = ImageTk.PhotoImage(file=self.leftArrowImagePath)
        
        # x/y increment/decrement
        self.xIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon, command=self.onXIncrement)
        self.xDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon, command=self.onXDecrement)
        self.yIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon, command=self.onYIncrement)
        self.yDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon, command=self.onYDecrement) 

        # color display
        self.colorBar = ttk.Frame(self.infoBar, height=50)
        # rgb text
        self.rgbText = ttk.Label(self.colorBar, text="R: 0 G: 0 B: 0", font=self.largeFont)
        # color at location text
        self.colorAtText = ttk.Label(self.colorBar, text="Color at location: ", font=self.largeFont)

        # Icons made by Freepik from www.flaticon.com; Modified by Gahngnin Kim
        self.rightArrowImagePath = os.path.join(Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Right2.png')
        self.leftArrowImagePath = os.path.join(Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Left2.png')

        self.rightArrowIcon = ImageTk.PhotoImage(file=self.rightArrowImagePath)
        self.leftArrowIcon = ImageTk.PhotoImage(file=self.leftArrowImagePath)
        
        # x/y increment/decrement
        self.xIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon, command=self.onXIncrement)
        self.xDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon, command=self.onXDecrement)
        self.yIncrementButton = ttk.Button(self.navBar, image=self.rightArrowIcon, command=self.onYIncrement)
        self.yDecrementButton = ttk.Button(self.navBar, image=self.leftArrowIcon, command=self.onYDecrement) 

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
    
    def validateCoords(self, x, y):
        xIsValid = x >= 0 and x < self.image.width()
        yIsValid = y >= 0 and y < self.image.height()
        
        return xIsValid and yIsValid

    def validateXInput(self, x=None) -> int:
        x = x if isinstance(x, str) else self.xInputVar.get()

        if not x.isdigit():
            self.xInputVar.set(str(self.cursorX))
            return 0
        
        x = int(x)
        if x >= 0 and x < self.image.width():
            self.cursorX = x
            self.updateCursor()
            return 1
        else:
            self.xInputVar.set(str(self.cursorX))
            return 0
    
    def validateYInput(self, y=None) -> int:
        y = y if isinstance(y, str) else self.yInputVar.get()

        if not y.isdigit():
            self.yInputVar.set(str(self.cursorY))
            return 0
        
        y = int(y)
        if y >= 0 and y < self.image.height():
            self.cursorY = y
            self.updateCursor()
            return 1
        else:
            self.yInputVar.set(str(self.cursorY))
            return 0
        

    def initImageCanvas(self):
        self.image = ImageTk.PhotoImage(file=self.imagePath)
        
        # Copy of image for scaling purposes
        self.scaledImage = ImageTk.PhotoImage(ImageTk.getimage(self.image))

        # Containing frame
        self.imageFrame = ttk.Frame(self.frame)
        self.imageFrame.grid(row=1, column=0, sticky=tk.NSEW)

        # canvas for displaying image
        self.imageCanvas = tk.Canvas(self.imageFrame, width=self.image.width(), height=self.image.height())
        self.imageCanvas.config(scrollregion=(0, 0, self.image.width(), self.image.height()))
        
        self.imageItemID = self.imageCanvas.create_image(0, 0, image=self.image, anchor=tk.NW)
        
        # self.imageCanvas.grid(row=1, sticky=tk.NW)
        
        # scrollbars on sides, see https://tkdocs.com/shipman/connecting-scrollbars.html
        self.xScrollbar = ttk.Scrollbar(self.imageFrame, orient=tk.HORIZONTAL, command=self.imageCanvas.xview)
        self.yScrollbar = ttk.Scrollbar(self.imageFrame, orient=tk.VERTICAL, command=self.imageCanvas.yview)
        
        self.imageCanvas.config(xscrollcommand=self.xScrollbar.set)
        self.imageCanvas.config(yscrollcommand=self.yScrollbar.set)

        self.imageCanvas.grid(row=0, column=0, sticky=tk.NW)
        
        self.xScrollbar.grid(row=1, column=0, sticky=tk.EW)
        self.yScrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        self.imageCanvas.bind('<Configure>', self.onScrollbarResize)
        # self.imageCanvas.bind('<1>', self.onImageClicked)
        self.imageCanvas.tag_bind(self.imageItemID, '<1>', self.onImageClicked)
        self.imageCanvas.tag_bind(self.imageItemID, '<Button1-Motion>', self.onImageClicked)
        
        self.imageCanvas.columnconfigure(0, weight=1)
        self.imageCanvas.rowconfigure(0, weight=1)
        self.imageFrame.columnconfigure(0, weight=1)
        self.imageFrame.rowconfigure(0, weight=1)

    def initCursor(self):
        self.cursorTag = 'cursor'
        
        # Should be odd number
        cursorRadius = 3
        
        self.cursorCenter = self.imageCanvas.create_line(cursorRadius, cursorRadius, cursorRadius, cursorRadius, width=1, fill='#FFFFFF', tags=self.cursorTag)
        self.cursorLine1 = self.imageCanvas.create_line(0, cursorRadius, cursorRadius*2 + 1, cursorRadius, width=3, fill='#000000', tags=self.cursorTag)
        self.cursorLine2 = self.imageCanvas.create_line(cursorRadius, 0, cursorRadius, cursorRadius*2 + 1, width=3, fill='#000000', tags=self.cursorTag)
        self.cursorLine3 = self.imageCanvas.create_line(1, cursorRadius, cursorRadius*2, cursorRadius, width=1, fill='#FFFF00', tags=self.cursorTag)
        self.cursorLine4 = self.imageCanvas.create_line(cursorRadius, 1, cursorRadius, cursorRadius*2, width=1, fill='#FFFF00', tags=self.cursorTag)

        self.imageCanvas.itemconfig(self.cursorTag, state='hidden')

        # self.cursorXVar.trace_add(mode='write', callback=self.updateCursor)
        # self.cursorYVar.trace_add(mode='write', callback=self.updateCursor)
 
    def resetCursor(self):
        self.imageCanvas.delete(self.cursorTag)
        self.initCursor()

    def updateCursor(self, *args):
        # self.imageCanvas.itemconfig(self.cursorTag, state='hidden')
        newX = self.cursorX * self.zoomFactorVariable.get()
        newY = self.cursorY * self.zoomFactorVariable.get()
        # print(f'Cursor at ({newX}, {newY})')

        self.imageCanvas.delete(self.cursorTag)
        self.imageCanvas.create_line(newX - self.CURSOR_RADIUS, newY, newX + self.CURSOR_RADIUS + 1, newY, width=3, fill='#000000', tags=self.cursorTag)
        self.imageCanvas.create_line(newX, newY - self.CURSOR_RADIUS, newX, newY + self.CURSOR_RADIUS + 1, width=3, fill='#000000', tags=self.cursorTag)
        self.imageCanvas.create_line(newX - self.CURSOR_RADIUS + 1, newY, newX + self.CURSOR_RADIUS, newY, width=1, fill='#FFFF00', tags=self.cursorTag)
        self.imageCanvas.create_line(newX, newY - self.CURSOR_RADIUS + 1, newX, newY + self.CURSOR_RADIUS, width=1, fill='#FFFF00', tags=self.cursorTag)

        # self.resetCursor()
        # self.imageCanvas.moveto(self.cursorTag,
                                #  int(newX),
                                #  int(newY))
        self.imageCanvas.itemconfig(self.cursorTag, state='normal')
        self.xInputVar.set(self.cursorX)
        self.yInputVar.set(self.cursorY)
        self.updateColor()
    
    def updateColor(self, *args):
        image = ImageTk.getimage(self.image)
        r, g, b, a = image.getpixel((self.cursorX, self.cursorY))
        self.rgbText.config(text=f'R: {r} G: {g} B: {b}')
        hexColor = f'#{bytes([r, g, b]).hex().upper()}'
        self.colorPatch.config(background=hexColor)
 
    def onImageClicked(self, event):
        newX = int(self.imageCanvas.canvasx(event.x, gridspacing=1) / self.zoomFactorVariable.get())
        newY = int(self.imageCanvas.canvasy(event.y, gridspacing=1) / self.zoomFactorVariable.get())

        self.validateXInput(str(newX))
        self.validateYInput(str(newY))

        # self.cursorXVar.set(str(newX))
        # self.cursorYVar.set(str(newY))
        
        # if self.validateXInput(str(newX)) and self.validateYInput(str(newY)):
        #     # self.cursorX = newX
        #     # self.cursorY = newY
            
        #     self.xInputVar.set(str(newX))
        #     self.yInputVar.set(str(newY))
    
    def onXIncrement(self, *args):
        newX = self.cursorX + 1
        self.validateXInput(str(newX))
        
    def onYIncrement(self, *args):
        newY = self.cursorY + 1
        self.validateYInput(str(newY))

    def onXDecrement(self, *args):
        newX = self.cursorX - 1
        self.validateXInput(str(newX))

    def onYDecrement(self, *args):
        newY = self.cursorY - 1
        self.validateYInput(str(newY))
        
    def onScrollbarResize(self, event):
        imageWidth = self.scaledImage.width()
        imageHeight = self.scaledImage.height()

        if event.width >= imageWidth:
            self.xScrollbar.grid_remove()
        elif event.width < imageWidth:
            self.xScrollbar.grid(row=1, column=0, sticky=tk.EW)
            
        if event.height >= imageHeight:
            self.yScrollbar.grid_remove()
        elif event.height < imageHeight:
            self.yScrollbar.grid(row=0, column=1, sticky=tk.NS)
    
    def initZoomMenu(self):
        # https://tkdocs.com/tutorial/menus.html
        # zoom menu item
        self.menubar = tk.Menu(self.root)
        self.zoomMenu = tk.Menu(self.menubar)
        self.menubar.add_cascade(menu=self.zoomMenu, label='Zoom')

        self.zoomFactorVariable = tk.DoubleVar()
        self.zoomFactorVariable.set(1.0)
        self.zoomLevels = [25, 50, 75, 100, 150, 200, 500]
        
        # menu entries
        for i in self.zoomLevels:
            self.zoomMenu.add_radiobutton(label=f'{i}%', variable=self.zoomFactorVariable, value=i/100)            

        self.zoomFactorVariable.trace_add(mode='write', callback=self.onZoom)
        
        self.root.config(menu=self.menubar)
        
    def onZoom(self, *args):
        scaleFactor = self.zoomFactorVariable.get()
        
        if scaleFactor != 1.0:
            self.scaledImage = ImageTk.getimage(self.image)
            self.scaledImage = ImageOps.scale(image=self.scaledImage, factor=scaleFactor)
            self.scaledImage = ImageTk.PhotoImage(self.scaledImage)
        else:
            self.scaledImage = self.image
        
        # self.imageCanvas.grid_remove()

        # newWidth = int(self.imageCanvas.winfo_width() * scaleFactor)
        # newHeight = int(self.imageCanvas.winfo_height() * scaleFactor)
        self.imageCanvas.itemconfig(self.imageItemID, image=self.scaledImage)
        # self.imageCanvas.scale(self.imageItemID, 0, 0, 1/scaleFactor, 1/scaleFactor)
        self.imageCanvas.config(width=self.scaledImage.width(), height=self.scaledImage.height())
        self.imageCanvas.config(scrollregion=(0, 0, self.scaledImage.width(), self.scaledImage.height()))
        
        # self.imageCanvas.grid()
        
        # self.resetCursor()
        self.updateCursor()
        
        # self.imageCanvas.config(width=newWidth, height=newHeight)
    
    def doQuit(self, *args):
        self.root.destroy()
        self.root.quit()
        del self.root


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