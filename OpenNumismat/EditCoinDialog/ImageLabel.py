from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import OpenNumismat
from OpenNumismat.Tools import TemporaryDir
from OpenNumismat.Tools.Gui import getSaveFileName
from OpenNumismat import version


class ImageLabel(QLabel):
    MimeType = 'num/image'

    def __init__(self, parent=None):
        super().__init__(parent)

        self.name = 'photo'

        self.clear()

        self.setBackgroundRole(QPalette.Base)
        self.setSizePolicy(QSizePolicy.Ignored,
                           QSizePolicy.Ignored)
        self.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.setFocusPolicy(Qt.StrongFocus)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenu)

    def contextMenu(self, pos):
        open_ = QAction(self.tr("Open"), self)
        open_.triggered.connect(self.openImage)

        copy = QAction(self.tr("Copy"), self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        save = QAction(self.tr("Save as..."), self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        menu = QMenu()
        menu.addAction(open_)
        menu.setDefaultAction(open_)
        menu.addAction(save)
        menu.addSeparator()
        menu.addAction(copy)
        menu.exec_(self.mapToGlobal(pos))

    def openImage(self):
        fileName = self._saveTmpImage()

        executor = QDesktopServices()
        executor.openUrl(QUrl.fromLocalFile(fileName))

    def mouseDoubleClickEvent(self, _e):
        self.openImage()

    def clear(self):
        self._data = None

        self.image = QImage()
        pixmap = QPixmap.fromImage(self.image)
        self.setPixmap(pixmap)

    def resizeEvent(self, _e):
        self._showImage()

    def showEvent(self, _e):
        self._showImage()

    def loadFromData(self, data):
        if not data:
            data = None

        self._data = data

        image = QImage()
        result = image.loadFromData(data)
        if result:
            self._setImage(image)

        return result

    def _setImage(self, image):
        self.image = image
        self._showImage()

    def _showImage(self):
        if self.image.isNull():
            return

        # Label not shown => can't get size for resizing image
        if not self.isVisible():
            return

        if self.image.width() > self.width() or \
                                        self.image.height() > self.height():
            scaledImage = self.image.scaled(self.size(),
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            scaledImage = self.image

        pixmap = QPixmap.fromImage(scaledImage)
        self.setPixmap(pixmap)

    def _saveTmpImage(self):
        tmpDir = QDir(TemporaryDir.path())
        file = QTemporaryFile(tmpDir.absoluteFilePath("img_XXXXXX.jpg"))
        file.setAutoRemove(False)
        file.open()

        fileName = QFileInfo(file).absoluteFilePath()
        self.image.save(fileName)

        return fileName

    def saveImage(self):
        filters = (self.tr("Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif)"),
                   self.tr("All files (*.*)"))
        # TODO: Set default name to coin title + field name
        fileName, _selectedFilter = getSaveFileName(
            self, 'save_image', self.name, OpenNumismat.IMAGE_PATH, filters)
        if fileName:
            self.image.save(fileName)

    def copyImage(self):
        if not self.image.isNull():
            mime = QMimeData()
            mime.setImageData(self.image)
            mime.setData(ImageLabel.MimeType, self._data)

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime)


class ImageEdit(ImageLabel):
    latestDir = OpenNumismat.IMAGE_PATH

    def __init__(self, name, label, parent=None):
        super().__init__(parent)

        self.name = name or 'photo'
        self.label = label
        self.title = None

        self.label.mouseDoubleClickEvent = self.renameImageEvent

        self.setFrameStyle(QFrame.Panel | QFrame.Plain)

        text = QApplication.translate('ImageEdit', "Exchange with")
        self.exchangeMenu = QMenu(text, self)

        self.changed = False

    def setTitle(self, title):
        self.title = title
        self.label.setText(title)

    def contextMenu(self, pos):
        style = QApplication.style()

        icon = style.standardIcon(QStyle.SP_DirOpenIcon)
        text = QApplication.translate('ImageEdit', "Load...")
        load = QAction(icon, text, self)
        load.triggered.connect(self.loadImage)

        text = QApplication.translate('ImageEdit', "Paste")
        paste = QAction(text, self)
        paste.triggered.connect(self.pasteImage)

        text = QApplication.translate('ImageEdit', "Copy")
        copy = QAction(text, self)
        copy.triggered.connect(self.copyImage)
        copy.setDisabled(self.image.isNull())

        icon = style.standardIcon(QStyle.SP_TrashIcon)
        text = QApplication.translate('ImageEdit', "Delete")
        delete = QAction(icon, text, self)
        delete.triggered.connect(self.deleteImage)
        delete.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Save as...")
        save = QAction(text, self)
        save.triggered.connect(self.saveImage)
        save.setDisabled(self.image.isNull())

        text = QApplication.translate('ImageEdit', "Rename...")
        rename = QAction(text, self)
        rename.triggered.connect(self.renameImage)

        menu = QMenu()
        menu.addAction(load)
        menu.setDefaultAction(load)
        menu.addAction(save)
        menu.addSeparator()
        menu.addAction(rename)
        menu.addMenu(self.exchangeMenu)
        menu.addSeparator()
        menu.addAction(copy)
        menu.addAction(paste)
        menu.addAction(delete)
        menu.exec_(self.mapToGlobal(pos))

    def mouseDoubleClickEvent(self, _e):
        if self.image.isNull():
            self.loadImage()
        else:
            super().mouseDoubleClickEvent(_e)

    def loadImage(self):
        caption = QApplication.translate('ImageEdit', "Open File")
        filter_ = QApplication.translate('ImageEdit',
                            "Images (*.jpg *.jpeg *.bmp *.png *.tiff *.gif);;"
                            "All files (*.*)")
        fileName, _selectedFilter = QFileDialog.getOpenFileName(self,
                caption, ImageEdit.latestDir, filter_)
        if fileName:
            file_info = QFileInfo(fileName)
            ImageEdit.latestDir = file_info.absolutePath()

            self.loadFromFile(fileName)

    def deleteImage(self):
        self.clear()

    def copyImage(self):
        if not self.image.isNull():
            mime = QMimeData()
            mime.setImageData(self.image)
            if not self.changed:
                mime.setData(ImageLabel.MimeType, self._data)

            clipboard = QApplication.clipboard()
            clipboard.setMimeData(mime)

    def pasteImage(self):
        mime = QApplication.clipboard().mimeData()
        if mime.hasFormat(ImageLabel.MimeType):
            self.loadFromData(mime.data(ImageLabel.MimeType))
        elif mime.hasImage():
            self._setNewImage(mime.imageData())
        elif mime.hasUrls():
            url = mime.urls()[0]
            self.loadFromFile(url.toLocalFile())
        elif mime.hasText():
            # Load image by URL
            self.loadFromUrl(mime.text())

    def clear(self):
        super().clear()
        self.changed = False

        text = QApplication.translate('ImageEdit',
                        "No image available\n(right-click to add an image)")
        self.setText(text)

    def loadFromFile(self, fileName):
        image = QImage()
        result = image.load(fileName)
        if result:
            self._setNewImage(image)

        return result

    def loadFromUrl(self, url):
        result = False

        import urllib.request
        try:
            # Wikipedia require any header
            req = urllib.request.Request(url,
                                    headers={'User-Agent': version.AppName})
            data = urllib.request.urlopen(req).read()
            image = QImage()
            result = image.loadFromData(data)
            if result:
                self._setNewImage(image)
        except:
            pass

        return result

    def data(self):
        if self.changed:
            return self.image
        return self._data

    def exchangeImageEvent(self):
        image = self.sender().data()

        original_data = self.data()

        if isinstance(image.data(), QImage):
            self._setImage(image.data())
            self.changed = True
        else:
            if image.data():
                self.loadFromData(image.data())
                self.changed = False
            else:
                self.clear()

        if isinstance(original_data, QImage):
            image._setImage(original_data)
            image.changed = True
        else:
            if original_data:
                image.loadFromData(original_data)
                image.changed = False
            else:
                image.clear()

    def connectExchangeAct(self, image, title):
        act = QAction(title, self)
        act.setData(image)
        act.triggered.connect(self.exchangeImageEvent)
        self.exchangeMenu.addAction(act)

    def renameImageEvent(self, _event):
        self.renameImage()

    def renameImage(self):
        title, ok = QInputDialog.getText(self, self.tr("Rename image"),
                self.tr("Enter new image name"), text=self.title,
                flags=(Qt.WindowCloseButtonHint | Qt.WindowSystemMenuHint))
        if ok:
            self.title = title
            self.label.setText(title)

    def _setNewImage(self, image):
        # Fill transparent color if present
        fixedImage = QImage(image.size(), QImage.Format_RGB32)
        fixedImage.fill(QColor(Qt.white).rgb())
        painter = QPainter(fixedImage)
        painter.drawImage(0, 0, image)
        painter.end()

        self._setImage(fixedImage)
        self.changed = True


class EdgeImageEdit(ImageEdit):
    def _setImage(self, image):
        if not image.isNull():
            if image.width() < image.height():
                matrix = QTransform()
                matrix.rotate(90)
                image = image.transformed(matrix, Qt.SmoothTransformation)

        super()._setImage(image)
