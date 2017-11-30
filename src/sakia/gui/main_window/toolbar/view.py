from PyQt5.QtWidgets import QFrame, QAction, QMenu, QSizePolicy, QInputDialog, QDialog, \
    QVBoxLayout, QTabWidget, QWidget, QLabel
from sakia.gui.widgets.dialogs import dialog_async_exec
from PyQt5.QtCore import QObject, QT_TRANSLATE_NOOP, Qt, QLocale
from .toolbar_uic import Ui_SakiaToolbar
from .about_uic import Ui_AboutPopup
from .about_money_uic import Ui_AboutMoney
from .about_wot_uic import Ui_AboutWot
from sakia.helpers import timestamp_to_dhms, dpi_ratio


class ToolbarView(QFrame, Ui_SakiaToolbar):
    """
    The model of Navigation component
    """
    _action_revoke_uid_text = QT_TRANSLATE_NOOP("ToolbarView", "Publish a revocation document")

    def __init__(self, parent):
        super().__init__(parent)
        self.setupUi(self)

        tool_menu = QMenu(self.tr("Tools"), self.toolbutton_menu)
        self.toolbutton_menu.setMenu(tool_menu)

        self.action_add_connection = QAction(self.tr("Add a connection"), tool_menu)
        tool_menu.addAction(self.action_add_connection)

        self.action_revoke_uid = QAction(self.tr(ToolbarView._action_revoke_uid_text), self)
        tool_menu.addAction(self.action_revoke_uid)

        self.action_parameters = QAction(self.tr("Settings"), tool_menu)
        tool_menu.addAction(self.action_parameters)

        self.action_plugins = QAction(self.tr("Plugins manager"), tool_menu)
        tool_menu.addAction(self.action_plugins)

        tool_menu.addSeparator()

        about_menu = QMenu(self.tr("About"), tool_menu)
        tool_menu.addMenu(about_menu)

        self.action_about_money = QAction(self.tr("About Money"), about_menu)
        about_menu.addAction(self.action_about_money)

        self.action_about_referentials = QAction(self.tr("About Referentials"), about_menu)
        about_menu.addAction(self.action_about_referentials)

        self.action_about_wot = QAction(self.tr("About Web of Trust"), about_menu)
        about_menu.addAction(self.action_about_wot)

        self.action_about = QAction(self.tr("About Sakia"), about_menu)
        about_menu.addAction(self.action_about)

        self.action_exit = QAction(self.tr("Exit"), tool_menu)
        tool_menu.addAction(self.action_exit)

        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum)
        self.setMaximumHeight(60)
        self.button_network.setIconSize(self.button_network.iconSize()*dpi_ratio())
        self.button_contacts.setIconSize(self.button_contacts.iconSize()*dpi_ratio())
        self.button_identity.setIconSize(self.button_identity.iconSize()*dpi_ratio())
        self.button_explore.setIconSize(self.button_explore.iconSize()*dpi_ratio())
        self.toolbutton_menu.setIconSize(self.toolbutton_menu.iconSize()*dpi_ratio())
        self.button_network.setFixedHeight(self.button_network.height()*dpi_ratio()+5*dpi_ratio())
        self.button_contacts.setFixedHeight(self.button_contacts.height()*dpi_ratio()+5*dpi_ratio())
        self.button_identity.setFixedHeight(self.button_identity.height()*dpi_ratio()+5*dpi_ratio())
        self.button_explore.setFixedHeight(self.button_explore.height()*dpi_ratio()+5*dpi_ratio())
        self.toolbutton_menu.setFixedHeight(self.toolbutton_menu.height()*dpi_ratio()+5*dpi_ratio())

    async def ask_for_connection(self, connections):
        connections_titles = [c.title() for c in connections]
        input_dialog = QInputDialog()
        input_dialog.setComboBoxItems(connections_titles)
        input_dialog.setWindowTitle(self.tr("Membership"))
        input_dialog.setLabelText(self.tr("Select a connection"))
        await dialog_async_exec(input_dialog)
        result = input_dialog.textValue()

        if input_dialog.result() == QDialog.Accepted:
            for c in connections:
                if c.title() == result:
                    return c

    def show_about_wot(self, params):
        """
        Set wot text from currency parameters
        :param sakia.data.entities.BlockchainParameters params: Parameters of the currency
        :return:
        """
        dialog = QDialog(self)
        about_dialog = Ui_AboutWot()
        about_dialog.setupUi(dialog)

        # set infos in label
        about_dialog.label_wot.setText(
            self.tr("""
            <table cellpadding="5">
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
<tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
</table>
""").format(
                QLocale().toString(params.sig_period / 86400, 'f', 2),
                self.tr('Minimum delay between 2 certifications (in days)'),
                QLocale().toString(params.sig_validity / 86400, 'f', 2),
                self.tr('Maximum age of a valid signature (in days)'),
                params.sig_qty,
                self.tr('Minimum quantity of signatures to be part of the WoT'),
                params.sig_stock,
                self.tr('Maximum quantity of active certifications made by member.'),
                params.sig_window,
                self.tr('Maximum delay a certification can wait before being expired for non-writing.'),
                params.xpercent,
                self.tr('Minimum percent of sentries to reach to match the distance rule'),
                params.ms_validity / 86400,
                self.tr('Maximum age of a valid membership (in days)'),
                params.step_max,
                self.tr('Maximum distance between each WoT member and a newcomer'),
            )
        )
        dialog.setWindowTitle(self.tr("Web of Trust rules"))
        dialog.exec()

    def show_about_money(self, params, currency, localized_data):
        dialog = QDialog(self)
        about_dialog = Ui_AboutMoney()
        about_dialog.setupUi(dialog)
        about_dialog.label_general.setText(self.general_text(localized_data))
        about_dialog.label_rules.setText(self.rules_text(localized_data))
        about_dialog.label_money.setText(self.money_text(params, currency))
        dialog.setWindowTitle(self.tr("Money rules"))
        dialog.exec()

    def show_about_referentials(self, referentials):
        dialog = QDialog(self)
        layout = QVBoxLayout(dialog)
        tabwidget = QTabWidget(dialog)
        layout.addWidget(tabwidget)
        for ref in referentials:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            label = QLabel()
            label.setText(self.text_referential(ref))
            layout.addWidget(label)
            tabwidget.addTab(widget, ref.translated_name())
        dialog.setWindowTitle(self.tr("Referentials"))
        dialog.exec()

    def general_text(self, localized_data):
        """
        Fill the general text with given informations
        :return:
        """
        # set infos in label
        return self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></div></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:2.2%} / {:} days</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                localized_data.get('ud', '####'),
                self.tr('Universal Dividend UD(t) in'),
                localized_data['diff_units'],
                localized_data.get('mass', "###"),
                self.tr('Monetary Mass M in'),
                localized_data['units'],
                localized_data.get('members_count', '####'),
                self.tr('Members N'),
                localized_data.get('mass_minus_1_per_member', '####'),
                self.tr('Monetary Mass per member M(t-1)/N(t-1) in'),
                localized_data['diff_units'],
                localized_data.get('actual_growth', 0),
                localized_data.get('days_per_dividend', '####'),
                self.tr('Actual growth c = UD(t)/[M(t-1)/N(t)]'),
                localized_data.get('ud_median_time_minus_1', '####'),
                self.tr('Penultimate UD date and time (t-1)'),
                localized_data.get('ud_median_time', '####') + " BAT",
                self.tr('Last UD date and time (t)'),
                localized_data.get('next_ud_median_time', '####') + " BAT",
                self.tr('Next UD date and time (t+1)'),
                localized_data.get('next_ud_reeval', '####') + " BAT",
                self.tr('Next UD reevaluation (t+1)')
            )

    def rules_text(self, localized_data):
        """
        Set text in rules
        :param dict localized_data:
        :return:
        """
        # set infos in label
        return self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                self.tr('{:2.2%} / {:} days').format(localized_data['growth'], localized_data['days_per_dividend']),
                self.tr('Fundamental growth (c) / Delta time (dt)'),
                self.tr('UDĞ(t) = UDĞ(t-1) + c²*M(t-1)/N(t-1)'),
                self.tr('Universal Dividend (formula)'),
                self.tr('{:} = {:} + {:2.2%}² * {:} / {:}').format(
                    localized_data.get('ud_plus_1', '####'),
                    localized_data.get('ud', '####'),
                    localized_data.get('growth', '####'),
                    localized_data.get('mass_minus_1', '####'),
                    localized_data.get('members_count_minus_1', '####')
                ),
                self.tr('Universal Dividend (computed)')
            )

    def text_referential(self, ref):
        """
        Set text from referentials
        """
        # set infos in label
        ref_template = """
                <table cellpadding="5">
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                <tr><th>{:}</th><td>{:}</td></tr>
                </table>
                """
        return ref_template.format(self.tr('Name'), ref.translated_name(),
                                                 self.tr('Units'), ref.units,
                                                 self.tr('Formula'), ref.formula,
                                                 self.tr('Description'), ref.description
                                                 )

    def money_text(self, params, currency):
        """
        Set text from money parameters
        :param sakia.data.entities.BlockchainParameters params: Parameters of the currency
        :param str currency: The currency
        """

        dt_dhms = timestamp_to_dhms(params.dt)
        if dt_dhms[0] > 0:
            dt_as_str = self.tr("{:} day(s) {:} hour(s)").format(*dt_dhms)
        else:
            dt_as_str = self.tr("{:} hour(s)").format(dt_dhms[1])
        if dt_dhms[2] > 0 or dt_dhms[3] > 0:
            dt_dhms += ", {:} minute(s) and {:} second(s)".format(*dt_dhms[1:])
        dt_reeval_dhms = timestamp_to_dhms(params.dt_reeval)
        dt_reeval_as_str = self.tr("{:} day(s) {:} hour(s)").format(*dt_reeval_dhms)

        # set infos in label
        return self.tr("""
            <table cellpadding="5">
            <tr><td align="right"><b>{:2.2%} / {:} days</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:} {:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:}</b></td><td>{:}</td></tr>
            <tr><td align="right"><b>{:2.0%}</b></td><td>{:}</td></tr>
            </table>
            """).format(
                params.c,
                QLocale().toString(params.dt / 86400, 'f', 2),
                self.tr('Fundamental growth (c)'),
                params.ud0,
                self.tr('Initial Universal Dividend UD(0) in'),
                currency,
                dt_as_str,
                self.tr('Time period between two UD'),
                dt_reeval_as_str,
                self.tr('Time period between two UD reevaluation'),
                params.median_time_blocks,
                self.tr('Number of blocks used for calculating median time'),
                params.avg_gen_time,
                self.tr('The average time in seconds for writing 1 block (wished time)'),
                params.dt_diff_eval,
                self.tr('The number of blocks required to evaluate again PoWMin value'),
                params.percent_rot,
                self.tr('The percent of previous issuers to reach for personalized difficulty')
            )

    def show_about(self, text):
        dialog = QDialog(self)
        about_dialog = Ui_AboutPopup()
        about_dialog.setupUi(dialog)
        about_dialog.label.setText(text)
        dialog.exec()
