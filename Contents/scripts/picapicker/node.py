# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
import uuid


class Node(QtWidgets.QGraphicsObject):
    DEF_Z_VALUE = 0.1

    # 移動中常に発動
    moving = QtCore.Signal()
    # 移動後に発動
    pos_changed = QtCore.Signal()

    node_snapping = QtCore.Signal(QtCore.QPointF, QtCore.QPointF, str)
    node_snapped = QtCore.Signal(str)

    @property
    def view(self):
        for _v in self.scene().views():
            if _v.isInteractive():
                return _v

    @property
    def center(self):
        center = QtCore.QPointF(self.rect.x() + self.rect.width() / 2, self.rect.y() + self.rect.height() / 2)
        return self.mapToScene(center)

    @property
    def rect(self):
        return QtCore.QRect(0, 0, self.width, self.height)

    def __init__(self, name='', width=30, height=30, label='', bg_color=None):
        super(Node, self).__init__()
        self.id = str(uuid.uuid4())
        self.name = name
        self.setZValue(self.DEF_Z_VALUE)
        self.width = width
        self.height = height
        self.drag = False
        if bg_color is None:
            self.bg_color = QtGui.QColor(60, 60, 60, 255)
        else:
            self.bg_color = bg_color
        self.label = label
        self._tooltip = label

        self.setAcceptHoverEvents(True)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.movable = True
        self.drag_node_origin = None
        self.origin_pos_dict = {}

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

    def set_movable_flag_from_scene(self):
        _flag = all([self.scene().enable_edit, self.scene().is_node_movable])
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, _flag)

    def set_selectable_flag_from_scene(self):
        pass

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
        if event.button() == QtCore.Qt.LeftButton:
            self.drag = True
            # 見やすくするために最前面表示
            # self.setZValue(100.0)
            self.drag_node_origin = self.pos()
            for _n in self.scene().selectedItems():
                self.origin_pos_dict[_n.id] = _n.pos()

        super(Node, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # super(Node, self).mouseMoveEvent(event)

        if self.drag:
            super(Node, self).mouseMoveEvent(event)
            self.moving.emit()

            if self.scene().snap_to_node_flag:
                x_node, y_node = self.search_snap_node()
                if x_node is not None:
                    self.setX(x_node.x())
                else:
                    self.node_snapped.emit('x')

                if y_node is not None:
                    self.setY(y_node.y())
                else:
                    self.node_snapped.emit('y')

                # ノードの位置補正後にライン表示しないとラインの始点がノードと違う位置になってしまう
                if x_node is not None:
                    self.node_snapping.emit(self.center, x_node.center, 'x')
                if y_node is not None:
                    self.node_snapping.emit(self.center, y_node.center, 'y')

                # 複数ノードをドラッグしていた場合にメインノードと同じ移動を入れる
                # スナップ補正された場合にデフォの移動機能だとノード同士の間隔がズレる為
                node_deff = self.drag_node_origin - self.pos()
                for _n in self.scene().selectedItems():
                    if _n == self:
                        continue
                    _n.setPos(self.origin_pos_dict[_n.id] - node_deff)

            for n in self.scene().selectedItems():
                self.scene().node_snap_to_grid(n)
            self.scene().update()

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = False
            # ノードを現在の描画順を維持したまま数値を整頓
            node_z_list = []
            for _n in self.view.get_nodes(self.__class__):
                node_z_list.append([_n.zValue(), _n])
            node_z_list = sorted(node_z_list, key=lambda x: x[0])
            for _i, _n in enumerate(node_z_list):
                _n[1].setZValue(self.DEF_Z_VALUE + 0.01 * _i)
            super(Node, self).mouseReleaseEvent(event)
            self.moving.emit()
            self.pos_changed.emit()

            self.node_snapped.emit('x')
            self.node_snapped.emit('y')

            self.origin_pos_dict = {}

    def hoverEnterEvent(self, event):
        QtWidgets.QToolTip.showText(QtGui.QCursor.pos(), self._tooltip)
        super(Node, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        QtWidgets.QToolTip.hideText()
        super(Node, self).hoverMoveEvent(event)

    def delete(self):
        self.scene().remove_item(self)

    def search_snap_node(self):

        if not self.scene().enable_edit:
            return None, None

        _threshold = 10
        _x_candidate = {}
        _y_candidate = {}

        for _n in self.view.get_nodes((GroupPicker, Picker), True):
            if self == _n or _n.isSelected() is True:
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


class Picker(Node):
    DEF_Z_VALUE = 10

    def get_save_data(self):
        return (
            self.id,
            self.x(),
            self.y(),
            self.zValue(),
            self.width,
            self.height,
            self.node_name,
            self.label,
            self.bg_color.rgba()
        )

    def load_data(self, data):
        self.id = data.value(0)
        self.setX(data.value(1))
        self.setY(data.value(2))
        self.setZValue(data.value(3))
        self.width = data.value(4)
        self.height = data.value(5)
        self.node_name = data.value(6)
        self.label = data.value(7)
        self.bg_color.setRgba(int(data.value(8)))

    def __init__(self, node_name='', *args, **kwargs):
        super(Picker, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.group_select = False
        self.node_name = node_name

        self.group_pen = QtGui.QPen()
        self.group_pen.setStyle(QtCore.Qt.DotLine)
        self.group_pen.setWidth(2)
        self.group_pen.setColor(QtGui.QColor(255, 255, 0, 255))

    def paint(self, painter, option, widget):
        self.brush.setColor(self.bg_color)
        painter.setBrush(self.brush)
        if self.isSelected():
            _b = QtGui.QBrush()
            _b.setStyle(QtCore.Qt.Dense3Pattern)
            _b.setColor(self.bg_color)
            painter.setBrush(_b)
            painter.setPen(self.sel_pen)
        elif self.group_select:
            _b = QtGui.QBrush()
            _b.setStyle(QtCore.Qt.Dense5Pattern)
            _b.setColor(self.bg_color)
            painter.setBrush(_b)
            painter.setPen(self.group_pen)
        else:
            painter.setPen(self.pen)
        painter.drawRoundedRect(self.rect, 2.0, 2.0)

        # painter.setPen(self.pen)
        # painter.setFont(QtGui.QFont('Decorative', 10, QtGui.QFont.Bold))
        # rect = self.boundingRect()
        # rect.moveTop(rect.y() - 2)
        # painter.drawText(rect, QtCore.Qt.AlignCenter, self.label)

    def mouseMoveEvent(self, event):
        super(Picker, self).mouseMoveEvent(event)

        # if event.buttons() == QtCore.Qt.MiddleButton:
        #     mimeData = QtCore.QMimeData()
        #     mimeData.setData("text/picknode", self.id)
        #     drag = QtGui.QDrag(self)
        #     drag.setMimeData(mimeData)
        #     drag.setHotSpot(QtCore.QPoint(event.pos().x() - self.pos().x(), event.pos().y() - self.pos().y()))
        #     dropAction = drag.exec_(QtCore.Qt.MoveAction)

    def get_dcc_node(self):
        """
        DCCツール側のノード情報を戻す
        :return:
        """
        pass


class GroupPicker(Node):
    DEF_Z_VALUE = 10

    def get_save_data(self):
        return (
            self.id,
            self.x(),
            self.y(),
            self.zValue(),
            self.width,
            self.height,
            None if self.member_nodes_id is None else ','.join(self.member_nodes_id),
            self.label,
            self.bg_color.rgba()
        )

    def load_data(self, data):
        self.id = data.value(0)
        self.setX(data.value(1))
        self.setY(data.value(2))
        self.setZValue(data.value(3))
        self.width = data.value(4)
        self.height = data.value(5)
        self.member_nodes_id = None if data.value(6) is None else set(data.value(6).split(','))
        self.label = data.value(7)
        self.bg_color.setRgba(int(data.value(8)))

    def __init__(self, member_nodes_id=None, *args, **kwargs):
        super(GroupPicker, self).__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.member_nodes_id = {}
        if member_nodes_id is not None:
            self.member_nodes_id = member_nodes_id

    def get_member_nodes(self):
        return [_i for _i in self.scene().items() if _i.id in self.member_nodes_id]

    def paint(self, painter, option, widget):
        self.brush.setColor(self.bg_color)
        painter.setBrush(self.brush)
        if self.isSelected():
            painter.setPen(self.sel_pen)
        else:
            painter.setPen(self.pen)
        painter.drawRoundedRect(self.rect, 20.0, 20.0)

    def add(self, nodes):
        self.member_nodes_id |= {_n.id for _n in nodes}

    def remove(self, nodes):
        self.member_nodes_id -= {_n.id for _n in nodes}


class ScriptButton(Node):
    DEF_Z_VALUE = 10

    def get_save_data(self):
        return (
            self.id,
            self.x(),
            self.y(),
            self.zValue(),
            self.width,
            self.height,
            self.label,
            self.bg_color.rgba()
        )

    def load_data(self, data):
        self.id = data.value(0)
        self.setX(data.value(1))
        self.setY(data.value(2))
        self.setZValue(data.value(3))
        self.width = data.value(4)
        self.height = data.value(5)
        self.label = data.value(7)
        self.bg_color.setRgba(int(data.value(8)))

    def __init__(self, member_nodes_id=None, *args, **kwargs):
        super(ScriptButton, self).__init__(*args, **kwargs)
        # self.setAcceptDrops(True)

    def mouseReleaseEvent(self, event):
        super(ScriptButton, self).mouseReleaseEvent(event)




class BgNode(Node):

    def get_save_data(self):
        barr = QtCore.QByteArray()
        buff = QtCore.QBuffer(barr)
        buff.open(QtCore.QIODevice.WriteOnly)
        self.image.save(buff, "PNG")

        return (
            self.id,
            self.x(),
            self.y(),
            self.zValue(),
            self.width,
            self.height,
            barr
        )

    def load_data(self, data):
        self.id = data.value(0)
        self.setX(data.value(1))
        self.setY(data.value(2))
        self.setZValue(data.value(3))
        self.width = data.value(4)
        self.height = data.value(5)
        self.image = QtGui.QPixmap()
        self.image.loadFromData(data.value(6))

    def __init__(self, url=None, image=None):
        super(BgNode, self).__init__()
        self.image = None
        self.setAcceptHoverEvents(False)
        self.movable = True

        if url is not None:
            self.image = QtGui.QImage(url)
        if image is not None:
            self.image = QtGui.QImage(image)
        if self.image is not None:
            self.image = QtGui.QPixmap.fromImage(self.image)
            self.width = self.image.width()
            self.height = self.image.height()

    def set_selectable_flag_from_scene(self):
        _flag = all([self.scene().enable_edit, self.scene().is_bg_image_selectable])
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, _flag)
        self.set_movable_flag_from_scene()

    def set_movable_flag_from_scene(self):
        _flag = all([self.scene().enable_edit, self.scene().is_node_movable, self.scene().is_bg_image_selectable])
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, _flag)

    def search_snap_node(self):
        return None, None

    def mouseMoveEvent(self, event):
        if self.drag:
            super(BgNode, self).mouseMoveEvent(event)

    def mousePressEvent(self, event):
        # ここで選択できなくしておかないと前面のpickerを矩形選択できない
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
        # if event.button() == QtCore.Qt.LeftButton and event.modifiers() == QtCore.Qt.ControlModifier:
        #     # ロックされてない場合のみ一時的にフラグを有効にして編集できるようにする
        #     if self.movable:
        #         self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        #         self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        # self.drag = True
        super(BgNode, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        # if self.drag:
        # if self.movable:
        # 削除のために選択状態は残しておく
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, False)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, False)
        super(BgNode, self).mouseReleaseEvent(event)

    def paint(self, painter, option, widget):
        painter.drawPixmap(0, 0, self.image)
        if self.isSelected():
            painter.setPen(self.sel_pen)
            painter.drawRoundedRect(self.rect, 2.0, 2.0)
# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
