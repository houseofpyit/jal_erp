from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedOpStockMst(models.Model):
    _inherit = "hop.op.stock.mst"

    state = fields.Selection([('draft', 'Draft'),('complete', 'Complete')], default='draft',tracking=True)
    replace_stock = fields.Boolean(string='Replace Stock',tracking=True)

    def action_complete_btn(self):
        for line in self.line_id:
            if not line.product_id:
                raise ValidationError(_("Please select a product before proceeding."))
            if line.pcs <= 0:
                raise ValidationError(_("Quantity must be greater than zero."))

        main_location = self.env['stock.location'].sudo().search([('main_store_location', '=', True)], limit=1)
        if not main_location:
            raise ValidationError("Main Store Location not found!")

        vendor_location = self.env['stock.location'].sudo().search([('usage', '=', 'supplier')], limit=1)
        if not vendor_location:
            raise ValidationError("Vendor Location not found!")

        in_picking_type = self.env['stock.picking.type'].sudo().search([('code', '=', 'incoming')], limit=1)
        if not in_picking_type:
            raise ValidationError("Incoming Picking Type not found!")

        out_picking_type = self.env['stock.picking.type'].sudo().search([('code', '=', 'outgoing')], limit=1)
        if not out_picking_type:
            raise ValidationError("Outgoing Picking Type not found!")


        if self.replace_stock:
            self._remove_existing_stock(main_location, vendor_location, out_picking_type)

        self._receive_new_stock(main_location, vendor_location, in_picking_type)

        self.state = 'complete'

    def _remove_existing_stock(self, main_location, vendor_location, out_picking_type):
        StockQuant = self.env['stock.quant'].sudo()
        out_moves = []

        for line in self.line_id:
            # quants = StockQuant.search([('product_id', '=', line.product_id.id),('location_id', '=', main_location.id),])

            # total_qty = sum(quants.mapped('quantity'))
            # total_bucket = sum(quants.mapped('on_hand_bucket'))

            if line.stock_qty > 0:
                out_moves.append((0, 0, {
                    'product_id': line.product_id.id,
                    'qty_done': line.stock_qty,
                    'demand_bucket': line.stock_bucket,
                    'done_bucket': line.stock_bucket,
                    'product_uom_id': line.unit_id.id,
                    'location_id': main_location.id,
                    'location_dest_id': vendor_location.id,
                }))

        if out_moves:
            out_picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': out_picking_type.id,
                'location_id': main_location.id,
                'location_dest_id': vendor_location.id,
                'origin': f"{self.name} - Stock Replace OUT",
                'move_line_ids_without_package': out_moves,
            })

            out_picking.action_confirm()
            self.env.context = dict(self.env.context, skip_backorder=True)
            out_picking.button_validate()

    def _receive_new_stock(self, main_location, vendor_location, in_picking_type):

        move_list = []

        for line in self.line_id:
            move_list.append((0, 0, {
                'name': line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.pcs,
                'demand_bucket': line.bucket,
                'done_bucket': line.bucket,
                'product_uom': line.unit_id.id,
                'location_id': vendor_location.id,
                'location_dest_id': main_location.id,
                'move_line_ids': [(0, 0, {
                    'product_id': line.product_id.id,
                    'qty_done': line.pcs,
                    'done_bucket': line.bucket,
                    'product_uom_id': line.unit_id.id,
                    'location_id': vendor_location.id,
                    'location_dest_id': main_location.id,
                    'date': fields.Datetime.now(),
                })],
            }))

        if move_list:
            picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': in_picking_type.id,
                'location_id': vendor_location.id,
                'location_dest_id': main_location.id,
                'origin': f"{self.name} - Receipt",
                'move_ids_without_package': move_list,
                'scheduled_date': fields.Datetime.now(),
            })

            picking.action_confirm()
            picking.action_assign()
            picking.action_set_quantities_to_reservation()
            picking.button_validate()

class inheritedOpStockMstLine(models.Model):
   _inherit = "hop.op.stock.line"

   bucket = fields.Float('Packing Unit')
   stock_qty = fields.Float('Stock Quantity')
   stock_bucket = fields.Float('Stock Packing Unit')

   @api.onchange('product_id')
   def _onchange_product_id_stock(self):
        main_location = self.env['stock.location'].sudo().search([('main_store_location', '=', True)], limit=1)
        for rec in self:
            quants = self.env['stock.quant'].sudo().search([('product_id', '=', rec.product_id.id),('location_id', '=', main_location.id)])
            
            rec.stock_qty = sum(quants.mapped('quantity'))
            rec.stock_bucket = sum(quants.mapped('on_hand_bucket'))