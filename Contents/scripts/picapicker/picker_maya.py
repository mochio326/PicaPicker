# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .node import PickNode
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import cmds
import copy

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
        bg_color = get_color(node)
        # if _color is None:
        #     bg_color = None
        # else:
        #     _color = [int(_c * 255) for _c in _color]
        #     bg_color = QtGui.QColor(_color[0], _color[1], _color[2])
        n = PickNode(label=split_text[-1], bg_color=bg_color)
        n.setPos(pos)
        return n

def get_color(node):
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

        _pick = self.menu_bar.addMenu('Picker')
        _pick.addAction('Color', self.node_change_color)
        _pick.addAction('Size', self.picker_size)
        _pick.addAction('WireFrame Color', self.set_wire_frame_color)


        _bgi = self.menu_bar.addMenu('Image')
        _lock_bg_image_action = QtWidgets.QAction('Lock', self, checkable=True)
        _lock_bg_image_action.setChecked(self.scene.lock_bg_image)
        _lock_bg_image_action.triggered.connect(_lock_bg_image_checked)
        _bgi.addAction(_lock_bg_image_action)
        _bgop = _bgi.addMenu('Opacity')

        ag = QtWidgets.QActionGroup(_bgop, exclusive=True)
        self.myID = [str(_i * 0.1) for _i in reversed(range(1, 11, 1))]
        _op_act = []
        for j in self.myID:
            _op_act.append(ag.addAction(QtWidgets.QAction(j, _bgop, checkable=True)))
            _bgop.addAction(_op_act[-1])

        # lambdaで引数渡す場合、forとかで回すと変数が同一になってしまって最後の数値しか渡らなくなるのでベタ書き
        _op_lam = []
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(1.0))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.9))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.8))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.7))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.6))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.5))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.4))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.3))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.2))
        _op_lam.append(lambda: self.scene.edit_bg_image_opacity(0.1))

        for a, l in zip(_op_act, _op_lam):
            a.triggered.connect(l)

        _bgg = self.menu_bar.addMenu('Grid')
        _draw_bg_grid_action = QtWidgets.QAction('Draw', self, checkable=True)
        _draw_bg_grid_action.setChecked(self.scene.draw_bg_grid)
        _draw_bg_grid_action.triggered.connect(_draw_bg_grid_checked)
        _bgg.addAction(_draw_bg_grid_action)

    def picker_size(self):
        w = 20
        h = 20
        sel = self.scene.get_selected_pick_nodes()
        if len(sel) > 0:
            w = sel[0].width
            h = sel[0].height
        w, h, result = CanvasSizeInputDialog.get_canvas_size(self, w, h)
        if not result:
            return
        for _n in self.scene.get_selected_pick_nodes():
            _n.width = w
            _n.height = h
            _n.update()

    def set_wire_frame_color(self):
        for _n in self.scene.get_selected_pick_nodes():
            _n.bg_color = get_color(_n.select_node[0])
            _n.update()

    def node_change_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(60, 60, 60, 255), self)
        if not color.isValid():
            return
        for _n in self.scene.get_selected_pick_nodes():
            _n.bg_color = color
            _n.update()

    def bg_edit_opacity(self, val):
        self.scene.edit_bg_image_opacity(float(val))


class CanvasSizeInputDialog(QtWidgets.QDialog):

    def __init__(self, parent, w, h):
        """init."""
        super(CanvasSizeInputDialog, self).__init__(parent)
        self.setWindowTitle("Input picker size")

        # スピンボックスを用意
        self.input_w = QtWidgets.QSpinBox(self)
        self.input_h = QtWidgets.QSpinBox(self)
        self.input_w.setRange(1, 8192)  # 値の範囲
        self.input_h.setRange(1, 8192)
        self.input_w.setFixedWidth(80)  # 表示する横幅を指定
        self.input_h.setFixedWidth(80)
        self.input_w.setValue(w)  # 初期値を設定
        self.input_h.setValue(h)

        # ダイアログのOK/キャンセルボタンを用意
        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        # 各ウィジェットをレイアウト
        gl = QtWidgets.QHBoxLayout()
        gl.addWidget(self.input_w, 1, 0)
        gl.addWidget(QtWidgets.QLabel("x", self), 1, 1)
        gl.addWidget(self.input_h, 1, 2)
        gl.addWidget(btns, 2, 3)
        self.setLayout(gl)

    def canvas_size(self):
        u"""キャンバスサイズを取得。(w, h)で返す."""
        w = int(self.input_w.value())
        h = int(self.input_h.value())
        return (w, h)

    @staticmethod
    def get_canvas_size(parent=None, w=20, h=20):
        u"""ダイアログを開いてキャンバスサイズとOKキャンセルを返す."""
        dialog = CanvasSizeInputDialog(parent, w, h)
        result = dialog.exec_()  # ダイアログを開く
        w, h = dialog.canvas_size()  # キャンバスサイズを取得
        return (w, h, result == QtWidgets.QDialog.Accepted)

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
