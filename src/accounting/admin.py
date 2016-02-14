# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

from datetime import date
from django.db import connection
from django.contrib import admin
from django.forms.widgets import TextInput

from .models import (
    Client, BonusPolicy, Service, Payment, InfoVar, models)

_m_list = [
    'Январь',
    'Февраль',
    'Март',
    'Апрель',
    'Май',
    'Июнь',
    'Июль',
    'Август',
    'Сентябрь',
    'Октябрь',
    'Ноябрь',
    'Декабрь',
]


class PeriodFilter(admin.SimpleListFilter):
    title = 'За месяц'
    parameter_name = 'created'

    def lookups(self, request, model_admin):
        # postgres only
        sql = """select distinct(
                    date_part('year', created)::text || ' ' ||
                    date_part('month', created)::text)
                from {};""".format(Payment._meta.db_table)

        cursor = connection.cursor()
        cursor.execute(sql)
        result = (map(int, row[0].split()) for row in cursor.fetchall())
        return [
            (
                '{}_{}'.format(year, month),
                '{} {}'.format(_m_list[month - 1], year),
            )
            for year, month in result
        ]

    def queryset(self, request, queryset):
        filter_value = self.value()
        if filter_value:
            year, month = map(int, filter_value.split('_'))
            begin = date(year, month, 1)
            if month < 12:
                end = date(year, month + 1, 1)
            else:
                end = date(year + 1, 1, 1)

            return queryset.filter(
                created__gte=begin,
                created__lt=end)
        else:
            return queryset


class BonusPolicyAdmin(admin.ModelAdmin):
    list_display = ('period_str', 'limit', 'percent')

    def period_str(self, obj):
        return obj.period


class ClientAdmin(admin.ModelAdmin):
    fields = ('name', 'phone', 'card', 'bonus')
    exclude = ('hash', 'created')
    list_display = ('card', 'name', 'phone', 'created_str', 'bonus')
    list_per_page = 50
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
    list_filter = (PeriodFilter, 'service',)

    list_per_page = 50

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
