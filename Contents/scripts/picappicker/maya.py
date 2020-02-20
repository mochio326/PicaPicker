# # -*- coding: utf-8 -*-
from pppicker.vendor.Qt import QtCore, QtGui, QtWidgets
from pppicker.node import Node
from pppicker.view import View
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


class Window(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('picker test app')
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        self.resize(600, 800)
        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(2)
        hbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(hbox)

        scene = QtWidgets.QGraphicsScene()
        scene.setObjectName('Scene')
        scene.setSceneRect(0, 0, 1000, 1000)
        self.view = View(scene, self)

        hbox.addWidget(self.view)

    def _context_menu(self, event):
        _menu = QtWidgets.QMenu()
        _menu.addAction('Add partition', self.hoge)
        _menu.addAction('Edit', self.hoge)

        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)


    def hoge(self):
        pass



'''
============================================================
---   SHOW WINDOW
============================================================
'''


def main(parent=None):
    from sys import exit, argv
    app = QtWidgets.QApplication(argv)
    nodeWindow = Window(parent)
    nodeWindow.show()
    exit(app.exec_())



def maya_main():
    import maya.OpenMayaUI as OpenMayaUI
    from shiboken2 import wrapInstance
    mainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
    mayaWindow = wrapInstance(long(mainWindowPtr), QtWidgets.QWidget)
    nodeWindow = Window()
    nodeWindow.show()


if __name__ == '__main__':
    main()
