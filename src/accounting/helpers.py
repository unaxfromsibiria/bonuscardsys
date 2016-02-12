# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

import string
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.http import HttpResponsePermanentRedirect
from functools import wraps
from random import SystemRandom

from . import msg
from .models import Client, Payment

DEFAULT_KEY_SIZE = 32


def to_decimal(value=None):
    return Decimal(str(value or 0).replace(',', '.'))


class MetaOnceObject(type):

    _classes = dict()

    def __call__(self, *args, **kwargs):
        cls = str(self)
        if cls not in self._classes:
            this = super().__call__(*args, **kwargs)
            self._classes[cls] = this
        else:
            this = self._classes[cls]
        return this


class CommonAuthMiddleware:

    @staticmethod
    def need_auth(view_method):
        @wraps(view_method)
        def view_wrapper(view, request):
            if getattr(request, 'sys_auth', False):
                return view_method(view, request)
            else:
                return HttpResponsePermanentRedirect(reverse(
                    viewname='no_auth_page'))

        return view_wrapper

    def process_request(self, request):
        cookies = getattr(request, 'COOKIES', None)
        request.sys_auth = None

        if cookies:
            value = cookies.get(settings.AUTH_COOKIE_NAME)
            if value:
                parts = value.split(':')
                if len(parts) == 2:
                    key, value = parts
                    sys_auth = cache.get(key)
                    if sys_auth and sys_auth.get('value') == value:
                        request.sys_auth = sys_auth

    def process_response(self, request, response):
        return response


class SysRand:
    __metaclass__ = MetaOnceObject
    _rand = None
    _chars = '0123456789{}{}'.format(
        string.ascii_lowercase, string.ascii_uppercase)

    def __init__(self):
        self._rand = SystemRandom()

    def create_keys(self, size=DEFAULT_KEY_SIZE, count=1):
        result = []
        for _ in range(count):
            result.append(
                ''.join(map(str, [
                    self._rand.choice(self._chars) for _ in range(size)])))
        return tuple(result)


def get_client_ip(request, default='unknown ip'):
    try:
        client_ip = request.META['HTTP_X_FORWARDED_FOR']
    except:
        client_ip = None

    try:
        client_ip = client_ip or request.META['REMOTE_ADDR']
    except:
        client_ip = default

    return client_ip


@transaction.atomic
def create_card(phone, number, name, result, update_mode=False):
    pk = None
    result.update(ok=False)
    used_number = Client.objects.filter(card=number).exists()
    if used_number and not update_mode:
        result.update(msg=msg.CARD_USED.format(number))
    else:
        if used_number:
            # update
            client = Client.objects.get(card=number)
        else:
            client = Client(card=number)

        client.phone = phone

        if name:
            client.name = name
        client.save()
        pk = client.pk
        result.update(ok=bool(pk))
    return pk


@transaction.atomic
def create_payment(client, use_sale, payments, percent, limit):
    client_pk = getattr(client, 'pk', client)
    bonus_volume = Client.objects.values_list(
        'bonus', flat=True).get(pk=client_pk)

    sale = to_decimal()
    summs = []
    for payment in payments:
        payment['price'] = to_decimal(payment.get('price'))
        summs.append(payment['price'])
        payment['bonus'] = payment['price'] / 100 * percent
        bonus_volume += payment['bonus']

    max_price = max(summs)

    if use_sale:
        sale = to_decimal(int(bonus_volume / limit)) * limit

    for payment in payments:
        record = Payment(
            summa_bonus=payment['bonus'],
            summa=payment['price'])
        record.client_id = client_pk
        record.service_id = payment['service_pk']

        if sale and record.summa == max_price:
            # скидка 1 раз записывается в самый большой платеж
            max_price = -1
            record.summa_sale = sale

        record.save()

    Client.objects.filter(pk=client_pk).update(bonus=bonus_volume - sale)
    return {
        'bonus': str(bonus_volume - sale),
        'sale': str(sale),
    }
