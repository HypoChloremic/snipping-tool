import tkinter as tk
import numpy as np
import cv2
from PIL import ImageGrab
from PyQt5 import QtWidgets, QtCore, QtGui
import SnippingMenu
from PyQt5.QtCore import Qt
import pyscreenshot


class SnippingWidget(QtWidgets.QWidget):
    num_snip = 0
    is_snipping = False
    background = True # unclear what this is

    def __init__(self, parent=None, mainclass=None):
        super(SnippingWidget, self).__init__()
        self.parent = parent
        self.mainclass = mainclass
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        print(f"screen width: {screen_width}")
        print(f"screen height: {screen_height}")
        self.setGeometry(0, 0, screen_width, screen_height)
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()

    def start(self):
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # for some reason, when this is turned false when 
        # the start method is called. 
        SnippingWidget.background = False 
        SnippingWidget.is_snipping = True
        # this sets the window opacity to 0.3
        # note that the setWindowOpacity method is inherited 
        # QTwidgets.QWidget
        self.setWindowOpacity(0.3)

        # Seems that this method is required to 
        # use cursor input. 
        # This will seemingly override the main windows cursor.
        # UPDATE: I think this is more important than we first considered
        # that this allows the app to pick up cursor information
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        print('Capture the screen...')
        print('Press q if you want to quit...')
        # self.show is a QT native method
        # thus it is inherited. 
        self.show()

    def paintEvent(self, event):
        if SnippingWidget.is_snipping:
            brush_color = (128, 128, 255, 100)
            lw = 3
            opacity = 0.3
        else:
            # reset points, so the rectangle won't show up again.
            self.begin = QtCore.QPoint()
            self.end = QtCore.QPoint()
            brush_color = (0, 0, 0, 0)
            lw = 0
            opacity = 0

        self.setWindowOpacity(opacity)
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), lw))
        qp.setBrush(QtGui.QColor(*brush_color))
        rect = QtCore.QRectF(self.begin, self.end)
        qp.drawRect(rect)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Q:
            print('Quit')
            self.close()
        event.accept()

    def mousePressEvent(self, event):
        self.begin = event.pos()
        # Linux
        self.begin.setX(self.begin.x() + 1920)
        self.end = self.begin
        print(f"mousePressEvent: {self.begin}, {self.end},  {self.begin.x()}")
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        # linux
        self.end.setX(self.end.x() + 1920)
        self.update()

    def mouseReleaseEvent(self, event):
        SnippingWidget.num_snip += 1
        SnippingWidget.is_snipping = False
        QtWidgets.QApplication.restoreOverrideCursor()
        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        self.repaint()
        QtWidgets.QApplication.processEvents()
        # ImageGrab is seemingly the important part of the application!
        # img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
        try: 
            img = pyscreenshot.grab(bbox=(x1, y1, x2, y2))
            QtWidgets.QApplication.processEvents()
            img = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)

            # add to the snips list the object that opens a window of the image
            print('inside snippingtool, running mainclass update_img')
            self.mainclass.update_img(img)
        except ValueError as e:
            print(f"Error while click: {e}")
        # SnippingMenu.Menu(img, SnippingWidget.num_snip, (x1, y1, x2, y2))