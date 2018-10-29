# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unicodecsv as csv
try:
    from StringIO import StringIO  # python 2
except ImportError:
    from io import StringIO  # python 3


class CSVRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        """ Returns a plain CSV-encoded string with content-type
        ``text/csv``. The content-type may be overridden by
        setting ``request.response.content_type``."""

        request = system.get('request')
        if request is not None:
            response = request.response
            ct = response.content_type
            if ct == response.default_content_type:
                response.content_type = b'text/csv'

        fout = StringIO()
        writer = csv.writer(fout, encoding='utf-8', delimiter=b',', quotechar=b'"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(value.get('header', []))
        writer.writerows(value.get('rows', []))

        return fout.getvalue()


def includeme(config):
    config.add_renderer('csv', 'skl_theme.renderers.CSVRenderer')
