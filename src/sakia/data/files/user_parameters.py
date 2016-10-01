import attr
import json
from ..entities import UserParameters


@attr.s(frozen=True)
class UserParametersFile:
    """
    The repository for UserParameters
    """
    _file = attr.ib()

    def save(self, user_parameters):
        """
        Commit a user_parameters to the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to commit
        """
        with open(self._file, 'w') as outfile:
            json.dump(attr.asdict(user_parameters), outfile, indent=4)

    def load(self):
        """
        Update an existing user_parameters in the database
        :param sakia.data.entities.UserParameters user_parameters: the user_parameters to update
        """
        with open(self._file, 'r') as json_data:
            user_parameters = UserParameters(**json.load(json_data))
        return user_parameters