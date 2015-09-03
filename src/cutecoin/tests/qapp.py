
_application_ = []


def get_application():
    """Get the singleton QApplication"""
    from PyQt5.QtWidgets import QApplication
    if not len(_application_):
        application = QApplication.instance()
        if not application:
            import sys
            application = QApplication(sys.argv)
        _application_.append( application )
    return _application_[0]

