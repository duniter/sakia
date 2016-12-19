from PyQt5.QtCore import QObject
import attr


@attr.s()
class ToolbarModel(QObject):
    """
    The model of Navigation component
    """

    app = attr.ib()
    navigation_model = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()
