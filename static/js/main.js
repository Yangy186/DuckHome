/**
 * 明湖鸭舍 - 多场景互动 + 鸭鸭聊天
 */

document.addEventListener('DOMContentLoaded', () => {
    // ── 鸭鸭聊天弹窗 ──
    const overlay = document.getElementById('chatOverlay');
    const messagesEl = document.getElementById('chatMessages');
    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSend');
    const closeBtn = document.getElementById('chatClose');

    function openChat() {
        if (overlay) {
            overlay.classList.add('open');
            setTimeout(() => inputEl && inputEl.focus(), 300);
        }
    }

    function closeChat() {
        if (overlay) overlay.classList.remove('open');
    }

    // 添加消息到聊天区
    function addMessage(text, type) {
        if (!messagesEl) return;
        const div = document.createElement('div');
        div.className = 'chat-msg ' + type + '-msg';
        const avatar = type === 'duck' ? '🦆' : '👤';
        div.innerHTML = `<span class="msg-avatar">${avatar}</span><div class="msg-bubble">${escapeHtml(text)}</div>`;
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return div;
    }

    // 添加打字中提示
    function addTyping() {
        if (!messagesEl) return null;
        const div = document.createElement('div');
        div.className = 'chat-msg duck-msg msg-typing';
        div.innerHTML = '<span class="msg-avatar">🦆</span><div class="msg-bubble">鸭鸭正在想...</div>';
        messagesEl.appendChild(div);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return div;
    }

    function removeTyping(el) {
        if (el) el.remove();
    }

    function escapeHtml(text) {
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }

    // 发送消息
    async function sendMessage() {
        if (!inputEl) return;
        const msg = inputEl.value.trim();
        if (!msg) return;

        // 显示用户消息
        addMessage(msg, 'user');
        inputEl.value = '';
        inputEl.disabled = true;
        sendBtn && (sendBtn.disabled = true);

        // 显示打字中
        const typing = addTyping();

        try {
            const resp = await fetch('/chat/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg }),
            });
            const data = await resp.json();
            removeTyping(typing);
            addMessage(data.reply || '嘎？鸭鸭没听懂～', 'duck');
        } catch (err) {
            removeTyping(typing);
            addMessage('嘎嘎～网络不太好，鸭鸭飞走了...等会再试试吧！', 'duck');
        }

        inputEl.disabled = false;
        sendBtn && (sendBtn.disabled = false);
        inputEl.focus();
    }

    // 事件绑定
    if (sendBtn) sendBtn.addEventListener('click', sendMessage);
    if (inputEl) inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
    if (closeBtn) closeBtn.addEventListener('click', closeChat);
    if (overlay) overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeChat();
    });

    // ESC 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && overlay && overlay.classList.contains('open')) {
            closeChat();
        }
    });

    // ── 鸭鸭点击：打开聊天（所有场景的鸭鸭都生效）──
    function initDuck(duckEl) {
        if (!duckEl) return;

        duckEl.addEventListener('click', (e) => {
            // 如果点的是蛋，不打开聊天
            if (e.target.closest('.egg-item')) return;
            // 睡觉中 → 不要吵醒
            if (duckEl.classList.contains('duck-sleeping')) {
                const msg = document.createElement('div');
                msg.className = 'sleep-poke-toast';
                msg.textContent = '💤 Zzz... 鸭鸭睡着了～别吵醒它哦';
                duckEl.appendChild(msg);
                setTimeout(() => {
                    msg.style.opacity = '0';
                    msg.style.transform = 'translateY(-20px)';
                    setTimeout(() => msg.remove(), 400);
                }, 1800);
                return;
            }
            openChat();
        });

        // 闲时蹦跳
        let idleTimer;
        const idleBounce = () => {
            duckEl.style.transition = 'transform 0.3s ease';
            duckEl.style.transform = 'translateY(-5px)';
            setTimeout(() => { duckEl.style.transform = 'translateY(0)'; }, 300);
            idleTimer = setTimeout(idleBounce, 4000 + Math.random() * 6000);
        };
        idleTimer = setTimeout(idleBounce, 5000);
    }

    // 给所有场景的鸭鸭绑定点击聊天
    document.querySelectorAll('.js-duck').forEach(initDuck);

    // ── 蛋点击特效 ──
    document.querySelectorAll('.egg-item').forEach(egg => {
        egg.addEventListener('click', function(e) {
            const sparkle = document.createElement('span');
            sparkle.textContent = '✨';
            sparkle.style.cssText = `
                position:absolute; font-size:24px;
                animation:sparkleFly 0.6s ease-out forwards; pointer-events:none;
                left:${e.offsetX}px; top:${e.offsetY}px;
            `;
            egg.appendChild(sparkle);
            setTimeout(() => sparkle.remove(), 600);
        });
    });

    // ── 消息自动消失 ──
    document.querySelectorAll('.nes-balloon').forEach(msg => {
        setTimeout(() => {
            msg.style.transition = 'opacity 0.5s, transform 0.5s';
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-20px)';
            setTimeout(() => msg.remove(), 500);
        }, 4000);
    });

    // ── 场景切换淡入 ──
    const activeScene = document.querySelector('.scene-active');
    if (activeScene) {
        activeScene.style.opacity = '0';
        activeScene.style.transition = 'opacity 0.25s ease';
        requestAnimationFrame(() => {
            activeScene.style.opacity = '1';
        });
    }

    // ── 真实时间光照 ──
    function applyTimeOfDay() {
        const wrapper = document.querySelector('.scene-wrapper');
        if (!wrapper) return;
        const hour = new Date().getHours();
        let timeClass;
        if (hour >= 5 && hour < 7)       timeClass = 'time-morning';    // 5-7  清晨
        else if (hour >= 7 && hour < 11) timeClass = 'time-forenoon';   // 7-11 上午
        else if (hour >= 11 && hour < 14) timeClass = 'time-noon';      // 11-14 正午
        else if (hour >= 14 && hour < 17) timeClass = 'time-afternoon'; // 14-17 下午
        else if (hour >= 17 && hour < 19) timeClass = 'time-dusk';      // 17-19 傍晚
        else                             timeClass = 'time-night';      // 19-5  夜晚
        wrapper.classList.add(timeClass);
    }
    applyTimeOfDay();

    // ── 加速挑战：贪吃蛇答题 ──
    const accelerateModal = document.getElementById('accelerateModal');
    const accelerateOpenBtn = document.getElementById('accelerateOpenBtn');
    if (accelerateModal && accelerateOpenBtn) {
        const feedAmountValue = document.getElementById('feedAmountValue');
        const screens = Array.from(accelerateModal.querySelectorAll('[data-accelerate-screen]'));
        const gameCards = Array.from(accelerateModal.querySelectorAll('[data-accelerate-game]'));
        const gameRulesBtn = document.getElementById('gameRulesBtn');
        const snakeStartBtn = document.getElementById('snakeStartBtn');
        const snakeRestartBtn = document.getElementById('snakeRestartBtn');
        const snakeCanvas = document.getElementById('snakeCanvas');
        const snakeRoundText = document.getElementById('snakeRoundText');
        const snakeQuestionText = document.getElementById('snakeQuestionText');
        const snakeScoreText = document.getElementById('snakeScoreText');
        const snakeStatusText = document.getElementById('snakeStatusText');
        const ctx = snakeCanvas && snakeCanvas.getContext('2d');
        const mineStartBtn = document.getElementById('mineStartBtn');
        const mineRestartBtn = document.getElementById('mineRestartBtn');
        const mineGrid = document.getElementById('mineGrid');
        const mineCountText = document.getElementById('mineCountText');
        const mineStatusText = document.getElementById('mineStatusText');
        const mineFlagModeBtn = document.getElementById('mineFlagModeBtn');
        const gomokuStartBtn = document.getElementById('gomokuStartBtn');
        const gomokuRestartBtn = document.getElementById('gomokuRestartBtn');
        const gomokuBoard = document.getElementById('gomokuBoard');
        const gomokuTurnText = document.getElementById('gomokuTurnText');
        const gomokuStatusText = document.getElementById('gomokuStatusText');
        const accelerateResultTitle = document.getElementById('accelerateResultTitle');
        const accelerateResultMessage = document.getElementById('accelerateResultMessage');
        const accelerateResultStayBtn = document.getElementById('accelerateResultStayBtn');
        const accelerateResultHomeBtn = document.getElementById('accelerateResultHomeBtn');
        let selectedAccelerateGame = 'snake';

        const snakeQuestions = [
            { text: '北京交通大学的英文缩写常写作 BJTU。', answer: true },
            { text: '北京交通大学的校训是“知行”。', answer: true },
            { text: '明湖是北京交通大学校园里的湖。', answer: true },
            { text: '北京交通大学前身之一是铁路管理传习所。', answer: true },
            { text: '校园里保持环境整洁是一种文明行为。', answer: true },
            { text: '图书馆里保持安静有助于大家学习。', answer: true },
            { text: '社区中的点赞和评论都属于互动行为。', answer: true },
            { text: '管理员可以维护社区秩序。', answer: true },
            { text: '北京交通大学位于北京市海淀区。', answer: true },
            { text: '高铁、地铁、公交都属于交通出行方式。', answer: true },
            { text: '北交大只研究医学，不涉及交通相关学科。', answer: false },
            { text: '明湖鸭鸭的饲料只能通过删除帖子获得。', answer: false },
            { text: '校园里乱扔垃圾是文明行为。', answer: false },
            { text: '红灯亮起时行人可以随意横穿马路。', answer: false },
            { text: '社区里违规帖子越多，生态越健康。', answer: false },

            { text: '汉字“明”由“日”和“月”组成。', answer: true },
            { text: '“人山人海”常用来形容人非常多。', answer: true },
            { text: '“春风又绿江南岸”中的“绿”可以作动词理解。', answer: true },
            { text: '“问渠那得清如许，为有源头活水来”强调来源和更新的重要性。', answer: true },
            { text: '议论文通常需要观点、论据和论证。', answer: true },
            { text: '“画蛇添足”常用来比喻多此一举。', answer: true },
            { text: '“沉舟侧畔千帆过，病树前头万木春”包含新旧更替的意味。', answer: true },
            { text: '“举头望明月”出自李白的《静夜思》。', answer: true },
            { text: '“鸟语花香”常用来描写美好景色。', answer: true },
            { text: '标点符号可以帮助表达停顿和语气。', answer: true },
            { text: '记叙文通常会交代人物、时间、地点和事件。', answer: true },
            { text: '“因为……所以……”常用于表示因果关系。', answer: true },
            { text: '“书山有路勤为径”强调勤奋学习。', answer: true },
            { text: '“鸭”字的偏旁与鸟类有关。', answer: true },
            { text: '“雪中送炭”表示在别人困难时继续添堵。', answer: false },
            { text: '“亡羊补牢”鼓励发现问题后坚决不改。', answer: false },
            { text: '《静夜思》的作者是杜甫。', answer: false },
            { text: '“井井有条”通常形容非常混乱。', answer: false },
            { text: '句号通常表示一句话还没有结束。', answer: false },
            { text: '“一望无际”通常形容范围很小。', answer: false },
            { text: '写作文时完全不需要围绕中心。', answer: false },
            { text: '“鸭鸭吃饲料吗？”不是疑问句。', answer: false },

            { text: '2 的 10 次方等于 1024。', answer: true },
            { text: '9 × 9 = 81。', answer: true },
            { text: '100 ÷ 4 = 25。', answer: true },
            { text: '偶数都能被 2 整除。', answer: true },
            { text: '三角形内角和是 180 度。', answer: true },
            { text: '长方形面积等于长乘宽。', answer: true },
            { text: '圆的周长公式可以写作 C = 2πr。', answer: true },
            { text: '0 既不是正数，也不是负数。', answer: true },
            { text: '质数 2 是最小的质数。', answer: true },
            { text: '分数 1/2 等于 0.5。', answer: true },
            { text: '如果 a = 3，那么 2a = 6。', answer: true },
            { text: '1 千米等于 1000 米。', answer: true },
            { text: '直角等于 90 度。', answer: true },
            { text: '正方形的四条边长度相等。', answer: true },
            { text: '平均数可以反映一组数据的集中趋势。', answer: true },
            { text: '圆周率 π 是一个无理数。', answer: true },
            { text: '两个负数相乘，结果为正数。', answer: true },
            { text: '一次函数 y = kx + b 的图像是一条直线。', answer: true },
            { text: '如果两个角互为补角，它们的和是 180 度。', answer: true },
            { text: '5 × 6 = 35。', answer: false },
            { text: '7 + 8 = 20。', answer: false },
            { text: '1 米等于 10 厘米。', answer: false },
            { text: '所有奇数都能被 2 整除。', answer: false },
            { text: '三角形有四条边。', answer: false },
            { text: '0.25 大于 0.5。', answer: false },
            { text: '圆有四个角。', answer: false },
            { text: '10 的平方等于 20。', answer: false },
            { text: '负数一定比 0 大。', answer: false },

            { text: 'The word “duck” means 鸭子。', answer: true },
            { text: '“Lake” means 湖。', answer: true },
            { text: '“Library” means 图书馆。', answer: true },
            { text: '“Student” means 学生。', answer: true },
            { text: '“Good morning” can be used in the morning.。', answer: true },
            { text: '“Thank you” is used to express thanks.。', answer: true },
            { text: '“Blue” is a color word.。', answer: true },
            { text: '“Run” can be a verb.。', answer: true },
            { text: '“Apple” is a kind of fruit.。', answer: true },
            { text: '“I am a student.” is an English sentence.。', answer: true },
            { text: '“School” means 学校。', answer: true },
            { text: '“Happy” means 开心的。', answer: true },
            { text: '“Book” means 书。', answer: true },
            { text: '“Duck” means 老虎。', answer: false },
            { text: '“Cat” means 鸭子。', answer: false },
            { text: '“Good night” is usually used in the morning.。', answer: false },
            { text: '“Red” means 绿色。', answer: false },
            { text: '“Teacher” means 学生。', answer: false },
            { text: '“Yes” means 不。', answer: false },
            { text: '“No” means 是。', answer: false },
            { text: '“Three” means 数字 4。', answer: false },
            { text: '“Water” means 火。', answer: false },

            { text: '水在标准大气压下通常 100 摄氏度沸腾。', answer: true },
            { text: '地球围绕太阳公转。', answer: true },
            { text: '植物进行光合作用通常需要光。', answer: true },
            { text: '声音传播需要介质。', answer: true },
            { text: '人体血液循环与心脏有关。', answer: true },
            { text: '氧气是人类呼吸需要的重要气体。', answer: true },
            { text: '磁铁有南极和北极。', answer: true },
            { text: '力可以改变物体的运动状态。', answer: true },
            { text: '太阳从西边升起。', answer: false },
            { text: '月球自己会发出强烈阳光。', answer: false },
            { text: '真空中声音传播最快。', answer: false },
            { text: '植物完全不需要水也能长期生长。', answer: false },
            { text: '铁永远不会生锈。', answer: false },
        ];

        const snakeGame = {
            gridSize: 20,
            cellSize: 20,
            snake: [],
            direction: { x: 1, y: 0 },
            nextDirection: { x: 1, y: 0 },
            fruits: [],
            questions: [],
            round: 0,
            score: 0,
            timerId: null,
            running: false,
            submitting: false,
        };

        const mineGame = {
            size: 9,
            mines: 10,
            cells: [],
            started: false,
            ended: false,
            flags: 0,
            flagMode: false,
            submitting: false,
        };

        const gomokuGame = {
            size: 15,
            board: [],
            ended: false,
            playerTurn: true,
            submitting: false,
            winningCells: [],
            duckTimerId: null,
        };

        function showAccelerateScreen(name) {
            screens.forEach(screen => {
                screen.classList.toggle('active', screen.dataset.accelerateScreen === name);
            });
        }

        function getYardSceneUrl() {
            const scene = accelerateModal.dataset.scene;
            return scene && scene !== 'minghu' ? `/?scene=${scene}` : '/';
        }

        function showAccelerateResult(title, message, options = {}) {
            stopSnakeGame();
            stopMineGame();
            if (!options.keepGomokuBoard) stopGomokuGame();
            if (accelerateResultTitle) accelerateResultTitle.textContent = title;
            if (accelerateResultMessage) accelerateResultMessage.textContent = message;
            showAccelerateScreen('result');
        }

        function updateFeedReward(data) {
            if (feedAmountValue && Number.isFinite(Number(data.feed_grams))) {
                feedAmountValue.textContent = String(data.feed_grams);
            }
        }

        function selectAccelerateGame(gameName) {
            selectedAccelerateGame = gameName;
            gameCards.forEach(card => {
                card.classList.toggle('active', card.dataset.accelerateGame === gameName);
            });
        }

        function openAccelerateModal() {
            accelerateModal.hidden = false;
            accelerateModal.style.display = 'flex';
            accelerateModal.classList.add('open');
            accelerateModal.setAttribute('aria-hidden', 'false');
            showAccelerateScreen('menu');
            stopSnakeGame();
            stopMineGame();
            stopGomokuGame();
        }

        function closeAccelerateModal() {
            accelerateModal.classList.remove('open');
            accelerateModal.setAttribute('aria-hidden', 'true');
            accelerateModal.style.display = 'none';
            accelerateModal.hidden = true;
            stopSnakeGame();
            stopMineGame();
            stopGomokuGame();
        }

        function shuffled(items) {
            return [...items].sort(() => Math.random() - 0.5);
        }

        function setSnakeStatus(text) {
            if (snakeStatusText) snakeStatusText.textContent = text;
        }

        function setMineStatus(text) {
            if (mineStatusText) mineStatusText.textContent = text;
        }

        function setGomokuStatus(text) {
            if (gomokuStatusText) gomokuStatusText.textContent = text;
        }

        function updateSnakeInfo() {
            if (snakeRoundText) snakeRoundText.textContent = `第 ${Math.min(snakeGame.round + 1, 10)} / 10 题`;
            if (snakeScoreText) snakeScoreText.textContent = String(snakeGame.score);
            if (snakeQuestionText) {
                const question = snakeGame.questions[snakeGame.round];
                snakeQuestionText.textContent = question ? question.text : '挑战结束';
            }
        }

        function isOnSnake(pos) {
            return snakeGame.snake.some(part => part.x === pos.x && part.y === pos.y);
        }

        function randomEmptyCell(used = []) {
            let pos;
            do {
                pos = {
                    x: Math.floor(Math.random() * snakeGame.gridSize),
                    y: Math.floor(Math.random() * snakeGame.gridSize),
                };
            } while (
                isOnSnake(pos) ||
                used.some(item => item.x === pos.x && item.y === pos.y)
            );
            return pos;
        }

        function placeFruits() {
            const green = randomEmptyCell();
            const red = randomEmptyCell([green]);
            snakeGame.fruits = [
                { ...green, answer: true, color: '#73c97b' },
                { ...red, answer: false, color: '#ef6f79' },
            ];
        }

        function drawSnakeGame() {
            if (!ctx) return;

            const size = snakeGame.gridSize * snakeGame.cellSize;
            ctx.clearRect(0, 0, size, size);

            ctx.fillStyle = '#fffaf4';
            ctx.fillRect(0, 0, size, size);

            ctx.strokeStyle = 'rgba(126, 106, 92, 0.08)';
            ctx.lineWidth = 1;
            for (let i = 0; i <= snakeGame.gridSize; i += 1) {
                const line = i * snakeGame.cellSize;
                ctx.beginPath();
                ctx.moveTo(line, 0);
                ctx.lineTo(line, size);
                ctx.stroke();
                ctx.beginPath();
                ctx.moveTo(0, line);
                ctx.lineTo(size, line);
                ctx.stroke();
            }

            snakeGame.fruits.forEach(fruit => {
                const x = fruit.x * snakeGame.cellSize + snakeGame.cellSize / 2;
                const y = fruit.y * snakeGame.cellSize + snakeGame.cellSize / 2;
                ctx.fillStyle = fruit.color;
                ctx.beginPath();
                ctx.arc(x, y, snakeGame.cellSize * 0.34, 0, Math.PI * 2);
                ctx.fill();
                ctx.fillStyle = 'rgba(255,255,255,0.82)';
                ctx.beginPath();
                ctx.arc(x - 3, y - 4, 3, 0, Math.PI * 2);
                ctx.fill();
            });

            snakeGame.snake.forEach((part, index) => {
                const x = part.x * snakeGame.cellSize + 2;
                const y = part.y * snakeGame.cellSize + 2;
                ctx.fillStyle = index === 0 ? '#ff9b62' : '#ffc36f';
                ctx.fillRect(x, y, snakeGame.cellSize - 4, snakeGame.cellSize - 4);
            });
        }

        function setSnakeDirection(name) {
            const map = {
                up: { x: 0, y: -1 },
                down: { x: 0, y: 1 },
                left: { x: -1, y: 0 },
                right: { x: 1, y: 0 },
            };
            const next = map[name];
            if (!next) return;
            const current = snakeGame.direction;
            if (current.x + next.x === 0 && current.y + next.y === 0) return;
            snakeGame.nextDirection = next;
        }

        function stopSnakeGame() {
            if (snakeGame.timerId) {
                clearInterval(snakeGame.timerId);
                snakeGame.timerId = null;
            }
            snakeGame.running = false;
        }

        function stopMineGame() {
            mineGame.ended = true;
            mineGame.flagMode = false;
            if (mineFlagModeBtn) {
                mineFlagModeBtn.classList.remove('active');
                mineFlagModeBtn.setAttribute('aria-pressed', 'false');
            }
        }

        function stopGomokuGame() {
            if (gomokuGame.duckTimerId) {
                clearTimeout(gomokuGame.duckTimerId);
                gomokuGame.duckTimerId = null;
            }
            gomokuGame.ended = true;
            gomokuGame.playerTurn = false;
        }

        function advanceQuestion(selectedAnswer) {
            const question = snakeGame.questions[snakeGame.round];
            if (question && selectedAnswer === question.answer) {
                snakeGame.score += 10;
                setSnakeStatus('答对啦，+10 分。继续下一题。');
            } else {
                setSnakeStatus('这题选错啦，下一题稳一点。');
            }

            snakeGame.round += 1;
            updateSnakeInfo();

            if (snakeGame.round >= 10) {
                finishSnakeGame();
                return;
            }

            placeFruits();
            drawSnakeGame();
        }

        function tickSnakeGame() {
            snakeGame.direction = snakeGame.nextDirection;
            const head = snakeGame.snake[0];
            const nextHead = {
                x: head.x + snakeGame.direction.x,
                y: head.y + snakeGame.direction.y,
            };

            if (
                nextHead.x < 0 ||
                nextHead.x >= snakeGame.gridSize ||
                nextHead.y < 0 ||
                nextHead.y >= snakeGame.gridSize ||
                isOnSnake(nextHead)
            ) {
                finishSnakeGame('贪吃蛇撞到了，挑战结束。');
                return;
            }

            snakeGame.snake.unshift(nextHead);
            const eatenFruit = snakeGame.fruits.find(fruit => fruit.x === nextHead.x && fruit.y === nextHead.y);
            if (eatenFruit) {
                advanceQuestion(eatenFruit.answer);
            } else {
                snakeGame.snake.pop();
            }

            drawSnakeGame();
        }

        async function submitSnakeReward() {
            snakeGame.submitting = true;
            setSnakeStatus('挑战成功，正在加速鸭鸭进食...');
            const csrfInput = accelerateModal.querySelector('[name=csrfmiddlewaretoken]');

            try {
                const resp = await fetch(accelerateModal.dataset.accelerateUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfInput ? csrfInput.value : '',
                    },
                    body: JSON.stringify({ game: 'snake_quiz', score: snakeGame.score }),
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) {
                    throw new Error(data.error || '加速失败啦，请稍后再试。');
                }

                setSnakeStatus(data.message || '加速成功！');
                updateFeedReward(data);
                showAccelerateResult('贪吃蛇挑战成功', data.message || '鸭鸭本次进食已加速 1 小时，并获得 60g 饲料。');
            } catch (err) {
                snakeGame.submitting = false;
                setSnakeStatus(err.message || '加速失败啦，请稍后再试。');
            }
        }

        function finishSnakeGame(reason = '') {
            stopSnakeGame();
            updateSnakeInfo();
            if (snakeGame.score > 60) {
                submitSnakeReward();
            } else {
                const prefix = reason ? `${reason} ` : '';
                setSnakeStatus(`${prefix}得分 ${snakeGame.score}，超过 60 分才算成功，可以再试一次。`);
            }
        }

        function startSnakeGame() {
            if (!ctx) return;
            stopSnakeGame();
            stopMineGame();
            snakeGame.snake = [
                { x: 5, y: 10 },
                { x: 4, y: 10 },
                { x: 3, y: 10 },
            ];
            snakeGame.direction = { x: 1, y: 0 };
            snakeGame.nextDirection = { x: 1, y: 0 };
            snakeGame.questions = shuffled(snakeQuestions).slice(0, 10);
            snakeGame.round = 0;
            snakeGame.score = 0;
            snakeGame.submitting = false;
            snakeGame.running = true;
            placeFruits();
            updateSnakeInfo();
            setSnakeStatus('用方向键或 WASD 控制，吃绿色表示“正确”，吃红色表示“错误”。');
            drawSnakeGame();
            snakeGame.timerId = setInterval(tickSnakeGame, 180);
        }

        function createMineCells() {
            mineGame.cells = [];
            for (let row = 0; row < mineGame.size; row += 1) {
                for (let col = 0; col < mineGame.size; col += 1) {
                    mineGame.cells.push({
                        row,
                        col,
                        mine: false,
                        revealed: false,
                        flagged: false,
                        adjacent: 0,
                    });
                }
            }
        }

        function mineIndex(row, col) {
            return row * mineGame.size + col;
        }

        function mineNeighbors(cell) {
            const neighbors = [];
            for (let dr = -1; dr <= 1; dr += 1) {
                for (let dc = -1; dc <= 1; dc += 1) {
                    if (dr === 0 && dc === 0) continue;
                    const row = cell.row + dr;
                    const col = cell.col + dc;
                    if (row >= 0 && row < mineGame.size && col >= 0 && col < mineGame.size) {
                        neighbors.push(mineGame.cells[mineIndex(row, col)]);
                    }
                }
            }
            return neighbors;
        }

        function placeMines(firstCell) {
            const safeIndex = mineIndex(firstCell.row, firstCell.col);
            const candidates = mineGame.cells
                .map((cell, index) => ({ cell, index }))
                .filter(item => item.index !== safeIndex);

            shuffled(candidates).slice(0, mineGame.mines).forEach(item => {
                item.cell.mine = true;
            });

            mineGame.cells.forEach(cell => {
                cell.adjacent = mineNeighbors(cell).filter(neighbor => neighbor.mine).length;
            });
            mineGame.started = true;
        }

        function updateMineCounter() {
            if (mineCountText) mineCountText.textContent = String(Math.max(0, mineGame.mines - mineGame.flags));
        }

        function renderMineGrid() {
            if (!mineGrid) return;
            mineGrid.innerHTML = '';
            mineGame.cells.forEach((cell, index) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'mine-cell';
                btn.dataset.index = String(index);
                btn.setAttribute('aria-label', `第 ${cell.row + 1} 行第 ${cell.col + 1} 列`);

                if (cell.revealed) {
                    btn.classList.add('revealed');
                    if (cell.mine) {
                        btn.textContent = '💣';
                        btn.classList.add('mine-hit');
                    } else if (cell.adjacent > 0) {
                        btn.textContent = String(cell.adjacent);
                        btn.classList.add(`n${cell.adjacent}`);
                    }
                } else if (cell.flagged) {
                    btn.textContent = '🚩';
                    btn.classList.add('flagged');
                }

                btn.addEventListener('click', () => handleMineCell(index, mineGame.flagMode));
                btn.addEventListener('contextmenu', (e) => {
                    e.preventDefault();
                    handleMineCell(index, true);
                });
                mineGrid.appendChild(btn);
            });
            updateMineCounter();
        }

        function toggleMineFlag(cell) {
            if (cell.revealed || mineGame.ended) return;
            cell.flagged = !cell.flagged;
            mineGame.flags += cell.flagged ? 1 : -1;
            setMineStatus(cell.flagged ? '已插旗。' : '已取消插旗。');
            renderMineGrid();
        }

        function revealMineCell(cell) {
            if (cell.revealed || cell.flagged || mineGame.ended) return;
            cell.revealed = true;
            if (cell.adjacent === 0 && !cell.mine) {
                mineNeighbors(cell).forEach(neighbor => revealMineCell(neighbor));
            }
        }

        function revealAllMines() {
            mineGame.cells.forEach(cell => {
                if (cell.mine) cell.revealed = true;
            });
        }

        function checkMineWin() {
            const safeCells = mineGame.size * mineGame.size - mineGame.mines;
            const revealedSafeCells = mineGame.cells.filter(cell => cell.revealed && !cell.mine).length;
            if (revealedSafeCells === safeCells) {
                mineGame.ended = true;
                setMineStatus('扫雷成功，正在加速鸭鸭进食...');
                renderMineGrid();
                submitMineReward();
            }
        }

        function handleMineCell(index, flagAction = false) {
            if (mineGame.ended || mineGame.submitting) return;
            const cell = mineGame.cells[index];
            if (!cell) return;

            if (flagAction) {
                toggleMineFlag(cell);
                return;
            }

            if (cell.flagged) return;
            if (!mineGame.started) placeMines(cell);

            if (cell.mine) {
                mineGame.ended = true;
                revealAllMines();
                setMineStatus('踩到雷啦，挑战失败，可以重新开始。');
                renderMineGrid();
                return;
            }

            revealMineCell(cell);
            setMineStatus(cell.adjacent ? `周围有 ${cell.adjacent} 颗雷。` : '空白区域已展开。');
            renderMineGrid();
            checkMineWin();
        }

        async function submitMineReward() {
            mineGame.submitting = true;
            const csrfInput = accelerateModal.querySelector('[name=csrfmiddlewaretoken]');
            try {
                const resp = await fetch(accelerateModal.dataset.accelerateUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfInput ? csrfInput.value : '',
                    },
                    body: JSON.stringify({ game: 'minesweeper', won: true }),
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) {
                    throw new Error(data.error || '加速失败啦，请稍后再试。');
                }

                setMineStatus(data.message || '加速成功！');
                updateFeedReward(data);
                showAccelerateResult('扫雷挑战成功', data.message || '鸭鸭本次进食已加速 1 小时，并获得 60g 饲料。');
            } catch (err) {
                mineGame.submitting = false;
                setMineStatus(err.message || '加速失败啦，请稍后再试。');
            }
        }

        function startMineGame() {
            stopSnakeGame();
            stopGomokuGame();
            createMineCells();
            mineGame.started = false;
            mineGame.ended = false;
            mineGame.flags = 0;
            mineGame.flagMode = false;
            mineGame.submitting = false;
            if (mineFlagModeBtn) {
                mineFlagModeBtn.classList.remove('active');
                mineFlagModeBtn.setAttribute('aria-pressed', 'false');
            }
            setMineStatus('左键翻开格子，右键插旗。第一下不会踩雷。');
            renderMineGrid();
        }

        function createGomokuBoard() {
            gomokuGame.board = Array.from({ length: gomokuGame.size }, () => Array(gomokuGame.size).fill(0));
        }

        function renderGomokuBoard() {
            if (!gomokuBoard) return;
            const winningSet = new Set(gomokuGame.winningCells.map(cell => `${cell.row},${cell.col}`));
            gomokuBoard.innerHTML = '';
            for (let row = 0; row < gomokuGame.size; row += 1) {
                for (let col = 0; col < gomokuGame.size; col += 1) {
                    const btn = document.createElement('button');
                    btn.type = 'button';
                    btn.className = 'gomoku-cell';
                    btn.dataset.row = String(row);
                    btn.dataset.col = String(col);
                    btn.setAttribute('aria-label', `第 ${row + 1} 行第 ${col + 1} 列`);
                    if (winningSet.has(`${row},${col}`)) btn.classList.add('win');

                    const value = gomokuGame.board[row][col];
                    if (value) {
                        const stone = document.createElement('span');
                        stone.className = `gomoku-stone ${value === 1 ? 'black' : 'white'}`;
                        btn.appendChild(stone);
                        btn.disabled = true;
                    } else {
                        btn.disabled = gomokuGame.ended || !gomokuGame.playerTurn;
                        btn.addEventListener('click', () => handleGomokuPlayerMove(row, col));
                    }
                    gomokuBoard.appendChild(btn);
                }
            }
            if (gomokuTurnText) {
                gomokuTurnText.textContent = gomokuGame.ended ? '结束' : (gomokuGame.playerTurn ? '黑棋' : '白棋');
            }
        }

        function countGomokuLine(row, col, player, dr, dc) {
            let count = 0;
            let r = row + dr;
            let c = col + dc;
            while (
                r >= 0 && r < gomokuGame.size &&
                c >= 0 && c < gomokuGame.size &&
                gomokuGame.board[r][c] === player
            ) {
                count += 1;
                r += dr;
                c += dc;
            }
            return count;
        }

        function getGomokuWinningCells(row, col, player) {
            const directions = [
                [1, 0],
                [0, 1],
                [1, 1],
                [1, -1],
            ];
            for (const [dr, dc] of directions) {
                const cells = [{ row, col }];
                let r = row + dr;
                let c = col + dc;
                while (
                    r >= 0 && r < gomokuGame.size &&
                    c >= 0 && c < gomokuGame.size &&
                    gomokuGame.board[r][c] === player
                ) {
                    cells.push({ row: r, col: c });
                    r += dr;
                    c += dc;
                }
                r = row - dr;
                c = col - dc;
                while (
                    r >= 0 && r < gomokuGame.size &&
                    c >= 0 && c < gomokuGame.size &&
                    gomokuGame.board[r][c] === player
                ) {
                    cells.unshift({ row: r, col: c });
                    r -= dr;
                    c -= dc;
                }
                if (cells.length >= 5) return cells.slice(0, 5);
            }
            return [];
        }

        function isGomokuWin(row, col, player) {
            const directions = [
                [1, 0],
                [0, 1],
                [1, 1],
                [1, -1],
            ];
            return directions.some(([dr, dc]) => (
                1 + countGomokuLine(row, col, player, dr, dc) + countGomokuLine(row, col, player, -dr, -dc) >= 5
            ));
        }

        function isGomokuBoardFull() {
            return gomokuGame.board.every(row => row.every(cell => cell !== 0));
        }

        function getGomokuPattern(row, col, player, dr, dc) {
            let forward = 0;
            let r = row + dr;
            let c = col + dc;
            while (
                r >= 0 && r < gomokuGame.size &&
                c >= 0 && c < gomokuGame.size &&
                gomokuGame.board[r][c] === player
            ) {
                forward += 1;
                r += dr;
                c += dc;
            }
            const forwardOpen = (
                r >= 0 && r < gomokuGame.size &&
                c >= 0 && c < gomokuGame.size &&
                gomokuGame.board[r][c] === 0
            );

            let backward = 0;
            r = row - dr;
            c = col - dc;
            while (
                r >= 0 && r < gomokuGame.size &&
                c >= 0 && c < gomokuGame.size &&
                gomokuGame.board[r][c] === player
            ) {
                backward += 1;
                r -= dr;
                c -= dc;
            }
            const backwardOpen = (
                r >= 0 && r < gomokuGame.size &&
                c >= 0 && c < gomokuGame.size &&
                gomokuGame.board[r][c] === 0
            );

            return {
                length: 1 + forward + backward,
                openEnds: Number(forwardOpen) + Number(backwardOpen),
            };
        }

        function scoreGomokuPattern(length, openEnds) {
            return length * 10 + openEnds * 3;
        }

        function evaluateGomokuMove(row, col, player) {
            const directions = [
                [1, 0],
                [0, 1],
                [1, 1],
                [1, -1],
            ];
            let best = 0;
            let total = 0;
            directions.forEach(([dr, dc]) => {
                const pattern = getGomokuPattern(row, col, player, dr, dc);
                const score = scoreGomokuPattern(pattern.length, pattern.openEnds);
                best = Math.max(best, score);
                total += score;
            });
            return best + total * 0.12;
        }

        function getGomokuEmptyCells() {
            const cells = [];
            for (let row = 0; row < gomokuGame.size; row += 1) {
                for (let col = 0; col < gomokuGame.size; col += 1) {
                    if (gomokuGame.board[row][col] === 0) cells.push({ row, col });
                }
            }
            return cells;
        }

        function hasGomokuNeighbor(row, col) {
            for (let dr = -1; dr <= 1; dr += 1) {
                for (let dc = -1; dc <= 1; dc += 1) {
                    if (dr === 0 && dc === 0) continue;
                    const r = row + dr;
                    const c = col + dc;
                    if (
                        r >= 0 && r < gomokuGame.size &&
                        c >= 0 && c < gomokuGame.size &&
                        gomokuGame.board[r][c] !== 0
                    ) {
                        return true;
                    }
                }
            }
            return false;
        }

        function findGomokuTacticalMove(player) {
            const empties = getGomokuEmptyCells();
            return empties.find(cell => {
                gomokuGame.board[cell.row][cell.col] = player;
                const wins = isGomokuWin(cell.row, cell.col, player);
                gomokuGame.board[cell.row][cell.col] = 0;
                return wins;
            }) || null;
        }

        function findBestGomokuThreatMove(player, minLength) {
            const center = Math.floor(gomokuGame.size / 2);
            const candidates = getGomokuEmptyCells().filter(cell => hasGomokuNeighbor(cell.row, cell.col));
            const pool = candidates.length ? candidates : getGomokuEmptyCells();
            return pool
                .map(cell => {
                    const directions = [
                        [1, 0],
                        [0, 1],
                        [1, 1],
                        [1, -1],
                    ];
                    const bestLength = Math.max(...directions.map(([dr, dc]) => (
                        getGomokuPattern(cell.row, cell.col, player, dr, dc).length
                    )));
                    return {
                        ...cell,
                        bestLength,
                        centerDistance: Math.abs(cell.row - center) + Math.abs(cell.col - center),
                    };
                })
                .filter(cell => cell.bestLength >= minLength)
                .sort((a, b) => (
                    b.bestLength - a.bestLength ||
                    a.centerDistance - b.centerDistance
                ))[0] || null;
        }

        function chooseDuckGomokuMove() {
            const winMove = findGomokuTacticalMove(2);
            if (winMove) return winMove;
            const blockMove = findGomokuTacticalMove(1);
            if (blockMove) return blockMove;
            const blockThreatMove = findBestGomokuThreatMove(1, 4);
            if (blockThreatMove) return blockThreatMove;

            const center = Math.floor(gomokuGame.size / 2);
            if (gomokuGame.board[center][center] === 0) return { row: center, col: center };

            const candidates = getGomokuEmptyCells().filter(cell => hasGomokuNeighbor(cell.row, cell.col));
            const pool = candidates.length ? candidates : getGomokuEmptyCells();
            return pool
                .map(cell => ({
                    ...cell,
                    score:
                        evaluateGomokuMove(cell.row, cell.col, 2) * 1.4 +
                        evaluateGomokuMove(cell.row, cell.col, 1) * 0.8 -
                        (Math.abs(cell.row - center) + Math.abs(cell.col - center)) * 0.05 +
                        Math.random() * 0.2,
                }))
                .sort((a, b) => b.score - a.score)[0];
        }

        async function submitGomokuReward() {
            gomokuGame.submitting = true;
            setGomokuStatus('你赢啦，正在加速鸭鸭进食...');
            const csrfInput = accelerateModal.querySelector('[name=csrfmiddlewaretoken]');
            try {
                const resp = await fetch(accelerateModal.dataset.accelerateUrl, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfInput ? csrfInput.value : '',
                    },
                    body: JSON.stringify({ game: 'gomoku', won: true }),
                });
                const data = await resp.json();
                if (!resp.ok || !data.ok) {
                    throw new Error(data.error || '加速失败啦，请稍后再试。');
                }

                setGomokuStatus(data.message || '加速成功！');
                updateFeedReward(data);
            } catch (err) {
                gomokuGame.submitting = false;
                setGomokuStatus(err.message || '加速失败啦，请稍后再试。');
            }
        }

        function finishGomoku(row, col, player) {
            gomokuGame.ended = true;
            gomokuGame.playerTurn = false;
            gomokuGame.winningCells = [];
            renderGomokuBoard();
            if (player === 1) {
                submitGomokuReward();
            } else {
                setGomokuStatus('鸭鸭连成五颗啦，挑战失败，可以重新开始。');
            }
        }

        function makeDuckGomokuMove() {
            if (gomokuGame.ended) return;
            const move = chooseDuckGomokuMove();
            if (!move) {
                gomokuGame.ended = true;
                setGomokuStatus('棋盘下满啦，平局。可以重新开始。');
                renderGomokuBoard();
                return;
            }
            gomokuGame.board[move.row][move.col] = 2;
            if (isGomokuWin(move.row, move.col, 2)) {
                finishGomoku(move.row, move.col, 2);
                return;
            }
            if (isGomokuBoardFull()) {
                gomokuGame.ended = true;
                setGomokuStatus('棋盘下满啦，平局。可以重新开始。');
                renderGomokuBoard();
                return;
            }
            gomokuGame.playerTurn = true;
            setGomokuStatus('鸭鸭落子了，轮到你下黑棋。');
            renderGomokuBoard();
        }

        function handleGomokuPlayerMove(row, col) {
            if (gomokuGame.ended || !gomokuGame.playerTurn || gomokuGame.board[row][col] !== 0) return;
            gomokuGame.board[row][col] = 1;
            if (isGomokuWin(row, col, 1)) {
                finishGomoku(row, col, 1);
                return;
            }
            if (isGomokuBoardFull()) {
                gomokuGame.ended = true;
                setGomokuStatus('棋盘下满啦，平局。可以重新开始。');
                renderGomokuBoard();
                return;
            }
            gomokuGame.playerTurn = false;
            setGomokuStatus('鸭鸭正在思考...');
            renderGomokuBoard();
            gomokuGame.duckTimerId = setTimeout(() => {
                gomokuGame.duckTimerId = null;
                makeDuckGomokuMove();
            }, 450);
        }

        function startGomokuGame() {
            stopSnakeGame();
            stopMineGame();
            createGomokuBoard();
            gomokuGame.ended = false;
            gomokuGame.playerTurn = true;
            gomokuGame.submitting = false;
            gomokuGame.winningCells = [];
            setGomokuStatus('你执黑先手，点击棋盘落子。');
            renderGomokuBoard();
        }

        accelerateOpenBtn.addEventListener('click', openAccelerateModal);
        accelerateModal.querySelectorAll('[data-accelerate-close]').forEach(el => {
            el.addEventListener('click', closeAccelerateModal);
        });
        accelerateModal.querySelectorAll('[data-accelerate-back]').forEach(el => {
            el.addEventListener('click', () => {
                stopSnakeGame();
                stopMineGame();
                stopGomokuGame();
                showAccelerateScreen('menu');
            });
        });
        gameCards.forEach(card => {
            card.addEventListener('click', () => {
                if (card.disabled) return;
                selectAccelerateGame(card.dataset.accelerateGame || 'snake');
            });
        });
        gameRulesBtn && gameRulesBtn.addEventListener('click', () => {
            const rulesScreen = {
                snake: 'rules',
                minesweeper: 'minesweeper-rules',
                gomoku: 'gomoku-rules',
            }[selectedAccelerateGame] || 'rules';
            showAccelerateScreen(rulesScreen);
        });
        snakeStartBtn && snakeStartBtn.addEventListener('click', () => {
            showAccelerateScreen('snake');
            startSnakeGame();
        });
        snakeRestartBtn && snakeRestartBtn.addEventListener('click', startSnakeGame);
        mineStartBtn && mineStartBtn.addEventListener('click', () => {
            showAccelerateScreen('minesweeper');
            startMineGame();
        });
        mineRestartBtn && mineRestartBtn.addEventListener('click', startMineGame);
        gomokuStartBtn && gomokuStartBtn.addEventListener('click', () => {
            showAccelerateScreen('gomoku');
            startGomokuGame();
        });
        gomokuRestartBtn && gomokuRestartBtn.addEventListener('click', startGomokuGame);
        accelerateResultStayBtn && accelerateResultStayBtn.addEventListener('click', closeAccelerateModal);
        accelerateResultHomeBtn && accelerateResultHomeBtn.addEventListener('click', () => {
            window.location.href = getYardSceneUrl();
        });
        mineFlagModeBtn && mineFlagModeBtn.addEventListener('click', () => {
            mineGame.flagMode = !mineGame.flagMode;
            mineFlagModeBtn.classList.toggle('active', mineGame.flagMode);
            mineFlagModeBtn.setAttribute('aria-pressed', mineGame.flagMode ? 'true' : 'false');
            setMineStatus(mineGame.flagMode ? '插旗模式已开启，点击格子插旗。' : '插旗模式已关闭，点击格子翻开。');
        });
        accelerateModal.querySelectorAll('[data-snake-dir]').forEach(btn => {
            btn.addEventListener('click', () => setSnakeDirection(btn.dataset.snakeDir));
        });

        document.addEventListener('keydown', (e) => {
            if (!accelerateModal.classList.contains('open')) return;
            const keyMap = {
                ArrowUp: 'up',
                w: 'up',
                W: 'up',
                ArrowDown: 'down',
                s: 'down',
                S: 'down',
                ArrowLeft: 'left',
                a: 'left',
                A: 'left',
                ArrowRight: 'right',
                d: 'right',
                D: 'right',
            };
            if (keyMap[e.key]) {
                e.preventDefault();
                setSnakeDirection(keyMap[e.key]);
            }
        });
    }
});
