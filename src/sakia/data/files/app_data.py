import attr
import json
import os
import logging
from ..entities import AppData


@attr.s(frozen=True)
class AppDataFile:
    """
    The repository for AppData
    """
    _file = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))
    filename = "appdata.json"

    @classmethod
    def in_config_path(cls, config_path):
        return cls(os.path.join(config_path, AppDataFile.filename))

    def save(self, app_data):
        """
        Commit a app_data to the database
        :param sakia.data.entities.AppData app_data: the app_data to commit
        """
        with open(self._file, 'w') as outfile:
            json.dump(attr.asdict(app_data), outfile, indent=4)

    def load_or_init(self):
        """
        Update an existing app_data in the database
        :param sakia.data.entities.AppData app_data: the app_data to update
        """
        try:
            with open(self._file, 'r') as json_data:
                app_data = AppData(**json.load(json_data))
        except OSError:
            app_data = AppData()
        return app_data
