from pathlib import Path
import os
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure--o=26ldjuz_@egpkbpavb#2n5n=6$$7s=als0yqu(=&@k2hd%g'

DEBUG = True

ALLOWED_HOSTS = []

# ----------------------------- INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles', 
    'coding',                # Your custom app
    'corsheaders',   
    'rest_framework',        # For cross-origin requests (frontend + backend)
]

# ----------------------------- MIDDLEWARE
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Add CORS support early
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'medical_coding_ai.urls'

# ----------------------------- TEMPLATES (used for index.html)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # Your HTML templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'medical_coding_ai.wsgi.application'

# ----------------------------- DATABASE
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ----------------------------- PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ----------------------------- TIME & LANGUAGE
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ----------------------------- STATIC FILES
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]             # ✅ for dev: put favicon, js, css here
STATIC_ROOT = BASE_DIR / "staticfiles"               # ✅ for collectstatic in deployment

# ----------------------------- CORS (Frontend <-> Backend)
CORS_ALLOW_ALL_ORIGINS = True  # Allow all origins (for local frontend POSTs)

# ----------------------------- DEFAULT FIELD TYPE
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
