"""
Created on 31 janv. 2015

@author: vit
"""

from PyQt5.QtWidgets import QWidget
from ..gen_resources.homescreen_uic import Ui_HomeScreenWidget
from ..__init__ import __version__


class HomeScreenWidget(QWidget, Ui_HomeScreenWidget):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)

        latest = app.latest_version()
        version_info = ""
        version_url = ""
        if not latest[0]:
            version_info = "Please get the latest release {version}" \
                            .format(version='.'.join(latest[1]))
            version_url = latest[2]

        self.label_welcome.setText(
            """
            <h1>Welcome to Cutecoin {version}</h1>
            <h2>{version_info}</h2>
            <h3><a href={version_url}>Download link</a></h3>
            """.format(version=__version__,
                       version_info=version_info,
                       version_url=version_url))
