# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import BgNode, GroupPicker, Picker
from .line import Line
import re


class View(QtWidgets.QGraphicsView):

    def __init__(self, scene, parent):
        super(View, self).__init__(parent)
        self.setObjectName('View')
        self.setScene(scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

        self.drag = False
        self._operation_history = [None]
        self._current_operation_history = 0
        self.setStyleSheet('background-color: rgb(40,40,40);')

        self.drop_node = None

        self.setAcceptDrops(True)

        self.press_alignment_key = False
        self.alignment_start_pos = None
        self.alignment_type = 'free'
        self.alignment_mode = False
        self.alignment_guide_path = None
        self._init_alignment_params()
        self.prev_pos = None

        self._snap_guide = {'x': None, 'y': None}

    def drop_create_node(self):
        return None

    def _context_menu(self, event):
        cursor = QtGui.QCursor.pos()

        def __enable_edit_checked():
            self.scene().enable_edit = _enable_edit_action.isChecked()
            self.scene().enable_edit_change()
            self.parent().menu_bar_visibility()

        def __add_group_picker(pos):
            picker =[_item.id for _item in self.scene().selectedItems() if isinstance(_item, Picker)]
            g = GroupPicker(member_nodes_id=picker)
            self.picker_init(g)
            g.setPos(pos)
            g.update()

        _menu = QtWidgets.QMenu()

        _enable_edit_action = QtWidgets.QAction('Enable edit', self, checkable=True)
        _enable_edit_action.setChecked(self.scene().enable_edit)
        _enable_edit_action.triggered.connect(__enable_edit_checked)
        _menu.addAction(_enable_edit_action)

        if not self.scene().enable_edit:
            _menu.exec_(cursor)
            return

        _menu.addSection('Add')
        _menu.addAction('Picker', lambda: self.create_nods_from_dcc_selection(self.mapToScene(event)))
        _menu.addAction('GroupPicker', lambda: __add_group_picker(self.mapToScene(event)))

        _menu.exec_(cursor)

    def create_nods_from_dcc_selection(self, pos):
        pass

    def get_nodes(self, cls, display_only=False):
        if display_only:
            _nodes = self.items(self.viewport().rect())
        else:
            _nodes = self.items()
        return [_n for _n in _nodes if isinstance(_n, cls)]

    def add_node_on_center(self, node):
        self.picker_init(node)
        node.setPos(self.get_view_center_pos())
        node.update()

    def get_view_center_pos(self):
        return self.mapToScene(self.width() / 2, self.height() / 2)

    def del_node_snapping_guide(self, type):
        if self._snap_guide[type] is not None:
            self.scene().remove_item(self._snap_guide[type])
            self._snap_guide[type] = None

    def show_node_snapping_guide(self, pos_a, pos_b, type):
        self.del_node_snapping_guide(type)
        self._snap_guide[type] = Line(pos_a, pos_b)
        self.scene().add_item(self._snap_guide[type])

    def _init_alignment_params(self):
        self.alignment_start_pos = None
        self.alignment_type = 'free'
        self.alignment_guide_path = None
        self.alignment_mode = False

    def dragMoveEvent(self, event):
        pos = self.mapToScene(event.pos())
        self.pickers_placement(self.drop_node, pos, 0.5)

    def dragLeaveEvent(self, event):
        """ドラッグが抜けた時の処理
        """
        if self.drop_node is not None:
            for _n in self.drop_node:
                self.scene().remove_item(_n)
            self.drop_node = None

    def dragEnterEvent(self, event):

        if not self.scene().enable_edit:
            return

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
            self.drop_node = [self.drop_create_node(_t, pos) for _t in text]
        else:
            event.ignore()

        if self.drop_node is None:
            return
        for _n in self.drop_node:
            self.picker_init(_n, 0.5)
        self.update()
        event.setAccepted(True)

    def picker_init(self, picker_instance, opacity=None):
        # picker作った際に必要な初期設定を行っとく
        self.scene().add_item(picker_instance)
        if opacity is not None:
            picker_instance.setOpacity(opacity)
        picker_instance.node_snapping.connect(self.show_node_snapping_guide)
        picker_instance.node_snapped.connect(self.del_node_snapping_guide)

    def pickers_placement(self, pickers, pos_origin, opacity=None):
        # 複数のpickerノードを横一列にいい感じに配置する
        for i, _n in enumerate(pickers):
            _n.setPos(pos_origin.x() + (_n.rect.width() + 10) * i, pos_origin.y())
            self.scene().node_snap_to_grid(_n)
            if property is not None:
                _n.setOpacity(opacity)
            _n.update()

    def dropEvent(self, event):
        event.acceptProposedAction()
        pos = self.mapToScene(event.pos())
        self.pickers_placement(self.drop_node, pos, 1)
        self.drop_node = None

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

            if not self.scene().enable_edit or len(self.scene().selectedItems()) < 2:
                return

            self.press_alignment_key = True
            if event.button() == QtCore.Qt.LeftButton:
                self.alignment_type = 'vertical'
            elif event.button() == QtCore.Qt.RightButton:
                self.alignment_type = 'horizontal'
            self.alignment_start_pos = self.mapToScene(event.pos())
            self.alignment_mode = True
            self.alignment_guide_path = Line(self.alignment_start_pos, self.alignment_start_pos, self.alignment_type)
            self.scene().add_item(self.alignment_guide_path)
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

        # 以下編集用ショートカット
        if not self.scene().enable_edit:
            return

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
        self.focus(self.items)

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
        if len(_sel) < 2:
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
