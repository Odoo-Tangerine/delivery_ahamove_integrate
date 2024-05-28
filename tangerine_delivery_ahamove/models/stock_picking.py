from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.tools import ustr
from odoo.exceptions import UserError
from odoo.addons.tangerine_delivery_base.settings import utils
from ..settings.constants import settings
from ..api.client import Client
from ..api.connection import Connection


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    ahamove_service_id = fields.Many2one('ahamove.service', string='Service Type',
                                         default=lambda self: self.picking_type_id.warehouse_id.default_ahamove_service_id.id)
    ahamove_service_request_ids = fields.Many2many('ahamove.service.request', 'picking_request_rel',
                                                   'picking_id', 'request_id', string='Request Type')
    ahamove_service_request_domain = fields.Binary(default=[], store=False)
    ahamove_payment_method = fields.Selection(selection=settings.payment_method, string='Payment Method',
                                              default=settings.default_payment_method)

    ahamove_shared_link = fields.Char(string='Shared Link')

    @api.onchange('ahamove_service_id')
    def _onchange_ahamove_service_id(self):
        for rec in self:
            if rec.ahamove_service_id:
                rec.ahamove_service_request_domain = [('service_id', '=', rec.ahamove_service_id.id)]

    def _ahamove_create_purchase_order_for_delivery_cost(self):
        self.ensure_one()
        partner_id = self.env.ref('tangerine_delivery_ahamove.tangerine_delivery_ahamove_provider')
        fpos = self.env['account.fiscal.position'].sudo()._get_fiscal_position(partner_id)
        po_id = self.env['purchase.order'].create({
            'company_id': self.sale_id.company_id.id,
            'currency_id': self.sale_id.company_id.currency_id.id,
            'origin': self.sale_id.name,
            'fiscal_position_id': fpos.id,
            'dest_address_id': False,
            'user_id': self.env.uid,
            'partner_id': partner_id.id,
            'partner_ref': partner_id.ref,
            'picking_type_id': self.picking_type_id.warehouse_id.in_type_id.id,
            'order_line': [(0, 0, {
                'product_id': self.carrier_id.product_id.id,
                'name': f'{self.carrier_tracking_ref}',
                'price_unit': self.carrier_price,
                'product_qty': 1.0,
                'taxes_id': [(6, 0, self.carrier_id.product_id.taxes_id.ids)]
            })]
        })
        return po_id

    def send_to_shipper(self):
        try:
            self.ensure_one()
            res = self.carrier_id.send_shipping(self)[0]
            if self.carrier_id.free_over and self.sale_id:
                amount_without_delivery = self.sale_id._compute_amount_total_without_delivery()
                if self.carrier_id._compute_currency(self.sale_id, amount_without_delivery,
                                                     'pricelist_to_company') >= self.carrier_id.amount:
                    res['exact_price'] = 0.0
            self.carrier_price = res['exact_price'] * (1.0 + (self.carrier_id.margin / 100.0))
            if res['tracking_number']:
                related_pickings = self.env['stock.picking'] if self.carrier_tracking_ref and res[
                    'tracking_number'] in self.carrier_tracking_ref else self
                accessed_moves = previous_moves = self.move_ids.move_orig_ids
                while previous_moves:
                    related_pickings |= previous_moves.picking_id
                    previous_moves = previous_moves.move_orig_ids - accessed_moves
                    accessed_moves |= previous_moves
                accessed_moves = next_moves = self.move_ids.move_dest_ids
                while next_moves:
                    related_pickings |= next_moves.picking_id
                    next_moves = next_moves.move_dest_ids - accessed_moves
                    accessed_moves |= next_moves
                without_tracking = related_pickings.filtered(lambda p: not p.carrier_tracking_ref)
                without_tracking.carrier_tracking_ref = res['tracking_number']
                for p in related_pickings - without_tracking:
                    p.carrier_tracking_ref += "," + res['tracking_number']
            order_currency = self.sale_id.currency_id or self.company_id.currency_id
            msg = _("Shipment sent to carrier %(carrier_name)s for shipping with tracking number %(ref)s",
                    carrier_name=self.carrier_id.name,
                    ref=self.carrier_tracking_ref) + \
                  Markup("<br/>") + \
                  _("Cost: %(price).2f %(currency)s",
                    price=self.carrier_price,
                    currency=order_currency.name)
            self.message_post(body=msg)
            if (
                    self.carrier_id.delivery_type == settings.ahamove_code and
                    self.ahamove_payment_method == 'CASH_BY_RECIPIENT' and
                    self.carrier_price
            ):
                self._ahamove_create_purchase_order_for_delivery_cost()
            else:
                self._add_delivery_cost_to_so()
        except Exception as e:
            if self.carrier_tracking_ref and self.carrier_id.delivery_type == settings.ahamove_code:
                client = Client(Connection(self))
                route_id = utils.get_route_api(self.carrier_id, settings.cancel_order_route_code)
                client.cancel_order(route_id, self.carrier_tracking_ref)
            raise UserError(ustr(e))
