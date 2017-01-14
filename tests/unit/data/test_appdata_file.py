from sakia.data.entities import AppData
from sakia.data.files import AppDataFile
import tempfile
import unittest
import os


class TestAppDataFile(unittest.TestCase):
    def test_init_save_load(self):
        file = os.path.join(tempfile.mkdtemp(), "params.json")
        app_data = AppData()
        app_data_file = AppDataFile(file)
        app_data.profiles.append("default")
        app_data_file.save(app_data)
        app_data_2 = app_data_file.load_or_init()
        self.assertEqual(app_data, app_data_2)
