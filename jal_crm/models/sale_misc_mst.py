from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class SaleIncotermMst(models.Model):
    _name = 'sale.incoterm.mst'
    _description = 'Incoterm Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    sequence = fields.Integer(default=10)

class SaleDeliveryTermsMst(models.Model):
    _name = 'sale.terms.mst'
    _description = 'Delivery terms Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    sequence = fields.Integer(default=10)

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
    _rec_name = 'display_name'
    
    name = fields.Char(string='Name',tracking=True)
    display_name = fields.Char(string='Display Name',tracking=True)
    bank_ac_name = fields.Char("Bank A/C Name",tracking=True)
    bank_ac_no = fields.Char("Bank A/C No",tracking=True)
    bank_branch_ifsc = fields.Char("Bank Branch IFSC",tracking=True)
    branch = fields.Char("Branch",tracking=True)
    swift_code = fields.Char("Swift Code",tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency",tracking=True)

    correspondent_bank = fields.Char("Correspondent Bank",tracking=True)
    swift_code1 = fields.Char("Swift Code",tracking=True)
    acc_no = fields.Char("Account Number",tracking=True)
    currency1_id = fields.Many2one('res.currency', string="Currency",tracking=True)

class SaleTermConditions(models.Model):
    _name = "sale.term.conditions"
    _description= "Sale Term Conditions"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name')
    note = fields.Html("Note")
    module_type = fields.Selection([
            ("sale", "Sale"),  
            ("purchase", "Purchase")],string="Type")
    
class SaleinspectionMaster(models.Model):
    _name = "sale.inspection.mst"
    _description= "Sale Inspection Master"
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name')