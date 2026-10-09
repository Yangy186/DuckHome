# 🦆 明湖鸭舍 — 开发说明文档

> 北京交通大学 · BS架构大作业 · Django 像素养成网页

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [快速启动](#3-快速启动)
4. [项目结构](#4-项目结构)
5. [数据模型](#5-数据模型)
6. [URL 路由表](#6-url-路由表)
7. [核心功能详解](#7-核心功能详解)
8. [前端架构](#8-前端架构)
9. [配置项说明](#9-配置项说明)
10. [扩展开发指南](#10-扩展开发指南)

---

## 1. 项目概述

### 1.1 玩法核心循环

```
拍动物照片 → 分享到社区（+180g 饲料）
    ↓
喂鸭鸭吃 180g 饲料（4小时消化）
    ↓
完成 2 次喂食 → 下一颗蛋 🥚
    ↓
收集鸭蛋 → 为明湖真鸭鸭赢得粮食 🎉
```

### 1.2 特色功能

| 功能 | 说明 |
|------|------|
| 🏛️ 6 个北交校园场景 | 明湖、思源楼、图书馆、银杏大道、芳华园、运动场 — 纯 CSS 像素画 |
| 🦆 9 款真实鸭鸭形象 | 每场景配不同鸭鸭 PNG + 心情标签 |
| 💬 AI 鸭鸭聊天 | DeepSeek API 驱动，鸭鸭人设对话 |
| 🌤️ 真实天气 | wttr.in 免费 API 获取北京天气，CSS 特效（雨/雪/雾/雷）|
| 🌅 时间光照 | 6 时段（清晨→夜晚）自动变换场景色调 + 星星 |
| 💤 鸭鸭睡觉 | 21:00-6:00 自动戴睡帽、闭眼、ZZZ 漂浮，禁止喂食 |
| 📸 社区广场 | 上传照片 + 点赞（切换式）+ 评论 + 管理员 |
| 🛡️ 管理员系统 | is_staff 用户：置顶帖子、删除帖子、管理员评论标签 |
| 🥚 下蛋进度 | 2 份饲料 → 1 颗蛋，可视化进度条 + 步骤指示器 |

---

## 2. 技术栈

| 层 | 技术 | 版本 |
|----|------|------|
| 后端框架 | Django | 4.2.x |
| 数据库 | SQLite | 3.x (Django 内置) |
| 前端 UI | NES.css | CDN |
| 字体 | ZCOOL KuaiLe (站酷快乐体) | Google Fonts |
| AI 对话 | DeepSeek API | `deepseek-chat` |
| 天气数据 | wttr.in | 免费 API |
| 运行环境 | Python | 3.11+ (Windows 11) |

### 2.1 为什么选 SQLite 而非 MySQL

- 零配置：无需安装 MySQL 服务
- 单文件：`db.sqlite3` 即整个数据库
- 可移植：拷贝项目文件夹即可迁移
- 足够用：课设规模完全胜任

---

## 3. 快速启动

### 3.1 环境准备

```bash
# 1. 进入项目目录
cd duckmocker

# 2. 安装依赖（仅两个包）
pip install django==4.2
pip install requests

# 或一键安装
pip install -r requirements.txt
```

### 3.2 数据库初始化

```bash
# 执行迁移（创建表结构）
python manage.py migrate

# 创建管理员账号（可选 — 用于社区管理功能）
python manage.py createsuperuser
# 按提示输入：用户名、邮箱、密码
```

### 3.3 启动服务

```bash
python manage.py runserver
```

浏览器访问：**http://127.0.0.1:8000/**

### 3.4 预置管理员账号

如果已运行过 `createsuperuser`，登录后即可使用社区管理功能。管理员与普通用户共用同一登录入口，登录后社区页面会自动显示管理工具栏。

---

## 4. 项目结构

```
duckmocker/
│
├── manage.py                    # Django 命令行入口
├── requirements.txt             # Python 依赖 (django>=4.2, requests)
├── db.sqlite3                   # SQLite 数据库文件（自动生成）
├── README.md                    # 本文件
│
├── duckmocker/                  # 项目配置包
│   ├── settings.py              # ★ Django 配置（数据库/AI/时区）
│   ├── urls.py                  # 根路由（admin + accounts + duckapp）
│   └── wsgi.py                  # 部署入口
│
├── duckapp/                     # 主应用（所有业务逻辑）
│   ├── models.py                # ★ 5 个数据模型
│   ├── views.py                 # ★ 全部视图函数（~503 行）
│   ├── urls.py                  # 应用路由表
│   └── admin.py                 # Django Admin 注册（预留）
│
├── templates/                   # HTML 模板
│   ├── base.html                # ★ 基础模板（导航栏 + 聊天弹窗 + 布局）
│   ├── registration/
│   │   └── login.html           # 登录页
│   └── duckapp/
│       ├── yard.html            # ★ 鸭舍主页（6 场景 + 时间/天气层）
│       ├── _duck_and_eggs.html  # ★ 鸭鸭+蛋 共享片段（含睡眠特效）
│       ├── _feed_panel.html     # ★ 喂食面板（含睡眠提示）
│       ├── _egg_panel.html      # ★ 下蛋进度面板
│       ├── community.html       # ★ 社区页（上传/点赞/评论/管理）
│       ├── register.html        # 注册页
│       └── stats.html           # 个人统计页
│
├── static/                      # 静态资源
│   ├── css/
│   │   └── style.css            # ★ 全部样式（~1100 行）
│   ├── js/
│   │   └── main.js              # ★ 全部前端 JS（~190 行）
│   └── images/
│       ├── duck图片1-9.png       # 9 张鸭鸭素材
│       └── 北交手绘地图.jpg      # 参考地图
│
└── media/                       # 用户上传文件（自动生成）
    └── photos/                  # 社区照片
```

> 标注 ★ 的是核心文件，修改功能时优先看这些。

---

## 5. 数据模型

### 5.1 ER 关系图

```
User (Django 内置)
  │
  ├──[1:1]── DuckProfile       用户鸭鸭档案
  │            ├─ feed_grams        剩余饲料(g)
  │            ├─ feed_start_time   喂食开始时间
  │            ├─ completed_feeds   已完成喂食次数 (0→1→2→0)
  │            └─ total_eggs        累计收蛋数
  │
  ├──[1:N]── Egg               鸭蛋
  │            ├─ laid_at          下蛋时间
  │            └─ collected        是否已收集
  │
  ├──[1:N]── Photo             社区照片
  │            ├─ image            图片文件
  │            ├─ description      描述
  │            ├─ approved         审核状态（默认 True）
  │            ├─ is_pinned        是否置顶
  │            └─ feed_earned      是否已发放饲料奖励
  │
  ├──[1:N]── Like              点赞 (user+photo 联合唯一)
  │
  └──[1:N]── Comment           评论 (最多 300 字)
```

### 5.2 DuckProfile 核心方法

```python
profile.is_feeding()           # → bool   是否正在喂食
profile.feeding_progress_percent()  # → int 0-100
profile.remaining_feed_hours() # → float  剩余小时
profile.egg_progress()         # → (done, total)  如 (1, 2)
profile.egg_progress_percent() # → int 0-100
```

### 5.3 下蛋机制（纯动态计算）

```
每次请求 yard_view → _sync_duck_state(profile)
  ├─ feed_start_time 距今 ≥ 4h
  │   ├─ completed_feeds += 1
  │   └─ feed_start_time = None
  └─ completed_feeds >= 2
      ├─ 创建 Egg(user=user)
      └─ completed_feeds = 0
```

> **设计要点**：没有 cron 定时任务，全在每次页面请求时动态计算。简单可靠。

---

## 6. URL 路由表

| 路由 | 方法 | 视图 | 说明 | 登录 |
|------|------|------|------|------|
| `/` | GET | `yard_view` | 鸭舍主页（6场景）| ✅ |
| `/register/` | GET/POST | `register_view` | 注册（送180g）| ❌ |
| `/accounts/login/` | GET/POST | Django内置 | 登录 | ❌ |
| `/feed/?scene=xxx` | POST | `feed_view` | 喂食（-180g）| ✅ |
| `/collect/<egg_id>/?scene=xxx` | GET | `collect_egg_view` | 收蛋 | ✅ |
| `/community/` | GET/POST | `community_view` | 社区（上传+浏览）| ✅ |
| `/stats/` | GET | `stats_view` | 个人统计 | ✅ |
| `/chat/` | POST | `chat_view` | 鸭鸭聊天 API（JSON）| ✅ |
| `/like/<photo_id>/` | POST | `like_view` | 点赞切换 API | ✅ |
| `/comment/<photo_id>/` | POST/DELETE | `comment_view` | 评论 API | ✅ |
| `/pin/<photo_id>/` | POST | `pin_photo_view` | 置顶切换（管理员）| ✅ |
| `/delete-photo/<photo_id>/` | POST | `delete_photo_view` | 删帖（管理员）| ✅ |
| `/admin/` | — | Django Admin | 后台管理 | ✅ staff |

### 场景参数说明

主页 URL 通过 `?scene=` GET 参数切换场景：

```
/?scene=minghu     明湖（默认）
/?scene=siyuan     思源楼广场
/?scene=library    图书馆
/?scene=ginkgo     银杏大道
/?scene=garden     芳华园
/?scene=sports     运动场
```

喂食和收蛋会保留该参数，跳回对应场景。

---

## 7. 核心功能详解

### 7.1 场景系统（SCENES 配置）

定义在 `views.py` 顶部 `SCENES` 列表（6 个 dict）：

```python
SCENES = [
    {'key': 'minghu', 'name': '明湖', 'icon': '🌊',
     'duck_img': 'duck图片7.png', 'duck_mood': '交大鸭鸭'},
    # ... 共 6 个
]
```

每个场景在 `yard.html` 中对应一个 `<div class="scene scene-{key}">`，CSS 控制显示/隐藏。场景切换通过 `<a href="?scene=xxx">` 实现（GET 请求，非 JS）。

### 7.2 鸭鸭 AI 聊天

**流程：**

```
用户点鸭鸭 → JS openChat() → 输入消息 → POST /chat/
    ↓
views.chat_view()
    ├─ 调用 DeepSeek API (deepseek-chat 模型)
    │   ├─ system prompt = DUCK_SYSTEM_PROMPT (鸭鸭人设)
    │   ├─ max_tokens = 150
    │   └─ temperature = 0.9
    ├─ 成功 → 返回 AI 回复
    └─ 失败 → 从 FALLBACK_REPLIES (8条) 随机选一条
    ↓
JS addMessage() 渲染聊天气泡
```

**配置位置**：`duckmocker/settings.py` 底部

```python
DEEPSEEK_API_KEY = 'sk-xxx'           # 更换为你的 API Key
DEEPSEEK_API_URL = '.../chat/completions'
DEEPSEEK_MODEL = 'deepseek-chat'
DUCK_SYSTEM_PROMPT = """你是..."""    # 鸭鸭人设文本
```

> **换 API**：chat_view 使用标准 OpenAI 兼容格式，换成 OpenAI/通义千问等只需改 URL + Key。

### 7.3 天气特效

**数据来源**：wttr.in 免费 API（无需注册）

**流程：**

```
每次 yard_view 请求
    ↓
get_weather()
    ├─ 缓存命中（30分钟内）→ 直接返回
    └─ 缓存过期
        ├─ GET https://wttr.in/Beijing?format=j1
        ├─ 解析 weatherCode → 映射天气类型
        └─ 更新缓存
    ↓
模板: <div class="scene-wrapper weather-{type}">
    ↓
CSS: .weather-rain / .weather-snow / ... 触发特效
```

**天气码映射表**（在 `_map_weather()` 中）：

| wttr.in 天气码 | 类型 | 特效 |
|---------------|------|------|
| 113 | sunny | 暖光光晕 |
| 116 | cloudy | 轻微变暗 |
| 119, 122 | overcast | 灰蒙遮罩 |
| 176, 263, 266, ... | rain | 斜向雨丝下落 |
| 200, 386, 389 | thunder | 雨丝 + 随机闪电 |
| 179, 323, 326, ... | snow | 40+ 雪花飘落 |
| 143, 248, 260 | fog | 底部雾层渐变 |

### 7.4 时间光照系统

纯前端实现（`main.js` → `applyTimeOfDay()`）：

| 时段 | 小时 | CSS class | 效果 |
|------|------|-----------|------|
| 清晨 | 5-6 | `time-morning` | 淡蓝紫微光 |
| 上午 | 7-10 | `time-forenoon` | 明亮暖黄 |
| 正午 | 11-13 | `time-noon` | 亮白高光 |
| 下午 | 14-16 | `time-afternoon` | 正常（无遮罩）|
| 傍晚 | 17-18 | `time-dusk` | 橙红晚霞 |
| 夜晚 | 19-4 | `time-night` | 深蓝暗色 + ✦ 星星闪烁 |

> 光照层 `<div class="time-overlay">` 覆盖在场景上方，`pointer-events: none` 不阻挡交互。

### 7.5 鸭鸭睡觉系统

**规则**：北京时间 21:00 - 次日 6:00

**后端**：`is_duck_sleeping()` 检测当前小时

**睡眠时发生的变化**：

| 元素 | 变化 |
|------|------|
| 🎩 睡帽 | 蓝色三角帽 + 白绒球，CSS 绘制，微微晃动 |
| 😴 闭眼 | 两条横线覆盖在鸭鸭图片眼睛位置 |
| 💤 ZZZ | 蓝紫色 "Z Z z" 依次向上漂浮消失 |
| 🛏️ 小窝 | 稻草纹理的温暖小窝（替代影子）|
| 🖼️ 图片 | 变暗 + 蓝调滤镜（opacity 0.65）|
| 🏷️ 标签 | 显示 "💤 睡觉中..." |
| 🥚 鸭蛋 | 隐藏不显示 |
| 🍞 喂食 | 面板替换为睡眠提示 + 倒计时 |
| 🖱️ 点击 | 弹出 "鸭鸭睡着了～别吵醒它哦" |

### 7.6 社区 + 管理员系统

**上传照片**：POST multipart/form → 自动审核通过 → +180g 饲料

**点赞**：POST JSON → toggle 模式（点一次赞、再点取消）

**评论**：POST 发表 / DELETE 删除（仅自己的评论）

**管理员**（`user.is_staff = True`）：

- 🛡️ 页面顶部显示深色管理工具栏
- 📌 置顶/取消置顶（金色边框 + 发光徽章，置顶帖排最前）
- 🗑️ 删除违规帖子（确认弹窗 + 收缩动画）
- 🏷️ 评论旁显示金色「管理员」标签
- 🔒 非 staff 调用 API 返回 403

---

## 8. 前端架构

### 8.1 模板片段（{% include %}）

```
yard.html
  ├─ {% include '_duck_and_eggs.html' %}   ← 每个场景各引用一次（共 6 次）
  ├─ {% include '_feed_panel.html' %}
  └─ {% include '_egg_panel.html' %}
```

> 修改鸭鸭形象只需改 `_duck_and_eggs.html` 一个文件，所有 6 个场景同步生效。

### 8.2 JS 功能清单（main.js）

| 函数 | 用途 |
|------|------|
| `openChat()` / `closeChat()` | 聊天弹窗开关 |
| `sendMessage()` | 发送消息 → fetch `/chat/` |
| `addMessage(text, type)` | 渲染聊天气泡 |
| `initDuck(duckEl)` | 鸭鸭点击 → 聊天 / 睡觉提示 |
| `applyTimeOfDay()` | 时间光照 class |
| `escapeHtml(text)` | XSS 防护 |
| 蛋点击 `✨` 特效 | inline 绑定 |
| 消息 4s 自动消失 | inline 绑定 |

### 8.3 社区页 JS（community.html 内嵌）

| 函数 | 用途 |
|------|------|
| `toggleLike(photoId, btn)` | 点赞切换 + 动画 |
| `toggleComments(photoId, btn)` | 评论区展开/收起 |
| `addComment(photoId)` | 发表评论 + 插入 DOM |
| `deleteComment(photoId, commentId, btn)` | 删除评论 |
| `togglePin(photoId, btn)` | 管理员置顶切换 |
| `deletePhoto(photoId, btn)` | 管理员删除帖子 + 动画 |
| `updateCommentCount(photoId)` | 更新评论计数 badge |

### 8.4 CSRF Token 处理

```javascript
// community.html 内嵌 <script> 中
const CSRF_TOKEN = '{{ csrf_token }}';  // Django 直接注入 token 字符串

// fetch 请求头
headers: { 'X-CSRFToken': CSRF_TOKEN }
```

> **注意**：不能用 `document.querySelector('[name=csrfmiddlewaretoken]')` 获取，因为 `<script>` 不在 `<form>` 内，且 `{% csrf_token %}` 输出的是 `<input>` 而非值。

---

## 9. 配置项说明

### 9.1 settings.py 关键配置

```python
# 数据库 → 改 MySQL 只需替换这里
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 时区（影响鸭鸭睡觉判断、时间光照）
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = True

# DeepSeek AI
DEEPSEEK_API_KEY = 'sk-xxx'               # ← 换成你的 key
DEEPSEEK_MODEL = 'deepseek-chat'           # ← 可换模型
DUCK_SYSTEM_PROMPT = """你是..."""         # ← 改鸭鸭人设

# 静态文件
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

# 用户上传
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 登录
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
```

### 9.2 修改睡眠时间

在 `views.py` 的 `is_duck_sleeping()` 中：

```python
def is_duck_sleeping():
    now = timezone.localtime(timezone.now())
    return now.hour >= 21 or now.hour < 6  # ← 改这两个数字
```

### 9.3 修改喂食参数

涉及多个位置：

- `_sync_duck_state()` 中 `elapsed >= 4.0` — 消化时间（小时）
- `feed_view()` 中 `feed_grams < 180` — 每次消耗量
- `DUCK_SYSTEM_PROMPT` 中可提及时长

---

## 10. 扩展开发指南

### 10.1 添加新场景

**步骤**：

1. **`views.py`**：在 `SCENES` 列表中添加一条
```python
{'key': 'newscene', 'name': '新场景', 'icon': '🏔️',
 'duck_img': 'duck图片3.png', 'duck_mood': '探险鸭'},
```

2. **`yard.html`**：复制一个 `<div class="scene scene-xxx">` 块，修改：
   - `class="scene scene-newscene"`
   - `id="scene-newscene"`
   - `scene-label` 文字
   - CSS 像素画建筑/装饰元素

3. **`style.css`**：添加 `.scene-newscene` 背景样式

### 10.2 换 AI 模型（如通义千问/OpenAI）

只需改 `settings.py` 三个值：

```python
DEEPSEEK_API_KEY = 'your-new-key'
DEEPSEEK_API_URL = 'https://api.openai.com/v1/chat/completions'
DEEPSEEK_MODEL = 'gpt-3.5-turbo'
```

> `chat_view()` 使用标准 `{role, content}` 消息格式，兼容所有 OpenAI 风格 API。

### 10.3 切换到 MySQL

1. 安装驱动：`pip install mysqlclient`（Windows 可能需要 `pip install pymysql`）
2. 修改 `settings.py`：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'duckmocker',
        'USER': 'root',
        'PASSWORD': 'yourpassword',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
3. `python manage.py migrate`

### 10.4 修改天气城市

在 `get_weather()` 中改 URL：

```python
resp = requests.get('https://wttr.in/Shanghai?format=j1', timeout=8)
#                                    ^^^^^^^^ 换城市名
```

支持中文城市名、拼音、英文名。

### 10.5 添加审核流程

当前 `community_view()` 中 `approved=True` 直接通过。改为手动审核：

```python
# models.py: approved 默认改为 False
approved = models.BooleanField(default=False)

# views.py: 上传时不设 approved
photo = Photo.objects.create(user=..., image=..., approved=False)

# Django Admin 或社区管理界面审核通过
```

### 10.6 添加新功能清单

| 想做的事 | 涉及文件 |
|----------|----------|
| 改鸭鸭图片 | `SCENES` 中 `duck_img` + `static/images/` |
| 改鸭鸭心情 | `SCENES` 中 `duck_mood` |
| 改颜色/字体 | `style.css` `:root` 变量 |
| 加新动画 | `style.css` 底部 `@keyframes` |
| 改聊天 FAQ | `FALLBACK_REPLIES` 列表 |
| 加新 API | `views.py` + `urls.py` + 前端 JS |
| 加数据统计 | `models.py` 新模型 + `stats_view()` |

---

## ⚠️ 注意事项

1. **静态文件**：添加新图片放在 `static/images/`，模板中 `{% static 'images/xxx.png' %}` 引用
2. **模板变量命名**：Django 模板不允许 `_` 前缀属性（如 `photo._liked`），用 `photo.user_liked`
3. **CSRF**：JS fetch 需要 `X-CSRFToken` 头，token 通过 `{{ csrf_token }}` 注入到 JS 变量
4. **时区**：所有时间相关功能（睡觉、时间光照）依赖 `TIME_ZONE = 'Asia/Shanghai'`
5. **天气降级**：wttr.in 请求失败时自动用缓存（30min）或默认晴天，不会报错
6. **DeepSeek 降级**：API 失败时用本地 `FALLBACK_REPLIES` 8 条随机回复

---

> 📅 开发时间：2026年6月
> 🏫 北京交通大学 · 软件工程课程设计
> 🦆 为明湖的鸭鸭们而建
