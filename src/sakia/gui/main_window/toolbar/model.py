from PyQt5.QtCore import QObject
import attr


@attr.s()
class ToolbarModel(QObject):
    """
    The model of Navigation component

    :param sakia.app.Application app: the application
    :param sakia.gui.navigation.model.NavigationModel navigation_model: The navigation model
    """

    app = attr.ib()
    navigation_model = attr.ib()

    def __attrs_post_init__(self):
        super().__init__()

    async def send_join(self, connection, password):
        return await self.app.documents_service.send_membership(connection, password, "IN")
