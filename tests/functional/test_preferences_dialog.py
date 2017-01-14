from sakia.gui.preferences import PreferencesDialog


def test_preferences_default(application):
    preferences_dialog = PreferencesDialog(application)
    assert preferences_dialog.combo_language.currentText() == application.parameters.lang
    assert preferences_dialog.combo_referential.currentIndex() == application.parameters.referential
    assert preferences_dialog.checkbox_expertmode.isChecked() == application.parameters.expert_mode
    assert preferences_dialog.checkbox_maximize.isChecked() == application.parameters.maximized
    assert preferences_dialog.checkbox_notifications.isChecked() == application.parameters.notifications
    assert preferences_dialog.checkbox_proxy.isChecked() == application.parameters.enable_proxy
    assert preferences_dialog.edit_proxy_address.text() == application.parameters.proxy_address
    assert preferences_dialog.spinbox_proxy_port.value() == application.parameters.proxy_port
