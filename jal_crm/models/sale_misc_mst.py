from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class SaleIncotermMst(models.Model):
    _name = 'sale.incoterm.mst'
    _description = 'Incoterm Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class SaleDeliveryTermsMst(models.Model):
    _name = 'sale.terms.mst'
    _description = 'Delivery terms Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class SaleDestinationPortMst(models.Model):
    _name = 'sale.port.mst'
    _description = 'Destination Port Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    country_id = fields.Many2one('res.country',string="Country",tracking=True)


class BankMaster(models.Model):
    _name = "bank.mst"
    _description= "Bank"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name')
    bank_ac_name = fields.Char("Bank A/C Name")
    bank_ac_no = fields.Char("Bank A/C No")
    bank_branch_ifsc = fields.Char("Bank Branch IFSC")

class SaleTermConditions(models.Model):
    _name = "sale.term.conditions"
    _description= "Sale Term Conditions"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name')
    note = fields.Html("Note")

class SaleinspectionMaster(models.Model):
    _name = "sale.inspection.mst"
    _description= "Sale Inspection Master"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name')