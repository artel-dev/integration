import base64
from datetime import datetime
import json
import logging
import re
import requests
from requests.auth import HTTPBasicAuth

from odoo import api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class Exchange(models.TransientModel):
    """
    Wizard exchange does the operations:
    - create requests
    - execute requests
    - read data from responses
    - create or update users, projects, tasks, timesheets
    """
    _name = 'ata.exchange'
    _description = 'Exchange'

    name = fields.Char()
    system_id = fields.Many2one(
        comodel_name='ata.external.system',
        related='service_id.system_id'
    )
    service_id = fields.Many2one(
        comodel_name='ata.external.service'
    )
    worklog_service_id = fields.Many2one(
        comodel_name='ata.external.service'
    )
    from_date = fields.Date()
    to_date = fields.Date()
    project_key = fields.Char()
    reporter_id = fields.Many2one(comodel_name='res.users')
    assignee_id = fields.Many2one(comodel_name='res.users')
    request_ids = fields.One2many(
        comodel_name='ata.external.request',
        inverse_name='exchange_id'
    )
    jira_issue_ids = fields.One2many(
        comodel_name='ata.jira.issue',
        inverse_name='exchange_id'
    )
    jira_worklog_ids = fields.One2many(
        comodel_name='ata.jira.worklog',
        inverse_name='exchange_id'
    )
    jira_comment_ids = fields.One2many(
        comodel_name='ata.jira.comment',
        inverse_name='exchange_id'
    )

    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        vals['service_id'] = self.env.ref(
            'ata_jira.ata_jira_external_service_issue_updated').id
        vals['worklog_service_id'] = self.env.ref(
            'ata_jira.ata_jira_external_service_worklog').id
        return vals

    @staticmethod
    def base64encodestring(s: str):
        return base64.b64encode(s.encode('ascii')).decode()

    @staticmethod
    def get_date_iso(date_str: str):
        date_str = date_str.split('.')[0]
        return datetime.fromisoformat(date_str)

    @staticmethod
    def get_selected_fields():
        selected_fields = [
            'id',
            'key',
            'self',
            'updated',
            'created',
            'status',
            'creator',
            'reporter',
            'issuetype',
            'description',
            'summary',
            'assignee',
            'comment',
            'worklog',
            'timetracking',
            'resolutiondate',
            'priority',
            'project',
            'parent',
            'customfield_10101',
            'customfield_10103',
            ]
        return selected_fields

    def get_image_from_url(self, url):
        """
        :return: Returns a base64 encoded string.
        """
        image_data = ""
        try:

            ext_system = self.system_id
            login = ext_system.login
            password = ext_system.password
            is_token_authentication = ext_system.is_token_authentication

            params = ''

            # calculate headers and auth
            headers = {
                'Content-Type': 'image/png'
            }
            auth = False
            if is_token_authentication and password:
                headers['Authorization'] = f'Bearer {password}'
            elif login and password:
                auth_header = "Basic " + self.base64encodestring(
                    f'{login}:{password}')
                headers['Authorization'] = auth_header
                auth = HTTPBasicAuth(username=login, password=password)

            timeout = 60

            # execute request
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                auth=auth,
                timeout=timeout
            )

            if response.status_code == 200:
                image_data = base64.b64encode(
                    response.content).replace(b"\n", b"")

        except Exception as e:
            _logger.warning(f"Can’t load the image from URL {url}")
            logging.exception(e)
        return image_data

    @api.model
    def get_user(self, name, email, avatar):
        user_manager = self.env['res.users']
        if not (name and email):
            return user_manager
        domain = [('email', '=', email)]
        user_vals = {
            'name': name,
            'login': email,
            'email': email,
            'image_1920': avatar,
        }
        user_recordset = user_manager.search(domain)
        if user_recordset:
            user = user_recordset[0]
            user.write(user_vals)
        else:
            user = user_manager.create(user_vals)
        return user

    @api.model
    def get_resource(self, user):
        domain = [('user_id', '=', user.id)]
        resource_vals = {
            'name': user.name,
            'user_id': user.id,
            'resource_type': 'user',
        }
        resource_manager = self.env['resource.resource']
        resource_recordset = resource_manager.search(domain)
        if resource_recordset:
            resource = resource_recordset[0]
        else:
            resource = resource_manager.create(resource_vals)
        return resource

    @api.model
    def get_employee(self, name, email, avatar):
        user = self.get_user(name, email, avatar)
        resource = self.get_resource(user)

        employee_domain = [('work_email', '=', email)]
        employee_vals = {
            'work_email': email,
            'resource_id': resource.id,
            'employee_type': 'employee',
        }
        employee_manager = self.env['hr.employee']
        employee_recordset = employee_manager.search(employee_domain)
        if employee_recordset:
            employee = employee_recordset[0]
        else:
            employee = employee_manager.create(employee_vals)
        return employee

    def import_jira_data(self):
        self.ensure_one()

        # Create requests
        self.clear_requests()
        self.create_requests(self.service_id)

        # Execute requests
        self.execute_requests()

        # Read data
        self.clear_data()
        self.read_data()

        # self.find_tasks()
        # self.create_update_tasks()

        exchange_action = {
            'type': 'ir.actions.act_window',
            'name': 'Exchange with Jira',
            'res_model': 'ata.exchange',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self['id'],
        }

        return exchange_action

    def clear_requests(self, issue_id=''):
        # clear current requests
        domain = [('exchange_id', '=', self['id'])]
        if issue_id:
            domain.append(('issue_id', '=', issue_id))
        request_manager = self.env['ata.external.request']
        request_recordset = request_manager.search(domain)
        request_recordset.unlink()

    def create_requests(self, ext_service, issue_id=0):
        request_manager = self.env['ata.external.request']
        method_name, params = self.get_request_parameters(
            ext_service, issue_id)
        vals = {
            'name': f'ex_id: {self["id"]}, service: {ext_service.name}',
            'exchange_id': self['id'],
            'issue_id': issue_id,
            'system_id': self.system_id.id,
            'service_id': ext_service.id,
            'method_name': method_name,
            'parameters': params,
            'result': '',
            'headers': '',
            'create_date': datetime.now(),
            'is_executed': False,
            'execution_date': False,
            'is_processed': False,
            'processing_date': False,
            'number_of_attempts': 0,
        }
        result = request_manager.create(vals)
        return result

    def get_request_parameters(self, ext_service, issue_id=0):
        method_name = ext_service.method_name
        inline_params = re.findall(r'{(.+?)}', method_name)

        params_dict, inline_params_dict = self.get_service_parameters(
            ext_service, issue_id, inline_params)

        for inline_param_name in inline_params:
            method_name = method_name.replace(
                '{' + inline_param_name + '}',
                inline_params_dict.get(inline_param_name, ''))

        if self.service_id.http_method == 'GET':
            params = ''
            for (key, value) in params_dict.items():
                delimiter = '&' if params else ''
                params += f'{delimiter}{key}={value}'
        else:
            params = json.dumps(params_dict)
        return method_name, params

    def get_service_parameters(self, ext_service, issue_id, inline_params):
        params_dict = dict()
        inline_params_dict = dict()

        parameter_manager = self.env['ata.external.service.parameter']
        domain = [('service_id', '=', ext_service.id)]
        parameter_recordset = parameter_manager.search(domain)
        for parameter in parameter_recordset:
            param_value = self.get_parameter_value(
                parameter.name, parameter.value, issue_id)
            if inline_params and parameter.name in inline_params:
                inline_params_dict[parameter.name] = param_value
            else:
                params_dict[parameter.name] = param_value
        return params_dict, inline_params_dict

    def get_parameter_value(
            self, parameter_name, parameter_value=None, issue_id=0):
        parameter_value = parameter_value or ''
        date_fmt = '%Y/%m/%d %H:%M'
        if parameter_name == 'updated1':
            value = self.from_date.strftime(date_fmt)
        elif parameter_name == 'updated2':
            value = self.to_date.strftime(date_fmt)
        elif parameter_name == 'ProjectKey':
            value = self.project_key
        elif parameter_name == 'fields':
            # value = ['*all'] can be also *all/navigable/WithoutSelected
            value = self.get_selected_fields()
        elif parameter_name == 'id':
            value = issue_id
        else:
            value = parameter_value
            sub_parameters = re.findall(r'{(.+?)}', parameter_value)
            for sub_parameter_name in sub_parameters:
                sub_parameter_value = self.get_parameter_value(
                    sub_parameter_name)
                value = value.replace(
                    '{' + sub_parameter_name + '}', sub_parameter_value)
        return value

    def execute_requests(self, issue_id=0):
        domain = [('exchange_id', '=', self['id'])]
        if issue_id:
            domain.append(('issue_id', '=', issue_id))
        request_manager = self.env['ata.external.request']
        request_recordset = request_manager.search(domain)
        for ext_request in request_recordset:
            self.execute_request(ext_request)

    @api.model
    def execute_request(self, ext_request):
        # source data for request
        ext_service = ext_request.service_id
        params = ext_request.parameters

        http_method = ext_service.http_method

        timeout = 60

        if http_method not in ['GET', 'POST']:
            msg_prefix = f'External service {ext_service.name}:'
            msg = f'{msg_prefix} unknown HTTP method {http_method}'
            raise UserError(msg)

        url = self.get_url(ext_request)
        headers, auth = self.get_headers_auth(ext_request)

        start_date = datetime.now()

        # execute request
        if http_method == 'GET':
            response = requests.get(
                url=url,
                params=params,
                headers=headers,
                auth=auth,
                timeout=timeout
            )
        elif http_method == 'POST':
            response = requests.post(
                url=url,
                data=params,
                headers=headers,
                auth=auth,
                timeout=timeout
            )
        else:
            return False

        finish_date = datetime.now()

        vals = {
            'status_code': response.status_code,
            'result': response.text,
            'headers': response.headers,
            'is_executed': True,
            'execution_date': datetime.now(),
            'number_of_attempts': ext_request.number_of_attempts + 1
        }

        ext_request.write(vals)

        self.create_exchange_log(
            ext_request,
            url=url,
            start_date=start_date,
            finish_date=finish_date
            )

        return True

    def create_exchange_log(self, ext_request, **kwargs):
        ext_system = ext_request.system_id
        ext_service = ext_request.service_id

        url = kwargs.get('url', '')
        start_date = kwargs.get('start_date')
        finish_date = kwargs.get('finish_date')

        exchange_log_manager = self.env['ata.exchange.log']
        log_vals = {
            'name': f'ex_id: {self["id"]}, service: {ext_service.name}',
            'service_id': ext_service.id,
            'server_address': ext_system.server_address,
            'server_port': ext_system.server_port,
            'method_name': ext_request.method_name,
            'parameters': ext_request.parameters,
            'request': url,
            'response': ext_request.result,
            'headers': ext_request.headers,
            'status_code': ext_request.status_code,
            'start_date': start_date,
            'finish_date': finish_date,
        }
        exchange_log_manager.create(log_vals)

    @api.model
    def get_url(self, ext_request, method_name=''):
        ext_system = ext_request.system_id
        if not method_name:
            method_name = ext_request.method_name

        server_address = ext_system.server_address
        server_port = ext_system.server_port
        is_secure_connection = ext_system.is_secure_connection

        # calculate url
        http_protocol = 'http' + ('s' if is_secure_connection else '')
        url_http_protocol = ''
        if not server_address.startswith('http'):
            url_http_protocol = f'{http_protocol}://'
        url_port = f':{server_port}' if server_port else ''
        method_name_prefix = '' if method_name.startswith('/') else '/'
        url_method_name = f'{method_name_prefix}{method_name}'
        url = f'{url_http_protocol}{server_address}{url_port}{url_method_name}'

        return url

    def get_headers_auth(self, ext_request):
        # source data for request
        ext_system = ext_request.system_id
        ext_service = ext_request.service_id

        login = ext_system.login
        password = ext_system.password
        is_token_authentication = ext_system.is_token_authentication

        method_name = ext_service.method_name

        # calculate headers and auth
        headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        auth = False
        apikey_not_in_method = (method_name.find('apikey') == -1)
        if is_token_authentication and password and apikey_not_in_method:
            headers['Authorization'] = f'Bearer {password}'
        elif login and password:
            auth_header = "Basic " + self.base64encodestring(
                f'{login}:{password}')
            headers['Authorization'] = auth_header
            auth = HTTPBasicAuth(username=login, password=password)
        return headers, auth

    def clear_data(self):
        domain = [('exchange_id', '=', self['id'])]

        jira_issue_manager = self.env['ata.jira.issue']
        jira_issue_recordset = jira_issue_manager.search(domain)
        jira_issue_recordset.unlink()

        jira_worklog_manager = self.env['ata.jira.worklog']
        jira_worklog_recordset = jira_worklog_manager.search(domain)
        jira_worklog_recordset.unlink()

        jira_comment_manager = self.env['ata.jira.comment']
        jira_comment_recordset = jira_comment_manager.search(domain)
        jira_comment_recordset.unlink()

    def read_data(self):
        domain = [('exchange_id', '=', self['id'])]
        request_manager = self.env['ata.external.request']
        request_recordset = request_manager.search(domain)
        for ext_request in request_recordset:
            self.read_request(ext_request)

    def read_request(self, ext_request):
        if not ext_request.is_executed:
            return
        if not ext_request.status_code == 200:
            return
        if not ext_request.result:
            return

        browse_link_prefix = self.get_url(ext_request, '/browse/')
        result_dict = json.loads(ext_request.result)
        issues = result_dict.get("issues", [])
        self.read_issues(issues, browse_link_prefix)

        vals = {
            'is_processed': True,
            'processing_date': datetime.now()
        }
        ext_request.write(vals)

    def read_issues(self, issues, browse_link_prefix):
        read_result = dict()
        if not issues:
            return read_result

        jira_issue_manager = self.env['ata.jira.issue']

        for issue in issues:
            issue_values = self.get_issue_values(issue)  # , browse_link_prefix
            if not issue_values:
                continue
            issue_id = issue.get('id')
            issue_fields = issue.get('fields')

            issue_worklog = issue_fields.get("worklog")
            issue_values["worklog_total"] = 0
            if issue_worklog:
                issue_values["worklog_total"] = issue_worklog.get("total", 0)

            issue_comment = issue_fields.get("comment")
            issue_values["comment_total"] = 0
            if issue_comment:
                issue_values["comment_total"] = issue_comment.get("total", 0)
            try:
                read_result["jira_issue_record"] = jira_issue_manager.create(
                    issue_values)
            except ValueError:
                raise ValueError('Value error: %s' % issue_values)

            read_result["jira_worklog_records"] = self.read_worklog(
                issue_worklog, issue_id)

            read_result["jira_comment_records"] = self.read_comment(
                issue_comment, issue_id, browse_link_prefix)

        return read_result

    def get_issue_values(self, issue):  # , browse_link_prefix
        issue_values = dict()
        issue_fields = issue.get('fields')
        if not issue_fields:
            return issue_values
        issue_values["exchange_id"] = self['id']
        issue_values["issue_key"] = issue["key"]
        issue_values["issue_id"] = issue["id"]
        # issue_values["self"] = issue["self"]
        issue_values["summary"] = issue_fields["summary"]
        issue_values["description"] = issue_fields["description"]

        issue_values["created_date"] = self.get_date_iso(
            issue_fields["created"])
        issue_values["updated_date"] = self.get_date_iso(
            issue_fields["updated"])
        if issue_fields.get("resolutiondate"):
            issue_values["resolution_date"] = self.get_date_iso(
                issue_fields["resolutiondate"])

        # issue_values["browse_link"] = f'{browse_link_prefix}{issue["key"]}'
        if issue_fields.get("status"):
            issue_values["status_name"] = issue_fields["status"]["name"]
        if issue_fields.get("issuetype"):
            issue_type = issue_fields["issuetype"]
            issue_values["issue_type_name"] = issue_type.get("name")
        if issue_fields.get("creator"):
            creator = issue_fields["creator"]
            issue_values["creator_name"] = creator.get("displayName")
            issue_values["creator_email"] = creator.get("emailAddress")
            if creator.get("avatarUrls"):
                avatar_url = creator["avatarUrls"]["48x48"]
                issue_values["creator_avatar"] = self.get_image_from_url(
                    avatar_url)
        if issue_fields.get("reporter"):
            reporter = issue_fields["reporter"]
            issue_values["reporter_name"] = reporter.get("displayName")
            issue_values["reporter_email"] = reporter.get("emailAddress")
        if issue_fields.get("assignee"):
            assignee = issue_fields["assignee"]
            issue_values["assignee_name"] = assignee.get("displayName")
            issue_values["assignee_email"] = assignee.get("emailAddress")
            if assignee.get("avatarUrls"):
                avatar_url = assignee["avatarUrls"]["48x48"]
                issue_values["assignee_avatar"] = self.get_image_from_url(
                    avatar_url)
        if issue_fields.get("timetracking"):
            time_tracking = issue_fields["timetracking"]
            issue_values["original_estimate"] = time_tracking.get(
                "originalEstimateSeconds", 0) / 3600
            issue_values["remaining_estimate"] = time_tracking.get(
                "remainingEstimateSeconds", 0) / 3600
            issue_values["time_spent"] = time_tracking.get(
                "timeSpentSeconds", 0) / 3600
        if issue_fields.get("project"):
            project = issue_fields["project"]
            issue_values["project_key"] = project.get("key")
            issue_values["project_name"] = project.get("name")
        # if issue_fields.get("parent"):
        #     parent = issue_fields["parent"]
        #     issue_values["parent_id"] = parent.get("id")
        #     issue_values["parent_key"] = parent.get("key")
        if issue_fields.get("priority"):
            priority = issue_fields["priority"]
            issue_values["priority"] = priority.get("name")
        # if issue_fields.get("customfield_10101"):
        #     issue_values["epic_key"] = issue_fields["customfield_10101"]
        # if issue_fields.get("customfield_10103"):
        #     issue_values["epic_name"] = issue_fields["customfield_10103"]

        return issue_values

    def read_worklog(self, issue_worklog, issue_id):
        jira_worklog_records = []
        if not issue_worklog:
            return jira_worklog_records

        jira_worklog_manager = self.env['ata.jira.worklog']

        worklog_total = issue_worklog.get("total")
        max_results = issue_worklog.get("maxResults")
        worklogs = issue_worklog.get("worklogs", [])

        if max_results and worklog_total > max_results:
            self.clear_requests(issue_id)
            self.create_requests(self.worklog_service_id, issue_id)
            self.execute_requests(issue_id)
            worklogs = self.get_issue_worklogs(issue_id)

        if not worklogs:
            return jira_worklog_records

        for worklog in worklogs:
            worklog_values = self.get_worklog_values(worklog, issue_id)

            jira_worklog_record = jira_worklog_manager.create(worklog_values)
            jira_worklog_records.append(jira_worklog_record)

        return jira_worklog_records

    def get_issue_worklogs(self, issue_id):
        worklogs = []

        domain = [
            ('exchange_id', '=', self['id']),
            ('issue_id', '=', issue_id)
        ]
        request_manager = self.env['ata.external.request']
        request_recordset = request_manager.search(domain)
        for ext_request in request_recordset:
            if not ext_request.is_executed:
                continue
            if not ext_request.status_code == 200:
                continue
            if not ext_request.result:
                continue

            result_dict = json.loads(ext_request.result)
            worklogs = result_dict.get("worklogs", [])
            if worklogs:
                break

        return worklogs

    @api.model
    def get_worklog_values(self, worklog, issue_id):
        author = worklog.get("author")
        update_author = worklog.get("updateAuthor")

        worklog_values = dict()
        worklog_values["exchange_id"] = self['id']
        worklog_values["worklog_id"] = worklog.get("id")
        worklog_values["issue_id"] = issue_id
        worklog_values["comment"] = worklog.get("comment")
        worklog_values["time_spent"] = worklog.get(
            "timeSpentSeconds", 0) / 3600
        worklog_values["created_date"] = self.get_date_iso(
            worklog.get("created"))
        worklog_values["updated_date"] = self.get_date_iso(
            worklog.get("updated"))
        worklog_values["started_date"] = self.get_date_iso(
            worklog.get("started"))
        worklog_values["author_name"] = author.get("name")
        worklog_values["author_display_name"] = author.get("displayName")
        worklog_values["author_email"] = author.get("emailAddress")
        if author.get("avatarUrls"):
            avatar_url = author["avatarUrls"]["48x48"]
            worklog_values["author_avatar"] = self.get_image_from_url(
                avatar_url)

        worklog_values["update_author_name"] = update_author.get("name")
        worklog_values["update_author_display_name"] = update_author.get(
            "displayName")
        worklog_values["update_author_email"] = update_author.get(
            "emailAddress")

        return worklog_values

    def read_comment(self, issue_comment, issue_id, browse_link_prefix):
        jira_comment_records = []
        if not issue_comment:
            return jira_comment_records

        jira_comment_manager = self.env['ata.jira.comment']

        comments = issue_comment.get("comments", [])
        if not comments:
            return jira_comment_records
        for comment in comments:
            comment_values = self.get_comment_values(
                comment, issue_id, browse_link_prefix)

            jira_comment_record = jira_comment_manager.create(comment_values)
            jira_comment_records.append(jira_comment_record)

        return jira_comment_records

    @api.model
    def get_comment_values(self, comment, issue_id, link_prefix):
        comment_id = comment.get("id")

        comment_link_suffix = f'{issue_id}?focusedCommentId={comment_id}'
        comment_link_suffix += '&page=com.atlassian.jira.plugin.system'
        comment_link_suffix += '.issuetabpanels:comment-tabpanel#comment-'
        link_suffix = f'{comment_link_suffix}{comment_id}'

        author = comment.get("author")
        update_author = comment.get("updateAuthor")

        comment_values = dict()
        comment_values["exchange_id"] = self['id']
        comment_values["comment_id"] = comment_id
        comment_values["issue_id"] = issue_id
        comment_values["body"] = comment.get("body")
        comment_values["created_date"] = self.get_date_iso(
            comment.get("created"))
        comment_values["updated_date"] = self.get_date_iso(
            comment.get("updated"))
        comment_values["author_name"] = author.get("name")
        comment_values["author_display_name"] = author.get("displayName")
        comment_values["author_email"] = author.get("emailAddress")
        comment_values["update_author_name"] = update_author.get("name")
        comment_values["update_author_display_name"] = update_author.get(
            "displayName")
        comment_values["update_author_email"] = update_author.get(
            "emailAddress")
        comment_values["comment_link"] = f'{link_prefix}{link_suffix}'

        return comment_values

    def find_tasks(self):
        task_manager = self.env['project.task']
        domain = [('exchange_id', '=', self['id'])]
        jira_issue_manager = self.env['ata.jira.issue']
        jira_issue_recordset = jira_issue_manager.search(domain)
        for jira_issue in jira_issue_recordset:
            task_domain = [('external_task_key', '=', jira_issue.issue_key)]
            task_recordset = task_manager.search(task_domain)
            if not task_recordset:
                continue
            task = task_recordset[0]
            vals = {
                'project_task_id': task.id
            }
            jira_issue.write(vals)

    def create_update_tasks(self):
        project_dict = dict()
        domain = [('exchange_id', '=', self['id'])]
        jira_issue_manager = self.env['ata.jira.issue']
        jira_issue_recordset = jira_issue_manager.search(domain)
        for jira_issue in jira_issue_recordset:
            project_key = jira_issue.project_key
            project = project_dict.get(project_key)
            if project_key and not project:
                project = self.create_update_project(jira_issue)
                project_dict[project_key] = project

            self.create_update_task(jira_issue, project)

    def create_update_project(self, jira_issue):
        user = self.get_user(
            jira_issue.creator_name,
            jira_issue.creator_email,
            jira_issue.creator_avatar
        )
        project_manager = self.env['project.project']

        description = f'{jira_issue.project_name} ({jira_issue.project_key})'
        project_vals = {
            'name': jira_issue.project_name,
            'description': description,
            'user_id': user.id if user else 0,
            'external_project_key': jira_issue.project_key,
        }
        project_domain = [
            ('external_project_key', '=', jira_issue.project_key)
        ]
        project_recordset = project_manager.search(project_domain)
        if project_recordset:
            project = project_recordset[0]
            project.write(project_vals)
        else:
            project = project_recordset.create(project_vals)
        return project

    def create_update_task(self, jira_issue, project):
        manager = self.get_user(
            jira_issue.creator_name,
            jira_issue.creator_email,
            jira_issue.creator_avatar
        )
        user = self.get_user(
            jira_issue.assignee_name,
            jira_issue.assignee_email,
            jira_issue.assignee_avatar
        )

        kanban_state = 'done' if jira_issue.status_name == 'Done' else 'normal'

        task_manager = self.env['project.task']
        jira_worklog_manager = self.env['ata.jira.worklog']

        user_ids = [(6, 0, [user.id])] if user else []

        task_vals = {
            'name': jira_issue.summary,
            'description': jira_issue.description,
            'project_id': project.id if project else 0,
            'manager_id': manager.id if manager else 0,
            'date_assign': jira_issue.created_date,
            'date_end': jira_issue.resolution_date,
            'kanban_state': kanban_state,
            'planned_hours': jira_issue.original_estimate,
            'external_task_key': jira_issue.issue_key,
            'user_ids': user_ids,
        }
        domain = [('external_task_key', '=', jira_issue.issue_key)]
        task_recordset = task_manager.search(domain)
        if task_recordset:
            task = task_recordset[0]
            task.write(task_vals)
        else:
            task = task_manager.create(task_vals)

        domain = [
            ('exchange_id', '=', self['id']),
            ('issue_id', '=', jira_issue.issue_id)
        ]
        jira_worklog_recordset = jira_worklog_manager.search(domain)
        for jira_worklog in jira_worklog_recordset:
            self.create_update_timesheet(task, jira_worklog)
        return task

    def create_update_timesheet(self, task, jira_worklog):
        timesheet_manager = self.env['account.analytic.line']

        timesheet_date = jira_worklog.started_date.date()
        employee = self.get_employee(
            jira_worklog.author_display_name,
            jira_worklog.author_email,
            jira_worklog.author_avatar
        )

        name = jira_worklog.comment if jira_worklog.comment else '<no details>'
        timesheet_vals = {
            'date': timesheet_date,
            'employee_id': employee.id if employee else 0,
            'project_id': task.project_id.id,
            'task_id': task.id,
            'name': name,
            'unit_amount': jira_worklog.time_spent,
            'company_id': task.company_id.id,
            'user_id': employee.user_id.id if employee else 0,
        }
        timesheet_domain = [
            ('task_id', '=', task.id),
            ('date', '=', timesheet_date),
            ('employee_id', '=', employee.id if employee else 0),
        ]
        timesheet_recordset = timesheet_manager.search(timesheet_domain)
        if timesheet_recordset:
            timesheet = timesheet_recordset[0]
            timesheet.sudo().write(timesheet_vals)
        else:
            timesheet = timesheet_recordset.sudo().create(timesheet_vals)

        return timesheet
