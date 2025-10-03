from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class ShiftgMst(models.Model):
    _name = 'shift.mst'
    _description = 'Shift Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
