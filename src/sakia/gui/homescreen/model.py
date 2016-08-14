from sakia.gui.component.model import ComponentModel


class HomeScreenModel(ComponentModel):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    @property
    def account(self):
        return self.app.current_account