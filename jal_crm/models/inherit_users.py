from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritResUsers(models.Model):
   _inherit = "res.users"
   
   crm_team_id = fields.Many2one('crm.team',string="Sales Team ")