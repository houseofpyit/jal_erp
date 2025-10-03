from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class PackingmMst(models.Model):
    _name = 'packing.mst'
    _description = 'Packing Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    capacity_id = fields.Many2one('capacity.mst',string='Capacity Per Drum',tracking=True)
    pouch_name_id = fields.Many2one('pouch.name.mst',string='Pouch Name',tracking=True)
    lid_color_id = fields.Many2one('lid.color.mst',string='Lid Color',tracking=True)
    branding_id = fields.Many2one('branding.mst',string='Branding',tracking=True)
    drum_color_id = fields.Many2one('drum.color.mst',string='Drum Color',tracking=True)
    scoops_id = fields.Many2one('scoops.mst',string='Scoops',tracking=True)
    outer_cartoons_id = fields.Many2one('outer.cartoons.mst',string='Outer Cartoons',tracking=True)


class CapacityMst(models.Model):
    _name = 'capacity.mst'
    _description = 'Capacity per drum'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    weight = fields.Float(string='Weight',tracking=True)
    uom_id = fields.Many2one('uom.uom',string='Unit',tracking=True)
    packaging_type = fields.Selection([("drum", "Drum"),("bucket", "Bucket"),("box", "Box"),],string="Packaging Type",tracking=True)


class PouchNameMst(models.Model):
    _name = 'pouch.name.mst'
    _description = 'Pouch Name Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class brandingMst(models.Model):
    _name = 'branding.mst'
    _description = 'Branding Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class LidColorMst(models.Model):
    _name = 'lid.color.mst'
    _description = 'Lid Color Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    color = fields.Integer(string='Color')

class DrumColorMst(models.Model):
    _name = 'drum.color.mst'
    _description = 'Drum Color Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    color = fields.Integer(string='Color')

class ScoopsMst(models.Model):
    _name = 'scoops.mst'
    _description = 'Scoops Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class OuterCartoonsMst(models.Model):
    _name = 'outer.cartoons.mst'
    _description = 'Outer Cartoons Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)

class BoxColorMst(models.Model):
    _name = 'box.color.mst'
    _description = 'Box Color Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    color = fields.Integer(string='Color')

class NameMst(models.Model):
    _name = 'name.mst'
    _description = 'Name Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)