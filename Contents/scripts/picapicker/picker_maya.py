# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as OpenMayaUI
from shiboken2 import wrapInstance


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
        cursor = QtGui.QCursor.pos()

        def __enable_edit_checked():
            self.view.enable_edit = _enable_edit_action.isChecked()
            self.view.enable_edit_change()

        def _lock_bg_image_checked():
            self.view.lock_bg_image = _lock_bg_image_action.isChecked()
            self.view.enable_edit_change()

        _menu = QtWidgets.QMenu()

        _enable_edit_action = QtWidgets.QAction('Enable edit', self, checkable=True)
        _enable_edit_action.setChecked(self.view.enable_edit)
        _enable_edit_action.triggered.connect(__enable_edit_checked)
        _menu.addAction(_enable_edit_action)

        if not self.view.enable_edit:
            _menu.exec_(cursor)
            return

        _menu.addSeparator()

        _lock_bg_image_action = QtWidgets.QAction('Lock background image', self, checkable=True)
        _lock_bg_image_action.setChecked(self.view.lock_bg_image)
        _lock_bg_image_action.triggered.connect(_lock_bg_image_checked)
        _menu.addAction(_lock_bg_image_action)


        # _menu.addAction('Add partition', self.hoge)
        #
        # black_color = QtWidgets.QAction('Black', _menu, checkable=True)
        #
        # _menu.addAction(black_color)
        # # _menu.triggered.connect(isChecked)

        _menu.exec_(cursor)


    def hoge(self):
        pass



'''
============================================================
---   SHOW WINDOW
============================================================
'''
def main():
    mainWindowPtr = OpenMayaUI.MQtUtil.mainWindow()
    mayaWindow = wrapInstance(long(mainWindowPtr), QtWidgets.QWidget)
    nodeWindow = Window()
    nodeWindow.show()


if __name__ == '__main__':
    main()
