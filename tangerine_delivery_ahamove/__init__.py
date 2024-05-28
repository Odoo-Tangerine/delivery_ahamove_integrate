from . import models, wizard, api, settings, schemas, controllers


def _sync_city_hook(env):
    env['res.country.state'].ahamove_city_synchronous()
