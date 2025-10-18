from odoo import models, fields, _, api
from odoo.exceptions import UserError, ValidationError


class ShiftgMst(models.Model):
    _name = 'shift.mst'
    _description = 'Shift Master'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Name',tracking=True)
    line_ids = fields.One2many('shift.time.line', 'mst_id')


class ShiftgTimeLine(models.Model):
    _name = 'shift.time.line'
    _description = 'Shift Time Line'
    
    mst_id = fields.Many2one('shift.mst',string="Mst",ondelete='cascade')
    name = fields.Char(string='Name')
    start_time = fields.Float(string='Start Time')
    end_time = fields.Float(string='End Time')

    def name_get(self):
        def float_to_time(float_time):
            hours = int(float_time)
            minutes = int(round((float_time - hours) * 60))
            return f"{hours:02d}:{minutes:02d}"

        res = []
        for rec in self:
            name = rec.name or ""
            if rec.start_time and rec.end_time:
                start = float_to_time(rec.start_time)
                end = float_to_time(rec.end_time)
                name = f"{name} ({start} - {end})"
            res.append((rec.id, name))
        return res

