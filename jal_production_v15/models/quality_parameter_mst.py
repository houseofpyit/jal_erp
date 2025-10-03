from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ProductAttribute(models.Model):
    _name = 'jal.product.attribute'
    _inherit = ['mail.thread']
    _description = "Product Attribute"

    name = fields.Char(string="Name",tracking=True)
    company_id = fields.Many2one('res.company',string="Comapany",default=lambda self: self.env.company.id)

class QualityValue(models.Model):
    _name = 'quality.value'
    _inherit = ['mail.thread']
    _description = "Quality Value"

    name = fields.Char(string="Parameter",required=True,tracking=True)
    calculation_type = fields.Selection([
        ('range','Range'),
        ('visual','Visual'),
        ('=','='),
        ('<','<'),
        ('>','>'),
        ('<=','<='),
        ('>=','>='),
    ],string="Calculation",required=True,tracking=True)
    fr_value = fields.Float(string="From Value",tracking=True)
    to_value = fields.Float(string="To Value",tracking=True)
    req_value = fields.Float(string="Value",tracking=True)
    remarks = fields.Text(string="Remarks",tracking=True)
    company_id = fields.Many2one('res.company',string="Comapany",default=lambda self: self.env.company.id)


    def name_get(self):
        result = []
        for i in self:
            if i.calculation_type == 'range':
                name = i.name + '(' + str(i.fr_value) + ' To ' + str(i.to_value) + ')'
            if i.calculation_type != 'range':
                name = i.name + '(' + i.calculation_type + ' ' +str(i.req_value) + ')'
            if i.calculation_type == 'visual':
                name = i.name
            result.append((i.id, name))
        return result