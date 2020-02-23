# -*- coding: utf-8 -*-
from .vendor.Qt import QtCore, QtGui, QtWidgets
import cmath


class LineArrow(QtWidgets.QGraphicsItem):
    def __init__(self, parent, color):
        super(LineArrow, self).__init__(parent)
        self.triangle = QtGui.QPolygon()
        self.color = color
        # Pen.
        self.pen = QtGui.QPen()
        self.pen.setStyle(QtCore.Qt.SolidLine)
        self.pen.setWidth(0)
        self.pen.setColor(self.color)

    @property
    def line(self):
        return self.parentItem()

    def paint(self, painter, option, widget):
        self.color = self.parentItem().color
        painter.setPen(self.pen)
        path = QtGui.QPainterPath()
        dx = self.line.point_b.x() - self.line.point_a.x()
        dy = self.line.point_b.y() - self.line.point_a.y()
        triangle_x = (self.line.point_a.x() + self.line.point_b.x()) / 2
        triangle_y = (self.line.point_a.y() + self.line.point_b.y()) / 2

        # 三角形の中心からの先端へのベクトル
        line_vector_x = self.line.point_a.x() - self.line.point_b.x()
        line_vector_y = self.line.point_a.y() - self.line.point_b.y()
        line_vector = complex(line_vector_x, line_vector_y)
        # 単位ベクトルに変換
        _p = cmath.phase(line_vector)
        line_vector = cmath.rect(1, _p)

        #
        triangle_points = [complex(-10, 0),
                           complex(10, 5),
                           complex(10, -5),
                           complex(-10, 0)]
        triangle_points = [_p * line_vector for _p in triangle_points]
        triangle_points = [QtCore.QPoint(triangle_x + _p.real, triangle_y + _p.imag) for _p in triangle_points]
        self.triangle = QtGui.QPolygon(triangle_points)
        path.addPolygon(self.triangle)
        painter.fillPath(path, self.pen.color())
        painter.drawPath(path)

    def boundingRect(self):
        return self.triangle.boundingRect()

    def shape(self):
        path = QtGui.QPainterPath()
        path.addEllipse(self.boundingRect())
        return path


class Line(QtWidgets.QGraphicsPathItem):
    DEF_Z_VALUE = 10.0

    def __init__(self, point_a, point_b, alignment_type='free'):
        """

        :param point_a: ラインの始点
        :param point_b: ラインの終点
        :param alignment_type: vertical / horizontal / free
        """
        # :param alignment_type: vertical　horizontal　free

        self.alignment_type = alignment_type
        super(Line, self).__init__()
        self.color = QtGui.QColor(255, 200, 200, 255)
        self._point_a = point_a
        self._point_b = point_b
        self.pen = QtGui.QPen()
        self.pen.setStyle(QtCore.Qt.SolidLine)
        self.pen.setWidth(1)
        self.pen.setColor(self.color)
        self.arrow = LineArrow(self, self.color)

        self.setZValue(self.DEF_Z_VALUE)
        self.setBrush(QtCore.Qt.NoBrush)
        self.setPen(self.pen)
        self.setOpacity(0.7)

        self.update_path()

    def delete(self):
        self.scene().views()[0].remove_item(self)

    def update_path(self):
        path = QtGui.QPainterPath()

        _point_end = self.point_b
        if self.alignment_type == 'vertical':
            _point_end.setX(self.point_a.x())
        elif self.alignment_type == 'horizontal':
            _point_end.setY(self.point_a.y())

        path.moveTo(self.point_a)
        path.cubicTo(self.point_a, _point_end, _point_end)
        self.setPath(path)

    def paint(self, painter, option, widget):
        painter.setPen(self.pen)
        painter.drawPath(self.path())
        self.arrow.paint(painter, option, widget)

    @property
    def point_a(self):
        return self._point_a

    @point_a.setter
    def point_a(self, point):
        self._point_a = point
        self.update_path()

    @property
    def point_b(self):
        return self._point_b

    @point_b.setter
    def point_b(self, point):
        self._point_b = point
        self.update_path()

# -----------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------
