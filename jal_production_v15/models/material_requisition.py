from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalMaterialRequisition(models.Model):
    _name = 'jal.material.requisition'
    _description = 'Material Requisition'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    state = fields.Selection([('draft', 'Draft'),('done', 'Done')], default='draft',tracking=True)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    from_location_id = fields.Many2one('stock.location',string="From Location",tracking=True,default=lambda self: self.env.user.location_id.id)
    to_location_id = fields.Many2one('stock.location',string="To Location",tracking=True,default=lambda self: self.env['stock.location'].sudo().search([('main_store_location', '=', True),('company_id', '=', self.env.company.id)],limit=1))
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    line_ids = fields.One2many('jal.material.line', 'mst_id')

    @api.model
    def create(self, vals):
        result = super(JalMaterialRequisition, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.material.requisition.seq') or _('New')
        
        return result

class JalProductionLine(models.Model):
    _name = 'jal.material.line'
    _description = "Material Line"

    mst_id = fields.Many2one('jal.material.requisition',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    demand_qty = fields.Float(string = "Demand Quantity")
    available_qty = fields.Float(string = "Available Quantity")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id