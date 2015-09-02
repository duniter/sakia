"""
Created on 31 janv. 2015

@author: vit
"""

from PyQt5.QtWidgets import QWidget, QFrame, QGridLayout, QLayout
from PyQt5.QtCore import QEvent, Qt
from ..gen_resources.homescreen_uic import Ui_HomescreenWidget
from .community_tile import CommunityTile


class FrameCommunities(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid_layout = QGridLayout()
        self.setLayout(self.grid_layout)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)

    def sizeHint(self):
        return self.parentWidget().size()

    def refresh(self, app):
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)

        for c in app.current_account.communities:
            self.layout().addWidget(CommunityTile(self, app, c))


class HomeScreenWidget(QWidget, Ui_HomescreenWidget):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.frame_communities = FrameCommunities(self)
        self.layout().addWidget(self.frame_communities)

    def refresh(self):
        self.frame_communities.refresh(self.app)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh_text()
        return super(HomeScreenWidget, self).changeEvent(event)


