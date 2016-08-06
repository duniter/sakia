from PyQt5.QtCore import QObject


class ComponentModel(QObject):
    """
    An component
    """

    def __init__(self, parent):
        """
        Constructor of an component

        :param sakia.gui.component.controller.ComponentController parent: the controller
        """
        super().__init__(parent)
