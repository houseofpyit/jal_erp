from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import date,datetime

class inheriteStockPicking(models.Model):
    _inherit = "stock.picking"

    production_id = fields.Many2one('jal.production',string="Production")
    quality_id = fields.Many2one('jal.quality',string="Quality")
    product_transformation_id = fields.Many2one('product.transformation',string="Product Transformation")
    constipation_material_id = fields.Many2one('constipation.material',string="Constipation Material")
    send_quality = fields.Boolean(string="Send For Quality")
    purchase_quality_count = fields.Integer("Purchase Quality count")
    booking_date = fields.Date(string="Booking Date",tracking=True)
    purchase_bill_count = fields.Integer(string='Purchase Bill', compute='compute_calculate_bill' )
    
    def button_validate(self):
        for line in self.move_lines:
            if self.picking_type_code == 'incoming' and line.quality_result == 'wt_for_qt':
                raise ValidationError(f"Product '{line.product_id.display_name}' is still waiting for quality test. Please complete the quality check before confirming.")
        res = super(inheriteStockPicking,self).button_validate()
        return res
    
    def action_create_invoice(self):
        line_list = []
        for line in self.move_ids_without_package:
            order_line_rec = self.env['purchase.order.line'].search([('id','=',line.purchase_line_id.id),('product_id','=',line.product_id.id)])
            line_list.append((0,0,{
                        'order_id':order_line_rec.order_id.id,
                        'order_line_id':order_line_rec.id,
                        'product_id':line.product_id.id,
                        'pcs':line.actual_qty if line.is_caustic else line.quantity_done,
                        'cost_center_id': order_line_rec.cost_id.id,
                        'hsn_id': order_line_rec.hsn_id.id,
                        'rate':order_line_rec.price_unit,
                        # 'pcs': order_line_rec.pcs,
                        'amount': order_line_rec.price_subtotal,
                        'gst_ids': [(6, 0, order_line_rec.gst_ids.ids)],
                        'disc_amt': order_line_rec.disc_amt,
                        'disc_per': order_line_rec.disc_per,
                        'add_amt': order_line_rec.add_amt,
                        'sgst_amt': order_line_rec.sgst_amt,
                        'cgst_amt': order_line_rec.cgst_amt,
                        'igst_amt': order_line_rec.igst_amt,
                        'final_amt': order_line_rec.final_amt,
                    }))

        bill_chr = 'BILL'
        bill_no = self.env['hop.purchasebill'].bill_chr_vld(bill_chr,self.env.company.id,date.today())
        purchase_bill_rec =self.env['hop.purchasebill'].create({
            'bill_chr': bill_chr,
            'bill_no': bill_no,
            'name': str(bill_chr)+ str(bill_no),
            'party_id':self.partner_id.id,
            'bill_number':self.vendor_bill_no,
            'date':date.today(),
            'rd_urd':self.partner_id.rd_urd,
            'picking_id':self.id,
            'due_days':self.partner_id.due_days,
            'line_id':line_list
        })
        for line in purchase_bill_rec.line_id:
            line._onchange_calc_amt()
        purchase_bill_rec._final_amt_calculate()

    def compute_calculate_bill(self):
        for i in self:
            i.purchase_bill_count = self.env['hop.purchasebill'].search_count([('picking_id', '=', i.id)])

    def action_view_bill(self):
        bill_rec = self.env['hop.purchasebill'].sudo().search([('picking_id', '=', self.id)])
        if len(bill_rec) == 1:
            return {
            'name': 'Bill',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'hop.purchasebill',
            'res_id': bill_rec.id,
            'context': {'create': False}
            }
        else:
            return {
            'name': 'Bill',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'hop.purchasebill',
            'domain': [('id', 'in', bill_rec.ids)],
            'context': {'create': False}
            }
    
    def action_confirm(self):
        res = super(inheriteStockPicking,self).action_confirm()
        if self.picking_type_code == 'incoming':
            for line in self.move_lines:
                stock_move = self.env['stock.move.line'].search([('picking_id', '=', line.picking_id.id),('product_id', '=', line.product_id.id)])
                stock_move.write({'done_bucket': line.demand_bucket})
        if self.picking_type_code == 'outgoing' or self.env.context.get('is_consumption', False) == True:
            for line in self.move_line_ids_without_package:
                stock_move = self.env['stock.move'].search([('picking_id', '=', line.picking_id.id),('product_id', '=', line.product_id.id)])
                stock_move.write({'demand_bucket': line.demand_bucket,'done_bucket': line.demand_bucket})
        return res
    
    def action_set_quantities_to_reservation(self):
        res = super(inheriteStockPicking,self).action_set_quantities_to_reservation()
        if self.picking_type_code == 'incoming':
            for line in self.move_lines:
                stock_move = self.env['stock.move.line'].search([('picking_id', '=', line.picking_id.id),('product_id', '=', line.product_id.id)])
                stock_move.write({'done_bucket': line.demand_bucket})
                line.write({'done_bucket': stock_move.done_bucket})
        return res
    
    def _compute_hide_pickign_type(self):
        res = super(inheriteStockPicking,self)._compute_hide_pickign_type()
        for pic in self:
            pic.purchase_quality_count = self.env['jal.purchase.quality'].sudo().search_count([('picking_id', '=', pic.id)]) or 0
        return res
    
    def get_action_view_purchase_quality(self):
        self.ensure_one()
        actions = self.env["ir.actions.actions"]._for_xml_id('jal_production_v15.action_jal_purchase_quality')
        quality_rec = self.env['jal.purchase.quality'].sudo().search([('picking_id', '=', self.id)])
        if quality_rec and len(quality_rec) > 1:
            actions['domain'] = [('id', 'in', quality_rec.ids)]
        elif len(quality_rec) == 1:
            res = self.env.ref('jal_production_v15.jal_purchase_quality_view_form', False)
            form_view = [(res and res.id or False, 'form')]
            actions['views'] = form_view + [(state, view) for state, view in actions.get('views', []) if view != 'form']
            actions['res_id'] = quality_rec.id
        return actions
        
    def create_purchase_quality(self):
        for line in self.move_lines:
            line_list = []
            if line.product_id.is_quality_required and line.quality_result == 'wt_for_qt':
                for par in line.product_id.quality_para_ids:
                    line_list.append((0,0,{
                    'item_attribute': par.item_attribute.id,
                    'required_value':par.required_value.id,
                    'parameter_remarks':par.remarks,
                    }))

                quality = self.env['jal.purchase.quality'].sudo().create({
                        'product_id': line.product_id.id,
                        'purchase_id': self.purchase_id.id,
                        'picking_id': self.id,
                        'qty': line.product_uom_qty,
                        'uom_id':line.product_uom.id,
                        'send_date':date.today(),
                        'company_id': self.company_id.id,
                        'line_ids': line_list,
                    })
        self.send_quality = True
    
class InheritStockMove(models.Model):
    _inherit = "stock.move"

    demand_bucket = fields.Float(string="Demand (Bucket/Bags/Pouch)")
    done_bucket = fields.Float(string="Done (Bucket/Bags/Pouch)")
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)
    is_caustic = fields.Boolean(related='product_id.is_caustic',string="Caustic Product")
    quality_per = fields.Float(string="Quality (%)")
    actual_qty = fields.Float(string="Actual Qty")
    quality_result = fields.Selection([
        ('wt_for_qt','Waiting For Quality'),
        ('pass','Pass'),
        ('fail','Fail'),
    ],string="Quality Result")

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
    demand_bucket = fields.Float(string="Demand (Bucket/Bags/Pouch)")
    uom_handling_type = fields.Selection(related='product_id.uom_handling_type',string="UoM Handling Type",store=False)

class InheritStockQuant(models.Model):
    _inherit = "stock.quant"

    on_hand_bucket = fields.Float(string="On Hand Packing Unit")

class inheriteStockLocation(models.Model):
    _inherit = "stock.location"

    main_store_location = fields.Boolean(string="Is a Main Store Location?",tracking=True)
    consumption_location = fields.Boolean(string="Consumption Location?",tracking=True)
