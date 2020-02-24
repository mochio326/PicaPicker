# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .node import PickNode
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import cmds


class MScene(Scene):

    def select_nodes(self):
        _select_nodes = []
        for _item in self.selectedItems():
            if not isinstance(_item, PickNode):
                continue
            _select_nodes.extend(_item.select_node)
        cmds.select(_select_nodes)


class MView(View):

    def drop_create_node(self, text, pos):
        split_text = text.split('|')
        # if len(split_text) != 2:
        #     return
        # class_name, node_name = split_text

        node = cmds.ls(text)[0]
        _color = self.get_color(node)
        if _color is None:
            bg_color = None
        else:
            _color = [int(_c * 255) for _c in _color]
            bg_color = QtGui.QColor(_color[0], _color[1], _color[2])
        n = PickNode(label=split_text[-1], bg_color=bg_color)
        n.setPos(pos)
        return n

    def get_color(self, node):
        # 描画のオーバーライドの色
        if not cmds.getAttr(node + '.overrideEnabled'):
            return None
        if cmds.getAttr(node + '.overrideRGBColors'):
            return list(cmds.getAttr(node + '.overrideColorRGB')[0])
        else:
            color_index = cmds.getAttr(node + '.overrideColor')
            return cmds.colorIndex(color_index, q=True)


class PickerWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self):
        super(PickerWidget, self).__init__()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('PicaPicker')

        self.resize(600, 800)
        self.menu_bar = QtWidgets.QMenuBar(self)

        self.scene = MScene()
        self.scene.setObjectName('Scene')
        self.scene.setSceneRect(0, 0, 1000, 1000)
        self.view = MView(self.scene, self)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(2)
        self.vbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.vbox)
        self.meke_menu_bar()
        self.vbox.addWidget(self.menu_bar)
        self.vbox.addWidget(self.view)

    def menu_bar_visibility(self):
        if self.scene.enable_edit:
            self.menu_bar.show()
        else:
            self.menu_bar.hide()

    def meke_menu_bar(self):

        def _lock_bg_image_checked():
            self.scene.lock_bg_image = _lock_bg_image_action.isChecked()
            self.scene.enable_edit_change()

        def _draw_bg_grid_checked():
            self.scene.draw_bg_grid = _draw_bg_grid_action.isChecked()

        self.menu_bar = QtWidgets.QMenuBar(self)

        _m_file = self.menu_bar.addMenu('File')
        _m_file.setTearOffEnabled(True)
        _m_file.setWindowTitle('File')
        exit = QtWidgets.QAction('Exit', self)
        _m_file.addAction(exit)

        _pick = self.menu_bar.addMenu('PickButton')
        _pick.addAction('Edit color', self.node_change_color)

        _bgi = self.menu_bar.addMenu('Image')
        _lock_bg_image_action = QtWidgets.QAction('Lock', self, checkable=True)
        _lock_bg_image_action.setChecked(self.scene.lock_bg_image)
        _lock_bg_image_action.triggered.connect(_lock_bg_image_checked)
        _bgi.addAction(_lock_bg_image_action)
        _bgi.addAction('Edit opacity', self.bg_edit_opacity)

        _bgg = self.menu_bar.addMenu('Grid')
        _draw_bg_grid_action = QtWidgets.QAction('Draw', self, checkable=True)
        _draw_bg_grid_action.setChecked(self.scene.draw_bg_grid)
        _draw_bg_grid_action.triggered.connect(_draw_bg_grid_checked)
        _bgg.addAction(_draw_bg_grid_action)

    def node_change_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(60, 60, 60, 255), self)
        if not color.isValid():
            return
        for _n in self.scene.get_selected_pick_nodes():
            _n.bg_color = color
            _n.update()

    def bg_edit_opacity(self):
        self.scene.edit_bg_image_opacity(0.5)

'''
============================================================
---   SHOW WINDOW
============================================================
'''


def main():
    nodeWindow = PickerWidget()
    nodeWindow.show()


if __name__ == '__main__':
    main()
