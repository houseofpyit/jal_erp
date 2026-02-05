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
    from_location_id = fields.Many2one('stock.location',string="From Location",tracking=True)
    # from_location_id = fields.Many2one('stock.location',string="From Location",tracking=True,default=lambda self: self.env.user.location_id.id)
    to_location_id = fields.Many2one('stock.location',string="To Location",tracking=True)
    # to_location_id = fields.Many2one('stock.location',string="To Location",tracking=True,default=lambda self: self.env['stock.location'].sudo().search([('main_store_location', '=', True),('company_id', '=', self.env.company.id)],limit=1))
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    line_ids = fields.One2many('jal.material.line', 'mst_id')

    @api.model
    def create(self, vals):
        result = super(JalMaterialRequisition, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.material.requisition.seq') or _('New')
        
        return result
    
    def action_complete_btn(self):
        self._create_stock_picking_Transit()
        self.state = 'done'

    def _create_stock_picking_Transit(self):
        StockQuant = self.env['stock.quant']
        StockPickingType = self.env['stock.picking.type']
        StockPicking = self.env['stock.picking']

        if not self.from_location_id:
            raise ValidationError(_("Please select a From Location first."))
        
        if not self.to_location_id:
            raise ValidationError(_("Please select a To Location first."))

        picking_type = StockPickingType.search([('code', '=', 'internal')], limit=1)
        if not picking_type:
            raise ValidationError(_("Internal Picking Type not found!"))


        def _validate_lines(lines, line_type):
            for line in lines:

                if not line.product_id:
                    raise ValidationError(_("Please select a product for %s.") % line_type)

                if line.demand_qty <= 0:
                    raise ValidationError(_("%s Demand quantity must be > 0 for product %s.") % (line_type, line.product_id.display_name))

                domain = [('product_id', '=', line.product_id.id),('location_id', '=', self.from_location_id.id)]

                stock_quants = StockQuant.search(domain)

                available_qty = sum(stock_quants.mapped('available_quantity'))
                if available_qty < line.demand_qty:
                    raise ValidationError(_("Insufficient Demand Quantity for %s. Available %s, Required %s.") % (line.product_id.display_name, available_qty, line.qty))


        _validate_lines(self.line_ids, "Products In ")

        move_list = []

        def _prepare_moves(lines):
            for line in lines:

                required_qty = line.demand_qty

                quants = StockQuant.search([('product_id', '=', line.product_id.id),('location_id', '=', self.from_location_id.id),('quantity', '>', 0)])

                remaining_qty = required_qty

                for quant in quants:

                    take_qty = min(quant.available_quantity, remaining_qty)

                    if take_qty <= 0:
                        continue

                    move_vals = {
                        'product_id': line.product_id.id,
                        'qty_done': take_qty,
                        'product_uom_id': line.uom_id.id,
                        'location_id': self.from_location_id.id,
                        'location_dest_id': self.to_location_id.id,
                    }

                    move_list.append((0, 0, move_vals))

                    remaining_qty -= take_qty

                    if remaining_qty <= 0:
                        break


        _prepare_moves(self.line_ids)
        
        picking = StockPicking.create({
            'location_id': self.from_location_id.id,
            'location_dest_id': self.to_location_id.id,
            'picking_type_id': picking_type.id,
            'product_transformation_id': self.id,
            'origin': f"{self.name} - Transit",
            'move_line_ids_without_package': move_list,
            'scheduled_date': fields.Datetime.now(),
        })
        picking.action_confirm()
        picking.action_assign()
        self.env.context = dict(self.env.context)
        self.env.context.update({'skip_backorder': True})
        picking.button_validate()

class JalProductionLine(models.Model):
    _name = 'jal.material.line'
    _description = "Material Line"

    mst_id = fields.Many2one('jal.material.requisition',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    demand_qty = fields.Float(string = "Demand Quantity")
    available_qty = fields.Float(string = "Available Quantity")
    remarks = fields.Char(string="Remarks")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.uom_id = False
            rec.available_qty = 0.0
            if not rec.product_id:
                return

            rec.uom_id = rec.product_id.uom_po_id.id

            quants = self.env['stock.quant'].search([
                ('product_id', '=', rec.product_id.id),
                ('company_id', '=', rec.company_id.id),
                ('location_id.usage', '=', 'internal'),
            ])
            rec.available_qty = sum(quants.mapped('quantity'))