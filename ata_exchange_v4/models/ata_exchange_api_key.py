import uuid
from odoo import api, fields, models

class AtaExchangeApiKey(models.Model):
    """
    Stores API keys for external system authentication.
    """
    _name = 'ata.exchange.api.key'
    _description = 'External System API Key'
    _rec_name = 'display_name' # Use a computed field for better display

    def _generate_api_key(self):
        """Generate a unique API key."""
        return str(uuid.uuid4())

    api_key = fields.Char(
        string='API Key',
        default=_generate_api_key,
        required=True,
        copy=False,
        index='trigram', # Use trigram index for faster search if enabled
    )
    system_id = fields.Many2one(
        'ata.exchange.system',
        string='External System',
        required=True,
        ondelete='cascade', # Or 'set null' if you want to keep keys after deleting system
        help="Optional: Link this key to a pre-defined external system. "
             "If linked, the 'Key Name / Owner' field will be automatically filled, "
             "but can still be manually overridden.",
    )
    name = fields.Char(
        string='Key Name / Owner',
        related='system_id.name', # Automatically get name from system if linked
        store=True,
        readonly=False, # Allow manual override if not linked to a system
        help="Name for this key, typically the owner or purpose. "
             "If an 'External System' is selected, this field defaults to the system name "
             "but can be changed. If no system is selected, this name must be set manually "
             "(or a default will be generated on creation)."
    )
    display_name = fields.Char( # Computed field for better representation in lists/dropdowns
        string='Display Name',
        compute='_compute_display_name',
        store=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Only active keys can be used for authentication."
    )
    description = fields.Text(string='Description')
    methods_ids = fields.Many2many(
        'ata.exchange.method',
        string='Methods',
        domain=[('type', '=', 'incoming_request')]
    )

    _sql_constraints = [
        ('api_key_uniq', 'unique (api_key)', 'API Key must be unique!')
    ]

    @api.depends('name', 'api_key', 'system_id')
    def _compute_display_name(self):
        """Compute a user-friendly display name."""
        for key in self:
            name_part = key.name or f"Key [{key.api_key[:8]}...]"
            key.display_name = name_part


    @api.model_create_multi
    def create(self, vals_list):
        """Ensure name is set if system_id is not provided."""
        for vals in vals_list:
            if not vals.get('system_id') and not vals.get('name'):
                # Generate a default name if none is provided
                vals['name'] = f"API Key [{vals.get('api_key', self._generate_api_key())[:8]}...]"
        return super().create(vals_list)

    def write(self, vals):
        """Update name if system_id changes and name was related."""
        # This logic might be complex if name was manually set.
        # For simplicity, we let the related field handle updates if system_id changes.
        # If name is manually set, it won't be overridden by system_id change.
        return super().write(vals)
