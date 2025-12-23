from odoo import api, models, fields
from datetime import date,datetime
from odoo.exceptions import ValidationError

class SaleAproveWiz(models.TransientModel):
    _name = 'sale.aprove.wiz'
    _description= "Sale Approve Wiz"

    name = fields.Text(string="Comment")
    aprove_type = fields.Selection([("account", "Account"), ("dispatch", "Dispatch"), ("saleteam", "Saleteam")],string="Approve Type")

    def action_approve_btn(self):
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        sale_order = self.env[active_model].browse(active_id)
        line_list = []
        if sale_order:
            line_list.append((0,0,{
                'user_id': self.env.user.id,
                'date':fields.Datetime.now(),
                'comment':self.name,
                'aprove_type':self.aprove_type,
                }))
            
            sale_order.sale_approve_ids = line_list
            if self.aprove_type == 'account':
                if sale_order.is_acc_approve:
                    sale_order.is_acc_approve_pi = True
                else:
                    sale_order.is_acc_approve = True
            if self.aprove_type == 'dispatch':
                sale_order.is_dis_approve = True
            if self.aprove_type == 'saleteam':
                if sale_order.is_team_approve:
                    sale_order.is_team_approve_pi = True
                else:
                    sale_order.is_team_approve = True