from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone


class DuckProfile(models.Model):
    """用户鸭鸭档案 - 1对1关联 User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='duck_profile')
    duck_name = models.CharField(max_length=20, default='明湖鸭鸭', verbose_name='鸭鸭名字')
    feed_grams = models.IntegerField(default=0, verbose_name='剩余饲料(g)')
    feed_start_time = models.DateTimeField(null=True, blank=True, verbose_name='喂食开始时间')
    total_eggs = models.IntegerField(default=0, verbose_name='累计收获鸭蛋')
    completed_feeds = models.IntegerField(default=0, verbose_name='已完成喂食次数(0-2)')
    last_feed_date = models.DateField(null=True, blank=True, verbose_name='上次喂食日期')
    feeding_streak_days = models.IntegerField(default=0, verbose_name='连续喂食天数')
    legendary_pity_days = models.IntegerField(default=0, verbose_name='传说蛋保底天数')
    best_feed_streak_days = models.IntegerField(default=0, verbose_name='最长连续喂食天数')
    feed_accelerate_date = models.DateField(null=True, blank=True, verbose_name='上次加速日期')
    feed_accelerate_count = models.IntegerField(default=0, verbose_name='今日加速次数')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '鸭鸭档案'
        verbose_name_plural = '鸭鸭档案'

    def feeding_elapsed_hours(self):
        """已喂食了多久（小时）"""
        if not self.feed_start_time:
            return 0
        delta = timezone.now() - self.feed_start_time
        hours = delta.total_seconds() / 3600
        return min(hours, 4.0)

    def is_feeding(self):
        """是否正在喂食中"""
        if not self.feed_start_time:
            return False
        return self.feeding_elapsed_hours() < 4.0

    def remaining_feed_hours(self):
        """剩余喂食时间（小时）"""
        if not self.is_feeding():
            return 0
        return max(0, 4.0 - self.feeding_elapsed_hours())

    def feeding_progress_percent(self):
        """喂食进度 0-100"""
        if not self.is_feeding():
            return 0
        return int((self.feeding_elapsed_hours() / 4.0) * 100)

    def egg_progress(self):
        """下蛋进度：(已完成次数, 需要次数)"""
        return (self.completed_feeds, 2)

    def egg_progress_percent(self):
        """下蛋进度 0-100%"""
        return int((self.completed_feeds / 2) * 100)

    def __str__(self):
        return f"{self.user.username} 的 {self.duck_name}"


class Egg(models.Model):
    """鸭蛋"""
    RARITY_COMMON = 'common'
    RARITY_RARE = 'rare'
    RARITY_LEGENDARY = 'legendary'
    RARITY_CHOICES = [
        (RARITY_COMMON, '明湖暖蛋'),
        (RARITY_RARE, '星露蓝蛋'),
        (RARITY_LEGENDARY, '金冠彩蛋'),
    ]
    RARITY_META = {
        RARITY_COMMON: {
            'name': '明湖暖蛋',
            'label': '普通',
            'image': 'v1.png',
        },
        RARITY_RARE: {
            'name': '星露蓝蛋',
            'label': '稀有',
            'image': 'v2.png',
        },
        RARITY_LEGENDARY: {
            'name': '金冠彩蛋',
            'label': '传说',
            'image': 'v3.png',
        },
    }

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='eggs')
    laid_at = models.DateTimeField(auto_now_add=True, verbose_name='下蛋时间')
    collected = models.BooleanField(default=False, verbose_name='是否已收集')
    rarity = models.CharField(
        max_length=20,
        choices=RARITY_CHOICES,
        default=RARITY_COMMON,
        verbose_name='稀有度',
    )

    class Meta:
        verbose_name = '鸭蛋'
        verbose_name_plural = '鸭蛋'
        ordering = ['-laid_at']

    def __str__(self):
        status = '🥚已收' if self.collected else '🥚待收'
        return f"{self.user.username} 的{self.rarity_name} ({status})"

    @property
    def rarity_name(self):
        return self.RARITY_META.get(self.rarity, self.RARITY_META[self.RARITY_COMMON])['name']

    @property
    def rarity_label(self):
        return self.RARITY_META.get(self.rarity, self.RARITY_META[self.RARITY_COMMON])['label']

    @property
    def image_name(self):
        return self.RARITY_META.get(self.rarity, self.RARITY_META[self.RARITY_COMMON])['image']


class Photo(models.Model):
    """社区照片"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photos/', verbose_name='照片')
    description = models.CharField(max_length=200, blank=True, verbose_name='描述')
    approved = models.BooleanField(default=True, verbose_name='审核通过')
    is_pinned = models.BooleanField(default=False, verbose_name='置顶')
    feed_earned = models.BooleanField(default=False, verbose_name='已获得饲料奖励')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '社区照片'
        verbose_name_plural = '社区照片'
        ordering = ['-is_pinned', '-uploaded_at']

    def __str__(self):
        return f"{self.user.username} 的照片 - {'✅' if self.approved else '⏳'}"

    def like_count(self):
        return self.likes.count()

    def comment_count(self):
        return self.comments.count()


class Like(models.Model):
    """点赞"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo')
        verbose_name = '点赞'
        verbose_name_plural = '点赞'

    def __str__(self):
        return f"{self.user.username} ❤️ {self.photo.id}"


class Comment(models.Model):
    """评论"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='comments')
    text = models.CharField(max_length=300, verbose_name='评论内容')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = '评论'
        verbose_name_plural = '评论'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"


class Feedback(models.Model):
    """用户反馈"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    text = models.CharField(max_length=500, verbose_name='反馈内容')
    contact = models.CharField(max_length=120, blank=True, verbose_name='联系方式')
    resolved = models.BooleanField(default=False, verbose_name='已处理')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='反馈时间')

    class Meta:
        verbose_name = '用户反馈'
        verbose_name_plural = '用户反馈'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"
