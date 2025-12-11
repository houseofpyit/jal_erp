from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime
from ...transaction import common_file

class ProductTransformation(models.Model):
    _name = 'product.transformation'
    _description = 'Product Transformation'
    _inherit = ['mail.thread']
    _order = "id desc"


    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    bill_chr = fields.Char(tracking=True)
    bill_no =  fields.Integer(required=True,copy=False,tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    packing_line_ids = fields.One2many('product.transformation.pack.line', 'mst_id')
    finished_line_ids = fields.One2many('product.transformation.finish.line', 'mst_id')
    state = fields.Selection([('draft', 'Draft'),('complete', 'Complete')], default='draft',tracking=True)
    packing_type = fields.Selection([("bucket", "Bucket"), ("pouch", "Pouch"),("tablet", "Tablet")],string="Packing Type",tracking=True)
    product_id = fields.Many2one('product.product', string='Product',tracking=True)
    uom_id = fields.Many2one('uom.uom', string='Uom',tracking=True)
    qty = fields.Float(string='Qty',tracking=True)
    bucket = fields.Float(string='Packing Unit',tracking=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.uom_id = self.product_id.uom_po_id.id

    @api.onchange('bill_chr','bill_no')
    def _onchange_chr_no(self):
        if self.bill_chr:
            self.name = str(self.bill_chr)+ str(self.bill_no)
        else:
            self.name = self.bill_no

    @api.model
    def create(self, vals):
        if vals.get('bill_no') == None:
            vals['bill_no'] = self.bill_chr_vld()
        bill_rec = self.env['product.transformation'].search([('bill_chr','=',vals.get('bill_chr')),('bill_no','=',vals.get('bill_no')),('company_id','=',vals.get('company_id'))]) 
        if bill_rec:
            vals['bill_no'] = self.bill_chr_vld(vals.get('bill_chr'),vals.get('company_id'),vals.get('date'))
        res = super(ProductTransformation, self).create(vals)
        res._onchange_chr_no()

        return res

    def write(self, vals):

        res = super(ProductTransformation, self).write(vals)
        domain = [('id','!=',self.id),('bill_chr','=',self.bill_chr),('bill_no','=',self.bill_no),('company_id','=',self.company_id.id)]
        if self.env.user.fy_year_id:
            domain.append(('date','>=',self.env.user.fy_from_date))
            domain.append(('date','<=',self.env.user.fy_to_date))
            domain.append(('opening','=','n'))
        if not self.env.user.fy_year_id:
            entry_date = vals.get('date') if vals.get('date') else self.date 
            date_year = common_file.get_fy_year(str(entry_date))
            domain.append(('date','>=',date_year[0]))
            domain.append(('date','<=',date_year[1]))
            domain.append(('opening','=','n'))

        pt_rec = self.env['product.transformation'].search(domain) 
        if pt_rec:
            raise ValidationError("Bill Number Must Be Unique !! ")

        return res
    
    @api.onchange('bill_chr')
    def _onchange_bill_chr(self):
        self.bill_no = self.bill_chr_vld()

    def bill_chr_vld(self,str_order_chr=False,company_id=False,entry_date=False):
        company_id = str(self.env.company.id) if self.env.company.id else str(company_id)
        query = ''' Select max(bill_no) From product_transformation Where company_id = ''' + str(company_id)
        if self.bill_chr:
            query += " and bill_chr = '" + self.bill_chr + "'"
        elif str_order_chr:
            query += " and bill_chr = '" + str_order_chr + "'"
        else:
            query += " and bill_chr IS NULL"
        if self.env.user.fy_year_id:
            query += " and date >=  " +"'" + str(self.env.user.fy_from_date) +"'"
            query += " and date <=  " +"'" + str(self.env.user.fy_to_date) +"'"
        if not self.env.user.fy_year_id:
            date_year = common_file.get_fy_year(entry_date)
            query += " and date >=  '" + str(date_year[0]) +"'"
            query += " and date <=  '" + str(date_year[1]) +"'"

        self.env.cr.execute(query)
        query_result = self.env.cr.dictfetchall()
        if query_result[0]['max'] == None :
            serial = 1
        else:
            serial = 1 + query_result[0]['max']
        return serial
    
    def action_complete_btn(self):
        self._create_stock_picking_receipts()
        self._create_stock_picking_out()
        self.state = 'complete'

    def _create_stock_picking_receipts(self):
        if not self.finished_line_ids:
            raise ValidationError("No finished products to receive!")

        for line in self.finished_line_ids:
            if not line.product_id:
                raise ValidationError(
                     _("Please select a product for finished lines before proceeding.")
                )
            
            if line.qty <= 0:
                raise ValidationError(
                    f"Finished Goods in Quantity must be greater than 0 for product: {line.product_id.display_name}"
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
                'demand_bucket': line.bucket,
                'done_bucket': line.bucket,
                'product_uom': line.uom_id.id,
                'location_id': src_location.id,
                'location_dest_id': main_location.id,
                # 'move_line_ids': [(0, 0, {
                #     'product_id': line.product_id.id,
                #     'qty_done': line.qty,
                #     'done_bucket': line.bucket,
                #     'product_uom_id': line.uom_id.id,
                #     'location_id': src_location.id,
                #     'location_dest_id': main_location.id,
                #     'date': fields.Datetime.now(),
                # })],
            }
            move_list.append((0, 0, move_vals))
        
        picking = self.env['stock.picking'].sudo().create({
            'location_id': src_location.id,
            'location_dest_id': main_location.id,
            'picking_type_id': picking_type.id,
            'product_transformation_id': self.id,
            'origin': f"{self.name} - Receipt",
            'move_ids_without_package': move_list,
            'scheduled_date': fields.Datetime.now(),
        })

        picking.action_confirm()
        picking.action_assign()
        self.env.context = dict(self.env.context, skip_backorder=True)
        picking.action_set_quantities_to_reservation()
        picking.button_validate()


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

                domain = [('product_id', '=', line.product_id.id),('location_id', '=', main_location.id)]

                stock_quants = StockQuant.search(domain)

                available_qty = sum(stock_quants.mapped('available_quantity'))
                if available_qty < line.qty:
                    raise ValidationError(_("Insufficient QTY for %s. Available %s, Required %s.") % (line.product_id.display_name, available_qty, line.qty))

                available_bucket = sum(stock_quants.mapped('on_hand_bucket'))
                if available_bucket < line.bucket:
                    raise ValidationError(_("Insufficient BUCKET for %s. Available %s, Required %s.") % (line.product_id.display_name, available_bucket, line.bucket))


        _validate_lines(self, "")
        _validate_lines(self.packing_line_ids, "Packing Materials")

        move_list = []

        def _prepare_moves(lines):
            for line in lines:

                required_qty = line.qty
                required_bucket = line.bucket

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


        _prepare_moves(self.packing_line_ids)
        _prepare_moves(self)
        
        picking = StockPicking.create({
            'location_id': main_location.id,
            'location_dest_id': des_location.id,
            'picking_type_id': picking_type.id,
            'product_transformation_id': self.id,
            'origin': f"{self.name} - Outgoing",
            'move_line_ids_without_package': move_list,
            'scheduled_date': fields.Datetime.now(),
        })
        picking.action_confirm()
        self.env.context = dict(self.env.context, skip_backorder=True)
        picking.button_validate()
    
class ProductTransformationPackLine(models.Model):
    _name = 'product.transformation.pack.line'
    _description = "Product Transformation Pack Line"

    mst_id = fields.Many2one('product.transformation',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    bucket = fields.Float(string='Packing Unit')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id

class ProductTransformationFinishLine(models.Model):
    _name = 'product.transformation.finish.line'
    _description = "Product Transformation Finish Line"

    mst_id = fields.Many2one('product.transformation',string="Mst",ondelete='cascade')
    product_id = fields.Many2one('product.product',required=True)
    uom_id = fields.Many2one('uom.uom',string="Unit")
    qty = fields.Float(string = "Quantity",digits='BaseAmount')
    bucket = fields.Float(string='Packing Unit')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_po_id.id