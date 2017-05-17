from PyQt5.QtGui import QTextDocument, QAbstractTextDocumentLayout, QPalette
from PyQt5.QtWidgets import QStyledItemDelegate, QApplication, QStyle
from PyQt5.QtCore import QSize, Qt, QSizeF
from .table_model import HistoryTableModel


class TxHistoryDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        self.initStyleOption(option, index)

        foreground = index.data(Qt.ForegroundRole)
        font = index.data(Qt.FontRole)
        style = QApplication.style()

        doc = QTextDocument()
        if index.column() == HistoryTableModel.columns_types.index('pubkey'):
            doc.setHtml(option.text)
        else:
            doc.setPlainText(option.text)

        option.text = ""
        style.drawControl(QStyle.CE_ItemViewItem, option, painter)

        ctx = QAbstractTextDocumentLayout.PaintContext()
        if foreground:
            if foreground.isValid():
                ctx.palette.setColor(QPalette.Text, foreground)
        if font:
            doc.setDefaultFont(font)
        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, option, index):
        self.initStyleOption(option, index)

        doc = QTextDocument()
        if index.column() == HistoryTableModel.columns_types.index('pubkey'):
            doc.setHtml(option.text)
        else:
            doc.setPlainText("")
        doc.setTextWidth(-1)
        return QSize(doc.idealWidth(), doc.size().height())
