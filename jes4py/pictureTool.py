#!/usr/bin/env python3

"""
pictureTool.py - script program to implement the "explore" functionality
                 in JES for the JES4py package

Written: 2020-07-24 Gahngnin Kim <gahngnin.kim@gordon.edu>
Modified: 2020-08-08 Jonathan Senning <jonathan.senning@gordon.edu>
- Completed work for crosshair cursor to work on Mac, Windows, and Linux (GTK)
Modified: 2024-08-26 Benjamin Pajunen <benjamin.pajunen@gordon.edu>
- Ported GUI from wxPython to Tkinter, added multiprocessing.Process wrapper

The "explore()" function in JES will open a new window and display the image
imported from the given file path. The window provides an interactive picture
tool for the user. It allows users to zoom in and out of the image and pick
a pixel to examine its RGB values with the color preview. When a pixel is
selected from the image, a crosshair will appear in that selected position.
Unlike, "show()" function, it cannot be repainted with "repaint()" method.

The JES4py's implementation of "explore()" function provides a nearly identical
experience with an improvement compared to JES's. Display and image size
detection code is added to ensure that the window size doesn't go beyond the
display resolution even if the image is larger. The image panel will set
scrollbars when a high-resolution image is imported will set the scrollbar to
fit the image in the window. The program can also work standalone.

This program was first developed during the Gordon College Computer Science
Summer 2020 Practicum as a part of the JES4py project, under the guidance of
Dr. Jonathan Senning.

Summer 2020 JES4py Team: Dr. Jonathan Senning
                         Nick Noormand
                         Gahngnin Kim

"""

import os, sys
from multiprocessing import Process
from threading import *
import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk, ImageOps
from jes4py import Config


class ExploreProcess(Process):
    def __init__(self, pipe, imagePath, imageTitle=None):
        Process.__init__(self)
        
        # Connection to main process
        self.pipe = pipe

        # Location from which to load image
        self.imagePath = imagePath
        
        # If the image has a title, use it for the GUI window.
        # Otherwise give it the generic title 'Picture'.
        self.imageTitle = imageTitle if imageTitle else 'Picture'
        
        # This causes run() to be invoked in a separate process
        self.start()
    
    def run(self):
        """Run the app in a subprocess"""
        # Create the GUI instance, which will start upon initialization
        self.app = ExploreApp(self.imagePath, self.imageTitle)
        
        # If we've gotten this far, the app has ended
        del self.app

        # Indicate to main process that this process is about to quit
        self.pipe.send(ExploreApp.EXIT_CODE)
        
        # The main process should reply with an exit instruction.
        # This is done primarily so that listener threads for show()
        # subprocesses (see show.py) can be stopped easily.
        # No listener here, so just recieve the message and exit.
        self.pipe.recv()
        exit()
        
    def exit(self):
        """Exit the subprocess"""
        self.terminate()
        
        # Handshake with the main process 
        # to confirm exit and close the pipe
        self.pipe.send(ExploreApp.EXIT_CODE)
        self.pipe.recv()

