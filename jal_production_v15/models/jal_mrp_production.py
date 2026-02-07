from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalMrpProduction(models.Model):
    _name = 'jal.mrp.production'
    _description = 'MRP Production'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    sale_id = fields.Many2one('sale.order', string='Sale')
    state = fields.Selection([('draft', 'Draft'),('running', 'Running'),('done', 'Done'),('cancel', 'Cancel')], default='draft',tracking=True)
    product_id = fields.Many2one('product.product',tracking=True)
    uom_id = fields.Many2one('uom.uom',string="Unit",tracking=True)
    qty = fields.Float(string = "Quantity",digits='BaseAmount',tracking=True)
    booking_date = fields.Date(string="Container stuffing date",tracking=True)
    country_id = fields.Many2one('res.country',string="Country",tracking=True)
    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]")
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]")
    bucket = fields.Float(string='Packing Unit',digits=(2, 3))
    pending_qty = fields.Float(string = "Pending Quantity",digits='BaseAmount',tracking=True)
    pending_bucket = fields.Float(string='Pending Weight',tracking=True,digits=(2, 3))

    line_ids = fields.One2many('jal.mrp.production.line', 'mst_id',string="Raw Material Products")
    packing_line_ids = fields.One2many('jal.mrp.production.packing.line', 'mst_id',string="Packing Products")
    complete_line_ids = fields.One2many('jal.mrp.production.complete.line', 'mst_id',string="Complete Products")

    # def name_get(self):
    #     result = []
    #     for i in self:
    #         if i.shift_id:
    #             name = i.name + ' ' + '(' + str(i.shift_id.name) + ')'
    #         else:
    #             name = i.name
    #         result.append((i.id, name))
    #     return result

    def action_document_order_form(self):
        logic_id = self.env['jal.logistics'].sudo().search([('sale_id','=',self.sale_id.id)],limit=1)
        return self.env.ref('jal_logistics.action_order_form_report').report_action(logic_id.id) if self.sale_id else False
    
    def action_running_btn(self):
        self.state = 'running'

    def action_done_btn(self):
        self.state = 'done'

    @api.onchange('complete_line_ids')
    def _onchange_complete_line_ids(self):
        for rec in self:
            rec.pending_qty = (rec.qty - sum(rec.complete_line_ids.mapped('qty')))
            rec.pending_bucket = (rec.bucket - sum(rec.complete_line_ids.mapped('bucket')))

    # def action_get_quality_btn(self):
    #     quality_rec = self.env['jal.quality'].search([('production_id', 'in', self.ids)])
    #     if not quality_rec:
    #         raise ValidationError(_("No Quality record found for Production: %s") % (self.name or ""))

    #     merged = {}

    #     for qual in quality_rec:
    #         for line in qual.quality_grade_ids:

    #             domain = [
    #                 ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.grade_id.id),
    #                 ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.mesh_id.id),
    #                 ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.bucket_id.id),
    #             ]
    #             products = self.env['product.product'].search(domain)
                
    #             product_id = products.id if len(products) == 1 else False
    #             domain_ids = products.ids if len(products) == 1 else self.env['product.product'].search([]).ids
    #             uom_id = products.uom_id.id if len(products) == 1 else False

    #             key = (line.grade_id.id, line.mesh_id.id, line.bucket_id.id, product_id)

    #             if key not in merged:
    #                 merged[key] = {
    #                     'grade_id': line.grade_id.id,
    #                     'mesh_id': line.mesh_id.id,
    #                     'bucket_id': line.bucket_id.id,
    #                     'bucket_qty': line.no_of_drum,
    #                     'qty': line.weight,
    #                     'product_id': product_id,
    #                     'product_doamin_ids': [(6, 0, domain_ids)],
    #                     'uom_id': uom_id,
    #                 }
    #             else:
    #                 merged[key]['bucket_qty'] += line.no_of_drum
    #                 merged[key]['qty'] += line.weight

    #     final_lines = [(0, 0, vals) for vals in merged.values()]

    #     self.finished_line_ids = [(5, 0, 0)] + final_lines

    # def action_complete_btn(self):
    #     self._create_stock_picking_receipts()
    #     self._create_stock_picking_out()
    #     self.state = 'complete'

    # def _create_stock_picking_receipts(self):
    #     if not self.finished_line_ids:
    #         raise ValidationError("No finished products to receive!")

    #     for line in self.finished_line_ids:
    #         if not line.product_id:
    #             raise ValidationError(
    #                  _("Please select a product for finished lines before proceeding.")
    #             )
            
    #         if line.qty <= 0:
    #             raise ValidationError(
    #                 f"Quantity must be greater than 0 for product: {line.product_id.display_name}"
    #             )

    #     main_location = self.env['stock.location'].sudo().search([('main_store_location', '=', True)], limit=1)
    #     if not main_location:
    #         raise ValidationError("Main Store Location not found!")

    #     src_location = self.env['stock.location'].sudo().search([('usage', '=', 'supplier')], limit=1)
    #     if not src_location:
    #         raise ValidationError("No Vendor/Partner location found!")

    #     picking_type = self.env['stock.picking.type'].sudo().search([('code', '=', 'incoming')], limit=1)
    #     if not picking_type:
    #         raise ValidationError("Incoming Picking Type not found!")

    #     move_list = []

    #     for line in self.finished_line_ids:
    #         move_vals = {
    #             'name': line.product_id.display_name,
    #             'product_id': line.product_id.id,
    #             'product_uom_qty': line.bucket_qty,
    #             'demand_bucket': line.qty,
    #             'done_bucket': line.qty,
    #             'product_uom': line.uom_id.id,
    #             'location_id': src_location.id,
    #             'location_dest_id': main_location.id,
    #             'move_line_ids': [(0, 0, {
    #                 'product_id': line.product_id.id,
    #                 'qty_done': line.bucket_qty,
    #                 'done_bucket': line.qty,
    #                 'product_uom_id': line.uom_id.id,
    #                 'location_id': src_location.id,
    #                 'location_dest_id': main_location.id,
    #                 'date': fields.Datetime.now(),
    #             })],
    #         }
    #         move_list.append((0, 0, move_vals))

    #     picking = self.env['stock.picking'].sudo().create({
    #         'location_id': src_location.id,
    #         'location_dest_id': main_location.id,
    #         'picking_type_id': picking_type.id,
    #         'production_id': self.id,
    #         'origin': f"{self.name} - Receipt",
    #         'move_ids_without_package': move_list,
    #         'scheduled_date': fields.Datetime.now(),
    #     })

    #     picking.action_confirm()
    #     picking.action_assign()
    #     self.env.context = dict(self.env.context, skip_backorder=True)
    #     picking.action_set_quantities_to_reservation()
    #     picking.button_validate()

    # def _create_stock_picking_out(self):
    #     StockQuant = self.env['stock.quant'].sudo()
    #     StockLocation = self.env['stock.location'].sudo()
    #     StockPickingType = self.env['stock.picking.type'].sudo()
    #     StockPicking = self.env['stock.picking'].sudo()

    #     main_location = StockLocation.search([('main_store_location', '=', True)], limit=1)
    #     if not main_location:
    #         raise ValidationError(_("Main Store Location not found!"))

    #     des_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
    #     if not des_location:
    #         raise ValidationError(_("No Vendor/Partner location found!"))

    #     picking_type = StockPickingType.search([('code', '=', 'outgoing')], limit=1)
    #     if not picking_type:
    #         raise ValidationError(_("Outgoing Picking Type not found!"))

    #     def _validate_lines(line_ids, line_type):
    #         for line in line_ids:
    #             if not line.product_id:
    #                 raise ValidationError(_("Please select a product for %s lines before proceeding.") % line_type)
    #             if line.qty <= 0:
    #                 raise ValidationError(_("Quantity must be greater than 0 for product: %s") % line.product_id.display_name)

    #             if line.product_id.tracking in ('lot', 'serial') and not line.lot_ids:
    #                 raise ValidationError(_("Please select a lot/serial number for tracked product: %s") % line.product_id.display_name)

    #             domain = [('product_id', '=', line.product_id.id), ('location_id', '=', main_location.id)]
    #             if line.lot_ids:
    #                 domain.append(('lot_id', 'in', line.lot_ids.ids))
    #             stock_quants = StockQuant.search(domain)

    #             available_qty = sum(stock_quants.mapped('available_quantity'))
    #             if available_qty < line.qty:
    #                 raise ValidationError(_("Insufficient stock for product %s. Available: %s, Required: %s") %
    #                                     (line.product_id.display_name, available_qty, line.qty))

    #     _validate_lines(self.line_ids, "Raw Materials")
    #     _validate_lines(self.packing_line_ids, "Packing Materials")

    #     move_list = []
    #     def _prepare_moves(lines):
    #         for line in lines:
    #             product = line.product_id
    #             required_qty = line.qty

    #             quants_domain = [('product_id', '=', product.id), ('location_id', '=', main_location.id), ('quantity', '>', 0)]
    #             if line.lot_ids:
    #                 quants_domain.append(('lot_id', 'in', line.lot_ids.ids))

    #             quants = StockQuant.search(quants_domain)
    #             remaining = required_qty

    #             for quant in quants:
    #                 take_qty = min(quant.available_quantity, remaining)
    #                 if take_qty <= 0:
    #                     continue

    #                 move_vals = {
    #                     'product_id': line.product_id.id,
    #                     'qty_done': take_qty,
    #                     'product_uom_id': line.uom_id.id,
    #                     'location_id': main_location.id,
    #                     'location_dest_id': des_location.id,
    #                 }

    #                 if product.tracking in ('lot', 'serial') and quant.lot_id:
    #                     move_vals['lot_id'] = quant.lot_id.id

    #                 remaining -= take_qty
    #                 if remaining <= 0:
    #                     break

    #             move_list.append((0, 0, move_vals))

    #     _prepare_moves(self.line_ids)
    #     _prepare_moves(self.packing_line_ids)
        
    #     picking = StockPicking.create({
    #         'location_id': main_location.id,
    #         'location_dest_id': des_location.id,
    #         'picking_type_id': picking_type.id,
    #         'production_id': self.id,
    #         'origin': f"{self.name} - Outgoing",
    #         # 'move_ids_without_package': move_list,
    #         'move_line_ids_without_package': move_list,
    #         'scheduled_date': fields.Datetime.now(),
    #     })

    #     picking.action_confirm()
    #     self.env.context = dict(self.env.context, skip_backorder=True)
    #     picking.button_validate()

    @api.model
    def create(self, vals):
        result = super(JalMrpProduction, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.material.requisition.seq') or _('New')
        
        return result

class JalMrpProductionLine(models.Model):
    _name = 'jal.mrp.production.line'
    _description = "Mrp Production Line"

    mst_id = fields.Many2one('jal.mrp.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

class JalMrpProductionPackingLine(models.Model):
    _name = 'jal.mrp.production.packing.line'
    _description = "Mrp Production Packing Line"

    mst_id = fields.Many2one('jal.mrp.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

class JalMrpProductionCompleteLine(models.Model):
    _name = 'jal.mrp.production.complete.line'
    _description = "Mrp Production Complete Line"

    mst_id = fields.Many2one('jal.mrp.production',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Complete Bucket Quantity",digits='BaseAmount')
    bucket = fields.Float(string='Complete Bucket Weight',digits=(2, 3))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
