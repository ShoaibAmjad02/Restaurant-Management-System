from .base import *
from .base import DATABASES
from .base import env


SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="temporary-secret-key-change-later"
)

DEBUG = False

ALLOWED_HOSTS = [
    "*"
]


DATABASES["default"]["CONN_MAX_AGE"] = 60
