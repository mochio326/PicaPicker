# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets, QtSql
from .node import Picker, BgNode, GroupPicker
from .line import Line


class SaveData(object):
    PICKER_TABLE_DATA = (('id', 'text PRIMARY KEY'),
                         ('x', 'real'),
                         ('y', 'real'),
                         ('z', 'real'),
                         ('width', 'integer'),
                         ('height', 'integer'),
                         ('node_name', 'text'),
                         ('label', 'text'),
                         ('bg_color', 'text')
                         )
    GROUP_PICKER_TABLE_DATA = (('id', 'text PRIMARY KEY'),
                               ('x', 'real'),
                               ('y', 'real'),
                               ('z', 'real'),
                               ('width', 'integer'),
                               ('height', 'integer'),
                               ('member_nodes_id', 'text'),
                               ('label', 'text'),
                               ('bg_color', 'text')
                               )
    BG_IMAGE_TABLE_DATA = (('id', 'text PRIMARY KEY'),
                           ('x', 'real'),
                           ('y', 'real'),
                           ('z', 'real'),
                           ('width', 'integer'),
                           ('height', 'integer'),
                           ('data', 'blob')
                           )

    def __init__(self, scene):
        self.scene = scene

    def table_is_exists(self, cursor, tebel_name):
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master 
            WHERE TYPE='table' AND name='{0}'
            """.format(tebel_name))
        if cursor.fetchone()[0] == 0:
            return False
        return True

    def load(self, file_path):
        for _i in self.scene.items():
            self.scene.remove_item(_i)

        db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(file_path)
        db.open()
        query = QtSql.QSqlQuery(db)
        self._create_picker(query, 'picker', Picker)
        self._create_picker(query, 'group_picker', GroupPicker)
        self._create_bg_image(query, 'bg_image')
        db.close()

    def _create_picker(self, query, table_name, picker_cls):
        query.exec_('SELECT * FROM {0}'.format(table_name))
        if not query.isActive():
            return

        query.first()
        while query.isValid():
            _n = picker_cls()
            self.scene.picker_init(_n, 1)
            _n.load_data(query)
            query.next()

    def _create_bg_image(self, query, table_name):
        query.exec_('SELECT * FROM {0}'.format(table_name))
        if not query.isActive():
            return

        query.first()
        while query.isValid():
            _n = BgNode()
            self.scene.add_item(_n)
            _n.load_data(query)
            _n.update()
            query.next()

    def _create_table(self, query, table_name, table_format, cls):
        _table_format_str = ', '.join([" ".join(map(str, _f)) for _f in table_format])
        _table_insert_value_format = ','.join(['?' for _ in table_format])

        query.exec_('DROP TABLE IF EXISTS {0}'.format(table_name))
        query.exec_('CREATE TABLE {0}({1})'.format(table_name, _table_format_str))
        query.prepare('insert into {0} values ({1})'.format(table_name, _table_insert_value_format))
        query.exec_()

        for _n in self.scene.items():
            if not isinstance(_n, cls):
                continue
            _data = _n.get_save_data()
            for i, v in enumerate(_data):
                query.bindValue(i, v)
            query.exec_()

    def save(self, file_path):
        db = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        db.setDatabaseName(file_path)
        db.open()
        query = QtSql.QSqlQuery(db)
        self._create_table(query, 'picker', self.PICKER_TABLE_DATA, Picker)
        self._create_table(query, 'group_picker', self.GROUP_PICKER_TABLE_DATA, GroupPicker)
        self._create_table(query, 'bg_image', self.BG_IMAGE_TABLE_DATA, BgNode)
        db.close()


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

    def load(self):
        _sd = SaveData(self)
        _sd.load(r'c:\temp\sample4.picap')

    def save(self):
        _sd = SaveData(self)
        _sd.save(r'c:\temp\sample4.picap')

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
