from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date,datetime

class JalLogistics(models.Model):
    _name = 'jal.logistics'
    _description = 'Logistics'
    _inherit = ['mail.thread']
    _order = "id desc"

    name = fields.Char(copy=False, index=True, default=lambda self: _('New'),tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    date = fields.Date(copy=False,string="Date",default=fields.Date.context_today)
    user_id = fields.Many2one('res.users',string="User",default=lambda self: self.env.user.id)
    sale_id = fields.Many2one('sale.order',string="Proforma Invoice")
    state = fields.Selection([('pending', 'Pending'),('pi_confirm', 'PI Confirm'),('booking_confirm', 'Booking Confirm'),('done', 'Done')], default='pending',tracking=True)

    # Pre-Shipment
    booking_id = fields.Many2one('booking.agent.mst',string="Booking Agent",tracking=True)
    transport_id = fields.Many2one('transport.agent.mst',string="Transport Agent",tracking=True)
    cha_id = fields.Many2one('cha.mst',string="CHA",tracking=True)
    shipping_id = fields.Many2one('product.shipping.mst',string="Shipping Name",tracking=True)
    hbl_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='HBL',tracking=True)
    booking_date = fields.Date(string="Booking Date",tracking=True)
    booking_received = fields.Char(string="Booking Received",tracking=True)
    planning_details = fields.Char(string="Planning Details",tracking=True)
    loading_planner = fields.Char(string="Loading Planner",tracking=True)
    planning_index = fields.Selection([('Urgent', 'Urgent'),('Hot', 'Hot'),('mild', 'Mild'),('cold', 'Cold')], string='Planning index',tracking=True)
    remarks = fields.Text(string="Remarks",tracking=True)

    total_containers = fields.Char(string="Total Containers",tracking=True)
    shipping_line_id = fields.Many2one('shipping.line.mst',string="Shipping line",tracking=True)
    freight_per_container = fields.Char(string="Freight per Container",tracking=True)
    vessel_date = fields.Date(string="Vessel cut-off date",tracking=True)
    container_stuffing_date = fields.Date(string="Container stuffing date",tracking=True)
    port_id = fields.Many2one('sale.port.mst',string="Port of Loading",tracking=True)
    loading_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='Loading Inspection',tracking=True)
    inspection_id = fields.Many2one('inspection.mst',string="Inspection Company",tracking=True)
    inspection_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='Inspection Scheduled',tracking=True)
    inspection_name = fields.Char(string="Inspector Name",tracking=True)
    inspection_date = fields.Date(string="Inspection Date",tracking=True)
    inspection_remarks = fields.Text(string="Inspection Remarks",tracking=True)

    # Dispatch
    attachment_batch_ids = fields.Many2many('ir.attachment','attachment_batch_id',string="Batch Label")
    attachment_branding_ids = fields.Many2many('ir.attachment','attachment_branding_id',string="Branding Label")
    attachment_packing_ids = fields.Many2many('ir.attachment','attachment_packing_id',string="Packing Photo")
    attachment_container_ids = fields.Many2many('ir.attachment','attachment_container_id',string="Container Photo")
    attachment_lr_ids = fields.Many2many('ir.attachment','attachment_lr_id',string="LR Copy of the Container")

    dispatch_line_ids = fields.One2many('logistics.dispatch.line','mst_id',string="Line Dispatch")

    # Documents
    epcg_liscence_used = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='EPCG Liscence Used')
    epcg_liscence_number = fields.Many2one('epcg.liscence.mst',string='EPCG Liscence Number')
    epcg_liscence_date = fields.Date(string='EPCG Liscence Date')
    advanced_liscence_used = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Advance Liscence Used')
    advanced_liscence_number = fields.Many2one('advanced.liscence.mst',string='Advanced Liscence Number')
    advanced_liscence_date = fields.Date(string='Advanced Liscence Date')
    rodtep_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Rodtep Claimed')
    rodtep_amount = fields.Char(string='Rodtep Amount')
    duty_drawback_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Duty Drawback Claimed')
    duty_drawback_amount = fields.Char(string='Duty Drawback Amount')
    lut_shipment = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Lut Shipment')
    lut_no = fields.Char(string='Lut No')
    gst_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='GST Claimed')
    gst_value = fields.Char(string='GST Value')  

    # Shipement Details
    invoice_number = fields.Char(string='Invoice Number',tracking=True)
    date = fields.Date(string='Invoice Date',default=fields.Date.context_today,tracking=True)
    total_cif_value = fields.Float(string='Total CIF Value',tracking=True)
    cif_currency_id = fields.Many2one('res.currency', string='CIF Currency',tracking=True)
    total_fob_value = fields.Float(string='Total FOB Value',tracking=True)
    fob_currency_id = fields.Many2one('res.currency', string='FOB Currency',tracking=True)
    total_freight_value = fields.Float(string='Total Freight Value',tracking=True)
    freight_currency_id = fields.Many2one('res.currency', string='Freight Currency',tracking=True)
    total_insurance_value = fields.Float(string='Total Insurance Value',tracking=True)
    insurance_currency_id = fields.Many2one('res.currency', string='Insurance Currency',tracking=True)
    total_net_wt_qty = fields.Float(string='Total Net Weight Quantity',tracking=True)
    net_wt_uom_id = fields.Many2one('uom.uom',string="Net Weight Quantity")
    total_gross_wt_qty = fields.Float(string='Total Gross Weight Quantity',tracking=True)
    gross_wt_uom_id = fields.Many2one('uom.uom',string="Gross Weight Quantity")

    @api.model
    def create(self, vals):
        result = super(JalLogistics, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.logistics.seq') or _('New')
        return result
    
    @api.onchange('epcg_liscence_used')
    def _onchange_epcg_liscence_used(self):
        if self.epcg_liscence_used == 'yes':
            self.duty_drawback_claimed = 'no'
        else:
            self.duty_drawback_claimed = ''

    @api.onchange('epcg_liscence_number')
    def _onchange_epcg_liscence_number(self):
        self.epcg_liscence_date = self.epcg_liscence_number.date


    @api.onchange('advanced_liscence_used')
    def _onchange_advanced_liscence_used(self):
        if self.advanced_liscence_used == 'yes':
            self.lut_shipment = 'no'
        else:
            self.lut_shipment = ''

    @api.onchange('advanced_liscence_number')
    def _onchange_advanced_liscence_number(self):
        self.advanced_liscence_date = self.advanced_liscence_number.date

    @api.onchange('lut_shipment')
    def _onchange_lut_shipment(self):
        if self.lut_shipment == 'yes':
            if self.advanced_liscence_used == 'yes':
                self.lut_shipment = 'no'
                return {
                    'warning': {
                        'title': "Validation",
                        'message': "You cannot set Lut Shipment to 'Yes' because Advance Liscence Used is already 'Yes'.",                    }
                }

            self.gst_claimed = 'no'
        else:
            self.gst_claimed = ''

    @api.onchange('gst_claimed')
    def _onchange_gst_claimed(self):
        if self.gst_claimed == 'yes':
            self.lut_shipment = 'no'
    
    @api.onchange('duty_drawback_claimed')
    def _onchange_duty_drawback_claimed(self):
        if self.duty_drawback_claimed == 'yes' and self.epcg_liscence_used == 'yes':
            self.duty_drawback_claimed = 'no'
            return {
                'warning': {
                    'title': "Validation",
                    'message': "You cannot set Duty Drawback Claimed to 'Yes' because EPCG Licence Used is already 'Yes'.",                    }
            }
        
    def action_booking_confirm(self):
        mo_rec = self.env['jal.mrp.production'].search([('sale_id', 'in', self.sale_id.ids)])
        for mo in mo_rec:
            mo.booking_date = date.today()
        for pic in self.sale_id.picking_ids:
            if pic.state != 'done':
                pic.booking_date = date.today()
        self.booking_date = date.today()
        self.state = 'booking_confirm'

    def action_done(self):
        self.state = 'done'

class LogisticsDispatchLine(models.Model):
    _name = 'logistics.dispatch.line'
    _description = 'Logistics Dispatch Line'
    _order = "id desc"

    mst_id = fields.Many2one('jal.logistics',string="Mst",ondelete='cascade')

    container_no = fields.Char(string="Container No")
    seal_no = fields.Char(string="Seal No")
    itek_seal_no = fields.Char(string="Itek Seal No")
    container_size = fields.Char(string="Container Size and type (Dry/Reefer)")
    total_drums = fields.Float(string="Total drums / container")
    lr_no = fields.Char(string="LR No")
    truck_no = fields.Char(string="Truck No")
    transport_id = fields.Many2one('transport.agent.mst',string="Transport Name")
    load_kg = fields.Float(string="Maximum Allowed Load (Kg)")
    tare_wt = fields.Float(string="Tare Wt. (Kg)")
    total_gross = fields.Float(string="Total Gross Including Tare")
    total_gross = fields.Float(string="Weighment Slip No")

    line_ids = fields.One2many('dispatch.packing.line','mst_id',string="Line Dispatch packing")

    palletized_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Palletized')
    palletized_line1_ids = fields.One2many('palletized1.line','mst_id',string="Palletized Line 1")
    palletized_line2_ids = fields.One2many('palletized2.line','mst_id',string="Palletized Line 2")
    palletized_line_ids = fields.One2many('palletized.line','mst_id',string="Palletized Line")
    truck_detention_line_ids = fields.One2many('truck.detention.line','mst_id',string="Truck Detention Line")

    detention_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Detention Applicable')
    detention_amount = fields.Float(string='Detention Amount')
    reason_detention = fields.Text(string='Reason for Detention')

class DispatchPackingLine(models.Model):
    _name = 'dispatch.packing.line'
    _description = 'Dispatch Packing Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    sale_line_id = fields.Many2one('sale.order.line',string="Packing Type (Name)")
    sale_id = fields.Many2one(related='mst_id.mst_id.sale_id',string="Proforma Invoice")
    qty = fields.Float(string="No. of Units.")


class Palletized1Line(models.Model):
    _name = 'palletized1.line'
    _description = 'Palletized1 Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    pallet_id = fields.Many2one('pallet.size.mst',string="Pallet Size")
    bucket_qty = fields.Integer(string="Bucket Qty")
    sale_id = fields.Many2one(related='mst_id.mst_id.sale_id',string="Proforma Invoice")
    sale_line_id = fields.Many2one('sale.order.line',string="Bucket Type")


class Palletized2Line(models.Model):
    _name = 'palletized2.line'
    _description = 'Palletized2 Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    pallet_id = fields.Many2one('pallet.size.mst',string="Pallet Size")
    bucket_qty = fields.Integer(string="Bucket Qty")
    sale_id = fields.Many2one(related='mst_id.mst_id.sale_id',string="Proforma Invoice")
    sale_line_id = fields.Many2one('sale.order.line',string="Bucket Type")


class PalletizedLine(models.Model):
    _name = 'palletized.line'
    _description = 'Palletized Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    sale_id = fields.Many2one(related='mst_id.mst_id.sale_id',string="Proforma Invoice")
    sale_line_id = fields.Many2one('sale.order.line',string="Bucket Type")
    line_ids = fields.One2many('layer.line','mst_id',string="Line Layer")


class LayerLine(models.Model):
    _name = 'layer.line'
    _description = 'Layer Line'
    _order = "id desc"

    mst_id = fields.Many2one('palletized.line',string="Mst",ondelete='cascade')

    name = fields.Char(string="Description")
    qty = fields.Float(string="Qty")

class TruckDetentionLine(models.Model):
    _name = 'truck.detention.line'
    _description = 'Truck Detention Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    date = fields.Date(string="Truck Arrival Date")
    time = fields.Float(string="Truck Arrival Time")
    dep_date = fields.Date(string="Truck Departure Date")
    dep_time = fields.Float(string="Truck Departure Time")
    