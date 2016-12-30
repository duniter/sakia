from PyQt5.QtWidgets import QFrame, QAction, QMenu, QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QT_TRANSLATE_NOOP, Qt
from .toolbar_uic import Ui_SakiaToolbar


class ToolbarView(QFrame, Ui_SakiaToolbar):
    """
    The model of Navigation component
    """
    _action_publish_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Publish UID")
    _action_revoke_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Revoke UID")

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        tool_menu = QMenu(self.tr("Tools"), self.toolbutton_menu)
        self.toolbutton_menu.setMenu(tool_menu)

        self.action_publish_uid = QAction(self.tr(ToolbarView._action_publish_uid_text), self)
        self.action_revoke_uid = QAction(self.tr(ToolbarView._action_revoke_uid_text), self)
        tool_menu.addAction(self.action_publish_uid)
        tool_menu.addAction(self.action_revoke_uid)

        menu_advanced = QMenu(self.tr("Advanced"), self.toolbutton_menu)
        self.action_gen_revokation = QAction(self.tr("Save revokation document"), menu_advanced)
        menu_advanced.addAction(self.action_gen_revokation)
        tool_menu.addMenu(menu_advanced)

        menu_options = QMenu(self.tr("Options"), self.toolbutton_menu)
        self.action_add_connection = QAction(self.tr("Add a connection"), menu_options)
        menu_options.addAction(self.action_add_connection)
        tool_menu.addMenu(menu_options)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumHeight(60)
