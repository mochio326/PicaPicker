# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .node import PickNode
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import maya.OpenMayaUI as OpenMayaUI
from shiboken2 import wrapInstance
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


class Window(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('picker test app')

        self.resize(600, 800)
        hbox = QtWidgets.QHBoxLayout()
        hbox.setSpacing(2)
        hbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(hbox)

        self.scene = MScene()
        self.scene.setObjectName('Scene')
        self.scene.setSceneRect(0, 0, 1000, 1000)
        self.view = MView(self.scene, self)

        hbox.addWidget(self.view)


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
