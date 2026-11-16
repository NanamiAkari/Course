# 本地安装说明：haiguang-course-handout × DeepSeek Harness

本文件记录这份技能的来源、本机适配与本次改动，删除不影响技能运行。

## 来源

- 基座：`course-handout`（2026-11-06 安装，来源包 `course-handout.skill (3).zip`）
- 安装路径：`C:\Users\ZZT1\.dsh\skills\haiguang-course-handout`（DSH 用户级技能根目录）
- 建档日期：2026-11-11，依据第 41 讲三轮改稿沉淀的做法（对齐 → 取材 → 成稿 → 就地修订）

## 与基座的差异

### 文案

- `SKILL.md` 重写：加"三条硬规矩"（先对齐 / 资料穷尽、图表并存 / 不覆盖用户 Word 修改）（2026-11-11 第二轮扩为四条、第三轮再改"资料覆盖"，见下），工作流现为 8 步，新增"讲义结构约定（本课程）"与"修订协议（摘要）"。
- 新增 `references/alignment.md`：五类提问（结构、粒度、理实比例、图表策略、交付）、停止条件、复述留痕。
- 新增 `references/revision-protocol.md`：lock → backup → diff → 就地改；Word 占用与"万不得已重建"的处理。
- `references/style-contract.md`：一级标题 17→20 pt（行距 22.1→26.0），二级 13→18 pt（行距 16.9→23.4，段前 10/段后 6 → 14/8）；删去"二三级同为 13 pt"。
- `references/lesson-structure.md`：学时改为可选；目标分知识与实操两组（知识目标可"了解"，但须有可判定达成标志）；新增"知识部分与实训部分并列"一节；来源节改为可选、外部数值须有出处；回看表须与目标同词。

### 脚本

- `scripts/build_handout.py`：`H1_SIZE/H1_LINE = 20/26.0`、`H2_SIZE/H2_LINE = 18/23.4`、`H3` 不变；把共用的 `HEADING_BEFORE/AFTER` 拆成 `H1_/H2_/H3_BEFORE/AFTER`（10/6、14/8、10/6），DOCX 与 ReportLab 两条路径同步。
- `scripts/validate_handout.py`：缺"来源"由失败改为告警（`warning:`）；新增"图片无题注"告警；图片与链接分开扫描。
- `scripts/test_skill.py`：断言改为 H2 18 / H1 20 / 正文 11.5，并新增"无来源节仍应通过且给出告警"的用例。
- 新增 `scripts/revision.py`：`lock`（占用检测）、`backup`（时间戳副本）、`diff`（段落增删改 + 格式差异 + 表格差异）。

### 未复制

- `LOCAL-PATCHES.diff`（基座对上游 `build_handout.py` 的三处 Windows 补丁 diff）：新版脚本已包含这些补丁且又改了排版，旧 diff 不再适用；补丁内容见下节。

## 继承自基座的 Windows 适配（已含在脚本里）

1. `harness_resource_dirs()`：Windows 下从注册表卸载项与 `%LOCALAPPDATA%`/`%PROGRAMFILES%` 找 LibreOffice Kit。
2. 转换器输出按 UTF-8 解码，避免中文路径抛 `UnicodeDecodeError`。
3. `INERT_TEMPLATE_FONTS` 过滤 python-docx 模板自带的 Courier/Symbol，避免误报缺字。

## 验证记录（2026-11-11）

- `python scripts/test_skill.py` → `haiguang-course-handout tests passed`
- 样例构建：二级标题 18 pt、段前 14 / 段后 8、一级 20 pt。
- 无来源节的样例：`validate_handout.py` 返回 0 并打印告警。
- `revision.py diff` 在真实改稿上给出可读清单；`revision.py lock` 能识别 Word 占用。
- 旧技能 `course-handout` 目录未改动（文件哈希与建档前一致）。

## 2026-11-11 第二轮：骨架固定

起因：42 讲用本技能生成后，理论与实训被切成"每章知识 + 每章末尾的逐步"，没有独立的实训节，也没有硬件与视频节。查下来的根因是骨架只存在于 41 讲那份 DOCX 里，技能既没写成清单，校验器也不检查结构。

