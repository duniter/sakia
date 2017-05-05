from PyQt5.QtCore import QObject
from sakia.money import Referentials


class StatusBarModel(QObject):
    """
    The model of status bar component
    """

    def __init__(self, parent, app, blockchain_processor):
        """
        The status bar model
        :param parent:
        :param sakia.app.Application app: the app
        :param sakia.data.processors.BlockchainProcessor blockchain_processor:
        """
        super().__init__(parent)
        self.app = app
        self.blockchain_processor = blockchain_processor

    def referentials(self):
        return Referentials

    def default_referential(self):
        return self.app.parameters.referential

    def current_block(self):
        return self.blockchain_processor.current_buid(self.app.currency)

    def current_time(self):
        time = self.blockchain_processor.time(self.app.currency)
        return self.blockchain_processor.adjusted_ts(self.app.currency, time)

