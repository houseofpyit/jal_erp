from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class DryerMst(models.Model):
    _name = 'dryer.mst'
    _description = 'Dryer Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)