# Lesson structure contract

骨架优先于"写得好看"。任何一讲先按骨架摆块，再谈段落怎么写。

## 一、固定骨架（必须）

| 节 | 必须 | 职责 |
| --- | --- | --- |
| `N.1、学习目标` | 是 | 知识目标、实操目标两组；每条目标可判定 |
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
- 写完解析就收尾，**不写「下一讲…」这类跨讲衔接句**。学员手上只有这一讲，衔接句对他没有用，还容易把讲次编号说错。

## 七、不写的话（meta 与防御性话术）

讲义是给学员看的成品，不是给自己看的说明。凡是**关于这份文档自身**的句子，一律不写。四类，逐类给反例和改法：

### 1. 出处不进正文

- 反例：`本节内容出自《H3C UniServer R4930 G7 用户指南》。` `本讲取材于厂商培训材料。`
- 出处放两处：**文末「来源」节**（首选）或**表注**（表题下或末列）。
- **图注与表题里不写来源括注**。不要写「（H3C iFIST 配置指导图3-19）」「（海光培训材料原图）」这类尾巴——图注只描述画面内容与编号对应关系，一行说完。
- 正文里出现"据××""出自××""取材于××"，说明你还没把事实融进讲解。

### 2. 范围不靠否定句划

- 反例：`本讲不讲×` `本节不涉及×` `本讲不做×` `不在本讲范围内` `本讲只做×这一层` `放到下一讲`。
- 要么直接不讲（学员看不出缺了什么），要么写成**正面条件**：
  - ✗ `本讲只做把挂耳装到机箱并锁到方孔条这一层。不开盖换挂耳。`
  - ✓ `挂耳装到机箱、锁到方孔条即可，不需要开盖。`
  - ✗ `本讲不测接地电阻、不测腐蚀性气体，那些放到下一讲的机房部分。`
  - ✓ `接地电阻与腐蚀性气体由机房环节检测。`

### 3. 不写跨讲衔接

- 反例：`下一讲进软件栈：驱动、DTK、DAS 与光合社区…` `本讲的内容为第 46 讲做铺垫`。
- 讲义自成一讲：讲到哪儿就在哪儿收尾。讲次先后、课程地图属于教学大纲与开场口径，不放在正文结尾。
- `validate_handout.py` 会对「下一讲」这类字样告警。

### 4. 不做免责声明

- 反例：`为避免误解` `需要说明的是` `需要强调的是` `严格来说` `限于篇幅` `不再赘述`。
- 这些话的作用是替作者兜底，不是帮学员理解。删掉之后句子通常更清楚；如果删不掉，说明那句话本身没说完。

一句话记法：**把"我不做什么"改成"你照着做什么"；改不动的，整句删掉。**

不算违规的句子：`本讲是海光专项的第一讲`、`学完本讲，你应当能够`、`表N-10、本讲涉及的术语`、`这一部分讲五件事：…`——这些是在讲课程内容，不是在解释文档。

## 八、内容检查

- Keep one main idea per paragraph or table row.
- Explain a new acronym at first use. Keep established technical names in English when translating would reduce precision.
- Distinguish a theoretical peak, a benchmark result, and a business outcome. Do not infer one from another without conditions.
- When comparing alternatives, use the same dimensions for each alternative and state what remains unknown.
- For operational topics, connect each task to the observation or decision it enables.
- If the source material is incomplete, write a bounded question or verification step rather than filling the gap with a guess.
- When the source is a vendor deck or a training video, keep its original figures and add a re-typeset table beside them; the two serve different later uses (reading now, slides and video later). Do not replace one with the other.
- Every number, table, and figure copied from external material carries its provenance in the sources section (preferred) or a table note — never as a parenthetical inside a figure caption or table title.
- Objectives and the recap table use the same wording; a mismatch between them is a defect, not a style choice.

## 九、Suggested Markdown metadata

```yaml
---
title: 第2讲 认识算力
subtitle: 算力类型与资源来源
audience: 算力运维工程师入门
duration: 45 分钟
chapter: 第一章 岗位认知与算力入门
course: 算力运维工程师
---
```

Optional `heading_font` and `body_font` change only the typefaces (for example `黑体` and `宋体`); sizes and weights stay fixed by the style contract. Metadata is optional, but `title` should be present for exported documents. `title` becomes the running footer, `course` and `chapter` become the running header (`课程名  /  章名`, with `course` defaulting to `算力运维工程师`), and `subtitle`, `audience`, `duration` share the subtitle line under the title. Leave all three out when the lesson opens straight into its own introduction. The builder ignores unknown fields so a project may add version or author metadata.

## 十、Chinese numbering and labels

- Use Arabic numerals for lesson and chapter-prefixed section numbering: `第2讲 认识算力`, `2.1、算力是什么`, `2.2、算力有多少`.
- Number subsections with their full parent path: `2.1.1、数据、算法与算力各做什么`, `2.2.1、先读单位`, `2.2.2、计算精度`. Use the lesson's chapter number instead of `2` when the lesson belongs to another chapter.
- Put instructional labels in Chinese corner brackets: `【例题】`, `【随堂思考】`, `【关键区别】`, and `【课后自测】`.
- Do not use Chinese numeral figure labels such as `图一`, `图二`, or `图三`. Give diagrams descriptive captions and refer to them with phrases such as“上面的服务链示意” or “下方流程图”.
- Number every table with a `表` line directly above it: `表2-1、常见数值格式的占用与用途`. The first number is the lesson, the second counts tables inside that lesson. A table without this line is a validation error.
