from PyQt5.QtWidgets import QWidget, QComboBox, QCompleter
from PyQt5.QtCore import QT_TRANSLATE_NOOP, pyqtSignal, Qt, QStringListModel
from sakia.data.entities import Contact
from .search_user_uic import Ui_SearchUserWidget
import re
import asyncio


class SearchUserView(QWidget, Ui_SearchUserWidget):
    """
    The model of Navigation component
    """
    _search_placeholder = QT_TRANSLATE_NOOP("SearchUserWidget", "Research a pubkey, an uid...")
    search_requested = pyqtSignal(str)
    reset_requested = pyqtSignal()
    node_selected = pyqtSignal(int)

    def __init__(self, parent):
        # construct from qtDesigner
        super().__init__(parent)
        self.setupUi(self)
        # Default text when combo lineEdit is empty
        self.combobox_search.lineEdit().setPlaceholderText(self.tr(SearchUserView._search_placeholder))
        #  add combobox events
        self.combobox_search.lineEdit().returnPressed.connect(self.search)
        self.button_reset.clicked.connect(self.reset_requested)
        # To fix a recall of the same item with different case,
        # the edited text is not added in the item list
        self.combobox_search.setInsertPolicy(QComboBox.NoInsert)
        self.combobox_search.activated.connect(self.node_selected)

    def clear(self):
        self.combobox_search.clear()
        self.combobox_search.lineEdit().setPlaceholderText(self.tr(SearchUserView._search_placeholder))

    def search(self, text=""):
        """
        Search nodes when return is pressed in combobox lineEdit
        """
        if text:
            result = re.match(Contact.re_displayed_text, text)
            if result:
                text = result.group(2)
        else:
            text = self.combobox_search.lineEdit().text()
        self.combobox_search.lineEdit().clear()
        self.combobox_search.lineEdit().setPlaceholderText(self.tr("Looking for {0}...".format(text)))
        self.search_requested.emit(text)

    def set_search_result(self, text, nodes):
        """
        Set the list of users displayed in the combo box
        :param str text: the text of the search
        :param list[str] nodes: the list of users found
        """
        self.blockSignals(True)
        self.combobox_search.clear()
        if len(nodes) > 0:
            self.combobox_search.lineEdit().setText(text)
            for uid in nodes:
                self.combobox_search.addItem(uid)
        self.blockSignals(False)
        self.combobox_search.showPopup()

    def retranslateUi(self, widget):
        """
        Retranslate missing widgets from generated code
        """
        self.combobox_search.lineEdit().setPlaceholderText(self.tr(SearchUserView._search_placeholder))
        super().retranslateUi(self)

    def set_auto_completion(self, string_list):
        completer = QCompleter()
        model = QStringListModel()
        model.setStringList(string_list)
        completer.setModel(model)
        completer.activated.connect(self.search, type=Qt.QueuedConnection)
        self.combobox_search.setCompleter(completer)
