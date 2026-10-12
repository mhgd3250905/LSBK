# 07 音频生产指南（脚本 → 成品播客）

> 来源：EP01 完整生产实战（含三次返工的踩坑记录）。本技能装有 `scripts/` 工具三件套，配合豆包播客语音 API 实现"脚本指哪打哪"的成品合成。凭据由用户提供（APP ID + Access Token），绝不硬编码进任何文件。

## 一、产物链路与单一真相源

```
脚本_第N幕.md（唯一源稿，人工/AI创作）
  → scripts/md_to_timeline.py → 第N幕_时间脚本.txt（生成物，勿手改）
  → scripts/doubao_podcast_pipeline.py → output/第N幕.mp3 + .srt + _时间轴.json
  → scripts/concat_episode.py → output/完整版.mp3 + .srt
```

**铁律：修改台词只改 md，然后重新生成 txt。** 不要手改 txt——EP01 返工教训之一就是 md 和 txt 双份手工维护导致内容漂移风险。txt 的时间戳只是估算参考（合成不依赖它，只依赖顺序+说话人+文本；SRT 时间戳来自 API 毫秒级回调）。

目录约定：`<项目>/podcasts/EP{编号}_{主题}/` 下放选题卡、大纲、各幕 md、各幕 txt、`output/`。

## 二、时间脚本 txt 格式（md_to_timeline 的输出规范）

```
[mm:ss - mm:ss] 说话人
台词正文（可多行）
```
- 头部元信息行（EP名/幕名/时长估算/说话人）与 `====` 分隔线：仅注释用，解析器跳过
- 尾注行（"（第X幕完 · 后接…）"）**严禁进入合成文本**——EP01 踩坑：曾被朗读进音频
- 舞台提示（（笑）（停顿））：解析器自动剥离，可保留在 md/txt 中供人读

## 三、豆包播客 API 要点（scripts/doubao_podcast_pipeline.py 已封装）

- 模式：**action=3**（`nlp_texts` 逐轮指定 speaker+text，服务端逐字合成不改写——"指哪打哪"）；action=0/4 是 AI 自己写稿，不要用于成品合成
- 必设参数：`speaker_info.random_order=false`（否则谁先开口随机）
- 限制：单轮 ≤300 字符（工具按 280 预切，句末标点处断）、单次调用 ≤10000 字符（工具自动分批）
- 音色：两男配对 `zh_male_liufei_v2_saturn_bigtts` + `zh_male_xiaolei_v2_saturn_bigtts`；一男一女 `zh_male_dayixiansheng_v2_saturn_bigtts` + `zh_female_mizaitongxue_v2_saturn_bigtts`；支持 TTS 音色与 ICL 复刻（复刻音色需与开通播客服务同 APPID）。配对音色效果最佳。《笑谈历史》当前采用豆包播客 API 默认推荐配对：大开=大壹先生（Dayi）、小李=咪仔（Mizai），不设第三人音色（原第三人备选潇磊已于 2026-09-21 弃用）。这能让默认男声更接近大开，但不保证模型绝不演绎出其他声部。
- 音色选型（2026-09 实测）：官方全库见 https://www.volcengine.com/docs/6561/1257544 ；**预置 ICL 音色（`ICL_` 开头）填进 voice_type 即可用于播客 API，无需 speaker_additions**（实测温润学者/仗剑侠客/幽默大爷/幽默叔叔均一次成功）；**多情感音色（`_emo_` 系列）与 mix 音色不可用于播客 API**；换音色只需 `--map 角色名=voice_type` 重跑
- 选型方法：让用户圈候选后，用 `scripts/voice_demo.py` 给每个音色合成 15 秒小样（同一句台词，组内一致好对比），人工试听定夺——音色气质靠听不靠猜。脚本内置《笑谈历史》15 个已验证候选与台词，新节目改脚本头部的 CANDIDATES 表与两句台词即可
- **非确定性**：同一文本两次合成，语速停顿有细微差异。返工整幕可接受；追求"只动一句"用句级补丁（见五）
- **戏剧化第三音色（EP05 多版返工实证，2026-09-21）**：action=3 虽为"指哪打哪"，模型遇**引号直接引语、叹号密集的角色台词、激烈喊叫词、家庭/角色关系场景类比（如"亲儿子伺候老爹"——EP05 此句连续两版被渲染成男声，改标点重录无效，换掉类比才根治）**仍会自主切换音色做戏剧演绎。预防：写稿阶段引语一律第三人称转述（见 SKILL.md 铁则 A7）；验收阶段除文本抽查外，对成品跑基频体检（项目内 `audit_voice.py`，先 ffmpeg 转 wav 再跑；脚本头部有结果解读指南——"声部错位"是硬指标，大量"双声部"是谐波误报）定位可疑段
- 协议坑（改协议代码前必读）：官方 PDF 文档的协议表格提取错位严重，**字节实现以 GitHub `bytedance/agentkit-samples` 的 `byted-podcast-gen` skill 源码为准**。正确时序：StartConnection(event=1,无session_id)→等服务端50→StartSession(**event=100**,带session_id+任务payload)→等150→FinishSession(event=102)→收流(360轮次元数据/361音频/362时间戳/363完整音频URL)→152→FinishConnection(event=2,无sid)。连接类事件(1/2)帧内不写session_id
- 凭据：命令行 `--appid/--token` 或环境变量 `VOLC_APP_ID/VOLC_ACCESS_TOKEN`，或 `--creds-file` 指向本地凭据文件（格式：`APP ID\n<id>\nAccess Token\n<token>`）。凭据文件不入 skill、不入 git

