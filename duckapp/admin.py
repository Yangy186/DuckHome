from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import DuckProfile, Egg, Photo, Like, Comment, Feedback


admin.site.site_header = '明湖鸭鸭后台管理'
admin.site.site_title = '明湖鸭鸭后台'
admin.site.index_title = '运营管理台'


class DuckProfileInline(admin.StackedInline):
    model = DuckProfile
    can_delete = False
    extra = 0
    fields = (
        'duck_name',
        'feed_grams',
        'total_eggs',
        'completed_feeds',
        'feed_start_time',
        'last_feed_date',
        'feeding_streak_days',
        'legendary_pity_days',
        'best_feed_streak_days',
        'feed_accelerate_date',
        'feed_accelerate_count',
        'created_at',
    )
    readonly_fields = ('created_at',)


admin.site.unregister(User)


@admin.register(User)
class DuckUserAdmin(UserAdmin):
    inlines = (DuckProfileInline,)
    list_display = ('username', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email')


@admin.register(DuckProfile)
class DuckProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'duck_name',
        'feed_grams',
        'completed_feeds',
        'feed_accelerate_count',
        'feeding_streak_days',
        'legendary_pity_days',
        'total_eggs',
    )
    list_editable = (
        'duck_name',
        'feed_grams',
        'completed_feeds',
        'feed_accelerate_count',
        'feeding_streak_days',
        'legendary_pity_days',
        'total_eggs',
    )
    list_filter = ('feed_accelerate_date', 'last_feed_date', 'created_at')
    search_fields = ('user__username', 'duck_name')
    readonly_fields = ('created_at',)
    actions = (
        'grant_180_feed',
        'grant_600_feed',
        'clear_feed',
        'reset_today_accelerate',
    )
    fieldsets = (
        ('用户档案', {
            'fields': ('user', 'duck_name', 'created_at'),
        }),
        ('饲料与喂养', {
            'fields': (
                'feed_grams',
                'feed_start_time',
                'completed_feeds',
                'last_feed_date',
                'feeding_streak_days',
                'best_feed_streak_days',
                'legendary_pity_days',
            ),
        }),
        ('小游戏加速', {
            'fields': ('feed_accelerate_date', 'feed_accelerate_count'),
        }),
        ('收集统计', {
            'fields': ('total_eggs',),
        }),
    )

    @admin.action(description='给选中用户增加 180g 饲料')
    def grant_180_feed(self, request, queryset):
        for profile in queryset:
            profile.feed_grams += 180
            profile.save(update_fields=['feed_grams'])

    @admin.action(description='给选中用户增加 600g 饲料')
    def grant_600_feed(self, request, queryset):
        for profile in queryset:
            profile.feed_grams += 600
            profile.save(update_fields=['feed_grams'])

    @admin.action(description='清空选中用户饲料')
    def clear_feed(self, request, queryset):
        queryset.update(feed_grams=0)

    @admin.action(description='重置今日加速次数')
    def reset_today_accelerate(self, request, queryset):
        queryset.update(feed_accelerate_count=0, feed_accelerate_date=None)


@admin.register(Egg)
class EggAdmin(admin.ModelAdmin):
    list_display = ('user', 'rarity', 'collected', 'laid_at')
    list_editable = ('rarity', 'collected')
    list_filter = ('rarity', 'collected')
    search_fields = ('user__username',)
    readonly_fields = ('laid_at',)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'description', 'approved', 'is_pinned', 'feed_earned', 'uploaded_at')
    list_editable = ('approved', 'is_pinned', 'feed_earned')
    list_filter = ('approved', 'is_pinned', 'feed_earned', 'uploaded_at')
    search_fields = ('user__username', 'description')
    readonly_fields = ('uploaded_at',)
    actions = ('approve_photos', 'pin_photos', 'unpin_photos')

    @admin.action(description='审核通过选中照片')
    def approve_photos(self, request, queryset):
        queryset.update(approved=True)

    @admin.action(description='置顶选中照片')
    def pin_photos(self, request, queryset):
        queryset.update(is_pinned=True)

    @admin.action(description='取消置顶选中照片')
    def unpin_photos(self, request, queryset):
        queryset.update(is_pinned=False)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'photo__description')
    readonly_fields = ('created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'photo', 'text', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'photo__description', 'text')
    readonly_fields = ('created_at',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'text', 'contact', 'resolved', 'created_at')
    list_editable = ('resolved',)
    list_filter = ('resolved', 'created_at')
    search_fields = ('user__username', 'text', 'contact')
    readonly_fields = ('created_at',)
    actions = ('mark_resolved', 'mark_unresolved')

    @admin.action(description='标记为已处理')
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)

    @admin.action(description='标记为未处理')
    def mark_unresolved(self, request, queryset):
        queryset.update(resolved=False)
