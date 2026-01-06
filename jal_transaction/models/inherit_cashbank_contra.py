from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritCashBankContra(models.Model):
    _inherit = "cashbank.contra"

    cash_id = fields.Many2one("res.partner", string='CR A/c',tracking=True,domain=[('acc_type','in',['CASH','BANK'])])
    bank_id = fields.Many2one("res.partner", string='DR A/c',tracking=True,domain=[('acc_type','in',['CASH','BANK'])])