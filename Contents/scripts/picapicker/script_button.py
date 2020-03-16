## -*- coding: utf-8 -*-
import os
import maya.cmds as cmds
import functools
import copy

from .vendor.Qt import QtCore, QtGui, QtWidgets


def make_menu_button_dict():
    return {'label': ' test001', 'use_externalfile': False, 'externalfile': '', 'code': '', 'script_language': 'Python'}


class LineNumberTextEdit(QtWidgets.QTextEdit):
    def __init__(self, parent=None):
        super(LineNumberTextEdit, self).__init__(parent)
        self.setViewportMargins(self.fontMetrics().width("8") * 8, 0, 0, 0)
        self.side = QtWidgets.QWidget(self)
        self.side.installEventFilter(self)
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height())
        self.setAcceptDrops(False)
        self.setLineWrapMode(QtWidgets.QTextEdit.NoWrap)

    def paintEvent(self, e):
        super(LineNumberTextEdit, self).paintEvent(e)
        # self.draw_eof()
        if self.side.height() == self.height():
            num = 1
        else:
            num = 0
        self.side.setGeometry(0, 0, self.fontMetrics().width("8") * 8, self.height() + num)
        self.draw_tab()

    def eventFilter(self, o, e):
        if e.type() == QtCore.QEvent.Paint and o == self.side:
            self.draw_line_number(o)
            return True
        return False

    def draw_eof(self):
        c = self.textCursor()
        c.movePosition(c.End)
        r = self.cursorRect(c)
        paint = QtGui.QPainter(self.viewport())
        paint.setPen(QtGui.QColor(255, 0, 0))
        paint.setFont(self.currentFont())
        paint.drawText(QtCore.QPoint(r.left(), r.bottom() - 3), "[EOF]")

    def draw_tab(self):
        tabchar = "›"
        c = self.cursorForPosition(QtCore.QPoint(0, 0))
        paint = QtGui.QPainter()
        paint.begin(self.viewport())
        paint.setPen(QtGui.QColor(150, 150, 150))
        paint.setFont(self.currentFont())
        c = self.document().find("	", c)
        while not c.isNull():
            c.movePosition(QtGui.QTextCursor.Left)
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10: break
            paint.drawText(QtCore.QPoint(r.left(), r.bottom() - 3), tabchar)
            c.movePosition(QtGui.QTextCursor.Right)
            c = self.document().find("	", c)
        paint.end()

    def draw_line_number(self, o):
        c = self.cursorForPosition(QtCore.QPoint(0, 0))
        block = c.block()
        paint = QtGui.QPainter()
        paint.begin(o)
        paint.setPen(QtGui.QColor(150, 150, 150))
        paint.setFont(self.currentFont())
        while block.isValid():
            c.setPosition(block.position())
            r = self.cursorRect(c)
            if r.bottom() > self.height() + 10: break
            paint.drawText(QtCore.QPoint(10, r.bottom() - 3), str(block.blockNumber() + 1))
            block = block.next()
        paint.end()


