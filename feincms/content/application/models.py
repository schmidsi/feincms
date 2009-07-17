import re

from django.conf import settings
from django.core import urlresolvers
from django.core.urlresolvers import Resolver404, resolve, reverse as _reverse
from django.db import models
from django.utils.thread_support import currentThread
from django.utils.translation import ugettext_lazy as _


_urlconfs = {}

def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None, *vargs, **vkwargs):
    ct = currentThread()
    if not urlconf and ct in _urlconfs:
        urlconf, prefix = _urlconfs[ct]

    return _reverse(viewname, urlconf, args, kwargs, prefix, *vargs, **vkwargs)
urlresolvers.reverse = reverse


class ApplicationContent(models.Model):
    urlconf_path = models.CharField(_('URLconf path'), max_length=100)

    class Meta:
        abstract = True
        verbose_name = _('application content')
        verbose_name_plural = _('application contents')

    def render(self, request, **kwargs):
        page_url = self.parent.get_absolute_url()

        # Get the rest of the URL
        path = re.sub('^' + re.escape(page_url[:-1]), '', request.path)

        # Change the prefix and urlconf for the monkey-patched reverse function ...
        _urlconfs[currentThread()] = (self.urlconf_path, page_url)

        try:
            fn, args, kwargs = resolve(path, self.urlconf_path)
        except (ValueError, Resolver404):
            # Silent failure if resolving failed
            del _urlconfs[currentThread()]
            return u''

        output = fn(request, *args, **kwargs)

        # ... and restore it after processing the view
        del _urlconfs[currentThread()]
        return output

