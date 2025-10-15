from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedResUsers(models.Model):
    _inherit = "res.users"

    location_id = fields.Many2one('stock.location', string='Location')