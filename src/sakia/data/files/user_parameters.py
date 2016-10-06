import attr
import json
import os
import logging
from ..entities import UserParameters


@attr.s(frozen=True)
class UserParametersFile:
    """
    The repository for UserParameters
    """
    _file = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))
    filename = "parameters.json"

    @classmethod
    def in_config_path(cls, config_path, profile_name):
        return cls(os.path.join(config_path, profile_name, UserParametersFile.filename))

    def save(self, user_parameters):
        """
        Commit a user_parameters to the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to commit
        """
        with open(self._file, 'w') as outfile:
            json.dump(attr.asdict(user_parameters), outfile, indent=4)

    def load_or_init(self):
        """
        Update an existing user_parameters in the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to update
        """
        try:
            with open(self._file, 'r') as json_data:
                user_parameters = UserParameters(**json.load(json_data))
        except OSError:
            user_parameters = UserParameters()
        return user_parameters
