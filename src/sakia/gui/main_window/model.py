from sakia.gui.component.model import ComponentModel


class MainWindowModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

