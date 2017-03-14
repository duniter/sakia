from PyQt5.QtGui import QTextDocument, QAbstractTextDocumentLayout
from PyQt5.QtWidgets import QStyledItemDelegate, QApplication, QStyle
from PyQt5.QtCore import QSize
from .table_model import HistoryTableModel


class TxHistoryDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        self.initStyleOption(option, index)

        style = QApplication.style()

        doc = QTextDocument()
        if index.column() == HistoryTableModel.columns_types.index('uid'):
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
        if index.column() == HistoryTableModel.columns_types.index('uid'):
            doc.setHtml(option.text)
        else:
            doc.setPlainText("")
        doc.setTextWidth(option.rect.width())
        return QSize(doc.idealWidth(), doc.size().height())
