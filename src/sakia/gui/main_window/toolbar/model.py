from sakia.gui.component.model import ComponentModel


class ToolbarModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