- `SKILL.md`：硬规矩由三条改四条，新增"骨架固定"（`N.1 目标 / N.2 理论 / N.3 实训 / N.4 硬件 / N.5 视频 / N.6 回顾 / N.7 附录可选`）；"讲义结构约定"改为骨架表 + 编号约定 + 理论与实训的界线；Quality gate 增加骨架、实训四列表、硬件与视频三节的要求。
- `references/lesson-structure.md`：重写。固定骨架放在最前；原 8 步 learner path 收窄为"理论节内部顺序"；新增实训节、硬件节、视频节、小结节的写法。
- `references/alignment.md`：五类问题改为骨架切分 / 粒度 / 图表 / 交付 / 出处边界，删掉已定的"理论与实践分不分节"；新增"骨架落盘"——先写 `outline.md` 并复述确认，再起草。
- `references/revision-protocol.md`：新增"结构大改：从当前 DOCX 反向抽取 Markdown"五步（只读抽取 → 段落级比对 → 以抽取稿重排 → 新旧再比 → 列差异清单）。
- `scripts/validate_handout.py`：新增 `structure_report()`，MD 与 DOCX 共用。错误项：六块是否齐全、顺序是否正确、目标与实训之间有没有理论节、理论节里有没有"逐步/实训/实操"小节、实训每个任务有没有步骤表、步骤表列头是不是"步 / 动作与要领 / 常见错误 / 检查点"；告警项：H2 未按 `N.M、` 编号、表格题注不连续、理论节末尾不是术语表、硬件或视频一节没有表格。
- `scripts/test_skill.py`：样例改为完整骨架（含四列步骤表）；新增四个负例——缺实训节、实训任务没有步骤表、步骤表列头不对、理论节里放"逐步"小节，都必须失败。
- 实际稿验证：新校验器对 41 讲通过、对新版 42 讲通过、对旧版 42 讲报"缺少实训节 / 硬件节 / 视频节"。

## 2026-11-11 第三轮：43 讲试跑暴露的四个缺口

用子 agent 只带技能跑了一遍第 43 讲（结构一次通过），它报回 10 条"技能没说清"的地方。本轮修其中四条：

- **讲次↔大纲映射**（`SKILL.md` 新增工作流第 1 步"核对讲次"，`alignment.md` 新增"零、先核对讲次"）：先在大纲里定位本讲那一行；发现已交付稿与大纲编号错位时停下问用户，不许自行顺延。`outline.md` 模板头部加"讲次 / 资料覆盖"两行。
  - 这次真的踩到了：交付的"第42讲"是大纲第 43 讲的内容，大纲第 42 讲（软件栈生态）没人做，于是"第43讲"只能取大纲第 44 讲。
- **"资料穷尽"没有边界**（`SKILL.md` 硬规矩 2 改写）：改成"覆盖判断"——每份资料要么读了，要么在 `outline.md` 写明不读的理由，不许默默跳过。
- **单元格里的竖线**（`validate_handout.py` 新增 `table_shape_errors()`，`style-contract.md` 加规则）：某行单元格数与表头不一致时报错，提示"可能写了竖线"。构建器按 `|` 切分，`lspci | grep K0` 会静默错列，md 层不报错、渲染才暴露。
- **ASCII 双引号**（`validate_handout.py` 新增 `quote_warnings()`，`style-contract.md` 新增"中文标点"一节）：正文出现半角双引号时告警（不拦），反引号里的代码段不计。
- `scripts/test_skill.py` 新增两个用例：单元格竖线必须报错、ASCII 引号必须告警但不失败。

未修（待定）：
- 硬件节"三列表"却列出四个字段名，导致 42 讲用三列、43 讲用四列。要统一，得先定口径，再改 43 讲那份稿。
- `outline.md` 模板没有"对齐问答"栏（问题 + 选项 + 自答），无法真实提问时无处留痕。

## 2026-11-11 第四轮：清掉"AI 防御性话术"

用户指出讲义里有"本节内容出自××""本节不讲××""本节不干××"这类句子——那是模型在替自己兜底，对学员没有信息量。

- `references/lesson-structure.md`：新增「七、不写的话」三类反例与改法（出处不进正文 / 范围不靠否定句划 / 不做免责），并给出"把'我不做什么'改成'你照着做什么'"的改写法；原七、八、九顺延为八、九、十。
- `SKILL.md`：Quality gate 增一条；「编号与标注」里补"出处只进图注、表注和来源节，不进正文句子"。
- `references/style-contract.md`：Restraints 增一条"讲义不写关于自己的话"。
- `scripts/validate_handout.py`：新增 `meta_phrase_errors()`，MD 与 DOCX 共用，级别为 **error**。正则四组：`(本节|本讲|本文|本课)内容?(出自|来自|取材)`、`(本节|本讲)(不|只|仅|不再)`、`不在(本节|本讲)|不属于本讲|超出本讲`、`为避免误解|需要说明的是|需要强调的是|严格来说|限于篇幅|不再赘述`。`本讲是…`、`学完本讲…`、`本讲涉及的术语` 不在正则里，不会误伤。
- `scripts/test_skill.py`：新增三个用例——"本讲不做开盖扩容"必须失败、"本节内容出自《用户指南》"必须失败、"本讲是海光专项的第一讲"必须通过。
- 42 讲：就地清掉 7 处（备份 → 逐段改 → 校验 → diff 确认只有这 7 段变化）。其中"扩容 OCP 网卡 1 要开盖、拆支撑架，本讲不做开盖扩容"删句后留下一个逗号，第二轮补成句号。
- 41 讲：全文只有 1 处——表41-14 单元格"铜排承载数百安培大电流，本讲只看不动"。改成"只看不动"即可，但当时文件被 WPS 占用，**未执行**，脚本备在 `tmp\lecture41\cleanup_meta41.py`。41 讲在改完之前会被校验器判为 1 条错误。

