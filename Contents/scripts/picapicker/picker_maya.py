# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .menu import MenuBar
from .node import Picker
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.api import OpenMaya as om2
from maya import cmds
import re


def get_short_name(search):
    search = re.sub(r'^.+:', '', str(search))
    if ('|' in search) is True:
        split_number = search.rfind('|')
        search = search[split_number + 1:len(search)]
    return search


def find_children(findname='*', root_node='', node_type=None, recursive=True):
    u"""
    指定した名前とタイプでオブジェクトを取得
    *にも対応
    recursive : 再帰的に検索するか True[def]:再帰的 Flase:直接の子のみ
    """
    # ワイルドカード対応
    if '*' in findname:
        findname = findname.replace("*", ".*")
    pattern = re.compile(r'^%s$' % findname)

    nodes = []
    if node_type is None:
        _children = cmds.listRelatives(root_node, ad=recursive, f=1)
    else:
        _children = cmds.listRelatives(root_node, ad=recursive, f=1, type=node_type)
    if _children is not None:
        for _n in _children:
            sn = get_short_name(_n)
            if not pattern.match(sn):
                continue
            nodes.append(_n)

    # 取得したリスト内容が孫から子へと逆順になってる
    if len(nodes) > 0:
        nodes.reverse()

    return nodes


def get_dcc_node(self):
    node_name = self.node_name

    if self.scene().select_type == 1:
        if self.scene().namespace is not None:
            return cmds.ls('{0}:{1}'.format(self.scene().namespace, node_name))
    else:
        if self.scene().root_node is not None:
            return find_children(node_name, self.scene().root_node)

    return cmds.ls(node_name, recursive=True)


def select_dcc_nodes(self, node_list):
    cmds.select(node_list)


def drop_create_node(self, text, pos):
    split_text = re.split('\||:', text)
    node = cmds.ls(text)[0]
    bg_color = get_color(self, node)
    n = Picker(node_name=split_text[-1], bg_color=bg_color)
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


# ---- Maya独自の関数や変数を入れ込む ----


Picker.get_dcc_node = get_dcc_node
Scene.select_dcc_nodes = select_dcc_nodes
Scene.namespace = None
Scene.root_node = None
Scene.select_type = 1  # 1:namespace 0:root_node
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

        self.ns_combo = QtWidgets.QComboBox()
        self.ns_combo.currentTextChanged.connect(self._change_name_space)
        self.hbox.addWidget(self.ns_combo)
        self._reload_name_space_list()

        self.ns_button = QtWidgets.QPushButton(u'🔁')
        self.ns_button.pressed.connect(self._reload_name_space_list)
        self.hbox.addWidget(self.ns_button)

        self.root_node_name = QtWidgets.QLabel('')
        self.hbox.addWidget(self.root_node_name)

        self.root_button = QtWidgets.QPushButton('Get')
        self.root_button.pressed.connect(self._get_root_node)
        self.hbox.addWidget(self.root_button)

        self.hbox.addWidget(QtWidgets.QLabel(' | '))

        self.type = QtWidgets.QRadioButton('Namespace')
        self.hbox.addWidget(self.type)
        self.type.setChecked(self.scene.select_type)
        _r = QtWidgets.QRadioButton('RootNode')
        self.hbox.addWidget(_r)
        self.type.toggled.connect(self.type_changed)
        self.type_changed()

    def type_changed(self):
        self.scene.select_type = int(self.type.isChecked())
        if self.type.isChecked():
            self.ns_combo.show()
            self.ns_button.show()
            self.root_node_name.hide()
            self.root_button.hide()
        else:
            self.ns_combo.hide()
            self.ns_button.hide()
            self.root_node_name.show()
            self.root_button.show()
        self.scene.select_nodes()

    def _get_root_node(self):
        sel = cmds.ls(sl=True)
        if len(sel) == 0:
            self.scene.root_node = None
            self.root_node_name.setText('')
            return
        m_sel = om2.MGlobal.getSelectionListByName(sel[0])
        dag = m_sel.getDagPath(0)
        self.scene.root_node = dag
        self.root_node_name.setText(dag.partialPathName() + ' ')
        self.scene.select_nodes()
        return

    def _reload_name_space_list(self):
        ns = list(set(cmds.namespaceInfo(recurse=1, listOnlyNamespaces=1)) - {u'UI', u'shared'})
        ns[0:0] = ['']
        _v = self.ns_combo.currentText()
        self.ns_combo.clear()
        self.ns_combo.addItems(ns)
        if _v in ns:
            self.ns_combo.setCurrentIndex(ns.index(_v))
        self._change_name_space()

    def _change_name_space(self):
        _v = self.ns_combo.currentText()
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
