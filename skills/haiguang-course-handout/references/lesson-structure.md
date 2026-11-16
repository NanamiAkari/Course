# Lesson structure contract

骨架优先于"写得好看"。任何一讲先按骨架摆块，再谈段落怎么写。

## 一、固定骨架（必须）

| 节 | 必须 | 职责 |
| --- | --- | --- |
| `N.1、学习目标` | 是 | 采用 41/42 圆点模板：`学完本讲，你应当能够：` + `了解……`（3–4 条） + `实训完成“……”的闭环`（1–2 条）；达成标志放 `N.6.1` |
| `N.2、<理论节名>` | 是，至少一节 | 全部知识内容；术语表是本节最后一小节 |
| `N.3、具体实训内容` | 是 | 全部动手任务；一个任务一张步骤表 |
| `N.4、需要的硬件设施` | 是 | 工位要备的件与工具 |
| `N.5、配套视频` | 是 | 要拍的片子与观看节奏 |
| `N.6、小结与自测` | 是 | 目标回看、课后自测、参考答案 |
| `N.7、附录` | 否 | 课堂填写单、台账、检查表 |

判定"理论节"的办法很简单：`N.1` 之后、`N.3` 之前的全部 H2 都是理论节。41 讲只有一节（产品与整机认知），42 讲也只有一节（到货验收与上架接线）；内容多时可以拆成两节，但不要拆成"每章一节"。

四条硬规则：

- 理论节里**禁止**出现以"逐步 / 实训 / 实操"开头的小节。动作一律进 `N.3`。这一条由 `validate_handout.py` 检查。
- 实训节里**不再展开原理**：原理在 `N.2` 讲完，`N.3` 只回答"手怎么动、做完看哪几项"。
- 术语表是 `N.2` 的最后一个小节，不放回顾之后、也不放附录之后。
- 回顾表在 `N.6`，逐条同词对应 `N.1` 的目标。

## 二、理论节的内部顺序

一个理论小节按下面的顺序写，写完就收，不拖到实训：

1. **本节导入**：一句话说这一节讲哪几件事。
2. **概念与判定**：术语第一次出现就解释；给"什么算对、什么算错、错了会怎样"。
3. **例题**：输入、判断、结论写全；标注这是课堂假设，不要写成产品事实。
4. **随堂思考**：问题留在正文，答案统一放 `N.6`。

不要在这里写"下面我们开始动手""这些讲完才好操作"这类过渡句——那是把理论写成实训的前奏。

学时、工位时长属于排课信息，默认不写进讲义；用户要求时放在开头定位段里。

## 三、实训节的写法

- 一个任务一个 H3，标题用"对象 + 动作"，例如"挂耳、滑道与抱轨安装"；不要用"逐步：…"当标题。
- 任务开头一句：从哪做到哪、交付什么、验收看什么。
- 一张四列表，列头固定：

  | 步 | 动作与要领 | 常见错误 | 检查点 |
  | --- | --- | --- | --- |

- 表后一条红线：`红线：…`，只写会出事的那几条（带电、装反、超载、泄密）。
- 步骤要能还原现场动作。孔位、扭矩、到位声这类随机件差异，写"以随机附件或讲师现场规范为准"，不编数字。
- "常见错误"从现场真实踩坑来：正文里的红线、对错表、检查点都可以搬进来，不要为了凑列编错误。

## 四、硬件节

按用途分四类，每类一张三列表（`名称 / 型号 / 规格 / 用途`）：

1. 防静电与安全用品
2. 上架与拆装工具
3. 耗材与标识
4. 机柜与供电配套

要求：

- 规格只写讲义里出现过、或干活必须用到且能核实的（T25 星型螺丝刀、1 MΩ 限流电阻的腕带、19 英寸机柜这类）。
- 数量按"一套教学工位"；现场另有配置的写"按现场"，不编数量。
- 厂商规格参数不搬到这里，那是 `N.2` 的内容。

## 五、视频节

- 三列表：`视频名 / 时长 / 内容要点`；一条视频只讲一件事，画面要能看清手部动作与接口特写。
- 已有素材与待拍分开说。没有实拍素材就明写"待拍"，不拿软件课或别家品牌的视频顶替。
- 补一段"观看节奏"：课前几天看哪几条，课上在哪个环节回放。

## 六、小结与自测

- 回看表：`学习目标 / 应能做出的判断`，可选一列`对应实训`（写 `N.3.x`）。
- 自测 3～5 题，问判断不问名词。
- 参考答案与解析放在本节最后，按"随堂思考"与"课后自测"分组。
- 与下一讲的衔接一句话，写在解析之后。

## 七、不写的话与去 AI 味规则

讲义是给学员看的成品，不是给自己看的说明，也不是凑字数的散文。凡是**关于这份文档自身**、**替作者叠甲**以及**AI 腔浓重的废话**，一律删改。四类，逐类给反例和改法：

### 1. 出处不进交付讲义（含正文、图注、图片画面、表注与文末）

- 反例：`本节内容出自《H3C UniServer R4930 G7 用户指南》。` `（源自《H3C UniServer R4930 G7 用户指南》，6W111-20260730）` `（海光培训材料原图）` `### N.6.3、资料来源`。
- 正文、图注、配图内副标题、表注以及文末**全部不保留**出处注释、文档编号、原图出处字样或独立的`资料来源`小节。
- 素材与文档编号溯源统一留在工作目录 `outline.md` 中内部留痕，不印入任何学员可见讲义。

