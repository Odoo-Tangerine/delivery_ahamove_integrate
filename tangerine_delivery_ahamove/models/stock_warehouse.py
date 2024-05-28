from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings import utils
from ..settings.constants import settings
from ..api.connection import Connection
from ..api.client import Client


class Warehouse(models.Model):
    _inherit = 'stock.warehouse'

    ahamove_service_ids = fields.One2many('ahamove.service', 'warehouse_id', string='Services')
    default_ahamove_service_id = fields.Many2one('ahamove.service', string='Default Service')

    def ahamove_service_sync(self):
        try:
            for warehouse in self:
                if not warehouse.partner_id.state_id.ahamove_code:
                    raise UserError(_('The address of warehouse not set ahamove code. Please mapping ahamove code'))
                provider_id = warehouse.env['delivery.carrier'].search([('delivery_type', '=', settings.ahamove_code)])
                client = Client(Connection(provider_id))
                route_id = utils.get_route_api(provider_id, settings.service_sync_route_code)
                result = client.ahamove_service_synchronous(route_id, warehouse.partner_id.state_id.ahamove_code)
                payload_service = []
                for service in result.lst_service:
                    service_id = warehouse.env['ahamove.service'].search([
                        ('code', '=', service._id),
                        ('warehouse_id', '=', warehouse.id)
                    ])
                    if not service_id:
                        payload_service_request = []
                        for request in service.requests:
                            request_id = warehouse.env['ahamove.service.request'].search([('code', '=', request._id)])
                            if not request_id:
                                payload_service_request.append((0, 0, {'name': request.name, 'code': request._id}))
                            else:
                                warehouse.env['ahamove.service.request'].write({'name': request.name, 'code': request._id})
                        payload_service.append({
                            'name': service.name,
                            'code': service._id,
                            'description': service.description_vi_vn,
                            'active': service.enable,
                            'warehouse_id': warehouse.id,
                            'request_ids': payload_service_request
                        })
                    else:
                        service_id.write({
                            'name': service.name,
                            'code': service._id,
                            'active': service.enable
                        })
                if payload_service:
                    warehouse.env['ahamove.service'].create(payload_service)
        except Exception as e:
            raise UserError(ustr(e))