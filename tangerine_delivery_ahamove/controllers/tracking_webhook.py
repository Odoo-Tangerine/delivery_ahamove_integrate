from odoo.tools import ustr
from odoo.http import request, Controller, route
from odoo.addons.tangerine_delivery_base.settings.utils import validate_api_key, response
from odoo.addons.tangerine_delivery_base.settings.status import status
from ..schemas.ahamove_schemas import TrackingWebhookRequest


class DeliveriesController(Controller):
    @validate_api_key
    @route('/api/v1/ahamove/webhook', type='json', auth='public', methods=['POST'])
    def ahamove_callback(self):
        try:
            body = TrackingWebhookRequest(**request.dispatcher.jsonrequest)
            picking_id = request.env['stock.picking'].sudo().search([
                ('carrier_tracking_ref', '=', body._id)
            ])
            if not picking_id:
                return response(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=f'The delivery id {body._id} not found.'
                )
            status_id = request.env['delivery.status'].sudo().search([
                ('code', '=', body.status),
                ('provider_id', '=', picking_id.carrier_id.id)
            ])
            if not status_id:
                return response(
                    status=status.HTTP_400_BAD_REQUEST,
                    message=f'The status {body.status} does not match my system.'
                )
            payload = {'status_id': status_id.id}
            if body.driver:
                payload.update({
                    'driver_name': body.supplier_name,
                    'driver_phone': body.supplier_id
                })
            picking_id.sudo().write(payload)
        except Exception as e:
            return response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, message=ustr(e))
