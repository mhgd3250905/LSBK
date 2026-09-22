# 《笑谈历史》小宇宙发布 SOP 与台账

> 每期发布照此执行。首次建立：2026-09-19（EP02 实战验证）。配套：`节目档案.md`（电台/班底/凭据）、skill `references/07-audio-production.md`（合成与修订）。

## 一、最优路径（七步，全流程约 20 分钟）

### 前置：发布材料四件套
| 材料 | 来源 | 存放 |
|---|---|---|
| 成品音频 完整版.mp3 | concat_episode.py 拼接 | `EP{N}_*/output/` |
| 标题 | 选题卡"标题候选"主选 | 选题卡.md |
| Shownotes | 按下方模板新写 | `EP{N}_*/shownotes.md`（存档） |
| 封面 3000×3000 | `EP02_赵敏恋爱小巧思/make_cover.py` 复用改字 | `EP{N}_*/EP{N}_封面.png` |

### 第 1 步：成品验收（发布前最后一道，全过才发）
```bash
cd podcasts/EP{N}_*/output
grep -c "^大开:" 完整版.srt; grep -c "^小李:" 完整版.srt     # 正向：应>0
for w in 周老师 阿灿 茶余饭后 伏笔 彩蛋 第.幕; do grep -c "$w" 完整版.srt; done  # 反向：应全为0
head -8 完整版.srt; tail -4 完整版.srt                        # 首尾台词人工读一遍
```

### 第 2 步：封面（make_cover.py 改字复用）
- 版式已定稿（EP02 用户确认）：**本集标题大字主导，台名退居顶部金色角标"笑谈历史·EP{N}"，右下朱砂印章点睛，左下"主播：大开 × 小李"**
- 印章字序：2×2 印章从**右列往下读**（右列上字→右列下字→左列上字→左列下字），第一版曾读成"要偏强勉"返工
- 改：主标题两行、副题、印章四字、EP 编号，跑 `python make_cover.py`

### 第 3 步：时间轴（shownotes 章节）
从完整版 srt 抓关键情节首次出现时间（关键词按本期内容换）：
```bash
python -c "
import re
srt = open('完整版.srt', encoding='utf-8').read()
blocks = re.findall(r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> \d{2}:\d{2}:\d{2},\d{3}\n(.+?)\n\n', srt, re.S)
for k in ['绿柳山庄','涮羊肉','灵蛇岛','金毛狮王','画眉']:
    for num, ts, text in blocks:
        if k in text: print(ts.split(',')[0][:8], k, text[:40]); break
"
```
⚠️ 关键词的**首次出现≠章节起点**（如"偏要勉强"在冷开场就出现），要人工核对语境再定章节时间。

### 第 4 步：Shownotes 模板（存档为 shownotes.md）
```
钩子两段（第一段：当下痛点；第二段：打破误解+本期预告，取自选题卡冷开场/核心反差）
【时间轴】mm:ss 章节——一句话悬念（×5~6）
【带走三把尺子】概念工具各一句（取自选题卡"可交付的概念工具"）
【互动】结尾设计的互动题原句
【下期挖坑】结尾预告原句
```
平台会把行首 `mm:ss `（后跟空格）自动识别为可跳转章节链接。

### 第 5 步：后台上传（bsk = browser-skill，用户 Edge 登录态；2026-09-21 EP04 实证更新）
1. 启动：`bsk daemon start --foreground`（持久后台任务）→ `bsk session start --browser <id>` → 导航 `podcaster.xiaoyuzhoufm.com`（用户浏览器登录态直接有效；Playwright MCP 独立 profile 的登录态会过期，已弃用）
2. 内容管理 → 创建单集
3. **音频**：点"点击上传播客" → 弹"上传播客"模态 → ⚠️ 上传控件已改系统级文件选择器，bsk 无法自动注入，**`bsk request-help` 请用户手动点「选择文件」选 mp3**（先 Python ctypes 置前 Agent Window，见坑⑨）
4. **封面**：同上手动选 PNG → 弹"单集封面裁切" → bsk click「**裁切**」按钮确认
5. **标题**：`bsk fill` 标题框
6. **AI 声明**：`bsk evaluate` 找文字"本音频为 AI 生成"最近的 input 执行 `.click()`（普通 click ref 易错位，见坑⑩）
7. **Shownotes**：`bsk evaluate` base64 传 HTML + `document.execCommand('insertHTML', false, html)`，写入后 innerText 长度验证
8. 勾"阅读并同意" → 点"创建"
9. **成功标志**：列表出现新单集、状态"转码中 + 单集审核中"；单集 ID 从 `a[href*=episode]` 的 stats 链接抓取

### 第 6 步：发布后确认
内容管理列表应显示该集，状态"**转码中 + 单集审核中**"→ 审核通过自动上线（几分钟到几小时），无需再操作。此时前台搜索还看不到，属正常。

### 第 7 步：台账回写
- 本文件"三、发布记录"加一行
- `节目档案.md` 发布记录更新；若结尾挖了新坑，同步进"已挖的坑"

## 二、踩坑档案（实战血泪，按流程顺序）

