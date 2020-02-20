# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
import uuid
from .line import Line
from maya import cmds


class Node(QtWidgets.QGraphicsObject):
    DEF_Z_VALUE = 0.1

    # 移動中常に発動
    moveing = QtCore.Signal()
    # 移動後に発動
    pos_changed = QtCore.Signal()

    @classmethod
    def scene_nodes_iter(cls, scene):
        # シーン内のノードのみ取得
        for _i in scene.items():
            if not isinstance(_i, cls):
                continue
            yield _i

    @property
    def center(self):
        center = QtCore.QPointF(self.rect.x() + self.rect.width() / 2, self.rect.y() + self.rect.height() / 2)
        return self.mapToScene(center)

    @property
    def rect(self):
        return QtCore.QRect(0, 0, self.width, self.height)

    def __init__(self, name='', width=30, height=30, label='node', bg_color=None):
        super(Node, self).__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.setZValue(self.DEF_Z_VALUE)
        self.width = width
        self.height = height
        self.drag = False
        self.snap = True
        if bg_color is None:
            self.bg_color = QtGui.QColor(60, 60, 60, 255)
        else:
            self.bg_color = bg_color
        self.label = label
        self._tooltip = label

        self.setAcceptHoverEvents(True)

        # Brush.
        self.brush = QtGui.QBrush()
        self.brush.setStyle(QtCore.Qt.SolidPattern)

        # Pen.
        self.pen = QtGui.QPen()
        self.pen.setStyle(QtCore.Qt.SolidLine)
        self.pen.setWidth(1)
        self.pen.setColor(QtGui.QColor(140, 140, 140, 255))

        self.sel_pen = QtGui.QPen()
        self.sel_pen.setStyle(QtCore.Qt.SolidLine)
        self.sel_pen.setWidth(2)
        self.sel_pen.setColor(QtGui.QColor(0, 255, 255, 255))

    def shape(self):
        path = QtGui.QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def boundingRect(self):
        return QtCore.QRectF(0, 0, self.width, self.height)

    def paint(self, painter, option, widget):
        self.brush.setColor(self.bg_color)
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.sel_pen)
        else:
            painter.setPen(self.pen)
        painter.drawRoundedRect(self.rect, 2.0, 2.0)

        # painter.setPen(self.pen)
        # painter.setFont(QtGui.QFont('Decorative', 10, QtGui.QFont.Bold))
        # rect = self.boundingRect()
        # rect.moveTop(rect.y() - 2)
        # painter.drawText(rect, QtCore.Qt.AlignCenter, self.label)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.ControlModifier:

            self.scene().clearSelection()
            for _n in self.get_source_nodes():
                _n.setSelected(True)
            self.setSelected(True)
            self.scene().update()

        elif event.button() == QtCore.Qt.LeftButton:
            self.drag = True
            # 見やすくするために最前面表示
            # self.setZValue(100.0)
        super(Node, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        super(Node, self).mouseMoveEvent(event)

        if self.drag:
            self.moveing.emit()
            # print self.center
            if self.snap:
                x_node, y_node = self.search_snap_node()
                if x_node is not None:
                    self.setX(x_node.x())
                    self.scene().views()[0].x_snap_guide.show()
                    self.scene().views()[0].x_snap_guide.point_a = self.center
                    self.scene().views()[0].x_snap_guide.point_b = x_node.center
                else:
                    self.scene().views()[0].x_snap_guide.hide()
                if y_node is not None:
                    self.setY(y_node.y())
                    self.scene().views()[0].y_snap_guide.show()
                    self.scene().views()[0].y_snap_guide.point_a = self.center
                    self.scene().views()[0].y_snap_guide.point_b = y_node.center
                else:
                    self.scene().views()[0].y_snap_guide.hide()
            self.scene().update()

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = False
            # ノードを現在の描画順を維持したまま数値を整頓
            node_z_list = []
            for _n in self.scene_nodes_iter(self.scene()):
                node_z_list.append([_n.zValue(), _n])
            node_z_list = sorted(node_z_list, key=lambda x: x[0])
            for _i, _n in enumerate(node_z_list):
                _n[1].setZValue(self.DEF_Z_VALUE + 0.01 * _i)
            super(Node, self).mouseReleaseEvent(event)
            self.moveing.emit()
            self.pos_changed.emit()

            self.scene().views()[0].x_snap_guide.hide()
            self.scene().views()[0].y_snap_guide.hide()

    def hoverEnterEvent(self, event):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self._tooltip)
        super(Node, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QtWidgets.QToolTip.hideText()
        super(Node, self).hoverMoveEvent(event)

    def delete(self):
        self.scene().views()[0].remove_item(self)

    def search_snap_node(self):
        _threshold = 10
        _x_candidate = {}
        _y_candidate = {}
        for _n in Node.scene_nodes_iter(self.scene()):
            if self == _n:
                continue
            _x_deff = abs(_n.center.x() - self.center.x())
            _y_deff = abs(_n.center.y() - self.center.y())

            if _x_deff < _threshold:
                _x_candidate[_x_deff] = _n
            if _y_deff < _threshold:
                _y_candidate[_y_deff] = _n

        _x_candidate = sorted(_x_candidate.items(), key=lambda x: x[0])
        _y_candidate = sorted(_y_candidate.items(), key=lambda x: x[0])

        x_node = None
        y_node = None
        if len(_x_candidate) >= 1:
            x_node = next(iter(_x_candidate))[1]
        if len(_y_candidate) >= 1:
            y_node = next(iter(_y_candidate))[1]

        return x_node, y_node


class PickNode(Node):
    DEF_Z_VALUE = 10

    @property
    def select_node(self):
        node_name = self.label
        return cmds.ls(node_name)

    def __init__(self, *args, **kwargs):
        super(PickNode, self).__init__(*args, **kwargs)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)


class BgNode(Node):

    def __init__(self, url=None, image=None):
        super(BgNode, self).__init__()
        self.ulr = url
        if url is not None:
            self.image = QtGui.QImage(self.ulr)
        if image is not None:
            self.image = QtGui.QImage(image)
        self.width = self.image.width()
        self.height = self.image.height()
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(False)
        self.snap = False

    def paint(self, painter, option, widget):
        painter.drawImage(0, 0, self.image)

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------