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
        if sale_order:
            if self.aprove_type == 'account':
                sale_order.acc_user_id = self.env.user.id
                sale_order.acc_date = fields.Datetime.now()
                sale_order.acc_comment = self.name

            if self.aprove_type == 'dispatch':
                sale_order.dis_user_id = self.env.user.id
                sale_order.dis_date = fields.Datetime.now()
                sale_order.dis_comment = self.name
            
            if self.aprove_type == 'saleteam':
                sale_order.team_user_id = self.env.user.id
                sale_order.team_date = fields.Datetime.now()
                sale_order.team_comment = self.name
