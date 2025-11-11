from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheriteStockPicking(models.Model):
    _inherit = "stock.picking"

    production_id = fields.Many2one('jal.production',string="Production")

    def action_confirm(self):
        res = super(inheriteStockPicking,self).action_confirm()
        for line in self.move_lines:
            stock_move = self.env['stock.move.line'].search([('picking_id', '=', line.picking_id.id),('product_id', '=', line.product_id.id)])
            stock_move.write({'done_bucket': line.done_bucket})
        return res
    
class InheritStockMove(models.Model):
    _inherit = "stock.move"

    demand_bucket = fields.Float(string="Demand (Bucket/Bags/Pouch)")
    done_bucket = fields.Float(string="Done (Bucket/Bags/Pouch)")
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)

        Quant = self.env['stock.quant']
        for move in self:
            for ml in move.move_line_ids:
                w = ml.done_bucket or 0.0
                if not w or not ml.product_id:
                    continue
                # print("*****src_usage*******",src_usage)
                src_usage = ml.location_id.usage
                dst_usage = ml.location_dest_id.usage

                # Internal -> External (Delivery): decrease source
                if src_usage == 'internal' and dst_usage != 'internal':
                    quant = Quant.search([
                        ('product_id', '=', ml.product_id.id),
                        ('location_id', '=', ml.location_id.id)
                    ], limit=1)
                    if quant:
                        quant.on_hand_bucket -= w

                # External -> Internal (Receipt): increase dest
                elif dst_usage == 'internal' and src_usage != 'internal':
                    quant = Quant.search([
                        ('product_id', '=', ml.product_id.id),
                        ('location_id', '=', ml.location_dest_id.id)
                    ], limit=1)
                    if quant:
                        quant.on_hand_bucket += w
                    else:
                        Quant.create({
                            'product_id': ml.product_id.id,
                            'location_id': ml.location_dest_id.id,
                            'on_hand_bucket': w,
                        })

                # Internal -> Internal (Transfer): move between quants
                elif src_usage == 'internal' and dst_usage == 'internal':
                    src_q = Quant.search([
                        ('product_id', '=', ml.product_id.id),
                        ('location_id', '=', ml.location_id.id)
                    ], limit=1)
                    if src_q:
                        src_q.on_hand_bucket -= w

                    dst_q = Quant.search([
                        ('product_id', '=', ml.product_id.id),
                        ('location_id', '=', ml.location_dest_id.id)
                    ], limit=1)
                    if dst_q:
                        dst_q.on_hand_bucket += w
                    else:
                        Quant.create({
                            'product_id': ml.product_id.id,
                            'location_id': ml.location_dest_id.id,
                            'on_hand_bucket': w,
                        })
        return res
    
    @api.onchange('move_line_nosuggest_ids')
    def _onchange_move_line_nosuggest_ids(self):
        for move in self:
            move.done_bucket = sum(move.move_line_nosuggest_ids.mapped('done_bucket'))

class InheritStockMoveLine(models.Model):
    _inherit = "stock.move.line"

    done_bucket = fields.Float(string="Done (Bucket/Bags/Pouch)")
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)

class InheritStockQuant(models.Model):
    _inherit = "stock.quant"

    on_hand_bucket = fields.Float(string="On Hand (Bucket/Bags/Pouch)")

class inheriteStockLocation(models.Model):
    _inherit = "stock.location"

    main_store_location = fields.Boolean(string="Is a Main Store Location?",tracking=True)
