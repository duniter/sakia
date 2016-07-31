from PyQt5.QtWidgets import QTreeView, QSizePolicy


class NavigationView(QTreeView):
    """
    The view of navigation panel
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Expanding)