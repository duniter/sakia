import attr
import json
from ..entities import AppData


@attr.s(frozen=True)
class AppDataFile:
    """
    The repository for AppData
    """
    _file = attr.ib()

    def save(self, app_data):
        """
        Commit a app_data to the database
        :param sakia.data.entities.AppData app_data: the app_data to commit
        """
        with open(self._file, 'w') as outfile:
            json.dump(attr.asdict(app_data), outfile, indent=4)

    def load(self):
        """
        Update an existing app_data in the database
        :param sakia.data.entities.AppData app_data: the app_data to update
        """
        with open(self._file, 'r') as json_data:
            app_data = AppData(**json.load(json_data))
        return app_data
