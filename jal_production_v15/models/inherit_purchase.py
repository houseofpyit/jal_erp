from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    purchase_quality_count = fields.Integer("Purchase Quality count")
    product_ids = fields.Many2many('product.product','ref_product',string="Products")

    @api.depends('picking_ids')
    def _compute_incoming_picking_count(self):
        res = super(inheritedPurchaseOrder, self)._compute_incoming_picking_count()
        for rec in self:
            rec.purchase_quality_count = self.env['jal.purchase.quality'].sudo().search_count([('purchase_id', '=', rec.id)]) or 0
        return res
    
    def get_action_view_purchase_quality(self):
        self.ensure_one()
        actions = self.env["ir.actions.actions"]._for_xml_id('jal_production_v15.action_jal_purchase_quality')
        quality_rec = self.env['jal.purchase.quality'].sudo().search([('purchase_id', '=', self.id)])
        if quality_rec and len(quality_rec) > 1:
            actions['domain'] = [('id', 'in', quality_rec.ids)]
        elif len(quality_rec) == 1:
            res = self.env.ref('jal_production_v15.jal_purchase_quality_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            actions['views'] = form_view + [(state, view) for state, view in actions.get('views', []) if view != 'form']
            actions['res_id'] = quality_rec.id
        return actions
    
    def action_fetch(self):
        lines_to_add = []
        for product in self.product_ids:
            vals = {
                'name': product.name,
                'product_id': product.id,
                'cost_id': product.cost_id.id,
                'product_uom': product.uom_id.id,
                'hsn_id': product.hsn_id.id,
            }
            lines_to_add.append((0, 0, vals))

        self.order_line = [(5, 0, 0)] + lines_to_add
        for line in self.order_line:
            line._onchange_hsn_id()

        self.product_ids = False

class inheritedPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    bucket = fields.Float(string='(Bucket/Bags/Pouch)',store=True)
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super(inheritedPurchaseOrderLine, self)._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        res.update({'demand_bucket':self.bucket})
        res.update({'quality_result':'wt_for_qt' if self.product_id.is_quality_required else ''})
        return res