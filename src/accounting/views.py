# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

import logging
import json
import hashlib

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.http.response import JsonResponse
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView, View
from django.utils.timezone import now as datetime_now

from . import msg
from .helpers import (
    SysRand, CommonAuthMiddleware, get_client_ip,
    create_card, create_payment)
from .models import Service, Client, BonusPolicy, Payment

auth_only = CommonAuthMiddleware.need_auth


class AuthPage(TemplateView):
    template_name = 'auth_page.html'

    def get_context_data(self, **kwargs):
        rand = SysRand()
        pub_key, check_key = rand.create_keys(count=2)
        cache.set(pub_key, {'key': check_key, 'try_count': 0}, 300)
        context = super().get_context_data(
            jsdata={'keys': {'pub': pub_key, 'in': check_key}},
            **kwargs)
        return context


class AuthController(View):

    http_method_names = ['post']

    def post(self, request):
        result = {'ok': False}
        pub_key = request.POST.get('key')
        password = request.POST.get('password')
        if pub_key and password:

            sec_data = cache.get(pub_key)
            if isinstance(sec_data, dict):
                logger = logging.getLogger('system')
                try_count = sec_data.get('try_count', 0) + 1
                sec_data.update(try_count=try_count)
                cache.set(pub_key, sec_data, 300)
                if try_count < settings.AUTH_COUNT_LIMIT:
                    sec_data = '{}{}{}'.format(
                        pub_key, settings.IN_PASSWORD, sec_data.get('key'))
                    sha = hashlib.sha256(sec_data.encode())
                    result.update(ok=password == sha.hexdigest())
                else:
                    cache.delete(pub_key)
                    logger.warn(
                        'Auth count limit! From: {}'.format(
                            get_client_ip(request)))

        if result.get('ok'):
            rand = SysRand()
            key_part1, key_part2, value = rand.create_keys(count=3)
            result.update(msg=msg.AUTH_OK)
            result = JsonResponse(result)
            key = '{}{}'.format(key_part1, key_part2)
            time_limit = 3600 * settings.AUTH_TIME
            cache.set(
                key,
                {'value': value, 'open': datetime_now().isoformat()},
                time_limit)

            result.set_cookie(
                settings.AUTH_COOKIE_NAME,
                value='{}:{}'.format(key, value),
                max_age=time_limit)

            logger.info(
                'Manager login from {} new key: {}'.format(
                    get_client_ip(request), key))

        else:
            result.update(msg=msg.INCORECT_PASSWORD)
            result = JsonResponse(result)
        return result


class NeedAuthPage(TemplateView):
    template_name = 'need_auth.html'


class BaseManagePage(TemplateView):
    http_method_names = ['get']

    @auth_only
    def get(self, request):
        return super().get(request)


class FrontManagePage(BaseManagePage):
    template_name = 'manage_page.html'


class AddCardManagePage(BaseManagePage):
    template_name = 'addcard_manage_page.html'


class PaymentManagePage(BaseManagePage):
    template_name = 'payment_manage_page.html'

    def get_context_data(self, **kwargs):
        now = datetime_now().date()
        variants = BonusPolicy.objects.filter(
            end__gte=now,
            begin__lte=now).order_by(
                # чем больше процент и чем меньше лимит
                '-percent', 'limit')

        try:
            policy = variants[:1].get().as_dict()
        except BonusPolicy.DoesNotExist:
            policy = {'persent': 0, 'limit': 0}

        context = super().get_context_data(
            policy=policy,
            **kwargs)

        return context


class AddCardController(View):

    http_method_names = ['post']

    def post(self, request):
        result = {'ok': False}
        if getattr(request, 'sys_auth', False):
            card = request.POST.get('card')
            phone = request.POST.get('phone')
            update_mode = (
                str(request.POST.get('update') or '').upper() == 'TRUE')
            if card and phone:
                logger = logging.getLogger('system')
                try:
                    pk = create_card(
                        phone=phone,
                        number=card,
                        name=request.POST.get('name'),
                        update_mode=update_mode,
                        result=result)
                except Exception as err:
                    result.update(
                        ok=False,
                        msg='Ошибка: {}'.format(err))

                    logger.error('Error of new card {}: {} from {}'.format(
                            card, err, get_client_ip(request)))
                else:
                    if pk:
                        logger.info('Card {} append as {} from {}'.format(
                            card, pk, get_client_ip(request)))
            else:
                result.update(msg=msg.INCORECT_CARD_DATA)
        else:
            result.update(msg=msg.NEED_RELOGIN)

        return JsonResponse(result)


