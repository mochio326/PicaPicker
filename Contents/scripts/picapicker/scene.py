# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import PickNode, BgNode


class Scene(QtWidgets.QGraphicsScene):
    def __init__(self):
        super(Scene, self).__init__()
        self.selectionChanged.connect(self.select_nodes)
        self.enable_edit = True
        self.lock_bg_image = False
        self.draw_bg_grid = True

        # memo
        # itemをリストに入れて保持しておかないと
        # 大量のitemが追加された際にPySideがバグってしまう事があった
        self.add_items = []

    def select_nodes(self):
        pass

    def enable_edit_change(self):
        for _i in self.items():
            if isinstance(_i, PickNode):
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, self.enable_edit)
            elif isinstance(_i, BgNode):
                _flg = self.enable_edit and not self.lock_bg_image
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, _flg)
                _i.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, _flg)

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

        grid_width = 20
        grid_height = 20
        grid_horizontal_count = int(round(scene_width / grid_width)) + 1
        grid_vertical_count = int(round(scene_height / grid_height)) + 1

        for x in range(0, grid_horizontal_count):
            xc = x * grid_width
            if x % 5 == 0:
                painter.setPen(sel_pen)
            else:
                painter.setPen(pen)
            painter.drawLine(xc, 0, xc, scene_height)

        for y in range(0, grid_vertical_count):
            yc = y * grid_height
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
