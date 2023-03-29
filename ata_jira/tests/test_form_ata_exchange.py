from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase


@tagged('post_install', '-at_install', 'ata_exchange', 'form')
class TestFormExchange(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_admin = cls.env.ref('base.user_admin')

    def test_form(self):
        default_service = self.env.ref(
            'ata_jira.ata_jira_external_service_issue_updated')
        default_worklog_service = self.env.ref(
            'ata_jira.ata_jira_external_service_worklog')

        project_key = "TEST"

        exchange_form = Form(self.env['ata.exchange'])
        exchange_form.project_key = project_key
        test_exchange1 = exchange_form.save()
        msg_pfx = f"Exchange service {test_exchange1.service_id.name}"
        msg_sfx = f"is not equal default value {default_service.name}"
        self.assertEqual(
            test_exchange1.service_id.id,
            default_service.id,
            msg=f"{msg_pfx} {msg_sfx}")
        test_worklog_service_name = test_exchange1.worklog_service_id.name
        msg_pfx = f"Exchange worklog service {test_worklog_service_name}"
        msg_sfx = f"is not equal default value {default_worklog_service.name}"
        self.assertEqual(
            test_exchange1.worklog_service_id.id,
            default_worklog_service.id,
            msg=f"{msg_pfx} {msg_sfx}")
        self.assertEqual(
            test_exchange1.project_key,
            project_key,
            msg=f"""Project key {test_exchange1.project_key}
                is not equal test value {project_key}"""
        )
