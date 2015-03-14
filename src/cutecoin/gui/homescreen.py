"""
Created on 31 janv. 2015

@author: vit
"""

from PyQt5.QtWidgets import QWidget
from ..gen_resources.homescreen_uic import Ui_HomeScreenWidget


class HomeScreenWidget(QWidget, Ui_HomeScreenWidget):
    """
    classdocs
    """

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
