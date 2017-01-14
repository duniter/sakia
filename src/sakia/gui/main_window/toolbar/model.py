from PyQt5.QtCore import QObject
from sakia.data.processors import ConnectionsProcessor
import attr
from sakia import __version__


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

    def notifications(self):
        return self.app.parameters.notifications

    def connections_with_uids(self):
        return ConnectionsProcessor.instanciate(self.app).connections_with_uids()

    def connections(self):
        return ConnectionsProcessor.instanciate(self.app).connections()

    def about_text(self):
        latest = self.app.available_version
        version_info = ""
        version_url = ""
        if not latest[0]:
            version_info = "Latest release : {version}" \
                            .format(version=latest[1])
            version_url = latest[2]

        new_version_text = """
            <p><b>{version_info}</b></p>
            <p><a href={version_url}>Download link</a></p>
            """.format(version_info=version_info,
                       version_url=version_url)
        return """
        <h1>Sakia</h1>

        <p>Python/Qt Duniter client</p>

        <p>Version : {:}</p>
        {new_version_text}

        <p>License : GPLv3</p>

        <p><b>Authors</b></p>

        <p>inso</p>
        <p>vit</p>
        <p>canercandan</p>
        <p>Moul</p>
        """.format(__version__,
                   new_version_text=new_version_text)