# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .menu import MenuBar
from .node import Picker
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import cmds
import re


def get_dcc_node(self):
    node_name = self.label
    if self.scene().namespace is not None:
        return cmds.ls('{0}:{1}'.format(self.scene().namespace, node_name))
    else:
        return cmds.ls(node_name, recursive=True)


def select_dcc_nodes(self, node_list):
    cmds.select(node_list)


def drop_create_node(self, text, pos):
    split_text = re.split('\||:', text)
    node = cmds.ls(text)[0]
    bg_color = get_color(self, node)
    n = Picker(label=split_text[-1], bg_color=bg_color)
    n.setPos(pos)
    return n


def get_color(self, node):
    # 描画のオーバーライドの色
    if not cmds.getAttr(node + '.overrideEnabled'):
        return None
    if cmds.getAttr(node + '.overrideRGBColors'):
        _color = list(cmds.getAttr(node + '.overrideColorRGB')[0])
    else:
        color_index = cmds.getAttr(node + '.overrideColor')
        _color = cmds.colorIndex(color_index, q=True)
    _color = [int(_c * 255) for _c in _color]
    return QtGui.QColor(_color[0], _color[1], _color[2])


def create_nods_from_dcc_selection(self, pos):
    _select = cmds.ls(sl=True, l=True)
    nodes = [drop_create_node(self, _s, pos) for _s in _select]
    [self.picker_init(_n, 1) for _n in nodes]
    self.pickers_placement(nodes, pos, 1)


Picker.get_dcc_node = get_dcc_node
Scene.select_dcc_nodes = select_dcc_nodes
Scene.namespace = None
View.drop_create_node = drop_create_node
View.create_nods_from_dcc_selection = create_nods_from_dcc_selection
MenuBar.get_node_color = get_color


class NameSpaceWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(NameSpaceWidget, self).__init__()

        self.view = parent.view
        self.scene = parent.scene

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('NameSpaceWidget')

        self.resize(100, 800)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setSpacing(2)
        self.hbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.hbox)

        self.hbox.addStretch(1)

        _label = QtWidgets.QLabel('Namespace : ')
        self.hbox.addWidget(_label)

        self.combo = QtWidgets.QComboBox()
        _name_space_list = list(set(cmds.namespaceInfo(recurse=1, listOnlyNamespaces=1)) - {u'UI', u'shared'})
        _name_space_list[0:0] = ['']

        self.combo.addItems(_name_space_list)
        self.combo.currentTextChanged.connect(self._change_name_space)
        self.hbox.addWidget(self.combo)

    def _change_name_space(self):
        _v = self.combo.currentText()
        self.scene.namespace = None if _v == '' else _v
        self.scene.select_nodes()


class PickerWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self):
        super(PickerWidget, self).__init__()

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('PicaPicker')

        self.resize(600, 800)

        self.scene = Scene()
        self.scene.setObjectName('Scene')
        self.scene.setSceneRect(0, 0, 1000, 1000)
        self.view = View(self.scene, self)

        self.nsw = NameSpaceWidget(self)

        self.menu_bar = MenuBar(self)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(2)
        self.vbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.vbox)
        self.vbox.addWidget(self.menu_bar)

        self.vbox.addWidget(self.nsw)

        self.vbox.addWidget(self.view)

    def menu_bar_visibility(self):
        if self.scene.enable_edit:
            self.menu_bar.show()
        else:
            self.menu_bar.hide()



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
