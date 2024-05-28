from odoo import fields, models, api
from odoo.exceptions import UserError
from odoo.tools import ustr
from odoo.addons.tangerine_delivery_base.settings import utils
from ..settings.constants import settings
from ..api.connection import Connection
from ..api.client import Client


class AhamoveResState(models.Model):
    _inherit = 'res.country.state'

    ahamove_code = fields.Char(string='Ahamove Code')

    @api.model
    def ahamove_city_synchronous(self):
        try:
            provider_id = self.env['delivery.carrier'].search([('delivery_type', '=', settings.ahamove_code)])
            client = Client(Connection(provider_id))
            result = client.ahamove_city_synchronous(utils.get_route_api(provider_id, settings.city_sync_route_code))
            for city in result.lst_city:
                state_id = self.search([('name', 'ilike', city.name_vi_vn)])
                if not state_id:
                    district_id = self.env['res.country.district'].search([('name', 'ilike', city.name_vi_vn)])
                    if not district_id:
                        continue
                    district_id.write(({'ahamove_code': city._id}))
                    continue
                state_id.write({'ahamove_code': city._id})
        except Exception as e:
            raise UserError(ustr(e))


class AhamoveResDistrict(models.Model):
    _inherit = 'res.country.district'

    ahamove_code = fields.Char(string='Ahamove Code')
