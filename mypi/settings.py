import os


def import_module(name):
    module = __import__(name)
    components = name.split('.')
    for components in components[1:]:
        module = getattr(module, components)
    return module


# We should try to import any custom settings.
SETTINGS_MODULE_NAME = os.getenv("MYPI_SETTINGS_MODULE")
if SETTINGS_MODULE_NAME:
    SETTINGS_MODULE = import_module(SETTINGS_MODULE_NAME)
else:
    SETTINGS_MODULE = object()

# Try to get everything from the custom settings, but provide a default.
PACKAGES_DIR = getattr(SETTINGS_MODULE, "PACKAGES_DIR", "./packages")

SITE_TITLE = getattr(SETTINGS_MODULE, "SITE_TITLE", "Python Packages")
SITE_URL_BASE = getattr(SETTINGS_MODULE, "SITE_URL_BASE", "")
if SITE_URL_BASE.endswith("/"):
    SITE_URL_BASE = SITE_URL_BASE[:-1]
