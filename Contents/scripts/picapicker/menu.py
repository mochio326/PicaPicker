# # -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import Picker, GroupPicker
import os


def change_picker_size(parent, scene):
    w = 20
    h = 20
    sel = scene.get_selected_all_pick_nodes()
    if len(sel) > 0:
        w = sel[0].width
        h = sel[0].height
    w, h, result = CanvasSizeInputDialog.get_canvas_size(parent, w, h)
    if not result:
        return
    for _n in scene.get_selected_all_pick_nodes():
        _n.width = w
        _n.height = h
        _n.update()


def node_change_color(self):
    color = QtWidgets.QColorDialog.getColor(QtGui.QColor(60, 60, 60, 255), self)
    if not color.isValid():
        return
    for _n in self.scene.get_selected_all_pick_nodes():
        _n.bg_color = color
        _n.update()

class MenuBar(QtWidgets.QMenuBar):

    def __add_separator(self, menu, label):
        if hasattr(menu, 'addSection'):
            menu.addSection(label)
        else:
            menu.addSeparator()

    def __init__(self, parent):
        super(MenuBar, self).__init__()
        self.view = parent.view
        self.scene = parent.scene

        _m_file = self.addMenu('File')
        _m_file.setTearOffEnabled(True)
        _m_file.setWindowTitle('File')
        _m_file.addAction('New', self.scene.clear)

        _m_file.addAction('Save', self.scene.save)
        _m_file.addAction('Load', self.scene.load)

        _pick = self.addMenu('Picker')
        _pick.setTearOffEnabled(True)
        _pick.setWindowTitle('Picker')

        _pick.addAction('Color', lambda: node_change_color(self))
        _pick.addAction('Size', lambda: change_picker_size(self, self.scene))
        _pick.addAction('Set WireFrame Color', self.set_wire_frame_color)
        self.__add_separator(_pick, 'Add')
        _pick.addAction('Picker', lambda: self.view.create_nods_from_dcc_selection(self.view.get_view_center_pos()))
        _pick.addAction('GroupPicker', lambda: self.view.add_node_on_center(
            GroupPicker(
                member_nodes_id={_item.id for _item in self.scene.selectedItems() if isinstance(_item, Picker)})))
        self.__add_separator(_pick, 'Edit Group')
        _pick.addAction('Add to Group', self.scene.add_to_group)
        _pick.addAction('Remove from Group', self.scene.remove_from_group)

        _bgi = self.addMenu('Image')
        _bgi.setTearOffEnabled(True)
        _bgi.setWindowTitle('Image')

        _lock_bg_image_action = self._create_checkbox(_bgi, 'Lock', self.scene.lock_bg_image,
                                                      self._lock_bg_image_checked)

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
        self.__add_separator(_bgg, 'Snap')

        self._snap_to_picker_action = self._create_checkbox(_bgg, 'Snap to Picker', self.scene.snap_to_node_flag,
                                                            self._snap_to_picker_checked)
        self._snap_to_grid_action = self._create_checkbox(_bgg, 'Snap to Grid', self.scene.snap_to_grid_flag,
                                                          self._snap_to_grid_checked)

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

    def add_guroup_picker(self):
        self.view.add_node_on_center(
            GroupPicker(member_nodes_id=[_item.id for _item in self.selectedItems() if isinstance(_item, Picker)]))

    def set_wire_frame_color(self):
        for _n in self.scene.get_selected_pick_nodes():
            _n.bg_color = self.get_node_color(_n.get_dcc_node()[0])
            _n.update()

    def get_node_color(self, n):
        pass


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


class EditToolWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(EditToolWidget, self).__init__()
        _self_dir = os.path.dirname(os.path.abspath(__file__))

        self.view = parent.view
        self.scene = parent.scene

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)

        self.setWindowTitle('EditToolWidget')

        self.resize(800, 40)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setSpacing(2)
        self.hbox.setContentsMargins(2, 2, 2, 2)
        self.setLayout(self.hbox)

        size = QtCore.QSize(25, 25)

        self.select_mode = False

        def _toggle_change(value_name, button):
            setattr(self.scene, value_name, not getattr(self.scene, value_name))
            if getattr(self.scene, value_name):
                button.setStyleSheet('background-color: rgb(240,131,0);')
            else:
                button.setStyleSheet('background-color: rgb(93,93,93);')

        def _create_button(icon_file, tooltip):
            _btn = QtWidgets.QPushButton()
            pixmap = QtGui.QPixmap('{0}/icons/{1}.png'.format(_self_dir, icon_file))
            _icon = QtGui.QIcon(pixmap)
            _btn.setIcon(_icon)
            _btn.setIconSize(size)
            _btn.setFixedSize(size)
            _btn.setToolTip(tooltip)
            self.hbox.addWidget(_btn)
            return _btn

        def _create_toggle_button(icon_file, toggle_value_name):
            _btn = _create_button(icon_file, icon_file)
            _btn.pressed.connect(lambda: _toggle_change(toggle_value_name, _btn))

        _create_toggle_button('position', 'is_node_movable')

        self.hbox.addSpacing(8)

        _create_toggle_button('bgimage', 'is_bg_image_selectable')

        self.hbox.addSpacing(8)

        self.plus_button = _create_button('plus', 'plus')
        self.plus_button.pressed.connect(self.scene.add_to_group)
        self.minus_button = _create_button('minus', 'minus')
        self.minus_button.pressed.connect(self.scene.remove_from_group)

        self.hbox.addSpacing(8)

        self.scale_button = _create_button('scale', 'Change Picker Size')
        self.scale_button.pressed.connect(lambda: change_picker_size(self, self.scene))

        self.hbox.addSpacing(8)

        self.color_button = _create_button('color', 'Change Picker Color')
        self.color_button.pressed.connect(lambda: node_change_color(self))

        self.hbox.addStretch(1)
