from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from deform_autoneed import need_lib
from fanstatic import Library
from fanstatic import Resource
from js.bootstrap import bootstrap_css
from voteit.core.fanstaticlib import voteit_main_css

library = Library('skl_theme', 'static')

skl_custom_bootstrap_css = Resource(library, 'css/bootstrap.css', supersedes=(bootstrap_css,))
skl_theme_css = Resource(library, 'css/main.css', depends = (skl_custom_bootstrap_css, voteit_main_css))


def need_subscriber(view, event):
    skl_theme_css.need()
    # Due to changes in the registration schema, the select 2 widget is needed at all times too
    need_lib('select2')

def includeme(config):
    config.add_subscriber(need_subscriber, [IBaseView, IViewInitializedEvent])
