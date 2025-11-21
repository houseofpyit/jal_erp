from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
from datetime import date,datetime

class InheritSale(models.Model):
    _inherit = 'sale.order'

    mo_count = fields.Integer(string="MO Count", copy=False,help="Count of the created sale for MO")
    logistics_count = fields.Integer(string="Lead Count", copy=False,help="Count of the created sale for Logistics")

    def action_create_pi(self):
        res = super(InheritSale, self).action_create_pi()
        for line in self.order_line:
            line_list = []
            packing_line_list = []
            for raw_line in line.product_id.rawmaterial_line_ids:
                line_list.append((0,0,{
                    'product_id': raw_line.product_id.id,
                    'uom_id': raw_line.uom_id.id,
                    'qty': line.product_uom_qty * raw_line.qty,
                    }))
            for pac_line in line.product_id.packing_line_ids:
                packing_line_list.append((0,0,{
                    'product_id': pac_line.product_id.id,
                    'uom_id': pac_line.uom_id.id,
                    'qty': line.product_uom_qty * pac_line.qty,
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
    
    def action_confirm_pi(self):
        logistics_rec = self.env['jal.logistics'].search([('sale_id', 'in', self.ids)])
        for log in logistics_rec:
            log.state = 'pi_confirm'
        self.state = 'sale'

    @api.depends('company_id.account_fiscal_country_id', 'fiscal_position_id.country_id', 'fiscal_position_id.foreign_vat')
    def _compute_tax_country_id(self):
        res = super(InheritSale, self)._compute_tax_country_id()
        for line in self:
            line.mo_count = len(self.env['jal.mrp.production'].search([('sale_id', '=', line.id)]))
            line.logistics_count = len(self.env['jal.logistics'].search([('sale_id', '=', line.id)]))
        return res
    
    def action_view_mo(self):
        mo_rec = self.env['jal.mrp.production'].search([('sale_id', 'in', self.ids)])
        if len(mo_rec) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'MO',
                'view_mode': 'form',
                'res_model': 'jal.mrp.production',
                'res_id': mo_rec.id,
                'context': {'create': False},
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'MO',
            'view_mode': 'tree,form',
            'res_model': 'jal.mrp.production',
            'domain': [('id', 'in', mo_rec.ids)],
            'context': {'create': False},
        }

    def action_view_logistics(self):
        logistics_rec = self.env['jal.logistics'].search([('sale_id', 'in', self.ids)])
        if len(logistics_rec) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Logistics',
                'view_mode': 'form',
                'res_model': 'jal.logistics',
                'res_id': logistics_rec.id,
                'context': {'create': False},
            }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Logistics',
            'view_mode': 'tree,form',
            'res_model': 'jal.logistics',
            'domain': [('id', 'in', logistics_rec.ids)],
            'context': {'create': False},
        }
    
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