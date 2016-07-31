from PyQt5.QtWidgets import QFrame, QAction, QMenu, QSizePolicy, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject, QT_TRANSLATE_NOOP, Qt
from .toolbar_uic import Ui_SakiaToolbar


class ToolbarView(QFrame, Ui_SakiaToolbar):
    """
    The model of Navigation agent
    """
    _action_showinfo_text = QT_TRANSLATE_NOOP("ToolbarView", "Show informations")
    _action_explore_text = QT_TRANSLATE_NOOP("ToolbarView", "Explore the Web of Trust")
    _action_publish_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Publish UID")
    _action_revoke_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Revoke UID")

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        tool_menu = QMenu(self.tr("Tools"), self.toolbutton_menu)
        self.toolbutton_menu.setMenu(tool_menu)

        self.action_publish_uid = QAction(self.tr(ToolbarView._action_publish_uid_text), self)
        self.action_revoke_uid = QAction(self.tr(ToolbarView._action_revoke_uid_text), self)
        self.action_showinfo = QAction(self.tr(ToolbarView._action_showinfo_text), self)
        self.action_explorer = QAction(self.tr(ToolbarView._action_explore_text), self)

        action_showinfo = QAction(self.tr("Show informations"), self.toolbutton_menu)
        action_showinfo.triggered.connect(lambda: self.show_closable_tab(self.tab_informations,
                                                                         QIcon(":/icons/informations_icon"),
                                                                         self.tr("Informations")))
        tool_menu.addAction(action_showinfo)

        action_showexplorer = QAction(self.tr("Show explorer"), self.toolbutton_menu)
        action_showexplorer.triggered.connect(lambda: self.show_closable_tab(self.tab_explorer.widget,
                                                                             QIcon(":/icons/explorer_icon"),
                                                                             self.tr("Explorer")))
        tool_menu.addAction(action_showexplorer)

        menu_advanced = QMenu(self.tr("Advanced"), self.toolbutton_menu)
        self.action_gen_revokation = QAction(self.tr("Save revokation document"), menu_advanced)
        menu_advanced.addAction(self.action_gen_revokation)
        tool_menu.addMenu(menu_advanced)
        tool_menu.addAction(self.action_publish_uid)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumHeight(60)

