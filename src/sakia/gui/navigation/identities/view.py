from PyQt5.QtCore import pyqtSignal, QT_TRANSLATE_NOOP, Qt, QEvent
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QAction
from .identities_uic import Ui_IdentitiesWidget


class IdentitiesView(QWidget, Ui_IdentitiesWidget):
    """
    View of the Identities component
    """
    view_in_wot = pyqtSignal(object)
    money_sent = pyqtSignal()
    search_by_text_requested = pyqtSignal(str)
    search_directly_connected_requested = pyqtSignal()

    _direct_connections_text = QT_TRANSLATE_NOOP("IdentitiesView", "Search direct certifications")
    _search_placeholder = QT_TRANSLATE_NOOP("IdentitiesView", "Research a pubkey, an uid...")

    def __init__(self, parent):
        super().__init__(parent)

        self.direct_connections = QAction(self.tr(IdentitiesView._direct_connections_text), self)
        self.direct_connections.triggered.connect(self.request_search_direct_connections)
        self.setupUi(self)

        self.table_identities.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_identities.sortByColumn(0, Qt.AscendingOrder)
        self.table_identities.resizeColumnsToContents()
        self.edit_textsearch.setPlaceholderText(self.tr(IdentitiesView._search_placeholder))
        self.button_search.addAction(self.direct_connections)
        self.button_search.clicked.connect(self.request_search_by_text)

    def set_table_identities_model(self, model):
        """
        Set the model of the table view
        :param PyQt5.QtCore.QAbstractItemModel model: the model of the table view
        """
        self.table_identities.setModel(model)
        model.modelAboutToBeReset.connect(lambda: self.table_identities.setEnabled(False))
        model.modelReset.connect(lambda: self.table_identities.setEnabled(True))

    def request_search_by_text(self):
        text = self.edit_textsearch.text()
        if len(text) < 2:
            return
        self.edit_textsearch.clear()
        self.edit_textsearch.setPlaceholderText(text)
        self.search_by_text_requested.emit(text)

    def request_search_direct_connections(self):
        """
        Search members of community and display found members
        """
        self.edit_textsearch.setPlaceholderText(self.tr(IdentitiesView._search_placeholder))
        self.search_directly_connected_requested.emit()

    def retranslateUi(self, widget):
        self.direct_connections.setText(self.tr(IdentitiesView._direct_connections_text))
        super().retranslateUi(self)

    def resizeEvent(self, event):
        self.busy.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super().changeEvent(event)

