# Lesson structure contract

Use this as a decision guide, not a rigid page count.

## Learner path

1. **Orientation** — state the lesson title, intended audience, estimated time, prerequisites, course positioning, and why the topic matters. Course positioning belongs at the beginning of the lesson, before the main concepts.
2. **Objectives** — use observable verbs such as explain, distinguish, calculate, inspect, compare, or choose. Each objective should be testable in a later activity.
3. **Entry scenario** — begin with a concrete task or question that gives the concepts a reason to exist.
4. **Concepts** — introduce terms in small groups. Keep the unit, precision, assumptions, and scope beside numerical or operational claims.
5. **Worked examples** — show the input, assumptions, reasoning, and conclusion. Mark teaching assumptions as examples; do not present them as product facts.
6. **Guided practice** — ask the learner to apply the same reasoning with enough response space. Include a short hint when the task would otherwise be ambiguous.
7. **Recap and self-test** — revisit the objectives through a compact table, questions, or a scenario. Prefer reasoning questions over terminology recall.
8. **Next step and sources** — connect to the next lesson and list sources with enough detail for a reader to find them. List them as plain bullet items; do not use numeric citation markers like `[1]` in the body or in the list.

## Content checks

- Keep one main idea per paragraph or table row.
- Explain a new acronym at first use. Keep established technical names in English when translating would reduce precision.
- Distinguish a theoretical peak, a benchmark result, and a business outcome. Do not infer one from another without conditions.
- When comparing alternatives, use the same dimensions for each alternative and state what remains unknown.
- For operational topics, connect each task to the observation or decision it enables.
- If the source material is incomplete, write a bounded question or verification step rather than filling the gap with a guess.
- For learners with a weak foundation, keep one idea per sentence, gloss each new term the first time, and replace bookish reference words (前者/后者/该) with the noun itself.
- Keep the body self-contained: state facts directly instead of citing a manual or page the reader cannot open, and move those citations to the Markdown-only reference block.
- Keep emphasis proportional: summarize routine checklist steps crisply in one table instead of padding minor items with dramatic warnings, and avoid AI clichés (fake "many beginners ask…" setups, rhyming summary jingles, bureaucratic words like 门禁/消缺/打回整改, and defensive value slogans at the end of rules or tables).

## Suggested Markdown metadata

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

Optional `heading_font` and `body_font` change only the typefaces (for example `黑体` and `宋体`); sizes and weights stay fixed by the style contract. Metadata is optional, but `title` should be present for exported documents. `title` becomes the running footer, `course` and `chapter` become the running header (`课程名  /  章名`, with `course` defaulting to `算力运维工程师`), and `subtitle`, `audience`, and `duration` share the subtitle line. The builder ignores unknown fields so a project may add version or author metadata.

## Chinese numbering and labels

- Use Arabic numerals for lesson and chapter-prefixed section numbering: `第2讲 认识算力`, `2.1、算力是什么`, `2.2、算力有多少`.
- Number subsections with their full parent path: `2.1.1、数据、算法与算力各做什么`, `2.2.1、先读单位`, `2.2.2、计算精度`. Use the lesson's chapter number instead of `2` when the lesson belongs to another chapter.
- Put instructional labels in Chinese corner brackets: `【例题】`, `【随堂思考】`, `【关键区别】`, and `【课后自测】`.
- Do not use Chinese numeral figure labels such as `图一`, `图二`, or `图三`. Give diagrams descriptive captions and refer to them with phrases such as“上面的服务链示意” or “下方流程图”.
- Number every table with a `表` line directly above it: `表2-1、常见数值格式的占用与用途`. The first number is the lesson, the second counts tables inside that lesson. A table without this line is a validation error.
