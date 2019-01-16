from .settings import *

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
    os.path.join(BASE_DIR, "assets"),
]

WEBPACK_LOADER = {
    'DEFAULT': {
            'BUNDLE_DIR_NAME': 'bundles/',
            'STATS_FILE': os.path.join(BASE_DIR, 'webpack-stats.prod.json'),
        }
}

# LDAP

AUTHENTICATION_BACKENDS = [
    'django_auth_ldap.backend.LDAPBackend',
]

# Baseline configuration.
AUTH_LDAP_SERVER_URI = os.environ.get('AUTH_LDAP_SERVER_URI', 'ldap://45.79.13.50:389')

AUTH_LDAP_BIND_DN = ''
AUTH_LDAP_BIND_PASSWORD = ''

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    'ou=people,dc=planetexpress,dc=com',
    ldap.SCOPE_SUBTREE,
    '(uid=%(user)s)',
)
