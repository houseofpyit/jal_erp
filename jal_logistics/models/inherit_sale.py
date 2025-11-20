from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
from datetime import date,datetime

class InheritSale(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(InheritSale, self).action_confirm()
        for line in self.order_line:
            line_list = []
            packing_line_list = []
            for raw_line in line.product_id.rawmaterial_line_ids:
                line_list.append((0,0,{
                    'product_id': raw_line.product_id.id,
                    'uom_id': raw_line.uom_id.id,
                    'qty': line.product_uom_qty * line.product_id.drum_cap_id.weight,
                    }))
            for pac_line in line.product_id.packing_line_ids:
                packing_line_list.append((0,0,{
                    'product_id': pac_line.product_id.id,
                    'uom_id': pac_line.uom_id.id,
                    'qty': line.product_uom_qty * line.product_id.drum_cap_id.weight,
                    }))

            mrp_production_rec = self.env['jal.mrp.production'].sudo().create({
                    'sale_id': self.id,
                    'date':date.today(),
                    'company_id': self.company_id.id,
                    'product_id': line.product_id.id,
                    'uom_id': line.product_uom.id,
                    'qty': line.product_uom_qty,
                    'line_ids': line_list,
                    'packing_line_ids': packing_line_list,
                })
        
        logistics_rec = self.env['jal.logistics'].sudo().create({
                'sale_id': self.id,
                'date':date.today(),
                'company_id': self.company_id.id,
            })
        
        return res
    
class inheritedSaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def name_get(self):
        result = []
        for rec in self:
            print("---------super(inheritedSaleOrderLine, rec).name_get()----",super(inheritedSaleOrderLine, rec).name_get())
            if rec.env.context.get('show_packing_name'):
                # Clean HTML tags from packing_name
                name = re.sub('<[^<]+?>', '', rec.packing_name or '')
            else:
                name = super(inheritedSaleOrderLine, rec).name_get()[0][1]
            result.append((rec.id, name))
        return result


    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         if rec.env.context.get('show_packing_name'):
    #             # Strip HTML tags for safe display
    #             clean_name = re.sub('<[^<]+?>', '', rec.packing_name or '')
    #             # Optionally shorten it if it’s long
    #             short_name = (clean_name[:120] + '...') if len(clean_name) > 120 else clean_name
    #             result.append((rec.id, short_name))
    #         else:
    #             result += super(inheritedSaleOrderLine, rec).name_get()
    #     return result