### 2. 范围不靠否定句划

- 反例：`本讲不讲×` `本节不涉及×` `本讲不做×` `不在本讲范围内` `本讲只做×这一层` `放到下一讲`。
- 要么直接不讲（学员看不出缺了什么），要么写成**正面条件**：
  - ✗ `本讲只做把挂耳装到机箱并锁到方孔条这一层。不开盖换挂耳。`
  - ✓ `挂耳装到机箱、锁到方孔条即可，不需要开盖。`
  - ✗ `本讲不测接地电阻、不测腐蚀性气体，那些放到下一讲的机房部分。`
  - ✓ `接地电阻与腐蚀性气体由机房环节检测。`

### 3. 不做免责声明与防御性宣讲

- 反例：`为避免误解` `需要说明的是` `需要强调的是` `严格来说` `限于篇幅` `不再赘述` `彻底消灭幽灵资产，确保精准落表` `守住职业运维准则` `严禁走形式提前签字投产`。
- 这些话的作用是替作者兜底或表态度，不是帮学员干活。表格“后果/用途”列只写具体技术或业务后果（如“单路掉电整机断电”），红线只写触发条件（如“命中任一项暂不签字，处理完再交接”），不写空洞口号。

### 4. 清理 AI 腔高频词、伪问题与顺口溜（重核心、轻琐事）

- **禁词替换**：不出现 `门禁`（改“第一步/首项核查”）、`消缺`（改“补齐/处理”）、`打回整改`（改“退回重做/处理后重核”）、`翻车场景`（改“常见问题”）、`临门一脚`、`拧成一股绳`、`桌面上`、`实物/机器/账面真源`、`零时刻微状态`、`算力积木`；正文也少用 `闭环`（除 `N.1` 固定句式外改用“完成/核对完毕/收齐”）。
- **砍掉伪问题与顺口溜**：删掉“很多新手会问：为什么……”“如果在微信里说张三用前两张……”这类 AI 脑补引入，删掉“先……再……重……交……”这类强行押韵的小结口诀。
- **重硬菜、轻琐事**：常规物理检查（拧螺丝、绕魔术贴、贴标签、盖挡板）**两句话 + 一张紧凑表一笔带过**，不在导语、`N.2`、`N.3`、`N.6` 重复铺陈；把主要篇幅留给架构机制、参数陷阱、隔离边界与实测验证。

一句话记法：**把"我不做什么/口号是什么"改成"你照着做什么、错了出什么现象"；简单常识一表带过，核心硬菜讲透。**

不算违规的句子：`本讲是海光专项的第一讲`、`学完本讲，你应当能够`、`表N-10、本讲涉及的术语`、`这一部分讲五件事：…`——这些是在讲课程内容，不是在解释文档或凑字数。

## 八、内容检查

- Keep one main idea per paragraph or table row.
- Explain a new acronym at first use. Keep established technical names in English when translating would reduce precision.
- Distinguish a theoretical peak, a benchmark result, and a business outcome. Do not infer one from another without conditions.
- When comparing alternatives, use the same dimensions for each alternative and state what remains unknown.
- For operational topics, connect each task to the observation or decision it enables.
- If the source material is incomplete, write a bounded question or verification step rather than filling the gap with a guess.
- When the source is a vendor deck or a training video, keep its original figures and add a re-typeset table beside them; the two serve different later uses (reading now, slides and video later). Do not replace one with the other.
- Every numeric threshold and vendor constraint must remain accurate and aligned with internal traceability in `outline.md`, without printing provenance footnotes (`源自…`, document IDs, or a visible `资料来源` section) in the student handout.
- Objectives and the recap table use the same wording; a mismatch between them is a defect, not a style choice.

## 九、Suggested Markdown metadata

```yaml
---
title: 第46讲 海光软件栈生态与光合开发者社区介绍
course: 算力运维工程师
chapter: 海光专项
heading_font: 黑体
body_font: 宋体
---
```

Optional `heading_font` and `body_font` change only the typefaces (for example `黑体` and `宋体`); sizes and weights stay fixed by the style contract. **Do not include `subtitle`, `audience`, or `duration`** under the title — open straight into the lesson introduction/objectives. `title` becomes the running footer, `course` and `chapter` become the running header (`课程名  /  章名`).

## 十、Chinese numbering and labels

- Use Arabic numerals for lesson and chapter-prefixed section numbering: `第2讲 认识算力`, `2.1、算力是什么`, `2.2、算力有多少`.
- Number subsections with their full parent path: `2.1.1、数据、算法与算力各做什么`, `2.2.1、先读单位`, `2.2.2、计算精度`. Use the lesson's chapter number instead of `2` when the lesson belongs to another chapter.
- Put instructional labels in Chinese corner brackets: `【例题】`, `【随堂思考】`, `【关键区别】`, and `【课后自测】`.
- Do not use Chinese numeral figure labels such as `图一`, `图二`, or `图三`. Give diagrams descriptive captions and refer to them with phrases such as“上面的服务链示意” or “下方流程图”.
- Number every table with a `表` line directly above it: `表2-1、常见数值格式的占用与用途`. The first number is the lesson, the second counts tables inside that lesson. A table without this line is a validation error.
