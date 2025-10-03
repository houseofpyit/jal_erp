from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class inheritedResCountry(models.Model):
   _inherit = "res.country"
   
   continent_type = fields.Selection([('africa', 'Africa'),('antarctica', 'Antarctica'),('asia', 'Asia'),('europe', 'Europe'),('north_america', 'North America'),('oceania', 'Oceania'),('south_america', 'South America'),],string="Continent")