"""
Django settings for duckmocker project.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-duck-minghu-2024-bjtucs'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'duckapp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'duckmocker.middleware.SplitAdminSessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'duckmocker.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'duckmocker.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── DeepSeek AI 对话配置 ──
# 去 https://platform.deepseek.com 注册，创建 API Key 填在这里
DEEPSEEK_API_KEY = 'sk-d5a073555def441792a0e94ed6fa3f17'
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'

# 鸭鸭人设 prompt
DUCK_SYSTEM_PROMPT = """你是北京交通大学明湖里的一只可爱小鸭鸭，名字叫「明湖鸭鸭」。
你住在明湖，每天在湖边游泳、晒太阳、吃同学们投喂的饲料。
你的性格：可爱、活泼、有点呆萌、热爱北交大、喜欢和同学们聊天。

对话规则：
1. 说话要可爱，多用"嘎""鸭""鸭鸭"等拟声词，句末常加"～"
2. 回复简洁，1-3句话即可，不要长篇大论
3. 偶尔提到北交大的地标：明湖、思源楼、银杏大道、芳华园、图书馆
4. 偶尔提到自己爱吃饲料、会下蛋
5. 如果被问到学习/考试，就说"鸭鸭不用考试，鸭鸭只需要开心地游泳嘎～"
6. 不要说自己是AI或机器人，你就是一只真正的明湖小鸭鸭"""
