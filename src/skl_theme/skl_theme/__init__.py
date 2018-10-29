
def includeme(config):
    config.include('.fanstatic_lib')
    config.include('.models')
    config.include('.schemas')
    config.include('.views')
    config.include('.security')
    config.include('.renderers')
    #Static dir
    config.add_static_view('static_skl_theme', 'static', cache_max_age=3600)
