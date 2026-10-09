import json
import random
import time
import requests
from functools import wraps
from datetime import timedelta
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from .models import DuckProfile, Egg, Photo, Like, Comment, Feedback


# ── 天气缓存（模块级，30分钟刷新一次）────────────────────────────

_weather_cache = {'data': None, 'ts': 0}

LEGENDARY_PITY_DAYS = 7
FEED_ACCELERATE_DAILY_LIMIT = 3
FEED_ACCELERATE_HOURS = 1
FEED_CHALLENGE_REWARD_GRAMS = 60
OUTFIT_UNLOCK_EGGS_REQUIRED = 2
OUTFIT_PREVIEW_UNLOCK_ALL = False
EGG_RARITY_WEIGHTS = [
    (Egg.RARITY_COMMON, 0.70),
    (Egg.RARITY_RARE, 0.25),
    (Egg.RARITY_LEGENDARY, 0.05),
]


def _roll_egg_rarity(profile):
    if profile.legendary_pity_days >= LEGENDARY_PITY_DAYS:
        return Egg.RARITY_LEGENDARY

    roll = random.random()
    cursor = 0
    for rarity, chance in EGG_RARITY_WEIGHTS:
        cursor += chance
        if roll < cursor:
            return rarity
    return Egg.RARITY_COMMON


def _record_daily_feed(profile):
    today = timezone.localdate()
    if profile.last_feed_date == today:
        return []

    if profile.last_feed_date == today - timedelta(days=1):
        profile.feeding_streak_days += 1
    else:
        profile.feeding_streak_days = 1

    profile.last_feed_date = today
    profile.legendary_pity_days += 1
    profile.best_feed_streak_days = max(profile.best_feed_streak_days, profile.feeding_streak_days)
    return [
        'last_feed_date',
        'feeding_streak_days',
        'legendary_pity_days',
        'best_feed_streak_days',
    ]


