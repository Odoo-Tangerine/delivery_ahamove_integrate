from typing import Optional
from pydantic import BaseModel, field_validator
from pydantic.dataclasses import dataclass
from odoo.addons.tangerine_delivery_base.settings.utils import standardization_e164


class TokenResponse(BaseModel):
    token: str
    refresh_token: str


@dataclass
class Item:
    num: int
    name: str
    price: int


class PathEstCost(BaseModel):
    address: str


class AhamoveEstCostRequest(BaseModel):
    token: Optional[str] = ''
    service_id: str
    path: list[PathEstCost]
    order_time: Optional[int] = 0
    items: list[Item]


class AhamoveEstCostResponse(BaseModel):
    distance: float
    duration: int
    total_price: int


class Path(BaseModel):
    address: str
    name: str
    mobile: str
    cod: Optional[int] = 0

    @field_validator('mobile')
    @classmethod
    def validate_mobile(cls, v: str) -> str:
        return standardization_e164(v)


@dataclass
class Request:
    _id: str
    num: int


class AhamoveCreateOrderRequest(BaseModel):
    order_time: int = 0
    path: list[Path]
    service_id: str
    requests: list[Request]
    payment_method: str
    items: list[Item]
    token: Optional[str] = None
    remarks: Optional[str] = None
    promo_code: Optional[str] = None


class Order(BaseModel):
    total_price: int


class AhamoveCreateOrderResponse(BaseModel):
    order_id: str
    order: Order


class AhamoveCancelOrderRequest(BaseModel):
    token: Optional[str] = ''
    order_id: str


@dataclass
class LstCity:
    _id: str
    name_vi_vn: str


class CitySyncResponse(BaseModel):
    lst_city: list[LstCity]


@dataclass
class ServiceRequest:
    _id: str
    name: str
    description_vi_vn: Optional[str] = ''


@dataclass
class Service:
    _id: str
    city_id: str
    name: str
    enable: bool = True
    description_vi_vn: Optional[str] = ''
    group_name_vi_vn: Optional[str] = ''
    group_id: Optional[str] = ''
    requests: Optional[list[ServiceRequest]] = None


class ServiceSyncResponse(BaseModel):
    lst_service: list[Service]


class TrackingWebhookRequest(BaseModel):
    _id: str
    status: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None

    order_time: Optional[int] = None
    create_time: Optional[int] = None
    accept_time: Optional[int] = None
    pickup_time: Optional[int] = None

    cancel_time: Optional[int] = None
    cancel_comment: Optional[str] = None
    cancel_by_user: Optional[str] = None

    complete_time: Optional[int] = None
    fail_time: Optional[int] = None
    fail_comment: Optional[str] = None

    distance: Optional[float] = None

