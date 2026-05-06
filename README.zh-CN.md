# LitMind

> 一个持久的、由 LLM 维护的 wiki，用来让你读过的 AI/ML 论文笔记**不断累积、互相补强**。

**Languages:** [English](README.md) · 中文

一个面向 AI/ML 论文阅读的个人知识库，同时也是一个 Obsidian vault。它的目标
是：让你每次读论文的产出**互相累积**，而不是每次都重新推导上下文。

围绕三个目标设计：

1. **看趋势** — 通过自底向上涌现的 topic 页和定期 reflect，看到行业方向上正在发生什么
2. **记细节** — 每篇论文页面遵循固定 schema，下次找细节知道去哪一栏看
3. **借经验** — 遇到新问题时，搜索过去读过的论文、想法、小 trick 看有没有可借鉴的

整个系统把 LLM（如 Claude Code）当作一个**永不疲倦的 wiki 维护者**：
你负责挑选源材料、提出战略性问题；LLM 处理所有 bookkeeping —— 摘要、跨文件
链接、lint、矛盾检测。

---

## 工作原理

故意分开的三层架构：

```
sources/   你拥有的不可变原始材料（PDF，按 domain 分类）
drafts/    LLM 提出的待审批改动
wiki/      已批准的知识库（markdown + Obsidian wikilinks）
```

`wiki/` 下六种 entity：

| 目录 | Entity | 作用 |
|---|---|---|
| `wiki/papers/` | paper | 一篇论文一个页面，固定 schema |
| `wiki/concepts/` | concept | 有名字的技术（MoE、RoPE、GRPO） |
| `wiki/topics/` | topic | 研究方向，自底向上涌现 |
| `wiki/ideas/` | idea | 你的想法，带生命周期 status |
| `wiki/people/` | person | 研究者 / 团队画像 |
| `wiki/tricks/` | trick | 小的实证经验 / 踩坑记录 |

五个核心操作（在 [CLAUDE.md](CLAUDE.md) 里定义，对话中调用）：

- `/ingest <pdf 或 url>` — 把源材料转成草稿 paper 页 + 提议链接
- `/approve <slug>` — 把草稿落到 wiki/，更新索引和 log
- `/ask <问题>` — 在 wiki 内检索，带 provenance 引用回答
- `/reflect <topic>` — 对某个研究方向做定期综合
- `/lint` — 通过 `tools/lint.py` 跑确定性检查

---

## 当前状态

**早期 / 实验性** —— 2026-05-06 开始搭建。

端到端跑通过（在真实输入上验证）：
- `/ingest` 一篇 PDF → 符合 schema 的草稿 paper 页（用 PyMuPDF 提取文本）
- `/approve` → 把草稿移入 `wiki/`，更新 MEMORY / log
- `/lint` → 确定性检查通过（frontmatter、必备 section、slug 唯一性、裸 slug
  wikilink、domain 文件夹一致性）
- Obsidian graph view 能看到 entity + 待 ingest 的悬空链接

设计好了但还没大规模跑过：
- `/ask` —— 检索 wiki 并带 provenance 引用回答
- `/reflect <topic>` —— 把研究方向定期综合成 `trends/` 页
- Tag 提升流程：lint 已经能在 ≥5 篇 paper 共享某 tag 时给提名，但目前只入库了
  一篇 paper，还没真正提升过 topic 页

还缺的：
- 测试 / CI
- `.claude/commands/` slash 命令（目前操作通过自然语言触发，可用但没有 tab
  补全）
- 第二篇 paper —— 才能开始跑 cross-link / tag-promotion 这些行为

Schema (CLAUDE.md) 在第一次 ingest 后已经主动修订过一次 —— 后续随着 wiki 增长
还会继续演化。Schema 变更全部记录在 `log.md`。

---

## 几个被实战验证有用的设计选择

这些来自 Karpathy gist 评论里的经验和我们自己运行后的体会：

- **Drafts 审批 gate**：LLM 永远不直接写 `wiki/`。每次改动先放到 `drafts/`，
  显式 `/approve` 才合并。避免那种你三周后才发现的 LLM 飘移。
