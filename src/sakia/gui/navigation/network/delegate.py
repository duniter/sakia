from PyQt5.QtGui import QTextDocument, QAbstractTextDocumentLayout
from PyQt5.QtWidgets import QStyledItemDelegate, QApplication, QStyle
from PyQt5.QtCore import QSize
from .table_model import NetworkTableModel


class NetworkDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        self.initStyleOption(option, index)

        style = QApplication.style()

        doc = QTextDocument()
        if index.column() in (NetworkTableModel.columns_types.index('address'),
                              NetworkTableModel.columns_types.index('port'),
                              NetworkTableModel.columns_types.index('api')):
            doc.setHtml(option.text)
        else:
            doc.setPlainText(option.text)

        option.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, option, painter)

        ctx = QAbstractTextDocumentLayout.PaintContext()

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        self.initStyleOption(option, index)

        doc = QTextDocument()
        if index.column() in (NetworkTableModel.columns_types.index('address'),
                              NetworkTableModel.columns_types.index('port'),
                              NetworkTableModel.columns_types.index('api')):
            doc.setHtml(option.text)
        else:
            doc.setPlainText("")
        doc.setTextWidth(option.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())
