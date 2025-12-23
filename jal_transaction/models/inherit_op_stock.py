from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class inheritedOpStockMst(models.Model):
    _inherit = "hop.op.stock.mst"

    state = fields.Selection([('draft', 'Draft'),('complete', 'Complete')], default='draft',tracking=True)

    def action_complete_btn(self):
        for line in self.line_id:
            if not line.product_id:
                raise ValidationError(_("Please select a product before proceeding."))

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

        for line in self.line_id:
                move_vals = {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.pcs,
                    'demand_bucket': line.bucket,
                    'done_bucket': line.bucket,
                    'product_uom': line.unit_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': main_location.id,
                    'move_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'qty_done': line.pcs,
                        'done_bucket': line.bucket,
                        'product_uom_id': line.unit_id.id,
                        'location_id': src_location.id,
                        'location_dest_id': main_location.id,
                        'date': fields.Datetime.now(),
                    })],
                }
                move_list.append((0, 0, move_vals))
        
        if move_list:
            picking = self.env['stock.picking'].sudo().create({
                'location_id': src_location.id,
                'location_dest_id': main_location.id,
                'picking_type_id': picking_type.id,
                'origin': f"{self.name} - Receipt",
                'move_ids_without_package': move_list,
                'scheduled_date': fields.Datetime.now(),
            })

            picking.action_confirm()
            picking.action_assign()
            self.env.context = dict(self.env.context, skip_backorder=True)
            picking.action_set_quantities_to_reservation()
            picking.button_validate()

            self.state = 'complete'

class inheritedOpStockMstLine(models.Model):
   _inherit = "hop.op.stock.line"

   bucket = fields.Float('Packing Unit')