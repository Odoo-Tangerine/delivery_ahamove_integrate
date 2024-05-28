# -*- coding: utf-8 -*-
from uuid import uuid4
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ahamove_api_key = fields.Char(string='API Key')

    def ahamove_generate_api_key(self):
        ICPModel = self.env['ir.config_parameter'].sudo()
        ICPModel.set_param('ahamove.ahamove_api_key', uuid4())

    def set_values(self):
        super().set_values()
        ICPModel = self.env['ir.config_parameter'].sudo()
        ICPModel.set_param('ahamove.ahamove_api_key', self.ahamove_api_key)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPModel = self.env['ir.config_parameter'].sudo()
        res.update(
            ahamove_api_key=ICPModel.get_param('ahamove.ahamove_api_key')
        )
        return res
