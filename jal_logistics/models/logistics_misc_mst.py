from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class BookingAgentMst(models.Model):
    _name = 'booking.agent.mst'
    _description = 'Booking Agent Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class TransportAgentMst(models.Model):
    _name = 'transport.agent.mst'
    _description = 'Transport Agent Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

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

class AdvancedLiscence(models.Model):
    _name = 'advanced.liscence.mst'
    _description = 'Advanced Liscence'
    _inherit = ['mail.thread']

    name = fields.Char(string='Liscence Number',tracking=True)
    date = fields.Date(string='Date',default=fields.Date.context_today,tracking=True)

class PalletSizeMst(models.Model):
    _name = 'pallet.size.mst'
    _description = 'Pallet Size Master'
    _inherit = ['mail.thread']

    name = fields.Char(string='Pallet Size',tracking=True)