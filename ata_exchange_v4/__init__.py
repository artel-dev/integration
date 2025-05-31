from . import models
from . import controllers

import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """Delete specific views before module update to avoid issues with old field references."""
    views_to_delete = [
        'ata_exchange_system_view_form',
        'ata_exchange_system_view_list',
        'ata_exchange_system_view_search'
    ]
    module_name = 'ata_exchange_v4'

    for view_name in views_to_delete:
        view_xml_id = f"{module_name}.{view_name}"
        _logger.info(f"Processing pre_init_hook for view: {view_xml_id}")

        # Find the ir.model.data record for this XML ID
        cr.execute("SELECT res_id FROM ir_model_data WHERE module = %s AND name = %s", (module_name, view_name))
        res = cr.fetchone()
        if not res:
            _logger.info(f"View with XML ID '{view_xml_id}' not found in ir.model.data. No action taken.")
            continue

        view_id = res[0]
        if not view_id:
            _logger.info(f"View ID for XML ID '{view_xml_id}' is null. No action taken.")
            continue

        _logger.info(f"Attempting to delete view with XML ID '{view_xml_id}' (DB ID: {view_id}) before module update.")

        # Check if the view exists in ir_ui_view
        cr.execute("SELECT id FROM ir_ui_view WHERE id = %s", (view_id,))
        if not cr.fetchone():
            _logger.info(f"View with DB ID {view_id} (XML ID: '{view_xml_id}') not found in ir_ui_view. It might have been deleted already.")
            continue

        try:
            # For now, we'll focus on deleting the ir_ui_view record.
            cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (view_id,))
            _logger.info(f"Successfully deleted view with DB ID {view_id} (XML ID: '{view_xml_id}') from ir_ui_view.")

        except Exception as e:
            _logger.error(f"Error deleting view with XML ID '{view_xml_id}' (DB ID: {view_id}): {e}", exc_info=True)
            # Continue to the next view if one fails, to attempt deleting others.
