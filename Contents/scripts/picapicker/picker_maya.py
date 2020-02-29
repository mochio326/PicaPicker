# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .view import View
from .scene import Scene
from .node import Picker, GroupPicker
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya import cmds


def get_dcc_node(self):
    node_name = self.label
    return cmds.ls(node_name)


def select_dcc_nodes(self, node_list):
    cmds.select(node_list)


def drop_create_node(self, text, pos):
    split_text = text.split('|')
    # if len(split_text) != 2:
    #     return
    # class_name, node_name = split_text

    node = cmds.ls(text)[0]
    bg_color = get_color(node)
    n = Picker(label=split_text[-1], bg_color=bg_color)
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


def create_nods_from_dcc_selection(self, pos):
    _select = cmds.ls(sl=True, l=True)
    nodes = [drop_create_node(self, _s, pos) for _s in _select]
    [self.picker_init(_n, 1) for _n in nodes]
    self.pickers_placement(nodes, pos, 1)


Picker.get_dcc_node = get_dcc_node
Scene.select_dcc_nodes = select_dcc_nodes
View.drop_create_node = drop_create_node
View.create_nods_from_dcc_selection = create_nods_from_dcc_selection


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self, parent):
        super(MenuBar, self).__init__()
        self.view = parent.view
        self.scene = parent.scene

        _m_file = self.addMenu('File')
        _m_file.setTearOffEnabled(True)
        _m_file.setWindowTitle('File')
        exit = QtWidgets.QAction('Exit', self)
        _m_file.addAction(exit)

        _pick = self.addMenu('Picker')
        _pick.setTearOffEnabled(True)
        _pick.setWindowTitle('Picker')

        _pick.addAction('Color', self.node_change_color)
        _pick.addAction('Size', self.picker_size)
        _pick.addAction('Set WireFrame Color', self.set_wire_frame_color)
        _pick.addSection('Add')
        _pick.addAction('Picker', lambda: self.view.create_nods_from_dcc_selection(self.view.get_view_center_pos()))
        _pick.addAction('GroupPicker', lambda: self.view.add_node_on_center(
            GroupPicker(
                member_nodes_id=[_item.id for _item in self.scene.selectedItems() if isinstance(_item, Picker)])))
        _pick.addSection('Edit Group')
        _pick.addAction('Add to Group', self.scene.add_to_group)
        _pick.addAction('Remove from Group', self.scene.remove_from_group)

        _bgi = self.addMenu('Image')
        _bgi.setTearOffEnabled(True)
        _bgi.setWindowTitle('Image')

        _lock_bg_image_action = self._create_checkbox(_bgi, 'Lock', self.scene.lock_bg_image, self._lock_bg_image_checked)

        _bgop = _bgi.addMenu('Opacity')

        ag = QtWidgets.QActionGroup(_bgop, exclusive=True)
        for j in [_i * 0.1 for _i in reversed(range(1, 11, 1))]:
            _action = ag.addAction(QtWidgets.QAction(str(j), _bgop, checkable=True))
            _bgop.addAction(_action)
            _action.triggered.connect(lambda x=j: self.scene.edit_bg_image_opacity(x))

        _bgg = self.addMenu('Setting')
        _bgg.setTearOffEnabled(True)
        _bgg.setWindowTitle('Setting')
        self._draw_bg_grid_action = self._create_checkbox(_bgg, 'DrawGrid', self.scene.draw_bg_grid,
                                                          self._draw_bg_grid_checked)
        _bgg.addSection('Snap')
        self._snap_to_picker_action = self._create_checkbox(_bgg, 'Snap to Picker', self.scene.snap_to_node_flag,
                                                            self._snap_to_picker_checked)
        self._snap_to_grid_action = self._create_checkbox(_bgg, 'Snap to Grid', self.scene.snap_to_grid_flag,
                                                          self._snap_to_grid_checked)

    def add_to_group(self):
        self

    def remove_from_group(self):
        pass

    def _lock_bg_image_checked(self):
        self.scene.lock_bg_image = self._lock_bg_image_action.isChecked()
        self.scene.enable_edit_change()

    def _draw_bg_grid_checked(self):
        self.scene.draw_bg_grid = self._draw_bg_grid_action.isChecked()

    def _snap_to_picker_checked(self):
        self.scene.snap_to_node_flag = self._snap_to_picker_action.isChecked()

    def _snap_to_grid_checked(self):
        self.scene.snap_to_grid_flag = self._snap_to_grid_action.isChecked()

    def _create_checkbox(self, menu, label, checked, connect_def):
        action = QtWidgets.QAction(label, self, checkable=True)
        action.setChecked(checked)
        action.triggered.connect(connect_def)
        menu.addAction(action)
        return action

    def add_many_picker(self):
        self.view.add_node_on_center(
            GroupPicker(member_nodes_id=[_item.id for _item in self.selectedItems() if isinstance(_item, Picker)]))

    def picker_size(self):
        w = 20
        h = 20
        sel = self.scene.get_selected_all_pick_nodes()
        if len(sel) > 0:
            w = sel[0].width
            h = sel[0].height
        w, h, result = CanvasSizeInputDialog.get_canvas_size(self, w, h)
        if not result:
            return
        for _n in self.scene.get_selected_all_pick_nodes():
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
        for _n in self.scene.get_selected_all_pick_nodes():
            _n.bg_color = color
            _n.update()


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

        self.menu_bar = MenuBar(self)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setSpacing(2)
        self.vbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.vbox)
        self.vbox.addWidget(self.menu_bar)
        self.vbox.addWidget(self.view)

    def menu_bar_visibility(self):
        if self.scene.enable_edit:
            self.menu_bar.show()
        else:
            self.menu_bar.hide()


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
