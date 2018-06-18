from arche.interfaces import IBaseView
from arche.interfaces import IViewInitializedEvent
from fanstatic import Library
from fanstatic import Resource
from js.bootstrap import bootstrap_css


library = Library('skl_theme', 'static')

skl_theme_css = Resource(library, 'css/main.css', depends = (bootstrap_css,))


#def need_subscriber(view, event):
#    skl_theme_css.need()


def includeme(config):
    pass
 #   config.add_subscriber(need_subscriber, [IBaseView, IViewInitializedEvent])
