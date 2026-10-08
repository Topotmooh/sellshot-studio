"""Генерация описаний для досок объявлений (только вещи)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SellerType(str, Enum):
    """Тип продавца."""
    INDIVIDUAL = "Физлицо"
    IP = "ИП"
    SELF = "Самозанятый"


@dataclass
class SellerInfo:
    """Данные продавца."""
    seller_type: SellerType = SellerType.INDIVIDUAL
    full_name: str = "[ФИО]"
    phone: str = "[телефон]"
    city: str = "[город]"
    district: str = "[район]"


DEFAULT_SELLER = SellerInfo()


def generate_avito_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для Авито."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Местоположение: {s.city}, {s.district}\n"
        f"📞 Связь: {s.phone}\n\n"
        f"🚚 Доставка: Авито Доставка / СДЭК / Почта России\n"
        f"💰 Оплата: при получении или онлайн\n"
        f"🔄 Возврат: в течение 14 дней"
    )


def generate_youla_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для Юлы."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Город: {s.city}\n"
        f"📞 Телефон: {s.phone}\n\n"
        f"🚚 Доставка: Юла Доставка / Почта России\n"
        f"💳 Оплата: онлайн или при встрече\n"
        f"✅ Возврат: в течение 14 дней"
    )


def generate_vk_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для VK Маркет."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Локация: {s.city}\n"
        f"📱 Связь: {s.phone}\n\n"
        f"🚚 Доставка: VK Доставка / СДЭК\n"
        f"💰 Оплата: VK Pay или при получении\n"
        f"🔄 Возврат: 14 дней по закону"
    )


def generate_gde_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для gde.ru."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Город: {s.city}\n"
        f"📞 Контакт: {s.phone}\n\n"
        f"🚚 Доставка: Почта России / СДЭК\n"
        f"💳 Оплата: при получении\n"
        f"✅ Гарантия качества"
    )


def generate_barahla_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для barahla.net."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Регион: {s.city}\n"
        f"📞 Связь: {s.phone}\n\n"
        f"🚚 Доставка: по договоренности\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен"
    )


def generate_kupipanda_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для kupipanda.ru."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Город: {s.city}\n"
        f"📱 Телефон: {s.phone}\n\n"
        f"🚚 Доставка: курьер / почта\n"
        f"💳 Оплата: онлайн / при получении\n"
        f"✅ Проверка перед покупкой"
    )


def generate_vkupiprodai_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для vkupiprodai.ru."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Местоположение: {s.city}\n"
        f"📞 Контакт: {s.phone}\n\n"
        f"🚚 Способы доставки: почта / СДЭК\n"
        f"💰 Оплата: перевод / при встрече\n"
        f"🔄 Обмен возможен"
    )


def generate_yandex_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для Яндекс Объявления."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Город: {s.city}\n"
        f"📞 Телефон: {s.phone}\n\n"
        f"🚚 Доставка: Яндекс Доставка / Почта\n"
        f"💰 Оплата: Яндекс Pay / при получении\n"
        f"✅ Безопасная сделка"
    )


def generate_meshok_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для Мешка (аукцион, винтаж)."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Отправка из: {s.city}\n"
        f"📞 Связь: {s.phone}\n\n"
        f"🚚 Доставка: Почта России / СДЭК\n"
        f"💳 Оплата: после окончания аукциона\n"
        f"⚠️ Состояние: см. фото и описание"
    )


def generate_looton_description(seller: Optional[SellerInfo] = None) -> str:
    """Описание для Looton (премиум ресейл)."""
    s = seller or DEFAULT_SELLER
    return (
        f"📍 Город: {s.city}\n"
        f"📱 Связь: {s.phone}\n\n"
        f"🚚 Доставка: Looton Delivery / СДЭК\n"
        f"💰 Оплата: безопасная сделка через платформу\n"
        f"✅ Аутентификация: оригинал гарантирован\n"
        f"🔒 Проверка подлинности экспертами"
    )