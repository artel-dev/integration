from odoo import api, models
from markupsafe import Markup
from odoo.exceptions import UserError, ValidationError

from dataclasses import dataclass, field
from typing import Any, cast
from pydantic import BaseModel as BaseModelPydantic, ValidationError as ValidationErrorPydantic

from .ata_exchange_base_incomingrequest_types import (
    IncomingParam, IncomingResponseParam
)
from .ata_exchange_method import AtaExchangeMethod
from .ata_exchange_system import AtaExchangeSystem
from odoo.addons.base.models.res_users import Users
from odoo.addons.mail.models.mail_thread import MailThread


@dataclass
class SearchRecordHandlerParams:
    search_ref: str | None = None  # search record by XML ID
    search_domain: list[tuple[str, str, Any]] | None = None  # domain for primary search record
    search_domain_second: list[tuple[str, str, Any]] | None = None  # domain for secondary search record (after matching)
    use_matching_data: bool = False  # use matching data for save pointer for record from external systems
    key_matching_data: str = 'id_matching'  # field of object data for search matching data ('id_matching' by default)
    ext_system_id: AtaExchangeSystem | None = None  # external system for search record
    method_id: AtaExchangeMethod | None = None  # method for search record
    stage: str = '' # stage for search record

    @classmethod
    def build(cls, inc_params: IncomingParam | None = None) -> 'SearchRecordHandlerParams':
        return cls(
            ext_system_id = inc_params.ext_system_id if inc_params else None,
            method_id     = inc_params.method_id if inc_params else None
        )

@dataclass
class RecordHandlerParams:
    model: models.BaseModel
    model_name: str
    data: dict = field(default_factory=dict)
    search_params: SearchRecordHandlerParams = field(default_factory=SearchRecordHandlerParams)
    incoming_params: IncomingParam | None = None
    stage: str = ''
    response_data: IncomingResponseParam = field(default_factory=IncomingResponseParam)
    warning_list: list[str] = field(default_factory=list)
    create_record: bool = False # create record if not found
    write_record: bool = False  # write data in record if found
    add_to_queue: bool = False  # add record to queue exchange to ext. system

    def _change_stage(self, value: str) -> None:
        """Synchronize stage with search_params and clear warnings."""
        if hasattr(self, 'search_params'):
            object.__setattr__(self.search_params, 'stage', value)
            
        if hasattr(self, 'warning_list') and self.warning_list:
            self.warning_list.clear()

    def __setattr__(self, name: str, value: Any) -> None:
        object.__setattr__(self, name, value)
        if name == 'stage':
            self._change_stage(value)

    @classmethod
    def build_from_class(cls, env, model_name: str, inc_params: IncomingParam|None = None) -> 'RecordHandlerParams':
        """Create a new instance directly from the class.
        Args:
            env: Odoo environment
            model_name: Name of the model
            inc_params: Incoming parameters for the exchange
        Returns:
            A new instance of RecordHandlerParams
        """
        return cls._build_params(env, model_name,
            IncomingParam.build(inc_params),
            SearchRecordHandlerParams.build(inc_params))

    def build(self, env, model_name: str, method: AtaExchangeMethod|None = None) -> 'RecordHandlerParams':
        """Build a new instance based on current instance with optional method override.
        Args:
            env: Odoo environment
            model_name: Name of the model
            method: Optional exchange method to override
        Returns:
            A new instance of RecordHandlerParams
        """
        final_inc_params = IncomingParam(
            method_id = method,
            ext_system_id = self.incoming_params.ext_system_id if self.incoming_params else None
        ) if method else self.incoming_params
        
        return RecordHandlerParams._build_params(env, model_name,
            final_inc_params,
            SearchRecordHandlerParams.build(final_inc_params),
            self.response_data)

    @staticmethod
    def _build_params(env, model_name: str,
        incoming_params: IncomingParam|None,
        search_params: SearchRecordHandlerParams,
        response_data: IncomingResponseParam|None = None) -> 'RecordHandlerParams':
        
        return RecordHandlerParams(
            model           = env[model_name],
            model_name      = model_name,
            incoming_params = incoming_params,
            search_params   = search_params,
            response_data   = response_data if response_data else IncomingResponseParam()
        )

