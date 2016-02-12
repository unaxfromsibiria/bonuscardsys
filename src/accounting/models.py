# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

import hashlib
from django.db import models
from django.core.cache import cache
from django.utils.timezone import now as datetime_now


class BonusPolicy(models.Model):
    begin = models.DateField('Начало действия', db_index=True)
    end = models.DateField('Окончание действия', db_index=True)
    limit = models.DecimalField('Сумма накоплений для скидки', max_digits=6, decimal_places=2, default=0)  # noqa
    percent = models.DecimalField('Проценты бонусов', max_digits=4, decimal_places=2, default=0)  # noqa

    class Meta:
        verbose_name = 'Политика начисление бонусов'
        verbose_name_plural = 'Политики начисления бонусов'

    @property
    def period(self):
        return 'с {} по {}'.format(
            self.begin.strftime('%d.%m.%Y'),
            self.end.strftime('%d.%m.%Y'))

    def __str__(self):
        return '{} {} руб. {}%'.format(
            self.period, self.limit, self.percent)

    def as_dict(self):
        return {
            'limit': str(self.limit),
            'percent': str(self.percent),
        }


class Client(models.Model):

    name = models.TextField('Имя', default='')
    phone = models.TextField('Телефон')
    card = models.TextField('Номер карты', unique=True, db_index=True)
    bonus = models.DecimalField('Бонусный счет', max_digits=6, decimal_places=2, default=0)  # noqa
    created = models.DateTimeField('Создан', db_index=True)
    # hidden
    hash = models.CharField(max_length=64, db_index=True)

    class Meta:
        ordering = ['created']
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return '{} {}'.format(self.phone, self.card)

    def as_dict(self):
        return {
            'name': self.name,
            'phone': self.phone,
            'card': self.card,
            'bonus': str(self.bonus),
        }

    def save(self, *args, **kwargs):
        if self.phone and self.card:
            # 10 знаков номера без (8 или +7)
            src = '{}{}'.format(self.phone[-10:], self.card)
            h = hashlib.sha256(src.encode())
            self.hash = h.hexdigest()
        if not self.created:
            self.created = datetime_now()
        return super().save(*args, **kwargs)


class Service(models.Model):
    name = models.TextField('Название')

    class Meta:
        ordering = ['name']
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return self.name

    def as_dict(self):
        return {'id': self.pk, 'name': self.name}


class Payment(models.Model):
    created = models.DateTimeField('Создан', auto_now_add=True, db_index=True)
    client = models.ForeignKey(Client, verbose_name='Клиент', related_name='payments')  # noqa
    service = models.ForeignKey(Service, verbose_name='Услуга')
    summa = models.DecimalField('Сумма', max_digits=6, decimal_places=2, default=0)  # noqa
    summa_sale = models.DecimalField('Сумма скидки', max_digits=6, decimal_places=2, default=0)  # noqa
    summa_bonus = models.DecimalField('Получено бонусов', max_digits=6, decimal_places=2, default=0)  # noqa

    class Meta:
        ordering = ['created']
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'

    def __str__(self):
        return '{} {}'.format(self.service, self.summa)

    def as_dict(self):
        return {
            'date': self.created.strftime("%d.%m.%Y"),
            'service': self.service.name,
            'summa': str(self.summa),
            'summa_sale': str(self.summa_sale),
            'summa_bonus': str(self.summa_bonus),
        }


class InfoVar(models.Model):
    cache_timeout = 3600

    code = models.TextField('Код')
    value = models.TextField('Значение')

    def __str__(self):
        return '{} = {}'.format(self.code, self.value[:32])

    class Meta:
        ordering = ['code']
        verbose_name = 'Информационное значение'
        verbose_name_plural = 'Информационные значения'

    @classmethod
    def _cahae_key(cls, code):
        return '{}:{}'.format(cls.__name__, code)

    def save(self, *args, **kwargs):
        cls = self.__class__
        cache.set(
            cls._cahae_key(self.code), self.value, cls.cache_timeout)
        return super().save(*args, **kwargs)

    @classmethod
    def get(cls, code):
        key = cls._cahae_key(code)
        value = cache.get(key)
        if value is None:
            try:
                value = cls.objects.get(code=code).value
            except cls.DoesNotExist:
                value = ''
            else:
                cache.set(key, value, cls.cache_timeout)

        return value
