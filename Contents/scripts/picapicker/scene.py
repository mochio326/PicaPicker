# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import Picker, BgNode, GroupPicker


class Scene(QtWidgets.QGraphicsScene):
    def __init__(self):
        super(Scene, self).__init__()
        self.selectionChanged.connect(self.select_nodes)
        self.enable_edit = True
        self.lock_bg_image = False
        self.draw_bg_grid = True

        self.grid_width = 20
        self.grid_height = 20

        self.snap_to_node_flag = True
        self.snap_to_grid_flag = True

        # memo
        # itemをリストに入れて保持しておかないと
        # 大量のitemが追加された際にPySideがバグってしまう事があった
        self.add_items = []

    def node_snap_to_grid(self, node):
        if not self.snap_to_grid_flag:
            return
        node.setX(node.x() - node.x() % self.grid_width)
        node.setY(node.y() - node.y() % self.grid_height)

    def select_nodes(self):
        _target_dcc_nodes = []
        self.blockSignals(True)
        for _item in self.items():
            if isinstance(_item, Picker):
                _item.group_select = False
                _item.update()

        for _item in self.selectedItems():
            if isinstance(_item, GroupPicker) and not _item.drag:
                for _n in _item.get_member_nodes():
                    # _n.setSelected(True)
                    _n.group_select = True
                    _n.update()
                    _target_dcc_nodes.extend(_n.get_dcc_node())
            elif isinstance(_item, Picker):
                _target_dcc_nodes.extend(_item.get_dcc_node())
        self.select_dcc_nodes(_target_dcc_nodes)
        self.blockSignals(False)

    def select_dcc_nodes(self, node_list):
        # DCCツール側のノード選択処理
        pass

    def enable_edit_change(self):
        for _i in self.items():
            if isinstance(_i, Picker):
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, self.enable_edit)
            elif isinstance(_i, BgNode):
                _flg = self.enable_edit and not self.lock_bg_image
                _i.movable = _flg
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, _flg)
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, _flg)

    def edit_bg_image_opacity(self, value):
        for _i in self.items():
            if isinstance(_i, BgNode):
                _i.setOpacity(value)

    def add_to_group(self):
        _p = self.get_selected_pick_nodes()
        for _g in self.get_selected_group_pick_nodes():
            _g.add(_p)

    def remove_from_group(self):
        _p = self.get_selected_pick_nodes()
        for _g in self.get_selected_group_pick_nodes():
            _g.remove(_p)

    def get_selected_pick_nodes(self):
        return [_n for _n in self.selectedItems() if isinstance(_n, Picker)]

    def get_selected_group_pick_nodes(self):
        return [_n for _n in self.selectedItems() if isinstance(_n, GroupPicker)]

    def get_selected_all_pick_nodes(self):
        return [_n for _n in self.selectedItems() if isinstance(_n, (Picker, GroupPicker))]

    def drawBackground(self, painter, rect):

        if not self.draw_bg_grid:
            return

        scene_height = self.sceneRect().height()
        scene_width = self.sceneRect().width()

        # Pen.
        pen = QtGui.QPen()
        pen.setStyle(QtCore.Qt.SolidLine)
        pen.setWidth(1)
        pen.setColor(QtGui.QColor(80, 80, 80, 125))

        sel_pen = QtGui.QPen()
        sel_pen.setStyle(QtCore.Qt.SolidLine)
        sel_pen.setWidth(1)
        sel_pen.setColor(QtGui.QColor(125, 125, 125, 125))

        grid_horizontal_count = int(round(scene_width / self.grid_width)) + 1
        grid_vertical_count = int(round(scene_height / self.grid_height)) + 1

        for x in range(0, grid_horizontal_count):
            xc = x * self.grid_width
            if x % 5 == 0:
                painter.setPen(sel_pen)
            else:
                painter.setPen(pen)
            painter.drawLine(xc, 0, xc, scene_height)

        for y in range(0, grid_vertical_count):
            yc = y * self.grid_height
            if y % 5 == 0:
                painter.setPen(sel_pen)
            else:
                painter.setPen(pen)
            painter.drawLine(0, yc, scene_width, yc)

    def add_item(self, widget):
        if not isinstance(widget, list):
            widget = [widget]
        for _w in widget:
            self.add_items.append(_w)
            self.addItem(_w)

            _shadow = QtWidgets.QGraphicsDropShadowEffect(self)
            _shadow.setBlurRadius(10)
            _shadow.setOffset(3, 3)
            _shadow.setColor(QtGui.QColor(10, 10, 10, 150))
            _w.setGraphicsEffect(_shadow)

    def remove_item(self, widget):
        if not isinstance(widget, list):
            widget = [widget]
        for _w in widget:
            self.add_items.remove(_w)
            self.removeItem(_w)

    def clear(self):
        self.clear()
        self.add_items = []

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
