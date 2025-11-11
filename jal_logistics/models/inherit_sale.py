from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re
    
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