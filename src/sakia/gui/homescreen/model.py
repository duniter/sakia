from sakia.gui.component.model import ComponentModel


class HomeScreenModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