| # | 症状 | 原因 | 解法 |
|---|---|---|---|
| ① | 点了上传按钮后 `file_upload` 报 "no modal state" | 点的是页面上传按钮，真正的文件选择器在**模态弹窗内的 dropzone** | 先点按钮 → 快照找到弹窗内"选择文件"区域再点 → 才出现 file chooser |
| ② | 点击页面元素报 "Modal-overlay intercepts pointer events" 超时 | 转码/裁切等模态弹窗开着，遮罩挡住背景 | 别盲目重试，先截图/快照确认弹窗，处理弹窗（如点"裁切"）后再继续 |
| ③ | 封面裁切弹窗找不到确认按钮 | 按钮文案是"裁切"，不是"确定/确认/使用" | 找文本"裁切"；3000×3000 图无需调整直接点 |
| ④ | AI 生成声明开关普通 click 超时 | Switch 的 trackLabel span 拦截了 pointer events | 用 `browser_evaluate` 对开关元素执行 `element.click()`，返回 checked=true 即成功 |
| ⑤ | shownotes 编辑器 fill / innerText 无效或不刷新 | 是富文本编辑器（Tiptap 类 contenteditable），不走受控 value | `browser_evaluate` 聚焦后 `document.execCommand('insertHTML', false, html)`，内容按 `<p>段</p>` 拼；写入后 innerText 长度验证 |
| ⑥ | 创建后前台搜不到节目 | 平台要转码+人工审核 | 后台列表看状态即可，审核通过自动上线；shownotes 事后可改，音频换源需重新审核 |
| ⑦ | 印章字读错序 | 2×2 印章传统读法是先右列后左列、每列自上而下 | 排字函数按"右列上下→左列上下"定位 |
| ⑧ | 时间轴章节时间错位 | grep 首次命中可能是冷开场提了一嘴的词 | 命中行要读语境，确认是情节本体而非预告/呼应 |
| ⑨ | 用户看不到 bsk 弹窗，request-help 反复超时 | bsk 的 Agent Window 是隐藏窗口（win32 TRAYAGENTWINDOW，IsWindowVisible=false） | Python ctypes 找 TRAYAGENTWINDOW 或 Chrome_WidgetWin 的 Edge 窗口 `ShowWindow(9)+SetForegroundWindow` 置前；置前后旧 session 失效需重建；详见记忆 lsbk-xiaoyuzhou-publish-bsk |
| ⑩ | 小宇宙上传控件改版（2026-09-21 起），自动化注入文件全部失败 | 改用系统级文件选择器（showOpenFilePicker 类），bsk upload click/drop 模式均被拦 | 音频/封面 `bsk request-help` 请用户手动选文件（各一次）；标题/AI声明/shownotes/协议/创建仍全自动；AI 声明开关用 evaluate 定位文字后 `.click()`，普通 click 的 ref 易错位到编辑器工具栏 |

## 三、发布记录

| 期 | 标题 | 时长 | 上传日期 | 单集ID | 状态 | 备注 |
|---|---|---|---|---|---|---|
| EP01 王阳明 | 笑谈历史EP01_王阳明 | 33:12 | 未上传 | — | 待传 | 音频已验收（大开54+小李44，刘飞+咪仔） |
| EP02 赵敏恋爱小巧思 | 赵敏的恋爱心理学：为什么说她是金庸宇宙最高段位的沟通大师？ | 29:04 | 2026-09-19 | 6aad767b0916f6f8b44587ee | 已上线 | 首期发布，全流程验证；封面v2标题主导版式定稿 |
| EP03 令狐冲任盈盈职场合谋 | 令狐冲与任盈盈：一场职场退休大佬与大厂顶级职业经理人的精准合谋 | 24:24 | 2026-09-20 | 6aaf4c3fac389df827348875 | 已上线 | 全程按本SOP执行约15分钟；时长低于30分钟目标（见下方注意）；"茶余饭后"在成稿中为成语用法（"茶余饭后的反面教材"），非台名残留，合法放行 |
| EP04 大明皇帝反常识 | 大明皇帝反常识：不上朝的三十年，万历到底在算计什么？ | 34:34 | 2026-09-21 | 6ab1c27693d5eb3bdc78f639 | 转码+审核中 | 双人纯度修复版：体检发现第三四幕 5 处男声串音，改写+重录后 3 处位置锚定串音用单句独立合成+句级补丁（patch_ep04.py）根治，零声部错位；修复 concat 字幕偏移缺陷（json vs mp3 实测差 +5.2s）；本次改用 bsk（browser-skill）发布：小宇宙上传控件已改新版系统文件选择器，音频/封面需用户手动选择，其余全自动 |
| EP05 心学狠人徐阶 | 徐阶潜伏二十年：王阳明心学到底是怎么教人当“狠人”的？ | 38:36 | 未上传 | — | 待传 | 第三音色根治版（2026-09-21）：二三四幕全部直接引语转述化+重录，15:26 处男声串音台词改写修复；基频体检正文 112 段零声部错位（大开62+小李54=116条，26.6MB），3000×3000封面已就绪 |

> 时长注意：EP03 仅 24 分钟，低于 30-40 分钟目标区间。后续选题大纲阶段按五段骨架的时长刻度控制，四幕各 2700-3900 字。

## 四、电台信息
- 电台：笑谈历史，ID `6aac78ec79171af37f7cdc7f`，后台 `podcaster.xiaoyuzhoufm.com/podcast/6aac78ec79171af37f7cdc7f`
- 节目级封面/简介：在"节目设置"维护（创建电台时已填简介，节目封面未上传——待定稿）