- **Provenance 必填**：每条事实性论断都带 `^[paper-id:section]` 引用，否则就
  必须放在 "My take" 段。对抗 LLM 的有损压缩。
- **自底向上的 topic**：不预设 topic 页。lint 在 ≥5 篇 paper 共享某 tag 时给
  提名，人确认后才生成 topic 页。
- **裸 slug wikilink**：用 `[[alpamayo-r1]]` 而不是 `[[paper/alpamayo-r1]]` —
  Obsidian 会把带路径前缀的当成字面路径，画 graph 时会变成幽灵节点。slug 在
  全 vault 内唯一，lint 强制检查。
- **失败的 idea 不删**：标记 `status: dead` + reason。**反重复记忆** —— 防止
  你半年后又冒出同一个死胡同想法。
- **确定性 lint 优于 LLM lint**：`tools/lint.py` 检查 frontmatter、必备
  section、slug 冲突、悬空 wikilink、tag 提名候选、domain-folder 一致性。
  快、可重复、CI 友好。

---

## 快速上手（fork 来记自己的笔记）

```bash
git clone https://github.com/jc3342/LitMind.git my-research-wiki
cd my-research-wiki
python3 -m pip install -r requirements.txt

# 用 Obsidian 打开整个目录：File -> Open vault
# （建议装的插件：Dataview 用来查询 frontmatter，Graph Analysis 看图谱）

# 把一篇 PDF 丢到 sources/papers/<DOMAIN>/ 下，然后在 Claude Code 会话里说：
#   "ingest sources/papers/AV/foo.pdf"
# Claude 会读 CLAUDE.md，先生成 draft，等你 /approve。
```

仓库里已经放了一篇示例 paper —— `wiki/papers/alpamayo-r1.md` —— 可以看看一个
完整的 entity 长什么样。

---

## 仓库结构

```
LitMind/
├── CLAUDE.md                # 给 LLM 的操作手册（从这里开始读）
├── MEMORY.md                # 所有 entity 的顶层索引
├── log.md                   # /approve 事件的 append-only 审计
├── README.md / README.zh-CN.md
├── LICENSE
├── requirements.txt
├── sources/                 # 原始 PDF，按 domain 分类，gitignored
│   ├── papers/<DOMAIN>/
│   ├── notes/
│   └── web/
├── drafts/                  # 待 /approve 的 LLM 提案
├── wiki/                    # 知识库本体
│   ├── papers/
│   ├── concepts/
│   ├── topics/
│   ├── ideas/
│   ├── people/
│   ├── tricks/
│   └── trends/
├── graph/
│   ├── edges.jsonl          # 语义关系
│   └── citations.jsonl      # 引用关系
└── tools/
    └── lint.py
```

---

## 致谢

直接的智识来源：

- **[Andrej Karpathy 的 LLM-Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)**
  —— 原始想法：把 LLM 当作能把综合成果**累积**起来的 wiki 维护者，而不是每次
  query 都重新推导。三层架构（sources / wiki / schema）来自这里。
- **[OmegaWiki](https://github.com/skyllwt/OmegaWiki)** by 北大 DAIR Lab ——
  同一思想的更丰富实现。我们借鉴了：分类型的 entity 体系、Obsidian wikilink
  格式、`graph/edges.jsonl` 单独存语义关系、failed-idea 作为反重复记忆的模式。
  砍掉了它的 24 个 slash command 和完整研究流水线，保持精简。

来自 gist 评论里的坑、以及我们的应对：

- **a-a-k**：摘要会有损压缩 → Key points 段 + provenance 引用
- **superimpactful**：索引反映 LLM 的分类，而非你的脑模型 → 自底向上的 topic
  涌现
- **ethanj** (llmwiki)：需要 claim 级别的 provenance + 审批 gate → drafts/
  工作流 + 强制 `^[id:loc]`
- **theafh**：lint 不可省 → `tools/lint.py` 确定性检查

---

## License

MIT —— 见 [LICENSE](LICENSE)。
