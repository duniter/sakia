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
        if not os.path.exists(os.path.join(config_path, profile_name)):
            os.makedirs(os.path.join(config_path, profile_name))
        return cls(os.path.join(config_path, profile_name, UserParametersFile.filename))

    def save(self, user_parameters):
        """
        Commit a user_parameters to the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to commit
        """
        if not os.path.exists(os.path.abspath(os.path.join(self._file, os.pardir))):
            os.makedirs(os.path.abspath(os.path.join(self._file, os.pardir)))
        with open(self._file, 'w') as outfile:
            json.dump(attr.asdict(user_parameters), outfile, indent=4)
        return user_parameters

    def load_or_init(self, profile_name):
        """
        Update an existing user_parameters in the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to update
        """
        try:
            with open(self._file, 'r') as json_data:
                user_parameters = UserParameters(**json.load(json_data))
                user_parameters.profile_name = profile_name
        except (OSError, json.decoder.JSONDecodeError):
            user_parameters = UserParameters(profile_name=profile_name)
        return user_parameters