def get_weather():
    """获取北京真实天气，wttr.in 免费 API，缓存 30 分钟"""
    now = time.time()
    if _weather_cache['data'] and (now - _weather_cache['ts']) < 1800:
        return _weather_cache['data']

    try:
        resp = requests.get('https://wttr.in/Beijing?format=j1', timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            cur = data['current_condition'][0]
            code = int(cur['weatherCode'])
            desc = cur['weatherDesc'][0]['value']
            temp = cur['temp_C']
            weather = _map_weather(code, desc, temp)
            _weather_cache['data'] = weather
            _weather_cache['ts'] = now
            return weather
    except Exception:
        pass

    # 降级：返回缓存 或 默认晴天
    if _weather_cache['data']:
        return _weather_cache['data']
    return {'type': 'sunny', 'desc': '晴天', 'temp': '20', 'icon': '☀️'}


def _map_weather(code, desc, temp):
    """wttr.in 天气码 → 我们的天气类型"""
    mapping = {
        (113,):            ('sunny',   '☀️'),
        (116,):            ('cloudy',  '⛅'),
        (119, 122):        ('overcast','☁️'),
        (176, 263, 266, 293, 296, 299, 302, 305, 308, 311, 314, 353, 356, 359):
                           ('rain',    '🌧️'),
        (179, 323, 326, 329, 332, 335, 338, 371, 395):
                           ('snow',    '🌨️'),
        (182, 185, 281, 284):
                           ('sleet',   '🌨️'),
        (200, 386, 389):   ('thunder', '⛈️'),
        (143, 248, 260):   ('fog',     '🌫️'),
    }
    for codes, (wtype, icon) in mapping.items():
        if code in codes:
            return {'type': wtype, 'desc': desc, 'temp': temp, 'icon': icon}
    return {'type': 'sunny', 'desc': desc, 'temp': temp, 'icon': '☀️'}


# ── 鸭舍状态计算（每次请求动态算）────────────────────────────────

def _sync_duck_state(profile):
    """
    同步鸭子状态：
    - 喂食超过4小时 → 消化完成 → completed_feeds + 1
    - 累计完成2次喂食 → 产1颗蛋 → completed_feeds 归零
    """
    if not profile.feed_start_time:
        return

    elapsed = (timezone.now() - profile.feed_start_time).total_seconds() / 3600

    if elapsed >= 4.0:
        # 本次喂食消化完成
        profile.feed_start_time = None
        profile.completed_feeds += 1
        update_fields = ['feed_start_time', 'completed_feeds']

        # 攒够2次 → 下蛋！
        if profile.completed_feeds >= 2:
            rarity = _roll_egg_rarity(profile)
            Egg.objects.create(user=profile.user, rarity=rarity)
            profile.completed_feeds = 0
            if rarity == Egg.RARITY_LEGENDARY:
                profile.legendary_pity_days = 0
                update_fields.append('legendary_pity_days')

        profile.save(update_fields=update_fields)


def is_duck_sleeping():
    """鸭鸭睡觉时间：21:00 - 次日 6:00（北京时间）"""
    now = timezone.localtime(timezone.now())
    return now.hour >= 21 or now.hour < 6


def get_sleep_countdown():
    """返回距离鸭鸭醒来的时间描述"""
    now = timezone.localtime(timezone.now())
    if now.hour >= 21:
        wake_hour = 6  # 明早6点
        remaining = (24 - now.hour) + wake_hour
    elif now.hour < 6:
        remaining = 6 - now.hour
    else:
        return ''
    if remaining == 0:
        return '鸭鸭马上就醒啦～'
    return f'还有约 {remaining} 小时'

# ── 用户注册 ────────────────────────────────────────────────

def _is_admin_user(user):
    return user.is_staff or user.is_superuser


def _safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ''


def front_user_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def frontend_login_view(request):
    if request.user.is_authenticated:
        return redirect(_safe_next_url(request) or 'yard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect(_safe_next_url(request) or 'yard')

    return render(request, 'registration/login.html', {
        'form': form,
        'next': _safe_next_url(request),
    })


def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 创建用户的鸭鸭档案，附赠 180g 新手饲料
            DuckProfile.objects.create(
                user=user,
                feed_grams=180,
                feed_start_time=None,
            )
            login(request, user)
            messages.success(request, '🎉 欢迎来到明湖鸭舍！送你一份 180g 新手饲料～')
            return redirect('yard')
    else:
        form = UserCreationForm()
    return render(request, 'duckapp/register.html', {'form': form})


# ── 鸭舍主页 ────────────────────────────────────────────────

SCENES = [
    {'key': 'minghu',  'name': '明湖',    'icon': '🌊', 'label': '明湖鸭舍',
     'duck_img': 'duck图片7.png', 'duck_mood': '交大鸭鸭'},
    {'key': 'siyuan',  'name': '思源楼',  'icon': '🏛️', 'label': '思源楼广场',
     'duck_img': 'duck图片1.png', 'duck_mood': '你人还怪好嘞'},
    {'key': 'library', 'name': '图书馆',  'icon': '📚', 'label': '图书馆',
     'duck_img': 'duck图片5.png', 'duck_mood': '学霸鸭'},
    {'key': 'ginkgo',  'name': '银杏大道','icon': '🍂', 'label': '银杏大道',
     'duck_img': 'duck图片9.png', 'duck_mood': '秋日鸭'},
    {'key': 'garden',  'name': '芳华园',  'icon': '🌸', 'label': '芳华园',
     'duck_img': 'duck图片2.png', 'duck_mood': '悠闲鸭'},
    {'key': 'sports',  'name': '运动场',  'icon': '⚽', 'label': '运动场',
     'duck_img': 'duck图片6.png', 'duck_mood': '活力鸭'},
]


@front_user_required
def yard_view(request):
    profile, _ = DuckProfile.objects.get_or_create(
        user=request.user,
        defaults={'feed_grams': 180},
    )
    _sync_duck_state(profile)

    # 当前场景
    scene_key = request.GET.get('scene', 'minghu')
    if scene_key not in [s['key'] for s in SCENES]:
        scene_key = 'minghu'

    # 获取待收集的蛋
    uncollected_eggs = Egg.objects.filter(user=request.user, collected=False).order_by('laid_at')
    collected_eggs = Egg.objects.filter(user=request.user, collected=True).count()
    outfit_unlocked = OUTFIT_PREVIEW_UNLOCK_ALL or collected_eggs >= OUTFIT_UNLOCK_EGGS_REQUIRED
    outfit_unlock_slots = collected_eggs // OUTFIT_UNLOCK_EGGS_REQUIRED
    rarity_counts = dict(
        Egg.objects.filter(user=request.user, collected=True)
        .values_list('rarity')
        .annotate(count=Count('id'))
    )

    # 喂食状态
    is_feeding = profile.is_feeding()
    progress = profile.feeding_progress_percent()
    remaining_h = profile.remaining_feed_hours()
    today = timezone.localdate()
    feed_accelerate_count = profile.feed_accelerate_count if profile.feed_accelerate_date == today else 0

    # 社区照片
    recent_photos = Photo.objects.filter(approved=True).order_by('-uploaded_at')[:8]

    # 北京真实天气
    weather = get_weather()

    # 鸭鸭睡眠状态
    sleeping = is_duck_sleeping()
    sleep_countdown = get_sleep_countdown() if sleeping else ''

    context = {
        'profile': profile,
        'uncollected_eggs': uncollected_eggs,
        'collected_eggs': collected_eggs,
        'outfit_unlock_eggs_required': OUTFIT_UNLOCK_EGGS_REQUIRED,
        'outfit_unlock_eggs_left': 0 if outfit_unlocked else max(0, OUTFIT_UNLOCK_EGGS_REQUIRED - collected_eggs),
        'outfit_unlock_slots': outfit_unlock_slots,
        'outfit_unlocked': outfit_unlocked,
        'is_feeding': is_feeding,
        'progress': progress,
        'remaining_h': remaining_h,
        'feed_accelerations_left': max(0, FEED_ACCELERATE_DAILY_LIMIT - feed_accelerate_count),
        'feed_accelerate_daily_limit': FEED_ACCELERATE_DAILY_LIMIT,
        'feed_accelerate_hours': FEED_ACCELERATE_HOURS,
        'feed_challenge_reward_grams': FEED_CHALLENGE_REWARD_GRAMS,
        'egg_progress_done': profile.egg_progress()[0],
        'egg_progress_total': profile.egg_progress()[1],
        'egg_progress_pct': profile.egg_progress_percent(),
        'common_eggs': rarity_counts.get(Egg.RARITY_COMMON, 0),
        'rare_eggs': rarity_counts.get(Egg.RARITY_RARE, 0),
        'legendary_eggs': rarity_counts.get(Egg.RARITY_LEGENDARY, 0),
        'feeding_streak_days': profile.feeding_streak_days,
        'legendary_pity_days': profile.legendary_pity_days,
        'legendary_pity_target': LEGENDARY_PITY_DAYS,
        'legendary_pity_left': max(0, LEGENDARY_PITY_DAYS - profile.legendary_pity_days),
        'recent_photos': recent_photos,
        'scenes': SCENES,
        'current_scene': scene_key,
        'weather': weather,
        'is_sleeping': sleeping,
        'sleep_countdown': sleep_countdown,
    }
    # 找出当前场景的鸭鸭图片
    for s in SCENES:
        if s['key'] == scene_key:
            context['duck_img'] = s['duck_img']
            context['duck_mood'] = s['duck_mood']
            break
    return render(request, 'duckapp/yard.html', context)


# ── 辅助：保持场景参数的跳转 ────────────────────────────────

def _redirect_yard(request):
    """跳回鸭舍，保留场景参数"""
    scene = request.GET.get('scene', '')
    url = '/'
    if scene:
        url += f'?scene={scene}'
    return redirect(url)


# ── 喂食 ────────────────────────────────────────────────────

@front_user_required
def feed_view(request):
    profile = request.user.duck_profile

    # 睡觉时间不能喂食
    if is_duck_sleeping():
        messages.warning(request, '🌙 鸭鸭已经睡着啦～晚上 21:00 到早上 6:00 是鸭鸭的休息时间，不要打扰它哦！明天再来喂食吧～')
        return _redirect_yard(request)

    if profile.is_feeding():
        messages.warning(request, '鸭鸭正在吃饭呢，别急～')
        return _redirect_yard(request)

    if profile.feed_grams < 180:
        messages.error(request, f'饲料不够啦！还需要 {180 - profile.feed_grams}g，快去社区分享照片吧～')
        return _redirect_yard(request)

    # 消耗 180g，开始喂食
    profile.feed_grams -= 180
    profile.feed_start_time = timezone.now()
    update_fields = ['feed_grams', 'feed_start_time'] + _record_daily_feed(profile)
    profile.save(update_fields=update_fields)

    pity_left = max(0, LEGENDARY_PITY_DAYS - profile.legendary_pity_days)
    if pity_left:
        pity_hint = f'连续喂养第 {profile.feeding_streak_days} 天，距离传说蛋保底还差 {pity_left} 天。'
    else:
        pity_hint = '保底已就绪：下一颗蛋必定是传说金冠彩蛋！'
    messages.success(request, f'🍞 投喂成功！鸭鸭开心地吃起来了～4小时后消化完毕，攒够2份饲料就能下一颗蛋哦！{pity_hint}')
    return _redirect_yard(request)


# ── 小游戏通关加速进食 ───────────────────────────────────────

@front_user_required
def accelerate_feed_view(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': '请用 POST'}, status=405)

    try:
        body = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        body = {}

    try:
        challenge_score = int(body.get('score', 0))
    except (TypeError, ValueError):
        challenge_score = 0

    game_name = body.get('game')
    challenge_passed = (
        (game_name == 'snake_quiz' and challenge_score > 60) or
        (game_name == 'minesweeper' and body.get('won') is True) or
        (game_name == 'gomoku' and body.get('won') is True)
    )
    if not challenge_passed:
        return JsonResponse({'ok': False, 'error': '挑战通关后才能加速哦～'}, status=400)

    profile = request.user.duck_profile
    _sync_duck_state(profile)

    if is_duck_sleeping():
        return JsonResponse({'ok': False, 'error': '鸭鸭已经睡着啦，明天再来挑战吧～'}, status=400)

    if not profile.is_feeding():
        return JsonResponse({'ok': False, 'error': '鸭鸭现在没有在吃饭，先投喂一份饲料吧～'}, status=400)

    today = timezone.localdate()
    if profile.feed_accelerate_date != today:
        profile.feed_accelerate_date = today
        profile.feed_accelerate_count = 0

    if profile.feed_accelerate_count >= FEED_ACCELERATE_DAILY_LIMIT:
        return JsonResponse({'ok': False, 'error': '今天的 3 次加速机会已经用完啦～'}, status=400)

    profile.feed_start_time -= timedelta(hours=FEED_ACCELERATE_HOURS)
    profile.feed_accelerate_count += 1
    profile.feed_grams += FEED_CHALLENGE_REWARD_GRAMS
    profile.save(update_fields=[
        'feed_grams',
        'feed_start_time',
        'feed_accelerate_date',
        'feed_accelerate_count',
    ])

    _sync_duck_state(profile)
    accelerations_left = max(0, FEED_ACCELERATE_DAILY_LIMIT - profile.feed_accelerate_count)
    completed = not profile.is_feeding()

    if completed:
        message = f'挑战成功！获得 {FEED_CHALLENGE_REWARD_GRAMS}g 饲料，这次进食也已经加速完成啦～'
    else:
        message = f'挑战成功！获得 {FEED_CHALLENGE_REWARD_GRAMS}g 饲料，本次进食加速 {FEED_ACCELERATE_HOURS} 小时，今天还剩 {accelerations_left} 次。'

    return JsonResponse({
        'ok': True,
        'message': message,
        'feed_grams': profile.feed_grams,
        'feed_reward_grams': FEED_CHALLENGE_REWARD_GRAMS,
        'completed': completed,
        'progress': profile.feeding_progress_percent(),
        'remaining_hours': round(profile.remaining_feed_hours(), 2),
        'accelerations_left': accelerations_left,
        'accelerations_used': profile.feed_accelerate_count,
    })


# ── 收集鸭蛋 ────────────────────────────────────────────────

@front_user_required
def collect_egg_view(request, egg_id):
    try:
        egg = Egg.objects.get(id=egg_id, user=request.user, collected=False)
        egg.collected = True
        egg.save(update_fields=['collected'])

        profile = request.user.duck_profile
        profile.total_eggs += 1
        profile.save(update_fields=['total_eggs'])

        if profile.total_eggs % OUTFIT_UNLOCK_EGGS_REQUIRED == 0:
            outfit_hint = '你获得了 1 个衣橱解锁名额，去鸭鸭衣橱选择一件服饰吧！'
        else:
            eggs_left = OUTFIT_UNLOCK_EGGS_REQUIRED - (profile.total_eggs % OUTFIT_UNLOCK_EGGS_REQUIRED)
            outfit_hint = f'再收集 {eggs_left} 颗蛋可获得 1 个衣橱解锁名额。'
        messages.success(request, f'🥚 收获{egg.rarity_label}蛋：{egg.rarity_name}！你为明湖的真鸭鸭赢得了一份粮食！{outfit_hint}')
    except Egg.DoesNotExist:
        messages.error(request, '这颗蛋已经被收走啦～')

    return _redirect_yard(request)


# ── 社区广场 ────────────────────────────────────────────────

@front_user_required
def community_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        photo = Photo.objects.create(
            user=request.user,
            image=request.FILES['image'],
            description=request.POST.get('description', ''),
            approved=True,       # 模拟审核：直接通过
            feed_earned=True,
        )
        # 发放 180g 饲料奖励
        profile = request.user.duck_profile
        profile.feed_grams += 180
        profile.save(update_fields=['feed_grams'])

        messages.success(request, f'📸 可爱照片分享成功！审核通过，获得 180g 饲料！当前饲料：{profile.feed_grams}g')
        return redirect('community')

    # 使用模型默认排序（置顶优先 + 时间倒序）
    photos = list(Photo.objects.filter(approved=True)[:20])

    # 为每张照片附加信息（不能用 _ 前缀，Django 模板禁止）
    for p in photos:
        p.user_liked = Like.objects.filter(photo=p, user=request.user).exists()
        p.comment_list = p.comments.select_related('user').all()[:10]
        # 标记评论者是否为管理员
        for c in p.comment_list:
            c.is_admin = c.user.is_staff

    return render(request, 'duckapp/community.html', {
        'photos': photos,
        'user': request.user,
        'is_staff': request.user.is_staff,
    })


# ── 点赞 API ────────────────────────────────────────────────

@csrf_exempt
@front_user_required
def like_view(request, photo_id):
    """POST: 切换点赞"""
    if request.method != 'POST':
        return JsonResponse({'error': '请用 POST'}, status=405)

    try:
        photo = Photo.objects.get(id=photo_id, approved=True)
    except Photo.DoesNotExist:
        return JsonResponse({'error': '照片不存在'}, status=404)

    like, created = Like.objects.get_or_create(user=request.user, photo=photo)
    if not created:
        # 已经点过赞 → 取消
        like.delete()
        return JsonResponse({'liked': False, 'count': photo.like_count()})

    return JsonResponse({'liked': True, 'count': photo.like_count()})


# ── 评论 API ────────────────────────────────────────────────

@csrf_exempt
@front_user_required
def comment_view(request, photo_id):
    """POST: 发表评论 | DELETE: 删除自己的评论"""
    try:
        photo = Photo.objects.get(id=photo_id, approved=True)
    except Photo.DoesNotExist:
        return JsonResponse({'error': '照片不存在'}, status=404)

    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            text = body.get('text', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'error': '格式错误'}, status=400)

        if not text or len(text) > 300:
            return JsonResponse({'error': '评论1-300字'}, status=400)

        comment = Comment.objects.create(user=request.user, photo=photo, text=text)
        return JsonResponse({
            'id': comment.id,
            'user': comment.user.username,
            'text': comment.text,
            'time': comment.created_at.strftime('%m/%d %H:%M'),
            'is_staff': request.user.is_staff,
        })

    if request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            comment_id = body.get('comment_id')
        except json.JSONDecodeError:
            return JsonResponse({'error': '格式错误'}, status=400)

        try:
            comment = Comment.objects.get(id=comment_id, photo=photo)
        except Comment.DoesNotExist:
            return JsonResponse({'error': '评论不存在'}, status=404)

        if comment.user != request.user:
            return JsonResponse({'error': '只能删除自己的评论'}, status=403)

        comment.delete()
        return JsonResponse({'deleted': True, 'count': photo.comment_count()})


# ── 管理员：置顶/取消置顶 ──────────────────────────────────────

@csrf_exempt
@login_required
def pin_photo_view(request, photo_id):
    """POST: 管理员切换置顶状态"""
    if not request.user.is_staff:
        return JsonResponse({'error': '仅管理员可操作'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': '请用 POST'}, status=405)

    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return JsonResponse({'error': '照片不存在'}, status=404)

    photo.is_pinned = not photo.is_pinned
    photo.save(update_fields=['is_pinned'])
    return JsonResponse({'pinned': photo.is_pinned})


# ── 管理员：删除帖子 ──────────────────────────────────────────

@csrf_exempt
@login_required
def delete_photo_view(request, photo_id):
    """POST: 管理员删除照片"""
    if not request.user.is_staff:
        return JsonResponse({'error': '仅管理员可操作'}, status=403)

    if request.method != 'POST':
        return JsonResponse({'error': '请用 POST'}, status=405)

    try:
        photo = Photo.objects.get(id=photo_id)
    except Photo.DoesNotExist:
        return JsonResponse({'error': '照片不存在'}, status=404)

    photo.image.delete(save=False)  # 删除文件
    photo.delete()
    return JsonResponse({'deleted': True})


@front_user_required
def profile_view(request):
    profile = request.user.duck_profile
    _sync_duck_state(profile)

    if request.method == 'POST':
        text = request.POST.get('feedback', '').strip()
        contact = request.POST.get('contact', '').strip()
        if not text:
            messages.error(request, '反馈内容不能为空哦～')
        elif len(text) > 500:
            messages.error(request, '反馈最多 500 字，稍微精简一下吧～')
        else:
            Feedback.objects.create(
                user=request.user,
                text=text,
                contact=contact[:120],
            )
            messages.success(request, '收到反馈啦，谢谢你帮鸭舍变得更好～')
            return redirect('profile')

    collected_eggs = Egg.objects.filter(
        user=request.user,
        collected=True,
    ).order_by('-laid_at')
    liked_photos = Photo.objects.filter(
        likes__user=request.user,
        approved=True,
    ).select_related('user').order_by('-likes__created_at')[:12]
    own_photos_count = Photo.objects.filter(user=request.user, approved=True).count()
    feedback_count = Feedback.objects.filter(user=request.user).count()
    rarity_counts = dict(
        Egg.objects.filter(user=request.user, collected=True)
        .values_list('rarity')
        .annotate(count=Count('id'))
    )

    return render(request, 'duckapp/profile.html', {
        'profile': profile,
        'collected_eggs': collected_eggs,
        'liked_photos': liked_photos,
        'own_photos_count': own_photos_count,
        'feedback_count': feedback_count,
        'common_eggs': rarity_counts.get(Egg.RARITY_COMMON, 0),
        'rare_eggs': rarity_counts.get(Egg.RARITY_RARE, 0),
        'legendary_eggs': rarity_counts.get(Egg.RARITY_LEGENDARY, 0),
    })


@front_user_required
def stats_view(request):
    profile = request.user.duck_profile
    photos_count = Photo.objects.filter(user=request.user, approved=True).count()
    collected = profile.total_eggs
    return render(request, 'duckapp/stats.html', {
        'profile': profile,
        'photos_count': photos_count,
        'collected': collected,
    })


# ── 鸭鸭聊天 API ────────────────────────────────────────────

FALLBACK_REPLIES = [
    "嘎～你好呀！鸭鸭今天在明湖游泳，水好凉快～",
    "嘎嘎！鸭鸭刚吃了一顿饲料，肚子圆滚滚的～",
    "鸭鸭最喜欢北交的银杏大道了，秋天的时候金灿灿的好漂亮嘎～",
    "你见过思源楼前面的喷泉吗？鸭鸭有时候会去那里玩水～",
    "嘎～别担心，鸭鸭每天都在努力下蛋呢！",
    "鸭鸭的梦想是让明湖的每一位同学都开开心心的～嘎！",
    "芳华园的花开了吗？鸭鸭想去看花花～",
    "嘎嘎嘎！你真好，陪鸭鸭聊天～",
]


@csrf_exempt
@front_user_required
def chat_view(request):
    """鸭鸭对话 API"""
    if request.method != 'POST':
        return JsonResponse({'error': '请用 POST'}, status=405)

    try:
        body = json.loads(request.body)
        user_message = body.get('message', '').strip()
    except json.JSONDecodeError:
        return JsonResponse({'error': '消息格式错误'}, status=400)

    if not user_message:
        return JsonResponse({'reply': '嘎？你想说什么呀～'})

    # 尝试调用 DeepSeek API
    api_key = settings.DEEPSEEK_API_KEY
    if api_key:
        try:
            resp = requests.post(
                settings.DEEPSEEK_API_URL,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'model': settings.DEEPSEEK_MODEL,
                    'messages': [
                        {'role': 'system', 'content': settings.DUCK_SYSTEM_PROMPT},
                        {'role': 'user', 'content': user_message},
                    ],
                    'max_tokens': 150,
                    'temperature': 0.9,
                },
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data['choices'][0]['message']['content'].strip()
                return JsonResponse({'reply': reply})
            else:
                # API 出错，用本地回复
                import random
                reply = random.choice(FALLBACK_REPLIES)
                return JsonResponse({'reply': reply})
        except requests.RequestException:
            pass

    # 无 API Key 或请求失败 → 本地随机回复
    import random
    reply = random.choice(FALLBACK_REPLIES)
    return JsonResponse({'reply': reply})