class ExploreApp():
    
    EXIT_CODE = bytes([0])
    CURSOR_RADIUS = 5
    CURSOR_TAG = 'cursor'
    MIN_WINDOW_WIDTH = 350
    MIN_WINDOW_HEIGHT = 0
    cursorX = 0
    cursorY = 0
    xInputVar = None
    yInputVar = None

    def __init__(self, imagePath, imageTitle):
        self.imagePath = imagePath
        self.imageTitle = imageTitle
        
        # Create the window
        self.root = tk.Tk()
        
        # Initialize window components
        self.initRoot()
        self.initContentFrame()
        self.initInfoBar()
        self.initImageCanvas()
        self.initZoomMenu()
        
        # Enter the GUI event loop
        self.root.mainloop()
        
    def initRoot(self):
        """Set configuration options for root window"""
        # Set window title to image title
        self.root.title(self.imageTitle)

        # Set defined minimum window size
        self.root.minsize(self.MIN_WINDOW_WIDTH, self.MIN_WINDOW_HEIGHT)

        # Calculate and apply maximum size
        # to ensure window fits entirely on screen
        maxWidth = int(self.root.winfo_screenwidth() * 0.95)
        maxHeight = int(self.root.winfo_screenheight() * 0.85)
        self.root.maxsize(maxWidth, maxHeight)

        # Root window can expand/shrink
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

    def initContentFrame(self):
        """Set up frame to hold all GUI elements"""
        self.frame = ttk.Frame(self.root)

        # Configure grid layout manager
        # See https://tkdocs.com/tutorial/grid.html
        self.frame.grid(sticky=tk.NSEW)
        # Frame can expand/shrink horizontally
        self.frame.columnconfigure(0, weight=1)
        # Ensure top bar has sufficient height and doesn't expand vertically
        self.frame.rowconfigure(0, minsize=66, weight=0)
        # Image panel has variable height
        self.frame.rowconfigure(1, weight=1)

    def initInfoBar(self):
        """Create GUI bar at top of window"""
        # Define fonts
        self.smallFont = font.Font(font='TkDefaultFont').copy()
        self.smallFont.config(size=10, weight=font.NORMAL)
        self.largeFont = font.Font(font='TkDefaultFont').copy()
        self.largeFont.config(size=12, weight=font.NORMAL)

        # main bar at top
        self.infoBar = ttk.Frame(self.frame)
        
        # navigation row
        self.navBar = ttk.Frame(self.infoBar)

        # x, y labels for input fields
        self.xText = ttk.Label(self.navBar, text='X:', font=self.smallFont)
        self.yText = ttk.Label(self.navBar, text='Y:', font=self.smallFont)

        # Tkinter string variables for coordinate input
        self.xInputVar = tk.StringVar()
        self.xInputVar.set('0')
        self.yInputVar = tk.StringVar()
        self.yInputVar.set('0')

        # Create Tcl wrappings for entry callbacks
        # to allow specifying callback parameters
        # See https://tkdocs.com/shipman/entry-validation.html
        self.xValidateCommand = self.navBar.register(self.validateXInput)
        self.yValidateCommand = self.navBar.register(self.validateYInput)

        # x input field
        self.xInput = ttk.Entry(
             self.navBar, name='x_input',
             width=6, font=self.smallFont,
             textvariable=self.xInputVar, validate='focus',
             validatecommand=(self.xValidateCommand, '%P'))
        # y input field
        self.yInput = ttk.Entry(
             self.navBar, name='y_input',
             width=6, font=self.smallFont,
             textvariable=self.yInputVar, validate='focus',
             validatecommand=(self.yValidateCommand, '%P'))

        # Key bindings for input fields
        self.xInput.bind('<Up>', self.onXIncrement)
        self.xInput.bind('<Down>', self.onXDecrement)
        self.xInput.bind('<Return>', self.validateXInput)
        self.yInput.bind('<Up>', self.onYIncrement)
        self.yInput.bind('<Down>', self.onYDecrement)
        self.yInput.bind('<Return>', self.validateYInput)

        # Icons made by Freepik from www.flaticon.com; Modified by Gahngnin Kim
        # Rescaled by Benjamin Pajunen 20x20px -> 18x18px
        self.rightArrowImagePath = os.path.join(
            Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Right2.png')
        self.leftArrowImagePath = os.path.join(
            Config.getConfigVal('CONFIG_JES4PY_PATH'), 'images', 'Left2.png')
        self.rightArrowIcon = ImageTk.PhotoImage(file=self.rightArrowImagePath)
        self.leftArrowIcon = ImageTk.PhotoImage(file=self.leftArrowImagePath)
        
        # Coordinate adjustment buttons
        self.xIncrementButton = ttk.Button(self.navBar,
                                            image=self.rightArrowIcon,
                                              command=self.onXIncrement)
        self.xDecrementButton = ttk.Button(self.navBar,
                                            image=self.leftArrowIcon,
                                              command=self.onXDecrement)
        self.yIncrementButton = ttk.Button(self.navBar,
                                            image=self.rightArrowIcon,
                                              command=self.onYIncrement)
        self.yDecrementButton = ttk.Button(self.navBar,
                                            image=self.leftArrowIcon,
                                              command=self.onYDecrement) 

        # Display of RGB color at selected pixel:
        self.colorBar = ttk.Frame(self.infoBar, height=50)
        
        # Text for displaying RGB values
        self.rgbText = ttk.Label(
            self.colorBar, text="R: 0 G: 0 B: 0", font=self.largeFont)
        # 'Color at' label
        self.colorAtText = ttk.Label(
            self.colorBar, text="Color at location: ", font=self.largeFont)
        # Patch displaying the color
        self.colorPatch = tk.Canvas(self.colorBar,
                                     background="black", relief='sunken',
                                       borderwidth=1, width=24, height=24)
        
        # Arrange items on info bar:
        # Frame containing entire bar
        self.infoBar.grid(row=0, sticky=tk.N, padx=10)
        # First row elements (navigation)
        self.navBar.grid(row=0, sticky=tk.N, pady=3)
        self.xText.grid(row=0, column=0)
        self.xDecrementButton.grid(row=0, column=1)
        self.xInput.grid(row=0, column=2)
        self.xIncrementButton.grid(row=0, column=3, padx=(0, 5))
        self.yText.grid(row=0, column=4, padx=(5, 0))
        self.yDecrementButton.grid(row=0, column=5)
        self.yInput.grid(row=0, column=6)
        self.yIncrementButton.grid(row=0, column=7)
        # Second row elements (color)
        self.colorBar.grid(row=1, sticky=tk.N, pady=3)
        self.rgbText.grid(row=0, column=0)
        self.colorAtText.grid(row=0, column=1)
        self.colorPatch.grid(row=0, column=2)
    
    def initImageCanvas(self):
        """Setup the canvas for displaying the image"""
        # Load image
        self.image = ImageTk.PhotoImage(file=self.imagePath)
        
        # Make copy of image for scaling purposes
        self.scaledImage = ImageTk.PhotoImage(ImageTk.getimage(self.image))

        # Create frame containing image and scrollbars
        self.imageFrame = ttk.Frame(self.frame)
        self.imageFrame.grid(row=1, column=0, sticky=tk.NSEW)

        # Canvas for displaying image
        self.imageCanvas = tk.Canvas(self.imageFrame,
                                      width=self.image.width(),
                                       height=self.image.height())
        self.imageCanvas.config(
            scrollregion=(0, 0, self.image.width(), self.image.height()))
        
        # Image item on Canvas
        self.imageItemID = self.imageCanvas.create_image(0, 0,
                                                          image=self.image,
                                                           anchor=tk.NW)
        
        # Scrollbars, see https://tkdocs.com/shipman/connecting-scrollbars.html
        self.xScrollbar = ttk.Scrollbar(self.imageFrame,
                                         orient=tk.HORIZONTAL,
                                           command=self.imageCanvas.xview)
        self.yScrollbar = ttk.Scrollbar(self.imageFrame,
                                         orient=tk.VERTICAL,
                                           command=self.imageCanvas.yview)
        
        self.imageCanvas.config(xscrollcommand=self.xScrollbar.set)
        self.imageCanvas.config(yscrollcommand=self.yScrollbar.set)
        
        # Setup event handlers
        self.imageCanvas.bind('<Configure>', self.onImageResize)
        self.imageCanvas.bind('<1>', self.onImageClicked)
        self.imageCanvas.bind('<Button1-Motion>', self.onImageClicked)
        
        # Arrange items using grid layout manager
        self.imageCanvas.grid(row=0, column=0, sticky=tk.NW)
        self.xScrollbar.grid(row=1, column=0, sticky=tk.EW)
        self.yScrollbar.grid(row=0, column=1, sticky=tk.NS)
        
        # Allow image canvas to be resized
        self.imageCanvas.columnconfigure(0, weight=1)
        self.imageCanvas.rowconfigure(0, weight=1)
        self.imageFrame.columnconfigure(0, weight=1)
        self.imageFrame.rowconfigure(0, weight=1)

    def initZoomMenu(self):
        """Create menu for zooming image"""
        # See https://tkdocs.com/tutorial/menus.html
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
        
        # Apply menu to root window
        self.root.config(menu=self.menubar)

    def validateXInput(self, x=None) -> int:
        """Correct and apply x-value inputs"""
        if isinstance(x, (str, int, float)):
            # x was passed as a single value:
            pass
        else:
            # x was not passed, or a button event was passed instead:
            # Get the current x-input
            x = self.xInputVar.get()

        try:
            # Cast to int
            x = int(x)
        except ValueError:
            # Casting failed, assume input was invalid
            # Reset input to current cursor position
            self.xInputVar.set(str(self.cursorX))
            return 0
        
        # Clamp x to the interval (0, width - 1)
        x = min(max(x, 0), self.image.width() - 1)

        # Apply input
        self.cursorX = x
        self.drawCursor()
        return 1

    def validateYInput(self, y=None) -> int:
        """Correct and apply y-value inputs"""
        if isinstance(y, (str, int, float)):
            # y was passed as a single value:
            pass
        else:
            # y was not passed, or a button event was passed instead:
            # Get the current y-input
            y = self.yInputVar.get()

        try:
            # Cast to int
            y = int(y)
        except ValueError:
            # Casting failed, assume input was invalid
            # Reset input to current cursor position
            self.yInputVar.set(str(self.cursorY))
            return 0

        # Clamp y to the interval (0, height - 1)
        y = min(max(y, 0), self.image.height() - 1)
        self.cursorY = y
        self.drawCursor()
        return 1
        
    def drawCursor(self):
        """(Re-)draw the pixel crosshairs at the current cursor location"""
        
        # Calculate new position relative to the image canvas
        newX = self.cursorX * self.zoomFactorVariable.get()
        newY = self.cursorY * self.zoomFactorVariable.get()

        # Delete previous cursor lines (if any)
        self.imageCanvas.delete(self.CURSOR_TAG)

        # Draw cursor
        self.imageCanvas.create_line(newX - self.CURSOR_RADIUS, newY, newX + self.CURSOR_RADIUS + 1, newY, width=3, fill='#000000', tags=self.CURSOR_TAG)
        self.imageCanvas.create_line(newX, newY - self.CURSOR_RADIUS, newX, newY + self.CURSOR_RADIUS + 1, width=3, fill='#000000', tags=self.CURSOR_TAG)
        self.imageCanvas.create_line(newX - self.CURSOR_RADIUS + 1, newY, newX + self.CURSOR_RADIUS, newY, width=1, fill='#FFFF00', tags=self.CURSOR_TAG)
        self.imageCanvas.create_line(newX, newY - self.CURSOR_RADIUS + 1, newX, newY + self.CURSOR_RADIUS, width=1, fill='#FFFF00', tags=self.CURSOR_TAG)

        # Ensure input fields reflect current cursor position
        self.xInputVar.set(self.cursorX)
        self.yInputVar.set(self.cursorY)
        
        # Update the color patch display
        self.updateColor()
    
    def updateColor(self):
        """Update RGB color display for selected pixel"""
        image = ImageTk.getimage(self.image)
        
        # Get pixel channel values
        r, g, b, a = image.getpixel((self.cursorX, self.cursorY))

        # Update the text with RGB numbers
        self.rgbText.config(text=f'R: {r} G: {g} B: {b}')

        # Convert 8-bit [r, g, b] to hexadecimal format '#RRGGBB'
        # as expected by the color patch component
        hexColor = f'#{bytes([r, g, b]).hex().upper()}'
        
        # Update color patch
        self.colorPatch.config(background=hexColor)
 
# ===========================================================================
# Event handlers
# ===========================================================================
 
    def onImageClicked(self, event):
        """Move pixel cursor on mouse click"""
        newX = int(self.imageCanvas.canvasx(event.x, gridspacing=1) /
                    self.zoomFactorVariable.get())
        newY = int(self.imageCanvas.canvasy(event.y, gridspacing=1) /
                    self.zoomFactorVariable.get())

        self.validateXInput(str(newX))
        self.validateYInput(str(newY))
    
    def onXIncrement(self, *args):
        """Add 1 to the cursor's x-position"""
        newX = self.cursorX + 1
        self.validateXInput(str(newX))
        
    def onYIncrement(self, *args):
        """Add 1 to the cursor's y-position"""
        newY = self.cursorY + 1
        self.validateYInput(str(newY))

    def onXDecrement(self, *args):
        """Subtract 1 from the cursor's x-position"""
        newX = self.cursorX - 1
        self.validateXInput(str(newX))

    def onYDecrement(self, *args):
        """Subtract 1 from the cursor's y-position"""
        newY = self.cursorY - 1
        self.validateYInput(str(newY))
        
    def onImageResize(self, event):
        """Show/hide image scrollbars as necessary"""
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
    
        
    def onZoom(self, *args):
        """Handle image zooming"""
        scaleFactor = self.zoomFactorVariable.get()
        
        if scaleFactor != 1.0:
            self.scaledImage = ImageTk.getimage(self.image)
            self.scaledImage = ImageOps.scale(image=self.scaledImage,
                                               factor=scaleFactor)
            self.scaledImage = ImageTk.PhotoImage(self.scaledImage)
        else:
            self.scaledImage = self.image

        self.imageCanvas.itemconfig(self.imageItemID, image=self.scaledImage)
        self.imageCanvas.config(
            width=self.scaledImage.width(), height=self.scaledImage.height(),
            scrollregion=(0, 0, self.scaledImage.width(), self.scaledImage.height()))
        
        self.drawCursor()

# ===========================================================================
# Main program
# ===========================================================================

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