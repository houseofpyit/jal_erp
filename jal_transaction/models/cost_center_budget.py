import logging
from odoo import models, fields,api
from odoo.exceptions import ValidationError

class CostCenterBudget(models.Model):
    _name = "cost.center.budget"
    _inherit = ['mail.thread']
    _description = 'Cost Budget'
    _rec_name = 'cost_id'

    cost_id = fields.Many2one('hop.cost.center',string="Cost Center",tracking=True)
    date = fields.Date(string="Date",tracking=True)
    amount = fields.Float(string="Amount",tracking=True)