@dataclass
class NotificationHandlerParams:
    """Parameters for creating notifications and activities for users."""
    user: Users | None
    record: models.BaseModel  # Record to attach notification to
    message_list: list[str]  # List of messages to send
    activity_summary: str = 'Notification from exchange'  # Activity summary
    activity_type_xmlid: str = 'mail.mail_activity_data_warning'  # Activity type XML ID


class AtaExchangeModelHandlerMixin(models.AbstractModel):
    _name = "ata.exchange.model.handler.mixin"
    _description = "Exchange model handler methods"

    @api.model
    def ata_exchange_get_model_record(self,
        record_params: RecordHandlerParams,
        only_search: bool = False) -> models.BaseModel:

        self.ata_exchange_check_record_params(record_params)
        if only_search:
            records = self.env['ata.exchange.model.handler'].search_records(record_params)
        else:
            records = self.env['ata.exchange.model.handler'].get_records(record_params)
        
        return next(iter(records), records)

    @api.model
    def ata_exchange_get_settings(self, param_name: str, block: str, Model: models.BaseModel) -> models.BaseModel:
        if not (sett_id:=self.env['ir.config_parameter'].get_param(param_name)):
            raise UserError(f"Setting '{param_name}' in {block} is not defined")
        else:
            return Model.browse(int(sett_id))

    def ata_exchange_process_data_with_pydantic(self, data: dict, pydantic_model: type[BaseModelPydantic]) -> BaseModelPydantic:
        try:
            return pydantic_model(**data)
        except ValidationErrorPydantic as e:
            error_message = f"Validation error data: {str(e)}"
            raise ValidationError(error_message) from e

    @api.model
    def ata_exchange_check_record_params(self, record_params: RecordHandlerParams):
        return True

    @api.model
    def ata_exchange_prepare_vals(self, record_params: RecordHandlerParams) -> dict:
        return record_params.data

    @api.model
    def ata_exchange_after_write(self, record_params: RecordHandlerParams):
        pass

    @api.model
    def ata_exchange_create_user_notification(self, 
        notification_params: NotificationHandlerParams,
        create_activity: bool = False,
        create_notification: bool = False):
        """Create notification and/or activity for user attached to record.
        
        Args:
            notification_params: Parameters for notification creation
            create_activity: Create mail.activity if True
            create_notification: Create message_post notification if True
        """
        if not notification_params.message_list:
            return
        
        message_body = Markup('<br/>'.join(notification_params.message_list))
        
        if not notification_params.user:
            notification_params.user = self.env.ref('base.user_admin')
        
        # Create mail.activity if requested
        if create_activity:
            activity_type = self.env.ref(notification_params.activity_type_xmlid, raise_if_not_found=False) or \
                self.env.ref('mail.mail_activity_data_warning')
            
            self.env['mail.activity'].create({
                'activity_type_id': activity_type.id,
                'res_id': notification_params.record.id,
                'res_model_id': self.env['ir.model']._get(notification_params.record._name).id,
                'user_id': notification_params.user.id,
                'summary': notification_params.activity_summary,
                'note': message_body,
            })
        
        # Create message_post notification if requested
        if create_notification:
            if isinstance(notification_params.record, MailThread):
                notification_params.record.message_post(
                    body=message_body,
                    partner_ids=[notification_params.user.partner_id.id],
                    message_type='notification',
                    subtype_xmlid='mail.mt_note',
                )
            else:
                raise UserError(
                    f"Model '{notification_params.record._name}' does not inherit 'mail.thread'. "
                    f"Cannot create notification."
                )

        notification_params.message_list.clear()