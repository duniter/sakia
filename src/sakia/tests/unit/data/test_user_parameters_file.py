from sakia.data.entities import UserParameters
from sakia.data.files import UserParametersFile
import tempfile
import unittest
import os


class TestUserParametersFile(unittest.TestCase):
    def test_init_save_load(self):
        file = os.path.join(tempfile.mkdtemp(), "params.json")
        user_parameters = UserParameters()
        user_parameters_file = UserParametersFile(file)
        user_parameters.proxy_address = "test.fr"
        user_parameters_file.save(user_parameters)
        user_parameters_2 = user_parameters_file.load()
        self.assertEqual(user_parameters, user_parameters_2)
