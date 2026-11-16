# skills

DSH（DeepSeek Harness）技能包，与仓库里的课程讲义（「前40讲」「后10讲（海光专项）」）配套。

| 技能 | 用途 |
| --- | --- |
| [`haiguang-course-handout`](haiguang-course-handout/SKILL.md) | 把海光专项课程资料做成中文讲义：先对齐再动笔、固定骨架、原图与重排表并存、去 AI 味与聚焦核心实操、修订不覆盖 Word 手改；产出 Markdown 源 + DOCX（可选 PDF） |
| [`course-handout`](course-handout/SKILL.md) | 通用课程讲义技能（前 40 讲）：将大纲与参考资料整理为结构统一、面向零基础学习者的 Markdown / DOCX / PDF 讲义 |

## 安装

```bash
git clone https://github.com/NanamiAkari/Course.git
cp -R Course/skills/haiguang-course-handout ~/.dsh/skills/
cp -R Course/skills/course-handout ~/.dsh/skills/
```

装好后在 DSH 里以技能名 `haiguang-course-handout` 调用。

## 字体（可选）

`haiguang-course-handout/assets/` 里的 Noto CJK 字体未入库（约 55 MB），只有显式指定字体族时才会用到。需要时按 `assets/OFL.txt` 的许可自行放入：

- `NotoSansCJKsc-Regular.otf`
- `NotoSansCJKsc-Bold.otf`
- `NotoSerifCJKsc-Regular.otf`

默认的黑体 / 宋体由系统提供，不放字体也能正常出 DOCX。
