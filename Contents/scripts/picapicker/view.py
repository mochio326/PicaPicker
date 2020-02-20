# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import PickNode, BgNode
from .line import Line
from maya import cmds
import re
import cmath


def drop_create_node(text, pos):
    split_text = text.split('|')
    # if len(split_text) != 2:
    #     return
    # class_name, node_name = split_text

    node = cmds.ls(text)[0]
    _color = get_color(node)
    if _color is None:
        bg_color = None
    else:
        _color = [int(_c * 255) for _c in _color]
        bg_color = QtGui.QColor(_color[0], _color[1], _color[2])
    n = PickNode(label=split_text[-1], bg_color=bg_color)
    n.setPos(pos)
    return n


def get_color(node):
    # 描画のオーバーライドの色
    if not cmds.getAttr(node + '.overrideEnabled'):
        return None
    if cmds.getAttr(node + '.overrideRGBColors'):
        return list(cmds.getAttr(node + '.overrideColorRGB')[0])
    else:
        color_index = cmds.getAttr(node + '.overrideColor')
        return cmds.colorIndex(color_index, q=True)


class View(QtWidgets.QGraphicsView):

    def __init__(self, scene, parent):
        super(View, self).__init__(parent)
        self.setObjectName('View')
        self.setScene(scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.drag = False
        self.add_items = []
        self._operation_history = [None]
        self._current_operation_history = 0
        self.setStyleSheet('background-color: rgb(40,40,40);')

        self.scene().selectionChanged.connect(self.select_nodes)
        self.drop_node = None

        self.setAcceptDrops(True)

        self.press_alignment_key = False
        self.alignment_start_pos = None
        self.alignment_type = 'free'
        self.alignment_mode = False
        self.alignment_guide_path = None
        self._init_alignment_params()

        orign = self.mapToScene(0, 0)
        self.x_snap_guide = Line(orign, orign)
        self.x_snap_guide.hide()
        self.add_item(self.x_snap_guide)
        self.y_snap_guide = Line(orign, orign)
        self.add_item(self.y_snap_guide)
        self.y_snap_guide.hide()

    def _init_alignment_params(self):
        self.alignment_start_pos = None
        self.alignment_type = 'free'
        self.alignment_guide_path = None
        self.alignment_mode = False

    def dragMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        for i, _n in enumerate(self.drop_node):
            _n.setPos(pos.x() + (_n.rect.width() + 10) * i, pos.y())
            _n.update()

    def dragLeaveEvent(self, event):
        """ドラッグが抜けた時の処理
        """
        if self.drop_node is not None:
            for _n in self.drop_node:
                self.remove_item(_n)
            self.drop_node = None

    def dragEnterEvent(self, event):

        pos = self.mapToScene(event.pos())

        if event.mimeData().hasUrls() and event.mimeData().hasText():
            self.drop_node = []
            # 画像フォーマットかどうかチェックいれる
            for url in event.mimeData().urls():
                if hasattr(url, 'path'):  # PySide
                    _path = re.sub("^/", "", url.path())
                else:  # PySide2
                    _path = re.sub("^file:///", "", url.url())
                self.drop_node.append(BgNode(_path))
        elif event.mimeData().hasText() and not event.mimeData().hasUrls():
            text = event.mimeData().text()
            text = text.split('\n')
            self.drop_node = [drop_create_node(_t, pos) for _t in text]
        else:
            event.ignore()

        if self.drop_node is None:
            return
        for _n in self.drop_node:
            self.add_item(_n)
            _n.setOpacity(0.5)
        self.update()
        event.setAccepted(True)

    def dropEvent(self, event):
        event.acceptProposedAction()
        pos = self.mapToScene(event.pos())
        for i, _n in enumerate(self.drop_node):
            _n.setPos(pos.x() + (_n.rect.width() + 10) * i, pos.y())
            _n.setOpacity(1)
            _n.update()
        self.drop_node = None

    def select_nodes(self):
        _select_nodes = []
        for _item in self.scene().selectedItems():
            if not isinstance(_item, PickNode):
                continue
            _select_nodes.extend(_item.select_node)
        cmds.select(_select_nodes)

    def drawBackground(self, painter, rect):
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

    def wheelEvent(self, event):
        """
        Zooms the QGraphicsView in/out.

        :param event: QGraphicsSceneWheelEvent.
        """
        in_factor = 1.1
        out_factor = 1 / in_factor
        old_pos = self.mapToScene(event.pos())
        if event.delta() > 0:
            zoom_factor = in_factor
        else:
            zoom_factor = out_factor
        self.scale(zoom_factor, zoom_factor)
        new_pos = self.mapToScene(event.pos())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def mousePressEvent(self, event):

        if event.modifiers() == QtCore.Qt.ShiftModifier:
            self.press_alignment_key = True
            if event.button() == QtCore.Qt.LeftButton:
                self.alignment_type = 'vertical'
            elif event.button() == QtCore.Qt.RightButton:
                self.alignment_type = 'horizontal'
            self.alignment_start_pos = self.mapToScene(event.pos())
            self.alignment_mode = True
            self.alignment_guide_path = Line(self.alignment_start_pos, self.alignment_start_pos, self.alignment_type)
            self.add_item(self.alignment_guide_path)
            return

        if event.button() == QtCore.Qt.MiddleButton and event.modifiers() == QtCore.Qt.AltModifier:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.drag = True
            self.prev_pos = event.pos()
            self.setCursor(QtCore.Qt.SizeAllCursor)
        elif event.button() == QtCore.Qt.LeftButton:
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        super(View, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.drag:
            # 等倍scaleかつ回転してないはずでscale取り出す…
            new_scale = self.matrix().m11()
            delta = (self.mapToScene(event.pos()) - self.mapToScene(self.prev_pos)) * -1.0 * new_scale
            center = QtCore.QPoint(self.viewport().width() / 2 + delta.x(), self.viewport().height() / 2 + delta.y())
            new_center = self.mapToScene(center)
            self.centerOn(new_center)
            self.prev_pos = event.pos()
            return

        if self.alignment_mode:
            _end_pos = self.mapToScene(event.pos())
            self.alignment(self.alignment_type, self.alignment_start_pos, _end_pos)
            self.alignment_guide_path.point_b = _end_pos
            return

        super(View, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drag:
            self.drag = False
            self.setCursor(QtCore.Qt.ArrowCursor)

        if self.alignment_mode:
            _end_pos = self.mapToScene(event.pos())
            self.alignment(self.alignment_type, self.alignment_start_pos, _end_pos)
            self.alignment_guide_path.delete()
            self._init_alignment_params()

        super(View, self).mouseReleaseEvent(event)
        self.press_alignment_key = False
        return False

    def keyPressEvent(self, event):
        if event.isAutoRepeat():
            event.ignore()
            return

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers == QtCore.Qt.ControlModifier:
            # この辺りの処理は各関数をオーバーライドアプリ側での独自実装
            if event.key() == QtCore.Qt.Key_C:
                self._copy()
                return
            if event.key() == QtCore.Qt.Key_V:
                self._paste()
                return
            if event.key() == QtCore.Qt.Key_X:
                self._cut()
                return
            if event.key() == QtCore.Qt.Key_Z:
                self._undo()
                return
            if event.key() == QtCore.Qt.Key_Y:
                self._redo()
                return

        if event.key() == QtCore.Qt.Key_F:
            # self.selected_item_focus()
            return

        if event.key() == QtCore.Qt.Key_A:
            # self.all_item_focus()
            return

        if event.key() == QtCore.Qt.Key_Delete:
            self._delete()
            return

    def keyReleaseEvent(self, event):
        if event.isAutoRepeat():
            event.ignore()
            return

    def selected_item_focus(self):
        self.focus(self.scene().selectedItems())

    def all_item_focus(self):
        self.focus(self.add_items)

    def focus(self, items):
        if not items:
            return
        self.resetMatrix()
        rect = QtCore.QRectF(0, 0, 0, 0)
        for _i in items:
            rect = rect.united(_i.sceneBoundingRect())
        center = QtCore.QPoint(rect.width() / 2 + rect.x(), rect.height() / 2 + rect.y())
        w_s = self.width() / rect.width()
        h_s = self.height() / rect.height()
        zoom_factor = w_s if w_s < h_s else h_s
        zoom_factor = zoom_factor * 0.9
        self.scale(zoom_factor, zoom_factor)
        self.centerOn(center)

    def add_node_on_center(self, node):
        self.add_item(node)
        _pos = self.mapToScene(self.width() / 2, self.height() / 2)
        node.setPos(_pos)
        node.update()

    def add_item(self, widget):
        if not isinstance(widget, list):
            widget = [widget]
        for _w in widget:
            self.add_items.append(_w)
            self.scene().addItem(_w)

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
            self.scene().removeItem(_w)

    def clear(self):
        self.scene().clear()
        self.add_items = []

    def _delete(self):
        for _n in self.scene().selectedItems():
            _n.delete()

    def _copy(self):
        pass

    def _paste(self):
        cb = QtGui.QClipboard()
        if cb.mimeData().hasImage():
            img = cb.image()
            n = BgNode(image=img)
            self.add_node_on_center(n)

    def _cut(self):
        pass

    def _undo(self):
        pass

    def _redo(self):
        pass

    def alignment(self, alignment_type='vertical', start_pos=None, end_pos=None):
        """
        :param alignment_type: vertical　horizontal　free
        :return:
        """
        _sel = self.scene().selectedItems()
        if len(_sel) == 0:
            return

        if start_pos is None:
            start_pos = self.mapToScene(self.width() / 2, self.height() / 2)

        _add_x = None
        _add_y = None

        if alignment_type == 'vertical' or alignment_type == 'free':
            if end_pos is None:
                _add_y = 30
            else:
                _add_y = (end_pos.y() - start_pos.y()) / (len(_sel) - 1)

        if alignment_type == 'horizontal' or alignment_type == 'free':
            if end_pos is None:
                _add_x = 30
            else:
                _add_x = (end_pos.x() - start_pos.x()) / (len(_sel) - 1)

        _pos_dict = {}
        animation_group = QtCore.QParallelAnimationGroup(self)

        _x = 0
        _y = 0

        for _n in _sel:
            x = _x + start_pos.x()
            y = _y + start_pos.y()
            animation = QtCore.QPropertyAnimation(_n, "pos", self)
            animation.setDuration(100)

            _center = [x - _n.rect.width() / 2, y - _n.rect.height() / 2]

            animation.setEndValue(QtCore.QPointF(_center[0], _center[1]))
            animation_group.addAnimation(animation)

            _pos_dict[_n.id] = _center

            if _add_x is not None:
                _x = _x + _add_x
            if _add_y is not None:
                _y = _y + _add_y

        animation_group.start()

        # アニメーションするだけではノードの位置が更新されないらしい
        # ので、アニメーション終了後に改めて位置をセットしておく
        for _n in _sel:
            _n.setX(_pos_dict[_n.id][0])
            _n.setY(_pos_dict[_n.id][1])

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
