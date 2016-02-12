# @author: Michael Vorotyntsev
# @email: linkofwise@gmail.com
# @github: unaxfromsibiria

import json
from django.conf import settings
from django.template import Library
from django.utils.safestring import mark_safe
from accounting.models import InfoVar

register = Library()


@register.filter
def tojs(value):
    if value is None:
        value = 'null'
    else:
        try:
            value = json.dumps(value)
        except Exception as err:
            value = json.dumps({'error': 'json dump: {}'.format(err)})
    return mark_safe(value)


@register.filter
def settings_value(attr, default_value=None):
    assert attr not in ['DATABASES', 'SECRET_KEY']
    value = getattr(settings, attr, None)
    if value is None and not(default_value is None):
        value = default_value

    return mark_safe(value)


@register.filter
def info_var(code):
    return mark_safe(InfoVar.get(code))
