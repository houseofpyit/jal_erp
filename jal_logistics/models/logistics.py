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
    # state = fields.Selection([('pending', 'Pending'),('pi_confirm', 'PI Confirm'),('booking_confirm', 'Booking Confirm'),('done', 'Done')], default='pending',tracking=True)
    state = fields.Selection([('pre_shipment', 'Pre-Shipment'),('dispatch_document', 'Dispatch/Document'),('post_shipment', 'Post Shipment'),('close', 'Close'),('cancel', 'Cancel')], default='pre_shipment',tracking=True)
    notes = fields.Html(string="Notes")

    # Pre-Shipment
    booking_id = fields.Many2one('res.partner',string="Booking Agent",tracking=True)
    transport_id = fields.Many2one('res.partner',string="Transport Agent",tracking=True)
    cha_id = fields.Many2one('cha.mst',string="CHA",tracking=True)
    shipping_id = fields.Many2one('product.shipping.mst',string="Shipping Name",tracking=True)
    hbl_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='HBL',tracking=True)
    booking_date = fields.Date(string="Booking Date",tracking=True)
    booking_received = fields.Date(string="Booking Received",tracking=True)
    planning_details = fields.Char(string="Planning Details",tracking=True)
    loading_planner_id = fields.Many2one('loading.planner.mst',string="Loading Planner",tracking=True)
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

    attachment_invoice_pre_ids = fields.Many2many('ir.attachment','attachment_invoice_pre_id',string="Invoice")
    attachment_packing_list_ids = fields.Many2many('ir.attachment','attachment_packing_list_id',string="packing list")
    attachment_iip1_ids = fields.Many2many('ir.attachment','attachment_iip1_id',string="IIP")
    attachment_msds_ids = fields.Many2many('ir.attachment','attachment_msds_id',string="MSDS")
    attachment_booking_copy_ids = fields.Many2many('ir.attachment','attachment_booking_copy_id',string="Booking copy")
    hold_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='Hold',tracking=True)
    remarks_hold = fields.Text(string='Hold Remark',tracking=True)

    haz_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='HAZ Label',tracking=True)
    label_remark_id = fields.Many2one('label.remark.mst',string='HAZ Remark',tracking=True)
    dead_fish_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='Dead Fish Label',tracking=True)
    label_remark1_id = fields.Many2one('label.remark.mst',string='HAZ Remark',tracking=True)
    un_printing_type = fields.Selection([('Yes', 'Yes'),('No', 'No')], string='UN Printing Label',tracking=True)
    label_remark2_id = fields.Many2one('label.remark.mst',string='HAZ Remark',tracking=True)

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
        ], string='EPCG Liscence Used',tracking=True)
    epcg_liscence_number = fields.Many2one('epcg.liscence.mst',string='EPCG Liscence Number',tracking=True)
    epcg_liscence_date = fields.Date(string='EPCG Liscence Date',tracking=True)
    advanced_liscence_used = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Advance Liscence Used',tracking=True)
    advanced_liscence_number = fields.Many2one('advanced.liscence.mst',string='Advanced Liscence Number',tracking=True)
    advanced_liscence_date = fields.Date(string='Advanced Liscence Date',tracking=True)
    rodtep_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Rodtep Claimed',tracking=True)
    rodtep_amount = fields.Char(string='Rodtep Amount',tracking=True)
    duty_drawback_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Duty Drawback Claimed',tracking=True)
    duty_drawback_amount = fields.Char(string='Duty Drawback Amount',tracking=True)
    lut_shipment = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Lut Shipment',tracking=True)
    lut_no = fields.Char(string='Lut No',tracking=True)
    gst_claimed = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='GST Claimed',tracking=True)
    gst_value = fields.Char(string='GST Value',tracking=True )

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

    # Documents for Customs
    attachment_invoice_ids = fields.Many2many('ir.attachment','attachment_invoice_id',string="Commercial invoice")
    attachment_packing_ph_ids = fields.Many2many('ir.attachment','attachment_packing_ph_id',string="Packing List")
    attachment_hazard_ids = fields.Many2many('ir.attachment','attachment_hazard_id',string="Hazard Declaration form")
    attachment_tax_invoice_ids = fields.Many2many('ir.attachment','attachment_tax_invoice_id',string="Tax Invoice")
    attachment_annexure_ids = fields.Many2many('ir.attachment','attachment_annexure_id',string="Annexure - A")
    attachment_examination_ids = fields.Many2many('ir.attachment','attachment_examination_id',string="Self- examination form")
    attachment_certificate_ids = fields.Many2many('ir.attachment','attachment_certificate_id',string="Certificate of Analysis")
    attachment_iip_ids = fields.Many2many('ir.attachment','attachment_iip_id',string="IIP-Copies")
    attachment_vgm_slip_ids = fields.Many2many('ir.attachment','attachment_vgm_slip_id',string="VGM slip")

    # Documentation for the Customer
    attachment_invoice1_ids = fields.Many2many('ir.attachment','attachment_invoice1_id',string="Commercial invoice")
    attachment_packing_ph1_ids = fields.Many2many('ir.attachment','attachment_packing_ph1_id',string="Packing List")
    attachment_certificate1_ids = fields.Many2many('ir.attachment','attachment_certificate1_id',string="Certificate of Origin")
    attachment_bill_ids = fields.Many2many('ir.attachment','attachment_bill_id',string="Bill of Lading Draft")
    attachment_certificate2_ids = fields.Many2many('ir.attachment','attachment_certificate2_id',string="Certificate of Analysis")
    attachment_insurance_ids = fields.Many2many('ir.attachment','attachment_insurance_id',string="Insurance")

    # Post Shipment
    bill_number = fields.Char(string='Shipping bill number',tracking=True)
    bill_date = fields.Date(string='Shipping bill date',tracking=True)
    attachment_shipping_ids = fields.Many2many('ir.attachment','attachment_shipping_id',string="Upload shipping bill document")

    bill_lading_line_ids = fields.One2many('bill.lading.line','mst_id',string="Bill Lading Dispatch")

    attachment_final_ladings_ids = fields.Many2many('ir.attachment','attachment_ladings1_id',string="Final Bill of lading")
    bi_date2 = fields.Date(string='BI date',tracking=True)

    bl_status_type = fields.Selection([
            ('scan_bl_pending', 'Scan BL Pending'),
            ('linder_draft_in_progress', 'Linder Draft in Progress'),
            ('surrender_draft_in_progress', 'Surrender Draft in Progress'),
        ], string='Status',tracking=True)

    bl_type = fields.Selection([
            ('surrender', 'Surrender'),
            ('courier', 'Courier'),
        ], string='Type of BL',tracking=True)
    balance_type = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Balance payment received',tracking=True)
    payment_remark = fields.Text(string='Payment Remarks',tracking=True)
    sale_team_type = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Sales team BL released confirmation',tracking=True)
    acoount_team_type = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Accounts team BL release confirmation',tracking=True)
    
    # SHIPPING INVOICES MANAGEMENT
    
    freight_inv_number = fields.Char(string='Freight invoices Number',tracking=True)
    attachment_freight_inv_ids = fields.Many2many('ir.attachment','attachment_freight_inv_id',string="Freight invoices")
    transport_inv_number = fields.Char(string='Transport invoices Number',tracking=True)
    attachment_transport_inv_ids = fields.Many2many('ir.attachment','attachment_transport_inv_id',string="Transport invoices")
    remarks_log_team = fields.Char(string='Remarks by logistic team',tracking=True)
    remarks_agent_team = fields.Char(string='Remarks by agent team',tracking=True)

    detention_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Detention',tracking=True)
    detention_amount = fields.Float(string='DetentionTotal Detention amount (INR)',tracking=True)
    detention_reason = fields.Char(string='Reason for Detention',tracking=True)
    late_bl_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Late Bl',tracking=True)
    late_bl_charges = fields.Float(string='Late Bl charges',tracking=True)
    bl_correction_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Bl correction',tracking=True)
    bl_correction_charges = fields.Float(string='Bl correction charges',tracking=True)
    inspection_chr_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Inspection charges',tracking=True)
    comments_log_team = fields.Char(string='Comments by the logistic team',tracking=True)
    comments_agent_team = fields.Char(string='Comments by the agent team',tracking=True)

    shipping_route = fields.Char(string="Shipping Route",tracking=True)
    shipping_line1_id = fields.Many2one('shipping.line.mst',string="Shipping line",tracking=True)
    transit_days = fields.Integer(string="Transit days",tracking=True)
    eta = fields.Date(string="ETA")
    etd = fields.Datetime(string="ETD")
    management_remarks = fields.Char(string="Remarks")
    is_finish_booking = fields.Boolean(string="Is Finish Booking")

    container_management_line_ids = fields.One2many('logistics.container.management.line','mst_id',string="Line Container Management")

    delivery_count = fields.Integer(string='Delivery Orders', compute="compute_logistics_delivery_count")

    @api.depends('sale_id','state')
    def compute_logistics_delivery_count(self):
        for order in self:
            order.delivery_count = len(order.sale_id.picking_ids)

    def action_view_logistics_delivery(self):
        return self.sale_id._get_action_view_picking(self.sale_id.picking_ids)

    @api.model
    def create(self, vals):
        result = super(JalLogistics, self).create(vals)
        if vals.get('name', _('New')) == _('New'):
            result['name'] = self.env['ir.sequence'].next_by_code('jal.logistics.seq') or _('New')
        return result
    
    def default_get(self, fields):
        res = super(JalLogistics, self).default_get(fields)
        usd = self.env.ref('base.USD').id
        res['cif_currency_id'] = usd
        res['fob_currency_id'] = usd
        res['freight_currency_id'] = usd
        res['insurance_currency_id'] = usd

        mt = self.env['uom.uom'].search([('name', '=', 'MT')], limit=1).id
        res['net_wt_uom_id'] = mt
        res['gross_wt_uom_id'] = mt
        return res
    
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
        
    def action_start_booking(self):
        self.booking_date = date.today()

    def action_finish_booking(self):
        if not self.container_stuffing_date:
            raise ValidationError("Please enter the Container Stuffing Date before finishing the booking.")

        if not self.booking_received:
            raise ValidationError("Please confirm the Booking Received Date before finishing the booking.")
        
        mo_rec = self.env['jal.mrp.production'].search([('sale_id', 'in', self.sale_id.ids)])
        for mo in mo_rec:
            mo.booking_date = self.container_stuffing_date
        for pic in self.sale_id.picking_ids:
            if pic.state != 'done':
                pic.booking_date = self.container_stuffing_date

        self.is_finish_booking = True

    def action_move_document(self):
        self.state = 'dispatch_document'

    def action_post_shipment(self):
        self.state = 'post_shipment'

    def action_close(self):
        self.state = 'close'

    def action_document_order_form(self):
        return self.env.ref('jal_crm.action_order_form_report').report_action(self.sale_id.id)

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
    transport_id = fields.Many2one('res.partner',string="Transport Name")
    load_kg = fields.Float(string="Maximum Allowed Load (Kg)")
    tare_wt = fields.Float(string="Tare Wt. (Kg)")
    total_gross = fields.Float(string="Total Gross Including Tare")
    total_gross = fields.Float(string="Weighment Slip No")
    label_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Label directly inside container',default='no')
    label_remark = fields.Char(string='Remarks')
    product_expiry = fields.Selection(related='mst_id.sale_id.product_expiry', string="Product Expiry")
    batch_number = fields.Char(string='Batch number')
    
    line_ids = fields.One2many('dispatch.packing.line','mst_id',string="Line Dispatch packing")

    palletized_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Palletized',default='no')
    palletized_line1_ids = fields.One2many('palletized1.line','mst_id',string="Palletized Line 1")
    palletized_line2_ids = fields.One2many('palletized2.line','mst_id',string="Palletized Line 2")
    palletized_line_ids = fields.One2many('palletized.line','mst_id',string="Palletized Line")

    date = fields.Date(string="Truck Arrival Date")
    time = fields.Float(string="Truck Arrival Time")
    dep_date = fields.Date(string="Truck Departure Date")
    dep_time = fields.Float(string="Truck Departure Time")

    detention_type = fields.Selection([('yes', 'Yes'),('no', 'No'),], string='Detention Applicable',default='no')
    detention_amount = fields.Float(string='Detention Amount')
    reason_detention = fields.Text(string='Reason for Detention')

    @api.onchange('line_ids','line_ids.qty')
    def _onchange_line_ids(self):
        self.total_drums = sum(self.line_ids.mapped('qty'))

