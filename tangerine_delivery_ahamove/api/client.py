# -*- coding: utf-8 -*-
import re
import time
import json
from dataclasses import dataclass
from odoo import _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval
from .connection import Connection
from odoo.addons.tangerine_delivery_base.settings.utils import URLBuilder
from ..schemas.ahamove_schemas import (
    TokenResponse,
    CitySyncResponse,
    ServiceSyncResponse,
    AhamoveEstCostRequest, AhamoveEstCostResponse,
    AhamoveCreateOrderRequest, AhamoveCreateOrderResponse
)


@dataclass
class Client:
    conn: Connection

    def _payload_get_token(self) -> dict[str, str]:
        return {
            'mobile': self.conn.provider.ahamove_partner_phone,
            'api_key': self.conn.provider.ahamove_api_key
        }

    @staticmethod
    def _clean_phone_number(phone):
        return re.sub('[^0-9]', '', phone)

    def _execute(self, route_id, params, is_unquote=True):
        return self.conn.execute_restful(
            url=URLBuilder.builder(
                host=self.conn.provider.domain,
                routes=[route_id.route],
                params=params,
                is_unquote=is_unquote
            ),
            headers=json.loads(safe_eval(route_id.headers)),
            method=route_id.method
        )

    def get_access_token(self, route_id) -> TokenResponse:
        return TokenResponse(**self._execute(
            route_id=route_id,
            params=self._payload_get_token(),
            is_unquote=False
        ))

    def ahamove_city_synchronous(self, route_id) -> CitySyncResponse:
        return CitySyncResponse(lst_city=self._execute(
            route_id=route_id,
            params=None,
            is_unquote=False
        ))

    def _param_service_synchronous(self, city_id) -> dict[str, str]:
        return {
            'token': self.conn.provider.access_token,
            'user_mobile': self.conn.provider.ahamove_partner_phone,
            'city_id': city_id
        }

    def ahamove_service_synchronous(self, route_id, city_id) -> ServiceSyncResponse:
        return ServiceSyncResponse(lst_service=self._execute(
            route_id=route_id,
            params=self._param_service_synchronous(city_id),
            is_unquote=False
        ))

    def _param_estimate_order(self, order) -> AhamoveEstCostRequest:
        warehouse_id = order.warehouse_id
        service_type = order.env.context.get('ahamove_service')
        request_type = order.env.context.get('ahamove_request')
        promo_code = order.env.context.get('promo_code')
        if not warehouse_id:
            raise UserError(_('The warehouse is required on sale order'))
        elif not warehouse_id.partner_id.state_id.ahamove_code:
            raise UserError(_('The ahamove code is not set on warehouse address'))
        elif not service_type:
            service_type = f'{warehouse_id.partner_id.state_id.ahamove_code}-BIKE'
        payload = {
            'token': self.conn.provider.access_token,
            'service_id': service_type,
            'items': [{
                'name': line.product_id.name,
                'num': line.qty_to_deliver,
                'price': line.price_subtotal
            } for line in order.order_line if not line.is_delivery or not line.is_service],
            'path': [
                {'address': warehouse_id.partner_id.shipping_address},
                {'address': order.partner_shipping_id.shipping_address}
            ]
        }
        if promo_code:
            payload.update({'promo_code': promo_code})
        if request_type:
            payload.update({'requests': [{'_id': code, 'num': 1} for code in request_type]})
        return AhamoveEstCostRequest(**payload)

    def estimate_order_fee(self, route_id, order):
        return AhamoveEstCostResponse(**self._execute(
            route_id=route_id,
            params=self._param_estimate_order(order).model_dump()
        ))

    def _param_create_order(self, picking):
        payload = {
            'token': self.conn.provider.access_token,
            'order_time': 0,
            'path': [
                {
                    'address': picking.picking_type_id.warehouse_id.partner_id.shipping_address,
                    'name': picking.picking_type_id.warehouse_id.partner_id.name,
                    'mobile': picking.picking_type_id.warehouse_id.partner_id.phone or picking.picking_type_id.warehouse_id.partner_id.mobile,
                    'tracking_number': picking.name
                },
                {
                    'address': picking.partner_id.shipping_address,
                    'name': picking.partner_id.name,
                    'mobile': picking.partner_id.phone or picking.partner_id.mobile
                },
            ],
            'service_id': picking.ahamove_service_id.code,
            'requests': [{
                '_id': rec.code,
                'num': 1,
            } for rec in picking.ahamove_service_request_ids],

            'payment_method': picking.ahamove_payment_method,
            'items': [
                {
                    '_id': package.product_id.default_code,
                    'num': package.quantity,
                    'name': package.product_id.name,
                    'price': package.product_id.list_price * package.quantity
                } for package in picking.move_line_ids_without_package
            ]
        }
        if picking.cash_on_delivery and picking.cash_on_delivery_amount > 0.0:
            payload['path'][1].update({'cod': picking.cash_on_delivery_amount})
        if picking.schedule_order:
            start_timestamp = int(time.mktime(picking.schedule_pickup_time_from.timetuple()))
            end_timestamp = int(time.mktime(picking.schedule_pickup_time_to.timetuple()))
            payload['order_time'] = end_timestamp - start_timestamp
        if picking.remarks:
            payload.update({'remarks': picking.remarks})
        if picking.promo_code:
            payload.update({'promo_code': picking.promo_code})
        return AhamoveCreateOrderRequest(**payload)

    def create_order(self, route_id, picking):
        return AhamoveCreateOrderResponse(**self._execute(
            route_id=route_id,
            params=self._param_create_order(picking).model_dump(exclude_none=True)
        ))

    def _param_cancel_shipment(self, order):
        return {'token': self.conn.provider.access_token, 'order_id': order}

    def cancel_order(self, route_id, order):
        self._execute(route_id=route_id, params=self._param_cancel_shipment(order))