## 四、整期合成 SOP

1. 每幕独立合成（分幕=质量与成本的最优单元，API 合成耗时约 2-4 分钟/幕，与节目时长无关）：
   - 幕1：`--no-tail-music`（只留片头音乐）
   - 中间幕：`--no-head-music --no-tail-music`
   - 末幕：`--no-head-music`（只留片尾音乐）
   - 单集独立发布时可默认头尾都有
2. 拼接：`concat_episode.py --dir <output目录> --out <完整版名> <幕1> <幕2> ...`。豆包会在逐轮 MP3 音流中插入 ID3v2 标签；拼接工具先剥离格式有效且后接 MPEG 帧的内嵌标签，再按清理后的音频用 ffprobe 实测各幕时长并偏移 SRT。**不要直接对未经清理的批次做字节拼接**：嵌入标签会被解码器当作坏帧。按各幕实测时长偏移字幕也不可省略；2026-09-21 EP04 实证，直接用时间轴 json 的 max end_time 会令三幕字幕累积偏移 +5.2s。
3. 验收：
   - 用 ffmpeg 解码整轨到临时 WAV，确认无 `Header missing` / `Invalid data`；逐轮标签导致的坏帧不能只靠文件存在或 ffprobe 成功判断
   - 正向抽查：改过的句子在完整版 SRT 中存在
   - 反向抽查：坏内容（旧句/尾注/剧本腔）在 SRT 中不存在
   - 试听点：幕间衔接前后各 12 秒（尾注/音乐切换最容易出问题的地方）
   - 字幕数 = 各幕话轮数之和（SRT 被污染的表征是条数异常偏多——流水线已修为先清空，但旧文件残留时用 rebuild_srt.py 重建）

## 五、修订 SOP（用户问"改句子要重做吗"的标准答案）

| 层级 | 场景 | 操作 | 成本 |
|---|---|---|---|
| 一（默认） | 改动散布多句 | 改 md → 重新生成该幕 txt → 重合成该幕 → 重拼接。其余幕音频不动 | ~3分钟+一次API |
| 二 | 只改一两轮且不想动其余音频 | 重合成目标轮次（单轮调 API）→ 音频层替换该时间段 → rebuild_srt 重建字幕。注意拼接处语气需人耳验收；句长变化会平移后续字幕 | ~1分钟 |
| 三 | 只改错字/文案 | 直接改 SRT 或 shownotes，音频不动 | 秒级 |

层级一为主：API 非确定性意味着小改多处时整幕重做反而听感更连贯。
`rebuild_srt.py`：从时间轴 json 重建某幕 SRT（不重烧 API），修复字幕污染、微调时间轴时用。

## 六、发布（小宇宙）

> 详细版在用户项目 `podcasts/发布SOP与台账.md`（含发布记录表，每期发布后回写）。核心路径：

1. **成品验收**：完整版 srt 正向抽查班底名（`^大开:`/`^小李:` 应>0）+ 反向抽查旧名与剧本腔词（应为0）+ 首尾台词人工读
2. **材料四件套**：mp3 / 标题（选题卡主选）/ shownotes（存档 `shownotes.md`）/ 封面 3000×3000
3. **时间轴**：从完整版 srt 抓关键情节首次出现时间戳做章节；注意首次命中可能是冷开场的预告提词，人工核对语境
4. **shownotes 结构**：钩子两段（当下痛点→打破误解）+ `mm:ss `章节轴（行首时间+空格，平台自动识别为跳转链接）+ 概念工具清单 + 互动题 + 下期挖坑
5. **封面**：复用 `assets/cover_template.py`（示例为 EP02 实际封面，改标题/副题/印章四字/EP 编号即可；3000×3000，宣纸底+标题主导版式：本集标题大字、台名金色角标、朱砂印章；2×2 印章从右列往下读）
6. **后台上传**（Playwright，用户已登录 `podcaster.xiaoyuzhoufm.com`）：创建单集 → 模态内 dropzone 传音频 → 传封面后点"裁切" → 标题 → AI 生成声明 → shownotes → 勾协议 → 创建；URL 跳到 `/episode/{ID}/stats` 即成功
7. **发布后**：状态"转码中+单集审核中"属正常，审核通过自动上线；台账回写

**Playwright 踩坑（血泪）**：
- 音频上传要点**模态弹窗内的"选择文件" dropzone**，不是页面按钮；弹窗开着时背景元素点击会报 overlay 拦截超时，先处理弹窗
- Switch 开关（AI 声明）普通 click 被 trackLabel 拦截超时 → `browser_evaluate` 对元素直接 `element.click()`
- shownotes 是富文本编辑器，fill 无效 → `document.execCommand('insertHTML', false, '<p>…</p>')` 逐段写入
- 封面裁切确认按钮文案是"裁切"

## 七、已知残留限制（诚实清单）

- MP3 字节拼接在极少数播放器可能出现的极短爆音——如遇，用 ffmpeg 正规 concat 重拼
- 幕间为硬切，无淡入淡出（可在 concat 前插入 0.3-0.5s 静音，当前工具未内置）
- 句级补丁（层级二）尚未工具化，需人工执行单轮合成+二进制替换
- API 无情感/停顿细粒度控制（舞台提示会被剥离，语气由音色模型自行演绎）