class DispatchPackingLine(models.Model):
    _name = 'dispatch.packing.line'
    _description = 'Dispatch Packing Line'
    _order = "id desc"

    mst_id = fields.Many2one('logistics.dispatch.line',string="Mst",ondelete='cascade')

    sale_line_id = fields.Many2one('sale.order.line',string="Stuffing Description")
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

class LogisticsContainerManagementLine(models.Model):
    _name = 'logistics.container.management.line'
    _description = 'Logistics Container Management Line'
    _order = "id desc"

    mst_id = fields.Many2one('jal.logistics',string="Mst",ondelete='cascade')

    name = fields.Char(string="Container No")
    check_eta = fields.Date(string="Check ETA")
    remarks = fields.Char(string="Remarks")
    
class BillLadingLine(models.Model):
    _name = 'bill.lading.line'
    _description = 'Bill of Lading Line'
    _order = "id desc"

    mst_id = fields.Many2one('jal.logistics',string="Mst",ondelete='cascade')

    attachment_ladings_ids = fields.Many2many(
        'ir.attachment',
        'jal_logistic_lading_rel',        # relation table name
        'logistic_id',                    # column referring to this model
        'attachment_id',                  # column referring to ir.attachment
        string="Draft Bill of Lading"
    )
    bi_date = fields.Date(string='Date',tracking=True)
    bi_type = fields.Selection([
            ('yes', 'Yes'),
            ('no', 'No'),
        ], string='Draft Bl Approved',tracking=True)
    comments_bi = fields.Char(string='Draft BL Change Comments',tracking=True)