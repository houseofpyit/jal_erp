from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalProduction(models.Model):
    _name = 'jal.production'
    _description = 'Production'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(copy=False, index=True, default=lambda self: _('New'))
    shift_id = fields.Many2one('shift.mst',string="Shift")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    line_ids = fields.One2many('jal.production.line', 'mst_id')
    state = fields.Selection([('draft', 'Draft'),('inprogres', 'Inprogres'),('done', 'Done')], default='draft')
    product_id = fields.Many2one('product.product')
    quality_count = fields.Integer(string="Quality Count", compute="_compute_quality_count", store=True)

    @api.depends('quality_count') 
    def _compute_quality_count(self):
        print("-------------quality_count--------------")
        for i in self:
            i.quality_count = self.env['jal.quality'].sudo().search_count([('production_id', '=', i.id)])

    def action_view_quality(self):
        quality_rec = self.env['jal.quality'].search([('production_id', '=', self.id)])
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality',
            'view_mode': 'form',
            'res_model': 'jal.quality',
            'res_id': quality_rec.id,
            'context': {'create': False}
            }

    def create_quality_btn(self):
        quality_rec = self.env['jal.quality'].create({
                                            'shift_id': self.shift_id.id,
                                            'production_id': self.id,
                                            })
        if quality_rec:
            self.state = 'inprogres'

    @api.model
    def create(self, vals):
        result = super(JalProduction, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.production.seq') or _('New')
        
        return result

class JalProductionLine(models.Model):
    _name = 'jal.production.line'
    _description = "Production Line"

    mst_id = fields.Many2one('jal.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

                