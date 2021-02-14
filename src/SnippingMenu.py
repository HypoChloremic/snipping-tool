import sys, random, re, string
from functools import wraps
from os.path import basename
from PyQt5.QtCore import QPoint, Qt, QRect
from PyQt5.QtWidgets import QAction, QMainWindow, QApplication, QPushButton, QMenu, QFileDialog, QInputDialog, QLineEdit
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
# from PyQt5.QtWidgets import QFileDialog 
import SnippingTool

# for clipboard stuff
import pyperclip

def stdout_log(func):
    '''stdout_log() will print statements
    upon entering and exiting a function, outputting the names of the 
    functions that are being called'''
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f'[{func.__name__}] Entering')
        result = func(*args, **kwargs)
        print(f'[{func.__name__}] Exiting')
        return result
    return wrapper

class Menu(QMainWindow):
    COLORS = ['Red', 'Black', 'Blue', 'Green', 'Yellow']
    SIZES = [1, 3, 5, 7, 9, 11]
    default_title = "Snipping Tool"

    # numpy_image is the desired image we want to display given as a numpy array.
    def __init__(
            self, 
            # this is passed to the class from the SnippingTool class
            numpy_image=None, 
            snip_number=None, 
            start_position=(300, 300, 350, 250) # also modded by snippingtool
            ):
        super().__init__()

        self.drawing = False
        self.brushSize = 3
        self.brushColor = Qt.red
        self.lastPoint = QPoint()
        self.total_snips = 0
        self.title = Menu.default_title

        # Get the main folder
        self.get_main_folder()

        # New snip
        new_snip_action = QAction('New', self) # TODO: check this
        new_snip_action.setShortcut('Ctrl+N')
        new_snip_action.setStatusTip('Snip!')
        new_snip_action.triggered.connect(self.new_image_window)
        
        # Brush color
        brush_color_button = QPushButton("Brush Color")
        colorMenu = QMenu()
        for color in Menu.COLORS:
            colorMenu.addAction(color)
        brush_color_button.setMenu(colorMenu)
        colorMenu.triggered.connect(lambda action: change_brush_color(action.text()))

        # Brush Size
        brush_size_button = QPushButton("Brush Size")
        sizeMenu = QMenu()
        for size in Menu.SIZES:
            sizeMenu.addAction("{0}px".format(str(size)))
        brush_size_button.setMenu(sizeMenu)
        sizeMenu.triggered.connect(lambda action: change_brush_size(action.text()))

        ### Save
        save_action = QAction('Save', self) # a QAction object, void method. 
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save')
        # When the action is emitted by the user, 
        # e.g. when user clicks menu option, or shortcut, or when trigger() is called,
        # 
        save_action.triggered.connect(self.save_file) # passing the save_file callback

        # Exit
        exit_window = QAction('Exit', self)
        exit_window.setShortcut('Ctrl+Q')
        exit_window.setStatusTip('Exit application')
        exit_window.triggered.connect(self.close)

        self.toolbar = self.addToolBar('Exit')
        self.toolbar.addAction(new_snip_action)
        self.toolbar.addAction(save_action)
        self.toolbar.addWidget(brush_color_button)
        self.toolbar.addWidget(brush_size_button)
        self.toolbar.addAction(exit_window)

        # Calling the imported SnippingTool class
        self.snippingTool = SnippingTool.SnippingWidget(mainclass=self) # this is the new addition
        self.setGeometry(*start_position)
        self.prefix_input() # personally added

        # From the second initialization, both arguments will be valid
        if numpy_image is not None and snip_number is not None:
            self.image = self.convert_numpy_img_to_qpixmap(numpy_image)
            self.change_and_set_title("Snip #{0}".format(snip_number))
        else:
            self.image = QPixmap("background.PNG")
            self.change_and_set_title(Menu.default_title)

        self.resize(self.image.width(), self.image.height() + self.toolbar.height())
        self.show()

        def change_brush_color(new_color):
            self.brushColor = eval("Qt.{0}".format(new_color.lower()))

        def change_brush_size(new_size):
            self.brushSize = int(''.join(filter(lambda x: x.isdigit(), new_size)))

    def prefix_input(self):
        text, okPressed = QInputDialog.getText(self, "Get Prefix", "Prefix:", QLineEdit.Normal, "")
        if okPressed and text != '':
            print(text)
            self.prefix = text

    # @stdout_log
    def get_main_folder(self) -> dict:
        # main_folder = str(input('[APPLICATION]: FOLDER TO SAVE TO: '))
        self.main_folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        print('main folder: ', self.main_folder)

    # snippingTool.start() will open a new window, so if this is the first snip, 
    # close the first window.
    def new_image_window(self):
        if self.snippingTool.background:
            self.close()
        self.total_snips += 1
        self.snippingTool.start()

    # @stdout_log
    def save_file(self): # an important callback
        # file_path, name = QFileDialog.getSaveFileName(self, "Save file", self.title, "PNG Image file (*.png)")
        if self.main_folder:
            rn_str = ''.join(random.choice(string.ascii_letters + string.digits) for letter in range(10))
            self.save_path = f'{self.main_folder}/{self.prefix}_{rn_str}.png'
            self.image.save(self.save_path) # self.image stores the image we have snipped
            self.change_and_set_title(basename(self.save_path))
            print(self.title, 'Saved')
            
            print(self.save_path)
            # parsing to clipboard
            # clipb = f'![{rn_str}]({"./" + "/".join(self.save_path.split("/")[-2:])})'
            clipb = f'<img src="{"./" + "/".join(self.save_path.split("/")[-2:])}" alt="{rn_str}" style="zoom:50%;" />'
            print(f'Parsing to clipboard: {clipb}')
            pyperclip.copy(clipb)

    def change_and_set_title(self, new_title):
        self.title = new_title
        self.setWindowTitle(self.title)

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = QRect(0,  self.toolbar.height(), self.image.width(), self.image.height())
        painter.drawPixmap(rect, self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.lastPoint = event.pos() - QPoint(0, self.toolbar.height())

    def mouseMoveEvent(self, event):
        if event.buttons() and Qt.LeftButton and self.drawing:
            painter = QPainter(self.image)
            painter.setPen(QPen(self.brushColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.lastPoint, event.pos() - QPoint(0, self.toolbar.height()))
            self.lastPoint = event.pos() - QPoint(0, self.toolbar.height())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button == Qt.LeftButton:
            self.drawing = False

    # TODO exit application when we exit all windows
    def closeEvent(self, event):
        event.accept()
    
    def update_img(self, img):
        print('update_img, running in snippingmenu class')
        self.image = self.convert_numpy_img_to_qpixmap(img)
        self.resize(self.image.width(), self.image.height() + self.toolbar.height())
        self.show()

    @staticmethod
    def convert_numpy_img_to_qpixmap(np_img):
        height, width, channel = np_img.shape
        bytesPerLine = 3 * width
        return QPixmap(QImage(np_img.data, width, height, bytesPerLine, QImage.Format_RGB888).rgbSwapped())


if __name__ == '__main__':
    # Contains the command-line arguments passed to the script
    # passing the sys.arguments or the command line arguments to
    # the QApplication
    app = QApplication(sys.argv)
    mainMenu = Menu()
    sys.exit(app.exec_())