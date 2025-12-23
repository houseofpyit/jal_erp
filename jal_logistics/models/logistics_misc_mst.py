from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class CHAMst(models.Model):
    _name = 'cha.mst'
    _description = 'CHA Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class ShippingLineMst(models.Model):
    _name = 'shipping.line.mst'
    _description = 'Shipping Line Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class InspectionMst(models.Model):
    _name = 'inspection.mst'
    _description = 'Inspection Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class EPCGLiscence(models.Model):
    _name = 'epcg.liscence.mst'
    _description = 'EPCG Liscence'
    _inherit = ['mail.thread']

    name = fields.Char(string='Liscence Number',tracking=True)
    date = fields.Date(string='Date',default=fields.Date.context_today,tracking=True)
    expiry_date = fields.Date(string='Expiry Date',tracking=True)

    @api.model
    def create(self, vals):
        name = vals.get('name')
        date = vals.get('date')

        if name and date:
            existing = self.search([('name', '=', name),('date', '=', date)])

            if existing:
                raise ValidationError(f"A record with Licence Number '{name}' and Date '{date}' already exists.")
        result = super(EPCGLiscence, self).create(vals)
        return result    

class AdvancedLiscence(models.Model):
    _name = 'advanced.liscence.mst'
    _description = 'Advanced Liscence'
    _inherit = ['mail.thread']

    name = fields.Char(string='Liscence Number',tracking=True)
    date = fields.Date(string='Date',default=fields.Date.context_today,tracking=True)
    expiry_date = fields.Date(string='Expiry Date',tracking=True)

class PalletSizeMst(models.Model):
    _name = 'pallet.size.mst'
    _description = 'Pallet Size Master'
    _inherit = ['mail.thread']

    name = fields.Char(string='Pallet Size',tracking=True)

class LoadingPlannerMst(models.Model):
    _name = 'loading.planner.mst'
    _description = 'Loading Planner Master'
    _inherit = ['mail.thread']

    name = fields.Char(string='Loading Planner Name',tracking=True)

class LabelRemarkMst(models.Model):
    _name = 'label.remark.mst'
    _description = 'Label Remark Master'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name',tracking=True)
    label_type = fields.Selection([('haz', 'HAZ Label'),('dead_fish', 'Dead Fish Label'),('un_print', 'UN Printing Label')], string='Label Type',tracking=True)
    