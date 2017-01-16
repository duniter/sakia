from PyQt5.QtWidgets import QFrame, QAction, QMenu, QSizePolicy, QInputDialog, QDialog
from sakia.gui.widgets.dialogs import dialog_async_exec
from PyQt5.QtCore import QObject, QT_TRANSLATE_NOOP, Qt
from .toolbar_uic import Ui_SakiaToolbar
from .about_uic import Ui_AboutPopup


class ToolbarView(QFrame, Ui_SakiaToolbar):
    """
    The model of Navigation component
    """
    _action_revoke_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Publish a revocation document")

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        tool_menu = QMenu(self.tr("Tools"), self.toolbutton_menu)
        self.toolbutton_menu.setMenu(tool_menu)

        self.action_add_connection = QAction(self.tr("Add a connection"), tool_menu)
        tool_menu.addAction(self.action_add_connection)

        self.action_revoke_uid = QAction(self.tr(ToolbarView._action_revoke_uid_text), self)
        tool_menu.addAction(self.action_revoke_uid)

        self.action_parameters = QAction(self.tr("Settings"), tool_menu)
        tool_menu.addAction(self.action_parameters)

        self.action_about = QAction(self.tr("About"), tool_menu)
        tool_menu.addAction(self.action_about)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumHeight(60)

    async def ask_for_connection(self, connections):
        connections_titles = [c.title() for c in connections]
        input_dialog = QInputDialog()
        input_dialog.setComboBoxItems(connections_titles)
        input_dialog.setWindowTitle(self.tr("Membership"))
        input_dialog.setLabelText(self.tr("Select a connection"))
        await dialog_async_exec(input_dialog)
        result = input_dialog.textValue()

        if input_dialog.result() == QDialog.Accepted:
            for c in connections:
                if c.title() == result:
                    return c

    def show_about(self, text):
        dialog = QDialog(self)
        about_dialog = Ui_AboutPopup()
        about_dialog.setupUi(dialog)
        about_dialog.label.setText(text)
        dialog.exec()