class SettingDialog(QtWidgets.QWidget):

    def __init__(self):
        super(SettingDialog, self).__init__()
        self.setWindowTitle("Button Setting")
        # self.setProperty(" saveWindowPref", True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        self.resize(800, 600)

        self.checkbox_externalfile = QtWidgets.QCheckBox()
        self.text_script_code = LineNumberTextEdit(self)
        self.combo_type = QtWidgets.QComboBox()
        self.combo_type.addItem('Normal Button')
        self.combo_type.addItem('Menu Button')

        self.combo_script_language = QtWidgets.QComboBox()
        self.combo_script_language.addItem('MEL')
        self.combo_script_language.addItem('Python')

        self.line_externalfile = QtWidgets.QLineEdit()

        # ダイアログのOK/キャンセルボタン
        # self.buttonbox.accepted.connect(self.accept)
        # self.buttonbox.rejected.connect(self.reject)

        self.menulist_model = QtCore.QStringListModel()
        self.menulist_widget = QtWidgets.QListView()
        self.menulist_widget.setModel(self.menulist_model)
        self.menulist_widget.resize(70, self.menulist_widget.height())
        self.menulist_widget.setMaximumSize(QtCore.QSize(200, 16777215))
        self.menulist_widget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.menulist_widget.customContextMenuRequested.connect(self._menulist_context)
        menulist_sel_model = self.menulist_widget.selectionModel()
        menulist_sel_model.selectionChanged.connect(self._menulist_changed)
        self.menulist_widget.setCurrentIndex(self.menulist_model.index(0))

        self.dele = ListDelegate()
        self.dele.changeValue.connect(self._menulist_change_value)
        self.menulist_widget.setItemDelegate(self.dele)

        self.button_externalfile = QtWidgets.QToolButton()
        self.button_externalfile.setText('...')

        _base_layout = QtWidgets.QVBoxLayout()

        _type_h_layout = QtWidgets.QHBoxLayout()
        # _type_h_layout.addStretch(1)
        _type_h_layout.addWidget(QtWidgets.QLabel('ButtonType:'))
        _type_h_layout.addWidget(self.combo_type)
        _type_h_layout.addStretch(1)
        # _type_h_layout.addSpacing(8)

        _h_layout = QtWidgets.QHBoxLayout()
        _h_layout.addWidget(self.menulist_widget)

        _v_layout2 = QtWidgets.QVBoxLayout()

        _h_layout2 = QtWidgets.QHBoxLayout()
        _h_layout2.addWidget(QtWidgets.QLabel('ScriptLanguage:'))
        _h_layout2.addWidget(self.combo_script_language)
        _v_layout2.addLayout(_h_layout2)

        _h_layout2 = QtWidgets.QHBoxLayout()
        _h_layout2.addWidget(QtWidgets.QLabel('ExternalFile:'))
        _h_layout2.addWidget(self.checkbox_externalfile)
        _h_layout2.addWidget(self.line_externalfile)
        _h_layout2.addWidget(self.button_externalfile)
        _v_layout2.addLayout(_h_layout2)

        _v_layout2.addWidget(self.text_script_code)

        _h_layout.addLayout(_v_layout2)

        _base_layout.addLayout(_type_h_layout)
        _base_layout.addLayout(_h_layout)

        self.setLayout(_base_layout)

        self._data_input()
        self._type_changed()

        # コールバック関数の設定
        func = self._redraw_ui

        self.combo_script_language.currentIndexChanged.connect(func)

        self.button_externalfile.clicked.connect(self._get_externalfile)
        self.checkbox_externalfile.stateChanged.connect(func)
        self.line_externalfile.textChanged.connect(func)

        self.combo_type.currentIndexChanged.connect(self._type_changed)

        # テキストエリアに日本語を入力中（IME未確定状態）にMayaがクラッシュする場合があった。
        # textChanged.connect をやめ、例えば focusOut や エンターキー押下を発火条件にすることで対応
        # self.text_label.textChanged.connect(func)
        # self.text_tooltip.textChanged.connect(func)

        def _focus_out(event):
            self._redraw_ui()

        def _key_press(event, widget=None):
            QtWidgets.QTextEdit.keyPressEvent(widget, event)

            key = event.key()
            if (key == QtCore.Qt.Key_Enter) or (key == QtCore.Qt.Key_Return):
                self._redraw_ui()

        self.text_script_code.focusOutEvent = _focus_out
        self.text_script_code.keyPressEvent = functools.partial(_key_press, widget=self.text_script_code)

    def _get_externalfile(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', os.path.expanduser('~') + '/Desktop')
        path = filename[0]
        self.line_externalfile.setText(path)

    def _type_changed(self):
        _idx = self.combo_type.currentIndex()
        if _idx == 0:
            self.menulist_widget.hide()
        elif _idx == 1:
            self.menulist_widget.show()

            _ls = []
            for _tmp in self.menu_data:
                _ls.append(_tmp['label'])

            self.menulist_model.setStringList(_ls)

        self._apply_script_commands_data()
        # self.resize(self.width(), 50)

    def _menulist_change_value(self, idx, value):
        self.menu_data[idx]['label'] = value

    def _menulist_changed(self, current, previous):
        self._apply_script_commands_data()

    def _menulist_context(self):
        _menu = QtWidgets.QMenu(self)
        _menu.addAction('Up', self._menulist_up)
        _menu.addAction('Down', self._menulist_down)
        _menu.addAction('Add', self._menulist_add)
        _menu.addAction('Delete', self._menulist_delete)
        cursor = QtGui.QCursor.pos()
        _menu.exec_(cursor)

    def _menulist_add(self):
        _dict = make_menu_button_dict()
        _dict['label'] = 'menu button' + str(len(self.menu_data))
        self.menu_data.append(_dict)
        self._menulist_redraw()

    def _menulist_redraw(self):
        _ls = []
        for _tmp in self.menu_data:
            _ls.append(_tmp['label'])
        self.menulist_model.setStringList(_ls)

    def _menulist_up(self):
        _index = self.menulist_widget.currentIndex()
        if _index.row() == 0 or _index is QtCore.QModelIndex():
            return
        _i = _index.row()
        self.menu_data[_i - 1], self.menu_data[_i] = self.menu_data[_i], self.menu_data[_i - 1]
        self._menulist_redraw()
        _sel = self.menulist_model.createIndex(_i - 1, 0)
        self.menulist_widget.setCurrentIndex(_sel)

    def _menulist_down(self):
        _index = self.menulist_widget.currentIndex()
        if _index.row() == len(self.menu_data) - 1 or _index is QtCore.QModelIndex():
            return
        _i = _index.row()
        self.menu_data[_i + 1], self.menu_data[_i] = self.menu_data[_i], self.menu_data[_i + 1]
        self._menulist_redraw()
        _sel = self.menulist_model.createIndex(_i + 1, 0)
        self.menulist_widget.setCurrentIndex(_sel)

    def _menulist_delete(self):
        _index = self.menulist_widget.currentIndex()
        self.menulist_model.removeRow(_index.row())
        del self.menu_data[_index.row()]
        if len(self.menu_data) == 0:
            self.combo_type.setCurrentIndex(0)

    def _keep_script_commands_data(self):
        _idx = self.combo_type.currentIndex()
        if _idx == 0:  # ノーマルボタン
            _d = self.normal_data
        else:  # メニューボタン
            _list_idx = self.menulist_widget.currentIndex()
            _d = self.menu_data[_list_idx.row()]

        _d['use_externalfile'] = self.checkbox_externalfile.isChecked()
        _d['externalfile'] = self.line_externalfile.text()
        _d['script_language'] = self.combo_script_language.currentText()
        _d['code'] = self.text_script_code.toPlainText()

    def _apply_script_commands_data(self):
        _idx = self.combo_type.currentIndex()
        if _idx == 0:  # ノーマルボタン
            _d = self.normal_data
        elif _idx == 1:  # メニューボタン
            _list_idx = self.menulist_widget.currentIndex()
            if len(self.menu_data) == 0:
                self._menulist_add()
            _d = self.menu_data[_list_idx.row()]

        self.text_script_code.setPlainText(_d['code'])
        self.line_externalfile.setText(_d['externalfile'])
        index = self.combo_script_language.findText(_d['script_language'])
        self.combo_script_language.setCurrentIndex(index)
        # checkbox_externalfileを最後に適用しないとline_externalfileが正常に反映されなかった。
        self.checkbox_externalfile.setChecked(_d['use_externalfile'])

    def _redraw_ui(self):
        # 外部ファイルを指定されている場合は言語を強制変更
        if self.checkbox_externalfile.isChecked() is True:
            _path = self.line_externalfile.text()
            _suffix = QtCore.QFileInfo(_path).completeSuffix()
            if _suffix == "py":
                script_language = 'Python'
            else:
                script_language = 'MEL'
            index = self.combo_script_language.findText(script_language)
            self.combo_script_language.setCurrentIndex(index)

        self._keep_script_commands_data()
        self.repaint()

        self.text_script_code.setReadOnly(self.checkbox_externalfile.isChecked())

    def _data_input(self):
        # データの入力
        # self.combo_type.setCurrentIndex(data.type_)
        # self.menu_data = copy.deepcopy(data.menu_data)
        self.combo_type.setCurrentIndex(1)

        # ノーマルボタン用のデータを保持
        _dict = make_menu_button_dict()

        self.menu_data = copy.deepcopy([make_menu_button_dict()])

        # _dict['code'] = data.code
        # _dict['use_externalfile'] = data.use_externalfile
        # _dict['externalfile'] = data.externalfile
        # _dict['script_language'] = data.script_language
        self.normal_data = _dict

    def get_button_data_instance(self):
        data = button.ButtonData()

        data.use_externalfile = self.normal_data['use_externalfile']
        data.externalfile = self.normal_data['externalfile']
        data.script_language = self.normal_data['script_language']
        data.code = self.normal_data['code']

        data.type_ = self.combo_type.currentIndex()
        data.menu_data = copy.deepcopy(self.menu_data)

        return data

    @staticmethod
    def get_data(parent=None, data=None):
        '''
        モーダルダイアログを開いてボタン設定とOKキャンセルを返す
        '''
        dialog = SettingDialog(parent, data)
        result = dialog.exec_()  # ダイアログを開く
        data = dialog.get_button_data_instance()
        dialog.normal_data = None
        return (data, result == QtWidgets.QDialog.Accepted)


class ListDelegate(QtWidgets.QItemDelegate):
    changeValue = QtCore.Signal(int, str)

    def createEditor(self, parent, option, index):
        # 編集する時に呼ばれるWidgetを設定
        editor = QtWidgets.QLineEdit(parent)
        return editor

    def setEditorData(self, LineEdit, index):
        # 編集されたときに呼ばれ、セットされた値をWidgetにセットする?
        value = index.model().data(index, QtCore.Qt.EditRole)
        LineEdit.setText(value)

    def setModelData(self, LineEdit, model, index):
        value = LineEdit.text()
        # 編集情報をSignalで発信する
        self.changeValue.emit(index.row(), value)
        model.setData(index, value, QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
