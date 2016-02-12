# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria


from django.contrib import admin
from django.forms.widgets import TextInput

from .models import (
    Client, BonusPolicy, Service, Payment, InfoVar, models)


class BonusPolicyAdmin(admin.ModelAdmin):
    list_display = ('period_str', 'limit', 'percent')

    def period_str(self, obj):
        return obj.period


class ClientAdmin(admin.ModelAdmin):
    fields = ('name', 'phone', 'card', 'bonus')
    exclude = ('hash', 'created')
    list_display = ('card', 'name', 'phone', 'created_str', 'bonus')
    formfield_overrides = {
        models.TextField: {'widget': TextInput},
    }

    def created_str(self, obj):
        return obj.created.strftime('%d.%m.%Y %H:%M')

    created_str.short_description = 'Date'


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name',)

    formfield_overrides = {
        models.TextField: {'widget': TextInput},
    }


class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        'created_str',
        'client_card',
        'service',
        'summa',
        'summa_sale',
        'summa_bonus',
    )

    formfield_overrides = {
        models.TextField: {'widget': TextInput},
    }

    def created_str(self, obj):
        return obj.created.strftime('%d.%m.%Y %H:%M')

    created_str.short_description = 'Date'

    def client_card(self, obj):
        return obj.client.card


class InfoVarAdmin(admin.ModelAdmin):

    list_display = (
        'code',
        'value_shot',
    )

    formfield_overrides = {
        models.TextField: {'widget': TextInput},
    }

    def value_shot(self, obj):
        return obj.value[:80]


admin.site.register(BonusPolicy, BonusPolicyAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(InfoVar, InfoVarAdmin)
