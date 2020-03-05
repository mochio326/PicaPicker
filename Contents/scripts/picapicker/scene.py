# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
from .node import Picker, BgNode, GroupPicker
from .line import Line
import sqlite3


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
        self.snap_to_grid_flag = False
        self._snap_guide = {'x': None, 'y': None}

        # memo
        # itemをリストに入れて保持しておかないと
        # 大量のitemが追加された際にPySideがバグってしまう事があった
        self.add_items = []

    def table_is_exists(self, cursor, tebel_name):
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE TYPE='table' AND name='{0}'
            """.format(tebel_name))
        if cursor.fetchone()[0] == 0:
            return False
        return True

    def load(self):
        for _i in self.items():
            self.remove_item(_i)
        conn = sqlite3.connect(r'c:\temp\sample3.picap')
        cursor = conn.cursor()
        for row in cursor.execute('select * from picker'):
            _n = Picker()
            self.picker_init(_n, 1)
            _n.load_data(row)
            _n.update()
        if self.table_is_exists(cursor, 'group_picker'):
            for row in cursor.execute('select * from group_picker'):
                _n = GroupPicker()
                self.picker_init(_n, 1)
                _n.load_data(row)
                _n.update()
        conn.close()

    def save(self):
        conn = sqlite3.connect(r'c:\temp\sample3.picap')
        conn.text_factory = str
        cursor = conn.cursor()

        cursor.execute('DROP TABLE IF EXISTS picker')
        cursor.execute(
            'CREATE TABLE picker(id text PRIMARY KEY, x real, y real, width integer, height integer, node_name text, label text, bg_color text)')
        _data = [_n.get_save_data() for _n in self.items() if isinstance(_n, Picker)]
        cursor.executemany("insert into picker values (?,?,?,?,?,?,?,?)", _data)

        cursor.execute('DROP TABLE IF EXISTS group_picker')
        cursor.execute(
            'CREATE TABLE group_picker(id text PRIMARY KEY, x real, y real, width integer, height integer, member_nodes_id text, label text, bg_color text)')
        _data = [_n.get_save_data() for _n in self.items() if isinstance(_n, GroupPicker)]
        cursor.executemany("insert into group_picker values (?,?,?,?,?,?,?,?)", _data)


        conn.commit()
        conn.close()

    def del_node_snapping_guide(self, type):
        if self._snap_guide[type] is not None:
            self.remove_item(self._snap_guide[type])
            self._snap_guide[type] = None

    def show_node_snapping_guide(self, pos_a, pos_b, type):
        self.del_node_snapping_guide(type)
        self._snap_guide[type] = Line(pos_a, pos_b)
        self.add_item(self._snap_guide[type])

    def picker_init(self, picker_instance, opacity=None):
        # picker作った際に必要な初期設定を行っとく
        self.add_item(picker_instance)
        if opacity is not None:
            picker_instance.setOpacity(opacity)
        picker_instance.node_snapping.connect(self.show_node_snapping_guide)
        picker_instance.node_snapped.connect(self.del_node_snapping_guide)


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
