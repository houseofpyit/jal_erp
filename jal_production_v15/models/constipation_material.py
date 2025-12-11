from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime
from ...transaction import common_file

class ConstipationMaterial(models.Model):
    _name = 'constipation.material'
    _description = 'Constipation Material'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    bill_chr = fields.Char(tracking=True)
    bill_no =  fields.Integer(required=True,copy=False,tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    line_ids = fields.One2many('constipation.material.line', 'mst_id')
    state = fields.Selection([('draft', 'Draft'),('complete', 'Complete')], default='draft',tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Employee',tracking=True)
    department_id = fields.Many2one('hr.department', string='Department',tracking=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.department_id = self.employee_id.department_id.id

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
        bill_rec = self.env['constipation.material'].search([('bill_chr','=',vals.get('bill_chr')),('bill_no','=',vals.get('bill_no')),('company_id','=',vals.get('company_id'))]) 
        if bill_rec:
            vals['bill_no'] = self.bill_chr_vld(vals.get('bill_chr'),vals.get('company_id'),vals.get('date'))
        res = super(ConstipationMaterial, self).create(vals)
        res._onchange_chr_no()

        return res

    def write(self, vals):

        res = super(ConstipationMaterial, self).write(vals)
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

        pt_rec = self.env['constipation.material'].search(domain) 
        if pt_rec:
            raise ValidationError("Bill Number Must Be Unique !! ")

        return res
    
    @api.onchange('bill_chr')
    def _onchange_bill_chr(self):
        self.bill_no = self.bill_chr_vld()

    def bill_chr_vld(self,str_order_chr=False,company_id=False,entry_date=False):
        company_id = str(self.env.company.id) if self.env.company.id else str(company_id)
        query = ''' Select max(bill_no) From constipation_material Where company_id = ''' + str(company_id)
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
        self._create_stock_picking_out()
        self.state = 'complete'

    def _create_stock_picking_out(self):
        StockQuant = self.env['stock.quant'].sudo()
        StockLocation = self.env['stock.location'].sudo()
        StockPickingType = self.env['stock.picking.type'].sudo()
        StockPicking = self.env['stock.picking'].sudo()

        main_location = StockLocation.search([('main_store_location', '=', True)], limit=1)
        if not main_location:
            raise ValidationError(_("Main Store Location not found!"))

        des_location = StockLocation.search([('consumption_location', '=', True)], limit=1)
        if not des_location:
            raise ValidationError(_("No Consumption location found!"))

        picking_type = StockPickingType.search([('code', '=', 'internal')], limit=1)
        if not picking_type:
            raise ValidationError(_("Internal Picking Type not found!"))


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


        _validate_lines(self.line_ids, "Products Materials")

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


        _prepare_moves(self.line_ids)
        
        picking = StockPicking.create({
            'location_id': main_location.id,
            'location_dest_id': des_location.id,
            'picking_type_id': picking_type.id,
            'constipation_material_id': self.id,
            'origin': f"{self.name} - Internal",
            'move_line_ids_without_package': move_list,
            'scheduled_date': fields.Datetime.now(),
        })
        picking.with_context(is_consumption=True).action_confirm()
        self.env.context = dict(self.env.context, skip_backorder=True)
        picking.button_validate()
    
class ConstipationMaterialPackLine(models.Model):
    _name = 'constipation.material.line'
    _description = "Constipation Material Line"

    mst_id = fields.Many2one('constipation.material',string="Mst",ondelete='cascade')
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
