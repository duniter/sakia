"""
Created on 31 janv. 2015

@author: vit
"""


class HomeScreenWidget(QWidget, Ui_HomescreenWidget):
    """
    classdocs
    """

    def __init__(self, parent, app, status_label):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.frame_communities = FrameCommunities(self)
        self.layout().addWidget(self.frame_communities)
        self.status_label = status_label

    def refresh(self):
        self.frame_communities.refresh(self.app)
        if self.app.current_account:
            self.frame_connected.show()
            self.label_connected.setText(self.tr("Connected as {0}".format(self.app.current_account.name)))
            self.frame_disconnected.hide()
        else:
            self.frame_disconnected.show()
            self.frame_connected.hide()

    def referential_changed(self):
        self.frame_communities.refresh_content()

    def showEvent(self, QShowEvent):
        """

        :param QShowEvent:
        :return:
        """
        self.frame_communities.refresh_content()
        self.status_label.setText("")

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super(HomeScreenWidget, self).changeEvent(event)