class ServiceController(View):

    http_method_names = ['get']

    def get(self, request):
        result = [
            service.as_dict() for service in Service.objects.all()]

        return JsonResponse({'list': result})


class ClientDataController(View):

    http_method_names = ['post']

    @auth_only
    def post(self, request):
        result = {}
        num = str(request.POST.get('number') or '')
        if len(num) == settings.CARD_NUMBER_SIZE:
            variants = Client.objects.filter(card=num)
        else:
            phone = num[-10:]
            variants = Client.objects.filter(
                Q(phone='8{}'.format(phone)) | Q(phone='+7{}'.format(phone)))

        try:
            # карта с самым большим бонусом
            client = variants.order_by('-bonus')[:1].get().as_dict()
        except Client.DoesNotExist:
            result.update(ok=False)
        else:
            result.update(
                client=client,
                ok=True)

        return JsonResponse(result)


class SavePaymentsController(View):

    http_method_names = ['post']

    @auth_only
    def post(self, request):
        result = {'ok': False}

        card = request.POST.get('card')
        payments = request.POST.get('payments')
        use_sale = str(request.POST.get('use_sale') or 'true').lower() == 'true'

        try:
            payments = json.loads(payments)
        except Exception as err:
            card = None
            logger = logging.getLogger('system')
            logger.error('json format error: {} {}'.format(err, payments))

        now = datetime_now().date()
        variants = BonusPolicy.objects.filter(
            end__gte=now,
            begin__lte=now).order_by(
                # чем больше процент и чем меньше лимит
                '-percent', 'limit')

        try:
            policy = variants[:1].get()
        except BonusPolicy.DoesNotExist:
            policy = None

        if card and policy:
            try:
                client_pk = Client.objects.values_list(
                    'id', flat=True).get(card=card)
            except Client.DoesNotExist:
                result.update(msg=msg.NOT_FOUND)
            else:
                try:
                    result.update(
                        ok=True,
                        payment=create_payment(
                            client=client_pk,
                            use_sale=use_sale,
                            payments=payments,
                            limit=policy.limit,
                            percent=policy.percent))

                except Exception as err:
                    result.update(
                        msg='Ошибка выполнения: {}'.format(err))
        else:
            result.update(msg=msg.PARAMS_ERR)

        if not result['ok']:
            logger = logging.getLogger('system')
            logger.warning('Error: {} from {}'.format(
                result['msg'], get_client_ip(request)))

        return JsonResponse(result)


class ClientFrontPage(TemplateView):

    template_name = 'client_account_page.html'

    http_method_names = ['get']

    def get(self, request):
        parent_get = super().get
        if settings.DEBUG:
            result = parent_get(request)
        else:
            @cache_page(3600)
            def simple_view(req):
                return parent_get(req)

            result = simple_view(request)

        return result


class ClientPaymentDataController(View):

    http_method_names = ['post']

    def post(self, request):
        result = {}
        try:
            client = Client.objects.get(
                hash=request.POST.get('client') or '!')
        except Client.DoesNotExist:
            result.update(ok=False, msg=msg.CLIENT_NOTFOUND)
        else:
            payments = Payment.objects.filter(
                client=client).order_by('-created')

            result.update(
                ok=True,
                payments=[
                    payment.as_dict() for payment in payments],
                client=client.as_dict())

        return JsonResponse(result)


class NotFoundPage(TemplateView):

    template_name = 'page_404.html'

    def dispatch(self, *args, **kwargs):
        response = super().dispatch(*args, **kwargs)
        response.status_code = 404
        return response
