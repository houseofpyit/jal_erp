from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheriteStockPicking(models.Model):
    _inherit = "stock.picking"

    production_id = fields.Many2one('jal.production',string="Production")

class inheriteStockLocation(models.Model):
    _inherit = "stock.location"

    main_store_location = fields.Boolean(string="Is a Main Store Location?",tracking=True)