## 已知限制

- 本版没有上标语法，`10^9` 按字面显示。
- 表格列宽按内容长度分配，个别短词在窄列仍可能折行。
- `revision.py diff` 按段落文本对齐，同一段文字出现两次时只报告第一处。

## 2026-11-11 第五轮：从 zip 包合并更新（macOS）

来源：`~/Downloads/haiguang-course-handout (2).zip`，解包后与本机安装版逐文件比对后合并。

**这个 zip 不是纯新版**：`references/`、`SKILL.md`、`validate_handout.py`、`test_skill.py`、`agents/openai.yaml` 是第二轮～第四轮的最新版（15:01），但包里的 `scripts/build_handout.py`（10:31）和 `references/style-contract.md` 丢掉第四轮前做的三处本机补丁与两条语法说明。因此：

- 取用 zip 的新文件：`SKILL.md`、`INSTALL-NOTES.md`、`agents/openai.yaml`、`references/alignment.md`、`references/lesson-structure.md`、`references/revision-protocol.md`、`references/style-contract.md`、`scripts/validate_handout.py`、`scripts/test_skill.py`。
- **保留本机 `scripts/build_handout.py`**（1046 行，含下面三处补丁），不用 zip 里那份未打补丁的 1012 行版本。
- `references/style-contract.md` 把 zip 删掉的两条语法说明补回（图片 `{width=55%}`、`<!-- md-only -->`），否则文档与代码不一致。

`scripts/build_handout.py` 三处补丁（向后兼容，2026-11-11 做第 42 讲时补，本轮保留）：

1. **`<!-- md-only --> … <!-- /md-only -->` 剥离**：`strip_md_only()` 在解析前整段丢弃，避免来源清单带着标记印进 DOCX。
2. **图片宽度提示** `![alt](path){width=55%}`：`Block.width_pct`，DOCX 与 ReportLab 两条路径都按版心比例插图。
3. **表题与表格绑页**：表题后不插空段，`keepNext` 直接作用到表格，避免"表题在页底、表格在下一页"。

安装位置：`~/.dsh/skills/haiguang-course-handout`（Python 为系统 `python3`，依赖 `python-docx`、`Pillow`、`PyMuPDF`）。更新前的完整副本：`~/.dsh/backups/skills/haiguang-course-handout-20261111-165848`。

## 2026-11-12：图注不挂来源括注

第 45 讲定稿时定的规矩：图注和表题只描述画面内容，不再带「（H3C iFIST 配置指导图3-19）」这类来源括注。出处统一进文末「来源」节，没有来源节就进表注。

改动：

1. `SKILL.md`：取材规则里的「图片题注写明来源」改成「图注只写画面内容」；「来源节」那条重写为「出处只进来源节或表注，不进正文、不进图注与表题」；Quality gate 里「每张外来源图有出处题注」改成「外来源图在来源节有交代，图注不挂来源括注」。
2. `references/style-contract.md`：图注小节加一条中文规则；Restraints 里「不声明出处（放图注、表注、来源节）」改成「放来源节或表注，图注不写」。
3. `references/lesson-structure.md`：§1「出处不进正文」从三处改为两处（来源节、表注），并明写图注不写括注；英文条目同步。
4. `scripts/validate_handout.py`：新增 `SOURCE_PAREN` + `caption_source_warnings()`，对 Markdown 的图注/表题、DOCX 的 Caption 段落扫「（…图x-x）」「（…手册/指南/配置指导/原图…）」，命中给 warning（不阻断）。`python scripts/test_skill.py` 仍通过。

## 2026-11-12（补）：不写「下一讲…」

第 45 讲定稿时追加的规矩：正文结尾不写跨讲衔接句（「下一讲进软件栈…」「为第 46 讲做铺垫」）。讲义自成一讲，讲次顺序属于大纲与开场口径。

改动：

1. `references/lesson-structure.md`：§六删掉「与下一讲的衔接一句话」这条要求，改成「写完解析就收尾，不写下一讲」；§七「不写的话」由三类扩为四类，新增「3. 不写跨讲衔接」，原免责声明顺延为第 4 类。
2. `SKILL.md`：骨架表 `N.6` 行补一句；「编号与标注」加一条禁止跨讲衔接，并说明校验器会告警。
3. `scripts/validate_handout.py`：新增 `NEXT_LESSON` + `next_lesson_warnings()`，Markdown 扫全文、DOCX 扫正文段落，命中「下一讲 / 下一节课 / 下一课：」给 warning（不阻断）。`test_skill.py` 仍通过。
