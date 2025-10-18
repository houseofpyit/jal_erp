from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalProduction(models.Model):
    _name = 'jal.production'
    _description = 'Production'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    shift_id = fields.Many2one('shift.mst',string="Shift",tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    line_ids = fields.One2many('jal.production.line', 'mst_id')
    packing_line_ids = fields.One2many('jal.packing.production.line', 'mst_id')
    finished_line_ids = fields.One2many('jal.finished.production.line', 'mst_id')
    state = fields.Selection([('draft', 'Draft'),('running', 'Running'),('complete', 'Complete')], default='draft',tracking=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product',tracking=True)
    electricity_exp = fields.Float(string="Electricity(KWH)",tracking=True)
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    employee_id = fields.Many2one('hr.employee', string='Shift Incharge',tracking=True)

    def name_get(self):
        result = []
        for i in self:
            if i.shift_id:
                name = i.name + ' ' + '(' + str(i.shift_id.name) + ')'
            else:
                name = i.name
            result.append((i.id, name))
        return result
    
    def action_running_btn(self):
        self.state = 'running'

    def action_get_quality_btn(self):
        quality_rec = self.env['jal.quality'].search([('production_id', '=', self.id)])
        if not quality_rec:
            raise ValidationError(_("No Quality record found for Production: %s") % (self.name or ""))
        
        line_list = []
        if quality_rec:
            domain = [
                ('product_template_attribute_value_ids.product_attribute_value_id', '=', quality_rec.grade_id.id),
                ('product_template_attribute_value_ids.product_attribute_value_id', '=', quality_rec.mesh_id.id),
                ('product_template_attribute_value_ids.product_attribute_value_id', '=', quality_rec.bucket_id.id),
            ]

            products = self.env['product.product'].search(domain)
            line_list.append((0,0,{
               'grade_id': quality_rec.grade_id.id,
               'mesh_id':quality_rec.mesh_id.id,
               'bucket_id':quality_rec.bucket_id.id,
               'product_id':products.id if products else False,
            }))
        self.finished_line_ids = line_list

    def action_complete_btn(self):
        self._create_stock_picking_receipts()
        self.state = 'complete'

    def _create_stock_picking_receipts(self):
        if not self.finished_line_ids:
            raise ValidationError("No finished products to receive!")

        for line in self.finished_line_ids:
            if line.qty <= 0:
                raise ValidationError(
                    f"Quantity must be greater than 0 for product: {line.product_id.display_name}"
                )

        main_location = self.env['stock.location'].sudo().search([('main_store_location', '=', True)], limit=1)
        if not main_location:
            raise ValidationError("Main Store Location not found!")

        src_location = self.env['stock.location'].sudo().search([('usage', '=', 'supplier')], limit=1)
        if not src_location:
            raise ValidationError("No Vendor/Partner location found!")

        picking_type = self.env['stock.picking.type'].sudo().search([('code', '=', 'incoming')], limit=1)
        if not picking_type:
            raise ValidationError("Incoming Picking Type not found!")

        move_list = []

        for line in self.finished_line_ids:
            move_vals = {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.qty,
                'demand_bucket': line.bucket_qty,
                'done_bucket': line.bucket_qty,
                'product_uom': line.uom_id.id,
                'location_id': src_location.id,
                'location_dest_id': main_location.id,
                'move_line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'qty_done': line.qty,
                    'done_bucket': line.bucket_qty,
                    'product_uom_id': line.uom_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': main_location.id,
                    'date': fields.Datetime.now(),
                })],
            }
            move_list.append((0, 0, move_vals))

        picking = self.env['stock.picking'].sudo().create({
            'location_id': src_location.id,
            'location_dest_id': main_location.id,
            'picking_type_id': picking_type.id,
            'production_id': self.id,
            'origin': f"{self.name} - Receipt",
            'move_ids_without_package': move_list,
            'scheduled_date': fields.Datetime.now(),
        })

        picking.action_confirm()
        picking.action_assign()
        self.env.context = dict(self.env.context, skip_backorder=True)
        picking.action_set_quantities_to_reservation()
        picking.button_validate()

        
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
    lot_ids = fields.Many2many('stock.production.lot', string='Lot/Serial',domain="[('product_id', '=', product_id)]")
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    product_tracking = fields.Selection(related='product_id.tracking')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

class JalPackingProductionLine(models.Model):
    _name = 'jal.packing.production.line'
    _description = "Packing Production Line"

    mst_id = fields.Many2one('jal.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    lot_ids = fields.Many2many('stock.production.lot', string='Lot/Serial',domain="[('product_id', '=', product_id)]")
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    product_tracking = fields.Selection(related='product_id.tracking')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

class JalFinishedProductionLine(models.Model):
    _name = 'jal.finished.production.line'
    _description = "Finished Production Line"

    mst_id = fields.Many2one('jal.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string="Quantity")
    bucket_qty = fields.Integer(string="Bucket Quantity")
    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]",tracking=True)
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]",tracking=True)
    bucket_id = fields.Many2one('product.attribute.value',string="Bucket",domain="[('attribute_id.attribute_type','=','bucket')]",tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('bucket_qty')
    def _onchange_bucket_qty(self):
        if self.bucket_qty > 0:
            if self.bucket_id.amount > 0:
                self.qty = self.bucket_qty * self.bucket_id.amount
        else:
            self.qty = 0

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id
                
    @api.onchange('grade_id', 'mesh_id', 'bucket_id')
    def _onchange_product_attributes(self):
        if not (self.grade_id and self.mesh_id and self.bucket_id):
            self.product_id = False
            return {'domain': {'product_id': []}}

        self.product_id = False

        domain = [
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.grade_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.mesh_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.bucket_id.id),
        ]

        products = self.env['product.product'].search(domain)

        return {'domain': {'product_id': [('id', 'in', products.ids)]}}