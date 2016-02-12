# -*- coding: utf-8 -*-
# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

from django.conf.urls import url
from django.contrib import admin

from accounting.views import (
    NotFoundPage, AuthPage, AuthController, FrontManagePage, NeedAuthPage,
    PaymentManagePage, AddCardManagePage, AddCardController,
    ServiceController, ClientDataController, SavePaymentsController,
    ClientFrontPage, ClientPaymentDataController)

urlpatterns = [
    url(r'^auth/check[.]{1}json$', AuthController.as_view(), name='auth_check'),  # noqa
    url(r'^manage$', FrontManagePage.as_view(), name='manage_page'),
    url(r'^no-auth$', NeedAuthPage.as_view(), name='no_auth_page'),
    url(r'^system/', admin.site.urls),
    url(r'^in$', AuthPage.as_view(), name='in_page'),
    url(r'^add-card$', AddCardManagePage.as_view(), name='add_card_page'),
    url(r'^payment$', PaymentManagePage.as_view(), name='payment_page'),
    url(r'^add-card[.]{1}json$', AddCardController.as_view(), name="add_card"),
    url(r'^service[.]{1}json$', ServiceController.as_view(), name='service_json'),  # noqa
    url(r'^client-data[.]{1}json$', ClientDataController.as_view(), name='get_client_data'),  # noqa
    url(r'^make-payments[.]{1}json$', SavePaymentsController.as_view(), name='make_payments'),  # noqa
    url(r'^client-payments[.]{1}json$', ClientPaymentDataController.as_view(), name='client_payments'),  # noqa
    url(r'^$', ClientFrontPage.as_view(), name='client_front_page'),  # noqa
    url(r'^.+', NotFoundPage.as_view()),
]
