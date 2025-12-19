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
    
    def unlink(self):
        for i in self:
            if i.state == 'complete':
                raise ValidationError("You cannot delete this record because it is already marked as Complete.")
            if i.state == 'running':
                raise ValidationError("You cannot delete this record because it is already marked as Running.")
        return super(JalProduction,self).unlink()
    
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        line_list = []
        packing_line_list = []
        for raw_line in self.product_tmpl_id.rawmaterial_line_ids:
            line_list.append((0,0,{
                'product_id': raw_line.product_id.id,
                'uom_id': raw_line.uom_id.id,
                }))
        for pac_line in self.product_tmpl_id.packing_line_ids:
            packing_line_list.append((0,0,{
                'product_id': pac_line.product_id.id,
                'uom_id': pac_line.uom_id.id,
                }))
            
        self.line_ids = line_list
        self.packing_line_ids = packing_line_list


    def action_running_btn(self):
        self.state = 'running'

    def action_get_quality_btn(self):
        quality_rec = self.env['jal.quality'].search([('production_id', 'in', self.ids),('state', '=', 'complete')])
        if not quality_rec:
            raise ValidationError(_("No Quality record found for Production: %s") % (self.name or ""))

        merged = {}

        for qual in quality_rec:
            for line in qual.quality_grade_ids:

                domain = [
                    ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.grade_id.id),
                    ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.mesh_id.id),
                    # ('product_template_attribute_value_ids.product_attribute_value_id', '=', line.bucket_id.id),
                ]
                products = self.env['product.product'].search(domain)
                
                product_id = products.id if len(products) == 1 else False
                domain_ids = products.ids if len(products) == 1 else self.env['product.product'].search([]).ids
                uom_id = products.uom_id.id if len(products) == 1 else False
                key = (line.product_id)

                if key not in merged:
                    merged[key] = {
                        'grade_id': line.grade_id.id,
                        'mesh_id': line.mesh_id.id,
                        # 'bucket_id': line.bucket_id.id,
                        'bucket_qty': line.no_of_drum,
                        'qty': line.weight,
                        'product_id': line.product_id.id,
                        'product_doamin_ids': [(6, 0, domain_ids)],
                        'uom_id': line.uom_id.id,
                    }
                else:
                    merged[key]['bucket_qty'] += line.no_of_drum
                    merged[key]['qty'] += line.weight

        final_lines = [(0, 0, vals) for vals in merged.values()]

        self.finished_line_ids = [(5, 0, 0)] + final_lines

    def action_complete_btn(self):
        self._create_stock_picking_receipts()
        self._create_stock_picking_out()
        self.state = 'complete'

    def _create_stock_picking_receipts(self):
        for line in self.finished_line_ids:
            if not line.product_id and ((line.extra_qty or 0) > 0 or (line.extra_weight or 0) > 0):
                raise ValidationError(_("Please select a product for finished lines before proceeding."))

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
            if line.extra_qty > 0 or line.extra_weight > 0:
                move_vals = {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.extra_qty,
                    'demand_bucket': line.extra_weight,
                    'done_bucket': line.extra_weight,
                    'product_uom': line.uom_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': main_location.id,
                    'move_line_ids': [(0, 0, {
                        'product_id': line.product_id.id,
                        'qty_done': line.extra_qty,
                        'done_bucket': line.extra_weight,
                        'product_uom_id': line.uom_id.id,
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
    #                 f"Finished Goods in Quantity must be greater than 0 for product: {line.product_id.display_name}"
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
    #             'product_uom_qty': line.qty,
    #             'demand_bucket': line.bucket_qty,
    #             'done_bucket': line.bucket_qty,
    #             'product_uom': line.uom_id.id,
    #             'location_id': src_location.id,
    #             'location_dest_id': main_location.id,
    #             'move_line_ids': [(0, 0, {
    #                 'product_id': line.product_id.id,
    #                 'qty_done': line.qty,
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

    def _create_stock_picking_out(self):
        StockQuant = self.env['stock.quant'].sudo()
        StockLocation = self.env['stock.location'].sudo()
        StockPickingType = self.env['stock.picking.type'].sudo()
        StockPicking = self.env['stock.picking'].sudo()

        main_location = StockLocation.search([('main_store_location', '=', True)], limit=1)
        if not main_location:
            raise ValidationError(_("Main Store Location not found!"))

        des_location = StockLocation.search([('usage', '=', 'customer')], limit=1)
        if not des_location:
            raise ValidationError(_("No Vendor/Partner location found!"))

        picking_type = StockPickingType.search([('code', '=', 'outgoing')], limit=1)
        if not picking_type:
            raise ValidationError(_("Outgoing Picking Type not found!"))


        def _validate_lines(lines, line_type):
            for line in lines:

                if not line.product_id:
                    raise ValidationError(_("Please select a product for %s.") % line_type)

                if line.qty <= 0:
                    raise ValidationError(_("%s quantity must be > 0 for product %s.") % (line_type, line.product_id.display_name))

                if line.product_id.tracking in ('lot', 'serial') and not line.lot_ids:
                    raise ValidationError(_("%s: Please select lot/serial for product %s.") % (line_type, line.product_id.display_name))

                domain = [('product_id', '=', line.product_id.id),('location_id', '=', main_location.id)]

                if line.lot_ids:
                    domain.append(('lot_id', 'in', line.lot_ids.ids))

                stock_quants = StockQuant.search(domain)

                available_qty = sum(stock_quants.mapped('available_quantity'))
                if available_qty < line.qty:
                    raise ValidationError(_("Insufficient QTY for %s. Available %s, Required %s.") % (line.product_id.display_name, available_qty, line.qty))

                available_bucket = sum(stock_quants.mapped('on_hand_bucket'))
                if available_bucket < line.bucket:
                    raise ValidationError(_("Insufficient BUCKET for %s. Available %s, Required %s.") % (line.product_id.display_name, available_bucket, line.bucket))


        _validate_lines(self.line_ids, "Raw Materials")
        _validate_lines(self.packing_line_ids, "Packing Materials")


        for line in self.finished_line_ids:

            if not line.product_id:
                raise ValidationError(_("Select a product for Finished Goods."))

            domain = [('product_id', '=', line.product_id.id),('location_id', '=', main_location.id)]

            stock_quants = StockQuant.search(domain)

            available_qty = sum(stock_quants.mapped('available_quantity'))
            if available_qty < line.wastage_qty:
                raise ValidationError(_("Insufficient finished QTY for %s. Available %s, Required %s.") % (line.product_id.display_name, available_qty, line.wastage_qty))

            available_bucket = sum(stock_quants.mapped('on_hand_bucket'))
            if available_bucket < line.wastage_weight:
                raise ValidationError(_("Insufficient finished BUCKET for %s. Available %s, Required %s.") % (line.product_id.display_name, available_bucket, line.wastage_weight))


        move_list = []

        def _prepare_moves(lines):
            for line in lines:

                required_qty = line.qty
                required_bucket = line.bucket

                quants = StockQuant.search([('product_id', '=', line.product_id.id),('location_id', '=', main_location.id),('quantity', '>', 0)])

                if line.lot_ids:
                    quants = quants.filtered(lambda q: q.lot_id.id in line.lot_ids.ids)

                remaining_qty = required_qty
                remaining_bucket = required_bucket

                for quant in quants:

                    take_qty = min(quant.available_quantity, remaining_qty)
                    take_bucket = min(quant.on_hand_bucket, remaining_bucket)

                    if take_qty <= 0 and take_bucket <= 0:
                        continue

                    move_vals = {
                        'product_id': line.product_id.id,
                        'qty_done': take_qty,
                        'demand_bucket': take_bucket,
                        'done_bucket': take_bucket,
                        'product_uom_id': line.uom_id.id,
                        'location_id': main_location.id,
                        'location_dest_id': des_location.id,
                    }

                    if line.product_id.tracking in ('lot', 'serial') and quant.lot_id:
                        move_vals['lot_id'] = quant.lot_id.id

                    move_list.append((0, 0, move_vals))

                    remaining_qty -= take_qty
                    remaining_bucket -= take_bucket

                    if remaining_qty <= 0 and remaining_bucket <= 0:
                        break


        _prepare_moves(self.line_ids)
        _prepare_moves(self.packing_line_ids)

        for line in self.finished_line_ids:

            required_qty = line.wastage_qty
            required_bucket = line.wastage_weight

            quants = StockQuant.search([('product_id', '=', line.product_id.id),('location_id', '=', main_location.id),('quantity', '>', 0)])

            remaining_qty = required_qty
            remaining_bucket = required_bucket

            for quant in quants:

                take_qty = min(quant.available_quantity, remaining_qty)
                take_bucket = min(quant.on_hand_bucket, remaining_bucket)

                if take_qty <= 0 and take_bucket <= 0:
                    continue

                move_vals = {
                    'product_id': line.product_id.id,
                    'qty_done': take_qty,
                    'demand_bucket': take_bucket,
                    'done_bucket': take_bucket,
                    'product_uom_id': line.uom_id.id,
                    'location_id': main_location.id,
                    'location_dest_id': des_location.id,
                }

                move_list.append((0, 0, move_vals))

                remaining_qty -= take_qty
                remaining_bucket -= take_bucket

                if remaining_qty <= 0 and remaining_bucket <= 0:
                    break

        if move_list:
            picking = StockPicking.create({
                'location_id': main_location.id,
                'location_dest_id': des_location.id,
                'picking_type_id': picking_type.id,
                'production_id': self.id,
                'origin': f"{self.name} - Outgoing",
                'move_line_ids_without_package': move_list,
                'scheduled_date': fields.Datetime.now(),
            })
            picking.action_confirm()
            self.env.context = dict(self.env.context, skip_backorder=True)
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
    lot_ids = fields.Many2many('stock.production.lot', string='Lot/Serial',domain="[('product_id', '=', product_id),('product_qty', '>', 0)]")
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    bucket = fields.Float(string='Packing Unit')
    product_tracking = fields.Selection(related='product_id.tracking')
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)
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
    lot_ids = fields.Many2many('stock.production.lot', string='Lot/Serial',domain="[('product_id', '=', product_id),('product_qty', '>', 0)]")
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    bucket = fields.Float(string='Packing Unit')
    product_tracking = fields.Selection(related='product_id.tracking')
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)
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
    product_id = fields.Many2one('product.product')
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string="Weight")
    bucket_qty = fields.Integer(string="No of Drum")
    wastage_qty = fields.Integer(string="Wastage Qty")
    wastage_weight = fields.Float(string="Wastage Weight")
    extra_qty = fields.Integer(string="Extra Qty")
    extra_weight = fields.Float(string="Extra Weight")
    grade_id = fields.Many2one('product.attribute.value',string="Grade",domain="[('attribute_id.attribute_type','=','grade')]")
    mesh_id = fields.Many2one('product.attribute.value',string="Mesh",domain="[('attribute_id.attribute_type','=','mesh')]")
    bucket_id = fields.Many2one('product.attribute.value',string="Bucket",domain="[('attribute_id.attribute_type','=','bucket')]")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    product_doamin_ids = fields.Many2many('product.product','product_doamin_ref_id')

    @api.onchange('bucket_qty')
    def _onchange_bucket_qty(self):
        if self.bucket_qty > 0:
            if self.bucket_id.amount > 0:
                self.qty = self.bucket_qty * self.bucket_id.amount
        else:
            self.qty = 0

    @api.onchange('product_id','wastage_qty')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

                rec.wastage_weight = rec.wastage_qty * rec.product_id.drum_cap_id.weight
                
    @api.onchange('grade_id', 'mesh_id', 'bucket_id')
    def _onchange_product_attributes(self):
        if not (self.grade_id and self.mesh_id):
            self.product_id = False
            return {'domain': {'product_id': []}}
        domain = [
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.grade_id.id),
            ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.mesh_id.id),
            # ('product_template_attribute_value_ids.product_attribute_value_id', '=', self.bucket_id.id),
        ]

        products = self.env['product.product'].search(domain)

        if products:
            self.product_id = products[0].id
            self.product_doamin_ids = [(6, 0, products.ids)]
            return {'domain': {'product_id': [('id', 'in', products.ids)]}}
        else:
            self.product_id = False
            all_products = self.env['product.product'].search([])
            self.product_doamin_ids = [(6, 0, all_products.ids)]
            return {'domain': {'product_id': [('id', 'in', all_products.ids)]}}

