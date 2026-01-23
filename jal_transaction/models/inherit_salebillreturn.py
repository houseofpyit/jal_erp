from odoo import models, fields, api, _
from odoo.exceptions import UserError


class inheritHopSaleBillReturn(models.Model):
    _inherit = "hop.salebillreturn"

    business_type = fields.Selection(
        [
            ("international", "International"),
            ("domestic", "Domestic"),
            ("trading", "Trading")
        ],
        string="Business Type",
        tracking=True
    )

    stage = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'Done'),
        ],
        string='Status',
        default='draft',
        readonly=True,
        tracking=True
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string="Stock Picking",
        readonly=True,
        copy=False
    )

    def action_confirm(self):
        StockPicking = self.env['stock.picking']

        for rec in self:
            if rec.picking_id:
                raise UserError("Stock Picking already created.")

            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', rec.company_id.id)],
                limit=1
            )
            if not warehouse:
                raise UserError("Warehouse not found for company.")

        
            src_location = self.env['stock.location'].search(
                [('usage', '=', 'customer'),
                 ('company_id', 'in', [rec.company_id.id, False])],
                limit=1
            )

            dest_location = warehouse.lot_stock_id

            picking_type = self.env['stock.picking.type'].search(
                [
                    ('warehouse_id', '=', warehouse.id),
                    ('code', '=', 'incoming')
                ],
                limit=1
            )

            if not picking_type:
                raise UserError("Incoming picking type not found.")

            move_lines = []
            for line in rec.line_id:
                if line.pcs <= 0:
                    raise UserError("PCS must be greater than zero.")

                move_lines.append((0, 0, {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.pcs,
                    'product_uom': line.unit_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': dest_location.id,
                }))

            picking = StockPicking.create({
                'picking_type_id': picking_type.id,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
                'origin': f"Sale Return {rec.name}",
                'move_ids_without_package': move_lines,
            })

            rec.picking_id = picking.id
            rec.stage = 'done'

            rec.message_post(
                body=f"""
                <b>Sale Return Receipt Created</b><br/>
                Receipt:
                <a href=# data-oe-model='stock.picking' data-oe-id='{picking.id}'>
                    {picking.name}
                </a><br/>
                <i>Stock will be added after validating the receipt.</i>
                """,
                subtype_xmlid="mail.mt_note"
            )

    def action_view_picking(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Receipt',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'target': 'current',
        }
