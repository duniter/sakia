from PyQt5.QtNetwork import QNetworkAccessManager
from PyQt5.QtCore import QUrl

class MockNetworkAccessManager(QNetworkAccessManager):
    def __init__(self):
        super().__init__()
        self.mock_path = ""

    def set_mock_path(self, mock_url):
        url = QUrl(mock_url)
        self.mock_path = url.path()

    def get(self, request):
        url = request.url()
        path = url.path()
        path = self.mock_path + path
        url.setPath(path)
        request.setUrl(url)
        return super().get(request)

    def post(self, request, post_data):
        url = request.url()
        path = url.path()
        path = self.mock_path + path
        url.setPath(path)
        request.setUrl(url)
        return super().post(request, post_data)