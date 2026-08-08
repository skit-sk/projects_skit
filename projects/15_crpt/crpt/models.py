"""Pydantic модели данных API ГИС МТ."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    code: Optional[str] = None
    error_message: str = ""
    description: Optional[str] = None


class Participant(BaseModel):
    inn: str
    status: str = ""
    name: Optional[str] = None
    is_registered: bool = False
    is_kfh: bool = False
    productGroups: list[str] = Field(default_factory=list)
    role: list[str] = Field(default_factory=list)


class MobilCheckResult(BaseModel):
    """Ответ mobile API /check."""
    status: int = 0
    message: str = ""
    code: Optional[str] = None
    codeType: Optional[str] = None
    gtin: Optional[str] = None
    productName: Optional[str] = None
    producerName: Optional[str] = None
    brandName: Optional[str] = None
    ownerInn: Optional[str] = None
    ownerName: Optional[str] = None
    statusEx: Optional[str] = None
    statusDate: Optional[str] = None


class CiseShort(BaseModel):
    """Краткая информация о КИ."""
    cis: str
    gtin: Optional[str] = None
    status: Optional[str] = None
    producerInn: Optional[str] = None
    ownerInn: Optional[str] = None
    emissionDate: Optional[str] = None


class CiseInfo(BaseModel):
    """Подробная информация о КИ."""
    cis: str
    status: str = ""
    gtin: Optional[str] = None
    productName: Optional[str] = None
    producerInn: Optional[str] = None
    ownerInn: Optional[str] = None
    emissionDate: Optional[str] = None
    introductionDate: Optional[str] = None
    turnoverDate: Optional[str] = None
    withdrawalDate: Optional[str] = None
    packageType: Optional[str] = None
    productGroup: Optional[str] = None
    childs: list[str] = Field(default_factory=list)
    parents: list[str] = Field(default_factory=list)


class CiseHistory(BaseModel):
    cis: str
    operations: list[dict] = Field(default_factory=list)


class ProductInfo(BaseModel):
    gtin: str
    name: Optional[str] = None
    brand: Optional[str] = None
    producerInn: Optional[str] = None
    productGroup: Optional[str] = None
    tnVedCode: Optional[str] = None
    description: Optional[str] = None
    attributes: list[dict] = Field(default_factory=list)


class Document(BaseModel):
    id: str
    type: Optional[str] = None
    status: Optional[str] = None
    createdDate: Optional[str] = None
    processedDate: Optional[str] = None
    senderInn: Optional[str] = None
    receiverInn: Optional[str] = None


class DispenserTask(BaseModel):
    id: str
    status: str = ""
    type: Optional[str] = None
    createdDate: Optional[str] = None


class ModInfo(BaseModel):
    kpp: Optional[str] = None
    fiasId: Optional[str] = None
    address: Optional[str] = None
    productGroup: Optional[str] = None
    isBlocked: bool = False


class TokenInfo(BaseModel):
    token: Optional[str] = None
    uuidToken: Optional[str] = None
    expireDate: Optional[str] = None


class AuthKey(BaseModel):
    uuid: str
    data: str
