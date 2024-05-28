from odoo import fields, models, api
from ..settings.constants import settings


class ChooseDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def default_get(self, fields_list):
        values = super(ChooseDeliveryCarrier, self).default_get(fields_list)
        if (not values.get('ahamove_service_id') and 'active_model' in self._context
                and self._context.get('active_model') == 'sale.order'):
            sale_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            if sale_id and sale_id.warehouse_id and sale_id.warehouse_id.default_ahamove_service_id:
                values['service_id'] = sale_id.warehouse_id.default_ahamove_service_id.id
        return values

    service_id = fields.Many2one('ahamove.service', string='Service')
    service_request_domain = fields.Binary(default=[])
    service_request_ids = fields.Many2many('ahamove.service.request', 'estimate_request_rel',
                                           'choose_id', 'request_id', string='Request Type')
    promo_code = fields.Char(string='Promotion Code')

    @api.onchange('service_id')
    def _onchange_service_id(self):
        for rec in self:
            if rec.service_id:
                rec.service_request_domain = [('service_id', '=', rec.service_id.id)]

    def _get_shipment_rate(self):
        if self.carrier_id.delivery_type == settings.ahamove_code:
            context = dict(self.env.context)
            context.update({
                'ahamove_service': self.service_id.code,
                'ahamove_request': [rec.code for rec in self.service_request_ids],
                'promo_code': self.promo_code
            })
            self.env.context = context
        return super(ChooseDeliveryCarrier, self)._get_shipment_rate()
