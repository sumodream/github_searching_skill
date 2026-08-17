# GitHub 项目搜索与推荐

## 元数据
- **名称**: github-project-search
- **版本**: 4.4.0
- **作者**: AI Assistant
- **描述**: 多源项目搜索与推荐技能。整合本地库、GitHub API、HelloGitHub 社区精选、阮一峰周刊、Awesome 列表、智能体技能/工具搜索十二大数据源（含 MCP Registry/Smithery/Glama/Hermes/虾评/SkillHub 跨平台搜索），支持关键词搜索、项目详情分析（含近30天/90天精确star增量统计）、仓库文档生成、信任评估、领域发现、学习导向搜索、智能体技能/工具分类搜索，内置 6 维度安全评价体系（代码透明度/来源可信度/维护活跃度/社区采纳度/权限透明度/安全记录）、源码级安全扫描（eval/exec/混淆base64/TLS降级/环境变量窃取等9类检测）、红旗项检测与多源交叉验证（识别控评行为）、区域适用性检测（国内/国际/通用，支持按网络环境过滤）。零配置即可使用（无Token走未认证模式60次/小时），解决 AI 幻觉推荐差项目的问题。
- **标签**: github, 开源项目, 项目推荐, 技术选型, hellogithub, ruanyf, awesome, agent, skill, mcp, safety, security, hermes, xiaping, region, star-history

## 数据来源与许可证

本技能整合了以下数据源，各数据源版权归原作者所有：

| 数据源 | 来源说明 | 许可证 |
|--------|---------|--------|
| 本地精选项目库 | 人工筛选的 2377 个项目元数据（名称、描述、标签等），存于 `data/projects_db.json` | 本技能原创整理 |
| GitHub Search API | GitHub 公共搜索 API，实时查询公开仓库信息 | [GitHub API Terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#api-terms) |
| GitHub Trending | GitHub Trending 页面公开数据 | 同上 |
| HelloGitHub 社区精选 | 来自 [521xueweihan/HelloGitHub](https://github.com/521xueweihan/HelloGitHub) 月刊，解析 content/ 目录下的 Markdown 文件 | [CC BY-NC-ND 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/)（署名-非商业性使用-禁止演绎） |
| 阮一峰周刊 | 来自 [ruanyf/weekly](https://github.com/ruanyf/weekly) 科技爱好者周刊，解析 docs/ 目录下的 Markdown 文件，提取「工具」和「AI 相关」板块的项目推荐 | 内容为阮一峰博客公开文章，周刊仓库无独立许可证声明 |
| Awesome 列表 | GitHub 上各领域 awesome-list 仓库的索引信息，通过 GitHub Search API 检索 | 各仓库独立许可证，详见对应仓库 |
| Awesome Agent Skills | 来自 [philipbankier/awesome-agent-skills](https://github.com/philipbankier/awesome-agent-skills) 跨平台技能目录，解析 README 中按平台分类的技能/工具/MCP/Cursor Rules 等条目 | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) |
| Awesome AI Agents | 来自 [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents) AI agent 项目列表，解析 README 中的开源 agent 框架/平台 | 无独立许可证声明 |
| GitHub Topics | 按 `coze-skill`/`ai-plugins`/`mcp-server`/`agent-framework` 等 topic 搜索 GitHub 仓库 | [GitHub API Terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#api-terms) |
| MCP Registry | [官方 MCP 注册中心](https://registry.modelcontextprotocol.io)，由 Anthropic + GitHub + PulseMCP 维护，4500+ 服务器，REST API 无需认证 | [MIT](https://github.com/modelcontextprotocol/registry) |
| Smithery | [Smithery MCP 平台](https://smithery.ai)，7300+ 服务器，支持语义搜索+verified过滤，需免费 token | [MIT](https://smithery.ai) |
| Glama MCP | [Glama MCP 目录](https://glama.ai/mcp/servers)，67960+ 服务器，自带 A/B/C 质量评级，网页解析 | [Glama](https://glama.ai) |
| Hermes Skills Hub | [Hermes Skills Bridge](https://github.com/freshtemp-labs/hermes-skills-bridge)，agentskills.io 标准 100+ 验证技能，含 popularity_score/category/tags | [MIT](https://github.com/freshtemp-labs/hermes-skills-bridge) |
| 虾评技能平台 | [虾评 xiaping.coze.com](https://xiaping.coze.com)，Agent 技能评测平台，含用户评分/下载量/多维评测，需 API Key | [虾评](https://xiaping.coze.com) |
| 腾讯 SkillHub | [SkillHub skillhub.cn](https://skillhub.cn)，基于 OpenClaw/ClawHub 生态，13000+ 技能，含 AI 评分和安全审核，网页解析 | [SkillHub](https://skillhub.cn) |

**注意**：HelloGitHub 数据受 CC BY-NC-ND 4.0 协议保护，使用时需保留署名，且不得用于商业用途或二次演绎。

## 环境变量（可选）
通过技能凭证配置 GitHub Token，代码通过 `os.getenv("COZE_GITHUB_TOKEN_{SKILL_ID}")` 读取：
- 凭证名: `github_token`
- 获取: GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
- 权限: 无需特殊权限，公共仓库读取即可（不勾选任何 scope）

**v4.3.0 起零配置即可使用**：
- **有 Token**：认证模式，5000次/小时，所有功能完整可用
- **无 Token**：未认证模式，60次/小时，本地库+GitHub API+HelloGitHub+阮一峰+Awesome 均可使用
- 未认证模式触发限速时，返回明确提示并建议配置 Token
- Token 无效/过期时返回 `invalid_token` 错误，不影响本地库功能

**推荐使用场景**：个人使用建议配置自己的 Token（免费创建，无scope要求）；技能分发时可不配置，安装者零配置即可体验基础功能。

**v4.0.0 新增可选环境变量**：
- `COZE_SMITHERY_TOKEN`：Smithery 平台免费 token，用于搜索 Smithery 的 7300+ MCP 服务器。未配置时自动跳过 Smithery 源，不影响其他功能。
  - 获取：smithery.ai 注册 → Account Settings → API Keys

**v4.1.0 新增可选环境变量**：
- `XIAPING_KEY`（或 `COZE_XIAPING_TOKEN`）：虾评平台 API Key，用于搜索虾评的 Agent 技能库。未配置时自动跳过虾评源，不影响其他功能。
  - 获取：xiaping.coze.com 注册 → 个人中心 → API Keys

### 能力矩阵（v4.3.0）

| 功能 | 无 Token（60次/时） | 有 Token（5000次/时） |
|------|---------|---------|
| 本地库搜索（2377项目） | ✅ 完整可用 | ✅ 完整可用 |
| 本地库领域发现/统计 | ✅ 完整可用 | ✅ 完整可用 |
| GitHub API 实时搜索 | ✅ 可用 | ✅ 完整可用 |
| Trending / HelloGitHub / 阮一峰 / Awesome | ✅ 可用 | ✅ 完整可用 |
| 项目详情/分析/文档生成 | ✅ 可用 | ✅ 完整可用 |
| 近30/90天star精确增量 | ⚠️ 跳过（需认证） | ✅ 精确统计 |
| 信任评估/安全评估/源码扫描 | ✅ 可用 | ✅ 完整可用 |
| 智能体技能/工具搜索 | ✅ 可用 | ✅ 完整可用 |
| 跨平台搜索（MCP Registry/Smithery/Glama/Hermes） | ✅ Registry+Glama+Hermes | ✅ 完整可用 |
| 多源交叉验证/广义搜索/区域过滤 | ✅ 完整可用 | ✅ 完整可用 |

**无 Token 说明**：v4.3.0 起所有功能零配置可用。未认证模式共享 60次/小时限额，轻度使用足够。配置免费 Token（无需任何权限scope）可提升至 5000次/小时，且解锁精确 star 增量统计。搜索/分析结果中 `token_mode` 字段标注当前模式（`authenticated` / `unauthenticated`）。

## 触发条件
用户表达以下意图时触发：
- "找一下...项目" / "推荐...工具" / "有什么好的..."
- "分析一下 [项目名/URL]"
- "这个项目是什么" / "帮我理解这个仓库" / "快速了解这个项目"
- "项目结构是怎样的" / "用了什么技术栈" / "怎么上手"
- "[项目A] 和 [项目B] 哪个好"
- "这个项目最近火吗" / "趋势如何"
- "支持 docker 吗" / "怎么部署"
- "有没有 agent 技能" / "找一下 MCP server" / "智能体工具" / "AI agent 框架"
- "安全的 MCP" / "靠谱的技能" / "有没有安全的 agent 工具"
- "不想接入 agent，能直接用的工具" / "不需要 agent 平台的"
- "HelloGitHub 有没有推荐..." / "HG 精选..."
- "阮一峰推荐..." / "周刊里的..." / "科技爱好者周刊..."
- "有哪些 awesome 列表" / "awesome + 领域关键词"
- "帮我发现...领域的项目" / "按领域/类别找项目"
- "有没有类似的" / "...的替代品" / "其他选择"
- "想找个项目练手" / "想通过重写学习" / "想参与开源贡献" / "找个简单的项目练手"
- "本地库有哪些领域" / "本地库能搜什么" / "有什么类别的项目"
- "按...分类浏览" / "按标签找项目"
- "这个项目靠谱吗" / "安全吗" / "有风险吗" / "许可证是什么" / "star 是真的吗"
- "评估一下这个项目" / "信任评分" / "帮我看看这个项目值不值得用"
- "国内能用的" / "不需要VPN的" / "国内环境适用" / "面向国内的技能"
- "国际通用的" / "外网环境" / "海外用户能用"

---

## 核心工作流

### 阶段 1: 理解用户意图
解析用户输入，确定：
1. **操作类型**: 搜索 / 详情分析 / 对比 / 趋势 / 社区精选 / 领域发现 / 同类替代 / 学习搜索
2. **关键词**: 从自然语言描述中提取核心搜索词（见下方关键词提取规则）
3. **语言偏好**: Python / JavaScript / Go 等（如有提及）
4. **输出格式**: 列表 / 卡片 / 表格 / 趋势

#### 关键词提取规则（重要）

用户经常用自然语言描述需求，如"Python的Web框架来开发后端API服务"。**不能直接把整句话丢给 GitHub Search API**——中文自然语言在 GitHub 上几乎搜不到结果。

**提取流程**：
1. 从用户输入中识别技术领域词（如 Web框架、后端、API、爬虫、机器学习）
2. 提取编程语言（如 Python、Go、Rust）
3. 去掉虚词和泛化词（如"的""来""开发""服务""项目""工具""请帮我"）
4. 剩余词传给 `main.py`，脚本会自动做中文→英文映射（KEYWORD_MAP 70+条映射）

**示例**：
| 用户输入 | 提取后 | GitHub 查询（自动转换） |
|---------|--------|----------------------|
| "Python的Web框架来开发后端API服务" | Python, Web框架, 后端, API | `python web framework backend server api` |
| "找一个可视化的数据分析工具" | 可视化, 数据分析 | `data analysis pandas visualization chart` |
| "自托管的即时通讯" | 自托管, 即时通讯 | `instant-messaging chat self-hosted` |

**注意**：脚本 `expand_keywords` 会自动处理映射，Agent 只需把原始关键词传给 `main.py search`，不需要手动翻译。但如果用户输入特别冗长（>20字），Agent 应先精简提取核心词再传入。

### 阶段 2: 选择数据源并执行

#### 2A. 本地库搜索（Agent 直接读取 JSON）
**不要调用 main.py local 命令。** Agent 直接读取 `data/projects_db.json`，用自身语义理解能力匹配：

```
读取 data/projects_db.json → 解析每个项目的 display_name、about、tags、scene
→ 用语义理解判断哪些项目匹配用户意图
→ 返回匹配的项目列表（标记 verified: true）
```

**匹配策略**（Agent 自行判断，不依赖脚本）：
- 关键词与 `display_name`、`about`、`scene` 的语义关联
- 标签与用户需求的相关性（参考 references/tag-guide.md）
- 语言偏好过滤

**本地库数据字段**（v4.4.0，数据源为飞书多维表格人工维护）：
```json
{
  "repo_name": "owner/repo",
  "display_name": "项目名称",
  "about": "一句话定位 / 项目简介",
  "tags": ["AI", "开源", "Python"],
  "scene": "适合场景描述",
  "verified": true,
  "html_url": "https://github.com/owner/repo",
  "value_prop": "可尝试价值描述",
  "form": "形式（开源项目/应用/网页/docker/git等）",
  "cost": "上手成本（低/中等/高等）",
  "source_url": "推荐来源链接",
  "proj_type": "类型（开源项目/金融/插件/资源/应用/模型）"
}
```

#### 2B. GitHub API 搜索（调用 main.py）
本地库结果不足时，调用 GitHub Search API：

```bash
python scripts/main.py search "关键词" [语言]
```

**注意**: `search` 命令只执行本地库 + GitHub API 搜索，**不自动调用 Trending/HelloGitHub/Awesome**。

#### 2C. HelloGitHub 社区精选（调用 main.py）
用户想看社区精选、人工推荐的项目时调用：

```bash
python scripts/main.py hellogithub "关键词" [期数]
```

**适用场景**：
- 用户说"HelloGitHub 推荐"、"社区精选"、"HG 精选"
- 需要中文社区人工筛选过的项目
- 搜索结果想要更有中文场景描述

**输出结构**：
```json
{
  "query": "推理引擎",
  "source": "hellogithub",
  "issues_searched": 3,
  "projects": [
    {
      "repo_name": "antirez/ds4",
      "display_name": "ds4",
      "about": "Redis 作者写的 DeepSeek 专用推理引擎...",
      "language": "C",
      "scene": "HelloGitHub 推荐",
      "_source": "hellogithub",
      "_issue": 122
    }
  ]
}
```

**注意**：
- `期数` 参数控制搜索最近几期月刊，默认10期（v3.4.0从5提升至10），最多20期
- HelloGitHub 月刊位于 `521xueweihan/HelloGitHub` 仓库的 `content/` 目录
- 结果中的 `about` 是中文人工描述，质量较高
- 搜索是关键词匹配，Agent 也可直接读取返回结果做语义过滤

#### 2D. 阮一峰周刊推荐（调用 main.py）
用户想看阮一峰科技爱好者周刊中的项目推荐时调用：

```bash
python scripts/main.py ruanyf "关键词" [期数]
```

**适用场景**：
- 用户说"阮一峰推荐"、"周刊里的"、"科技爱好者周刊"
- 需要中文技术圈KOL人工筛选过的项目
- 想发现星数不高但质量不错的小众项目
- 需要AI相关工具推荐（周刊有专门的「AI 相关」板块）

**输出结构**：
```json
{
  "query": "截图工具",
  "source": "ruanyf_weekly",
  "issues_searched": 10,
  "projects": [
    {
      "repo_name": "HuibingLin/LiteSnap",
      "display_name": "LiteSnap",
      "about": "开源的 Windows 截图工具。",
      "language": "",
      "scene": "阮一峰周刊·工具",
      "verified": false,
      "_source": "ruanyf_weekly",
      "_issue": 407
    }
  ]
}
```

**注意**：
- `期数` 参数控制搜索最近几期周刊，默认10期，最多20期
- 周刊位于 `ruanyf/weekly` 仓库的 `docs/` 目录，文件名格式为 `issue-{N}.md`
- 每周五发布，已累计400+期
- 仅解析「工具」和「AI 相关」两个板块的 GitHub 项目
- 周刊不标注项目语言，`language` 字段为空；语言过滤仅在描述文本中匹配
- 阮一峰推荐的项目通常星数不高但实用性强，适合发现小众优质工具

#### 2E. Awesome 列表搜索（调用 main.py）
用户想按领域/类别发现项目清单时调用：

```bash
python scripts/main.py awesome "关键词" [语言]
```

**适用场景**：
- 用户说"有哪些 awesome 列表"、"按领域找项目"
- 想发现某个领域/赛道的完整资源清单
- 想快速了解某个领域有哪些工具和库

**输出结构**：
```json
{
  "query": "machine-learning",
  "source": "awesome",
  "lists": [
    {
      "repo_name": "josephmisiti/awesome-machine-learning",
      "display_name": "awesome-machine-learning",
      "about": "A curated list of awesome Machine Learning frameworks...",
      "star_count": 72757,
      "language": "Python",
      "html_url": "https://github.com/josephmisiti/awesome-machine-learning",
      "_source": "awesome_search"
    }
  ]
}
```

**注意**：
- Awesome 列表返回的是**资源清单仓库**，不是具体项目
- 用户拿到 awesome 列表后，可以用 `analyze` 命令查看某个列表的内容
- 搜索策略：先搜 `topic:awesome-list`，再放宽条件搜 `awesome + 关键词`

#### 2F. 学习导向搜索（调用 main.py）

用户想通过实践学习编程时调用——找适合重写或贡献的项目：

```bash
python scripts/main.py learning rewrite "关键词" [语言]
python scripts/main.py learning contribute "关键词" [语言]
```

**适用场景**：
- 用户说"想找个项目练手"、"想通过重写学习"、"找个简单的项目换语言重写"
- 用户说"想参与开源贡献"、"找个项目提PR"、"入门开源"
- 用户表达"在实践中提升语言技巧"的需求

**两种模式**：

| 模式 | 目标 | 搜索策略 | 排序依据 |
|------|------|---------|---------|
| `rewrite` | 换语言重写学习 | 低star门槛(stars:≥50)，简单小型项目 | 简单性评分：fork少+star适中+有文档 |
| `contribute` | 参与开源贡献 | good-first-issue topic，活跃项目 | 贡献友好度：gfi+open issues+活跃 |

**rewrite 模式核心逻辑**：可移植性 > 完整性
- 优先单语言、小代码量的项目（重写成本低）
- `languages_summary` 展示语言组成比例（单语言占比高 = 更适合重写）
- `project_type` 辅助判断：`tool`/`library` 最适合重写，`application` 重写成本高

**contribute 模式核心逻辑**：友好度 > 项目规模
- 优先有 `good-first-issue` 标签的项目
- open issues 多 = 有明确待做工作
- 近期活跃 = 维护者会回应 PR

**输出结构**：
```json
{
  "query": "Python的Web框架",
  "mode": "rewrite",
  "language": "python",
  "merged": [
    {
      "repo_name": "owner/repo",
      "display_name": "name",
      "star_count": 800,
      "language": "Python",
      "forks_count": 45,
      "open_issues": 12,
      "size_kb": 1200,
      "has_wiki": true,
      "_learning_score": 5,
      "_learning_note": "forks:45, stars:800, 文档:2/2"
    }
  ]
}
```

**注意**：
- 学习模式不自动调用 Trending/HelloGitHub/Awesome
- 本地库项目会标注 `_learning_note: "本地精选项目"`（默认评分3）
- rewrite 模式的简单性评分范围 0-6，contribute 模式的贡献友好度范围 0-6

### 阶段 3: 解析输出

#### 2G. 本地库统计与发现（v3.4.0 新增）

**db-stats** — 查看本地库的领域覆盖、标签分布和新鲜度：

```bash
python scripts/main.py db-stats
```

**适用场景**：
- 用户想了解本地库能搜到什么领域的项目
- 用户想知道本地库数据是否过时
- Agent 判断是否需要走 GitHub API 补充搜索

**输出结构**：
```json
{
  "total_projects": 2377,
  "unique_tags": 2714,
  "db_last_modified": "2026-08-14",
  "domain_coverage": {
    "AI": {"project_count": 530, "top_tags": [...]},
    "开源/工具/效率": {"project_count": 803, "top_tags": [...]},
    ...
  },
  "api_available": true,
  "token_mode": "authenticated"
}
```

**discover** — 按标签浏览本地库项目：

```bash
python scripts/main.py discover "AI" [数量]
```

**适用场景**：
- 用户说"本地库有哪些AI项目" / "按标签浏览"
- 想按领域/标签发现项目，而非关键词搜索
- 代替"搜索"，做更宽泛的浏览式发现

**输出结构**：
```json
{
  "tag": "AI",
  "total": 638,
  "projects": [
    {"repo_name": "...", "display_name": "...", "about": "...", "tags": [...], "value_prop": "...", "cost": "..."}
  ],
  "api_available": true
}
```

**本地库领域覆盖概览**（v4.4.0，数据源：飞书多维表格人工维护）：

| 领域 | 项目数 | 说明 |
|------|--------|------|
| 开源/工具/效率 | 803 | 最大领域，含开源项目、各类工具、效率应用 |
| AI | 530 | AI Agent、LLM、MCP、RAG、Claude Code等 |
| 编程语言 | 412 | Python/Rust/Go/TS/JS 等语言项目和资源 |
| 跨平台/桌面 | 192 | 跨平台应用、macOS/Windows/Linux/Android/iOS |
| Web/前端 | 92 | 前端框架、React、Web应用、低代码 |
| 基础设施 | 92 | Docker、数据库、监控、运维 |
| 开发 | 87 | 编辑器、IDE、DevOps、API、测试 |
| 游戏/多媒体 | 87 | 游戏引擎、视频、音乐、图片处理、3D |
| 内容/知识 | 77 | 知识管理、文档、博客、Markdown、教程 |
| 安全/隐私 | 75 | 安全工具、渗透测试、隐私保护 |
| 金融 | 33 | 量化交易、金融数据 |

**Agent 使用建议**：搜索结果为空时，先执行 `db-stats` 查看该领域是否在本地库覆盖范围内；如果领域项目数较少，主动走 GitHub API 补充。

#### 2H. 项目信任评估（v3.6.0 新增）

受 [Starguard](https://github.com/m-ahmed-elbeskeri/Starguard) 启发，对目标项目进行多维度信任评估，输出 0-100 的综合信任分数。

**独立命令**：
```bash
python scripts/main.py trust owner/repo
```

**自动集成**：`analyze` 命令执行时自动附带信任评估结果，无需单独调用。

**四个评估维度**：

| 维度 | 检测内容 | 风险信号 |
|------|---------|----------|
| Star 质量 | star/fork 比例异常检测 | ratio > 30 可疑，> 100 高度可疑（可能存在刷星） |
| 许可证风险 | 许可证类型分级（safe/moderate/high/unknown） | GPL/AGPL 对商用有限制；无许可证存在法律风险 |
| 维护者健康度 | 贡献者数量、最近提交时间、贡献集中度 | 单人维护(bus factor=1)、长期无提交(>180天)、单人贡献>80% |
| 依赖安全 | manifest 文件存在性、lockfile、可疑文件 | 无 lockfile（依赖版本浮动）、.env 文件暴露 |

**输出结构**：
```json
{
  "trust_score": 82,
  "trust_badge": "✅ reliable",
  "checks": {
    "license": { "risk_level": "safe", "score": 95, "assessment": "..." },
    "star_quality": { "star_fork_ratio": "14.3:1", "risk": "low", "score": 95, "assessment": "..." },
    "maintainer_health": { "contributors": 74, "last_commit_days_ago": 3, "score": 80, "assessment": "..." },
    "dependency_safety": { "has_lockfile": true, "score": 95, "assessment": "..." }
  },
  "warnings": [],
  "highlights": ["..."]
}
```

**信任等级**：≥80 ✅ reliable | ≥60 🟡 generally safe | ≥40 🟠 caution | <40 🔴 risky

**Agent 使用场景**：
- 用户问"这个项目靠谱吗" / "值不值得用" / "安全吗" → `trust` 命令
- 用户要求分析项目时 → `analyze` 已自动包含信任评估
- 推荐项目后，主动展示信任评估帮助用户决策

**本地库搜索结果**: Agent 自行解析 JSON 数组

**GitHub search 命令输出结构**:
```json
{
  "query": "量化交易",
  "api_available": true,
  "token_mode": "authenticated",
  "local_results": [...],
  "github_results": [...],
  "merged": [
    {
      "repo_name": "vnpy/vnpy",
      "display_name": "vn.py",
      "about": "专业量化交易框架",
      "tags": ["金融", "量化交易", "python库"],
      "star_count": 33000,
      "language": "Python",
      "status": "active",
      "created_at": "2015-03-15",
      "last_update": "2026-06-10",
      "verified": false,
      "_source": "github_search"
    }
  ]
}
```

**analyze 命令输出结构**:
```json
{
  "repo_name": "vnpy/vnpy",
  "display_name": "vn.py",
  "about": "...",
  "tags": ["python", "trading", "quant"],
  "star_count": 33000,
  "language": "Python",
  "languages": {"Python": 123456, "JavaScript": 6789, "HTML": 1234},
  "languages_summary": {"Python": "92.3%", "JavaScript": "5.1%", "HTML": "1.5%"},
  "project_type": "application",
  "license": "MIT",
  "status": "active",
  "created_at": "2015-03-15",
  "last_update": "2026-06-10",
  "homepage": "https://vnpy.com",
  "has_wiki": false,
  "html_url": "https://github.com/vnpy/vnpy",
  "readme_preview": "...",
  "docker_support": true,
  "install_methods": ["pip", "docker"],
  "age_days": 4100,
  "star_per_day": 8.05,
  "star_30d": 245,
  "star_90d": 680,
  "star_method": "events_api",
  "star_history_url": "https://star-history.com/#vnpy/vnpy&Date",
  "deepwiki_url": "https://deepwiki.com/vnpy/vnpy",
  "zread_url": "https://zread.ai/r/vnpy/vnpy"
}
```

**Star 增量字段说明**（v4.3.0）：
- `star_per_day`：生命周期平均日均增速（粗略），`total_stars / age_days`
- `star_30d`：近30天精确 star 增量（Events API 统计）
- `star_90d`：近90天精确 star 增量（Events API 统计）
- `star_method`：数据来源标记
  - `events_api`：精确统计，覆盖完整90天窗口
  - `events_api_partial`：部分统计（高活跃项目事件过多，5页上限内未覆盖完整窗口）
  - `no_token`：无Token时跳过（仅 analyze/details 命令需要）
- 对比使用：`star_per_day` 反映历史总趋势，`star_30d`/`star_90d` 反映近期热度。若 `star_30d` 明显高于 `star_per_day × 30`，说明项目在加速增长

**project_type 类型说明**：

| 类型 | 含义 | 学习场景暗示 |
|------|------|------------|
| `tool` | 单功能工具（如 markitdown） | 适合重写：代码集中，目标明确 |
| `library` | 开发库/SDK | 适合重写：API 设计是核心 |
| `application` | 完整应用（有前端/后端/交互） | 重写成本高，适合局部贡献 |
| `framework` | 框架/引擎 | 适合学习架构，不适合整体重写 |
| `tutorial` | 教程/资源集合 | 适合学习参考，不是重写对象 |
| `resource` | awesome 列表/数据集 | 纯参考 |

**推断逻辑**：基于客观特征（名称模式、topics、README 关键词、语言组成），按优先级 resource > tutorial > framework > library > tool > application（默认）。不做"成熟度"或"完成度"等主观判断。

**languages_summary 说明**：
- `languages`：原始数据（语言→代码字节数），来自 GitHub API
- `languages_summary`：百分比摘要（≥1% 单独显示，<1% 合并为 Other）
- 用途：直观展示项目技术栈复杂度；单语言占比高 = 更适合重写学习
- 示例：`markitdown` 的 `{"Python": "92.3%", "CSS": "5.1%"}` 一眼就能看出是轻量单语言工具

**注意**: `learning_cost` 和 `scene` 仅存在于本地库 `projects_db.json`，不在 analyze 输出中。格式F雷达图需要这两个字段时，Agent 需从 projects_db.json 按 `repo_name` 匹配补充；项目不在本地库时使用默认值（`learning_cost=""` 评5分基线，`scene=""` 无场景加分）。

#### 2I. 仓库文档生成（v3.7.0 新增）

**独立命令**：`python scripts/main.py docs owner/repo`
**自动集成**：`analyze` 命令输出末尾自动附带 `deepwiki_url` 和 `zread_url` 链接

**功能说明**：
通过 GitHub API 获取仓库目录树（递归，最深 2 层）+ README + 配置文件，自动生成「快速理解」文档，包含：
- **技术栈推断**：从 package.json / Cargo.toml / go.mod 等配置文件自动识别语言、框架、包管理器、CI/CD
- **目录结构统计**：文件总数、目录总数、Top 10 文件类型（按扩展名）
- **关键模块提取**：顶层目录（排除 .github / docs / test 等常见非模块目录）
- **Quick Start 提取**：从 README 中自动截取 Quick Start / Installation / Usage 段落
- **深度阅读链接**：自动生成 DeepWiki 和 Zread 链接，用户可一键进入完整交互式文档

**输出结构**：
```json
{
  "repo_name": "owner/repo",
  "display_name": "...",
  "about": "...",
  "star_count": 12345,
  "language": "Python",
  "license": "MIT",
  "tech_stack": {
    "language": "TypeScript",
    "framework": "Next.js",
    "package_manager": "npm/yarn",
    "build_tool": "Docker",
    "ci_cd": ["GitHub Actions"]
  },
  "directory_structure": {
    "total_files": 250,
    "total_dirs": 35,
    "top_file_types": [{"ext": ".ts", "count": 120}, {"ext": ".json", "count": 15}]
  },
  "key_modules": ["src", "lib", "packages"],
  "quick_start": "...",
  "deepwiki_url": "https://deepwiki.com/owner/repo",
  "zread_url": "https://zread.ai/r/owner/repo"
}
```

**API 调用次数**：最多 5 次（details + languages + tree + readme + 配置文件），对大仓库的 tree 限制 300 条防止超时。

**与 DeepWiki/Zread 的定位差异**：
- DeepWiki/Zread 需要克隆仓库 + 建向量索引 + LLM 逐页生成，耗时长但内容深
- 本技能的 `docs` 命令轻量快速（秒级），适合「快速判断是否值得深入」的场景
- 如需深度理解项目架构，引导用户使用输出中的 DeepWiki/Zread 链接

#### 2J. 智能体技能/工具搜索（v4.2.0）

用户想搜索 AI agent 技能、MCP server、agent 框架或可接入 agent 的工具时调用：

```bash
python scripts/main.py agent "关键词" [模式] [--region cn|global|all]
```

**五种模式**（对应不同的用户需求）：

| 模式 | 说明 | 用户意图 |
|------|------|---------|
| `all`（默认） | 返回所有 agent 相关项目 | 想了解某个方向的 agent 生态 |
| `skill` | 仅返回技能/插件 | 想找能直接加载到 agent 平台的技能 |
| `standalone` | 排除技能，仅返回可独立使用的 | 不想接入 agent，想直接用 |
| `integrate` | 仅返回可接入 agent 的项目 | 想找能集成到现有 agent 的工具/框架 |
| `safe` | 仅返回安全评分≥60的结果，按安全评分排序 | 优先考虑安全可靠的项目 |

**三个分类维度**（每个项目都会标注）：

| 维度 | 字段 | 说明 |
|------|------|------|
| 是否技能 | `is_skill` | 技能/插件需要 agent 平台才能运行（如 SKILL.md、Cursor Rules、Coze Skill） |
| 接入方式 | `agent_integration` | 如何接入 agent：MCP / SKILL.md / framework / plugin / None |
| 可独立使用 | `standalone` | 是否不依赖 agent 平台即可使用 |

**重要区分**：`is_skill` 和 `agent_integration` 是独立维度：
- 技能（is_skill=True）一定可接入 agent，但可接入 agent 的不一定是技能
- MCP server 不是技能（is_skill=False）但可以接入 agent（agent_integration="MCP"）且能独立使用
- LangChain 不是技能但可接入 agent，也能独立使用

**数据源**（v4.1.0 共 10 个数据源）：
1. `philipbankier/awesome-agent-skills` — 跨平台技能目录
2. `e2b-dev/awesome-ai-agents` — AI agent 框架/平台列表
3. GitHub Topics — `coze-skill`、`ai-plugins`、`mcp-server`、`agent-framework`、`llm-agent`、`ai-agent`
4. **MCP Registry**（v4.0.0）— 官方注册中心，4500+ 服务器，无需认证
5. **Smithery**（v4.0.0）— 7300+ 服务器，需免费 token（可选）
6. **Glama MCP**（v4.0.0）— 67960+ 服务器，网页解析，自带质量评级
7. **Hermes Skills Hub**（v4.1.0 新增）— agentskills.io 标准，100+ 验证技能，含 popularity_score
8. **虾评**（v4.1.0 新增）— Agent 技能评测平台，含用户评分/下载量/多维评测（需 API Key，可选）
9. **腾讯 SkillHub**（v4.1.0 新增）— 13000+ 技能，含 AI 评分和安全审核，网页解析
10. **广义搜索+适配检测**（v4.1.0 新增）— 先搜索关键词本身，再检测是否有 agent 适配信号，发现后续做了适配但未打标签的项目

**安全评估**（v4.0.0 新增）：
每个搜索结果自动附带 6 维度安全评估，输出 `safety` 和 `safety_summary` 字段：

```json
{
  "name": "example/mcp-server",
  "safety": {
    "safety_score": 82,
    "risk_level": "low",
    "risk_badge": "🟢",
    "risk_label": "低风险",
    "dimensions": {
      "code_transparency": {"score": 90, "detail": "源码托管在 GitHub，可公开审查"},
      "source_credibility": {"score": 75, "detail": "来自 GitHub 组织 (example)"},
      "maintenance": {"score": 90, "detail": "最近 5 天内有更新"},
      "community_adoption": {"score": 85, "detail": "⭐5000"},
      "permission_transparency": {"score": 95, "detail": "MIT — 最宽松的开源许可"},
      "security_record": {"score": 70, "detail": "未检测到已知安全事件"}
    },
    "red_flags": []
  },
  "safety_summary": "🟢 安全82(低风险)"
}
```

**安全评价 6 维度与权重**：

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| 代码透明度 | 30% | 源码是否公开可审查（GitHub > 有链接 > 无源码） |
| 来源可信度 | 25% | 是否来自已知组织/验证发布者 |
| 维护活跃度 | 15% | 最近更新时间（≤30天高分，>365天低分） |
| 社区采纳度 | 15% | Star 数 / 下载量 |
| 权限透明度 | 10% | 许可证类型与权限声明 |
| 安全记录 | 5% | 已知安全事件（基于公开信息） |

**风险等级**：🟢 低风险(80-100) | 🟡 中风险(60-79) | 🟠 高风险(30-59) | 🔴 极高风险(0-29)

**红旗项检测（Red Flags）**：
- 🔴 硬编码公网 IP 地址（参考 JetBrains 恶意插件事件）
- 🔴 疑似硬编码 API Key/Token
- 🟠 非加密 HTTP 传输
- 🟠 无公开源码链接
- 🟠 未声明许可证
- 🟡 来源未经平台验证

检测到红旗项时自动降级安全评分：critical 级 → 上限 25 分；2+ high 级 → 上限 40 分；1 high 级 → 上限 55 分。

**源码级安全扫描**（v4.1.0 新增）：
对小项目（< 5000KB）自动下载代码文件进行深度扫描，检测 9 类可疑模式：

| 检测类型 | 严重度 | 说明 |
|---------|--------|------|
| eval/exec 动态执行 | 🔴 critical | `eval(input(...))` / `exec(base64...)` 等动态代码执行 |
| 混淆 base64 | 🔴 critical | `base64.b64decode("长字符串")` 可能隐藏恶意代码 |
| 导入注入 | 🔴 critical | `__import__(input/base64/eval)` 动态导入 |
| TLS 降级 | 🔴 critical | `X509TrustManager` / `verify=False` / `CERT_NONE` 等证书验证降级 |
| 环境变量窃取 | 🔴 critical | `os.environ["API_KEY"]` 等敏感环境变量读取 |
| subprocess shell | 🟠 high | `subprocess.call(..., shell=True)` 命令注入风险 |
| os.system 调用 | 🟠 high | `os.system(...)` 直接执行命令 |
| 数据外泄 | 🟠 high | `curl/wget --data http://` 向外部发送数据 |
| 敏感路径访问 | 🟠 high | `/etc/passwd` / `.ssh/id_rsa` / `.aws/credentials` |

扫描限制：最多 3 个项目、每个项目最多 10 个文件，避免 API 超时。

**多源交叉验证**（v4.1.0 新增）：
当同一项目出现在多个平台时，自动对比各平台评分，识别可能的控评行为：
- 统一各平台评分到 0-5 分制（用户评分/popularity/AI评分/star数对数缩放）
- 评分差异 > 2 分标记为"⚠评分差异大"，提示可能存在控评
- 输出 `cross_validation` 字段，含各平台评分、平均分、最大差异

**广义搜索+适配检测**（v4.1.0 新增）：
不只搜"XXX技能"，而是先搜"XXX"再检测是否有智能体适配信号：
- 检查 README 描述、topics、名称中的 MCP/Skill/Plugin/Agent 关键词
- 发现后续做了智能体适配但未打标签的项目
- 标注检测到的适配方式（MCP/SKILL.md/plugin/framework）

**区域适用性检测**（v4.2.0 新增）：
自动检测每个项目的区域适用性，帮助不同网络环境的用户筛选掉不可用的技能：
- 分析项目描述、名称、tags 中的服务依赖信号（如 WeChat/支付宝/钉钉 → 国内；OpenAI/Stripe/Slack → 国际）
- 结合来源平台（虾评/SkillHub → 偏国内；MCP Registry/Smithery → 偏国际）和域名（gitee.com → 国内）
- 每个项目标注 `region` 字段：

| 区域标签 | 说明 | 适用用户 |
|---------|------|---------|
| `domestic` | 面向国内环境，依赖国内服务/API | 国内用户 |
| `international` | 面向国际环境，依赖外网服务/API | 国际用户（国内无VPN可能不可用） |
| `universal` | 通用，无明显区域依赖或同时支持国内外 | 所有用户 |

**区域过滤**（`--region` 参数）：
- `--region cn`：仅保留 domestic + universal（国内用户无VPN时推荐）
- `--region global`：仅保留 international + universal
- `--region all`（默认）：不过滤

输出中包含 `region_stats` 字段统计各区域分布，`region_filter` 字段标注当前过滤模式。

**输出结构**（v4.2.0 含安全评估+源码扫描+交叉验证+区域检测）：
```json
{
  "query": "MCP",
  "source": "agent",
  "mode": "all",
  "region_filter": "all",
  "total_found": 45,
  "safety_enabled": true,
  "code_scan_enabled": true,
  "cross_validation_count": 2,
  "source_stats": {"awesome-agent-skills": 5, "github-topic:mcp-server": 10, "mcp-registry": 3, "hermes": 2, "broad-agent-match": 4},
  "region_stats": {"universal": 30, "international": 12, "domestic": 3},
  "projects": [
    {
      "name": "modelcontextprotocol/servers",
      "repo_name": "modelcontextprotocol/servers",
      "html_url": "https://github.com/modelcontextprotocol/servers",
      "about": "Official reference MCP server implementations.",
      "is_skill": false,
      "agent_integration": "MCP",
      "standalone": true,
      "region": "universal",
      "_source": "awesome-agent-skills",
      "safety": {"safety_score": 82, "risk_badge": "🟢", ...},
      "safety_summary": "🟢 安全82(低风险)",
      "cross_validation": {
        "sources": ["awesome-agent-skills", "github-topic:mcp-server"],
        "avg_rating": 4.58,
        "max_discrepancy": 0.12,
        "flag_review_manipulation": false
      }
    }
  ]
}
```

**适用场景**：
- 用户说"有没有 MCP server"、"找一下 agent 技能"、"智能体工具"
- 用户说"不想接入 agent，能直接用的工具" → 使用 `standalone` 模式
- 用户说"能接入 agent 的工具" → 使用 `integrate` 模式
- 用户说"Coze 技能"、"Claude 技能" → 使用 `skill` 模式
- 用户说"安全的 MCP"、"靠谱的技能" → 使用 `safe` 模式
- 用户关注安全时 → 所有模式均展示 `safety_summary`，`safe` 模式仅返回安全评分≥60的结果
- 用户在国内无VPN → 使用 `--region cn` 过滤掉依赖外网服务的项目
- 用户面向国际用户 → 使用 `--region global` 过滤掉依赖国内生态的项目
- 每个项目展示区域标签：🇨🇳国内 / 🌍国际 / 🌐通用

### 阶段 4: 渲染输出
根据用户意图和输出模板（references/output-templates.md）渲染：

**搜索类** → 格式A（快速列表）或 格式B（详细卡片）
- 本地库结果标记 ✅，GitHub API 结果标记 ⏳，HelloGitHub 结果标记 📖，阮一峰周刊结果标记 📰

**智能体技能/工具类** → 格式A + 分类标签 + 安全徽章
- 每个项目标注分类标签：🏷️技能 / 🔌可接入 / 🖥️独立可用
- 每个项目标注安全徽章：🟢低风险 / 🟡中风险 / 🟠高风险 / 🔴极高风险
- 每个项目标注区域标签：🇨🇳国内 / 🌍国际 / 🌐通用
- 根据用户选择的 mode（all/skill/standalone/integrate/safe）决定展示哪些类型
- 技能类项目提醒"需要 agent 平台才能使用"
- 高风险/极高风险项目提醒"建议仔细审查后使用"
- `safe` 模式下仅展示安全评分≥60的结果，按安全评分排序

**社区精选类** → 格式A + 标注"第N期推荐"
- HelloGitHub 结果标注期号
- 阮一峰周刊结果标注期号 + 板块（工具/AI相关）

**领域发现类** → 专门格式（Awesome 列表）
- 列出 awesome 列表名称、⭐数、简介
- 用户可点击链接进入列表查看

**分析类** → 格式B（详细卡片）+ 格式D（趋势分析）

**对比类** → 格式C（对比表格）或 格式F（雷达图，2-3个项目对比时优先）

**趋势类** → 格式D（趋势分析）

#### 横向同类推荐（格式E · 轻量补充）

在搜索结果（格式A/B）末尾，**仅当满足以下条件时**追加一行同类推荐：

**触发条件（必须同时满足）**：
1. 当前对话轮次 ≤ 3 轮（短对话、低信息密度场景）
2. 搜索结果中本地库项目 ≥ 1 个（有 verified ✅ 的结果）
3. 该项目的 tags 在 projects_db.json 中可找到其他同类项目（标签重叠 ≥ 2）

**禁止触发的场景**：
- 用户已明确表示满意（如"就这个了"、"够了"）
- 用户在追问部署/配置/使用细节（已经进入深入阶段）
- 对话轮次 ≥ 4 轮（信息已足够丰富）
- 用户明确说"不要推荐"、"就查这一个"

**渲染方式**（仅一行，不展开）：
```
🔁 同类项目: {项目A} ({tag重叠说明}) · {项目B} ({tag重叠说明}) · {项目C}
💡 说"对比一下"查看详细对比表
```

**选择同类项目的规则**：
- 从 projects_db.json 中找到与搜索结果 top1 项目标签重叠 ≥ 2 的其他项目
- 优先选择 verified 项目
- 最多展示 3 个同类项目
- 每个只显示 display_name + 简短区分特征（不要完整卡片）

**注意**：这是轻量提示，不是完整推荐。用户说"对比一下"才展开为格式C或格式F。

#### 雷达图对比（格式F · 可视化）

在用户说"对比一下"或"画个对比图"时，**2-3个项目对比**优先生成雷达图 HTML 文件；4个及以上项目仍用格式C文字表格。

**触发条件**：
1. 用户说"对比一下" / "画个图" / "可视化对比" / "雷达图"
2. 对比项目数 2-3 个（格式E同类推荐展开时自动满足）

**渲染流程**：

1. **收集数据**：对每个项目执行 `main.py analyze`，同时从 projects_db.json 读取 learning_cost/scene 补充本地字段（按 repo_name 匹配；不在本地库的项目使用默认值，不影响图表生成）
2. **生成雷达图**：
   ```bash
   python scripts/radar_chart.py --data-file /tmp/radar_input.json --output /tmp/radar_{timestamp}.html
   ```
   Agent 先将所有项目数据写入临时 JSON 文件，再调用脚本生成 HTML
3. **交付**：将 HTML 文件发送给用户，附一行极简结论

**五维评分体系**（0-10 分，脚本自动计算）：

| 维度 | 数据来源 | 评分逻辑 |
|------|---------|---------|
| 社区活跃度 | star_count + star_per_day + last_update | stars 对数分档 + 增速分档 + 更新新鲜度 |
| 功能覆盖 | tags 数量 + scene | 标签丰富度 + 场景描述完整度 |
| 上手友好度 | learning_cost + docker_support + install_methods + languages_summary | 学习成本低=高分 + Docker加分 + 多安装方式加分 + 单语言占比高加分 |
| 文档质量 | has_wiki + about + install_methods | wiki + 描述完整度 + 安装说明 |
| 维护状态 | status + last_update + star_per_day | 未归档 + 更新新鲜度 + 增速 |

**输出格式**（成功时）：
```
📊 {项目A} vs {项目B} 雷达图已生成
{项目A} 在{维度X}领先 · {项目B} 在{维度Y}领先
[雷达图文件链接]

💡 说"详细对比"查看文字表格
```

**边界规则**：
- **图表成功时不重复罗列数据**：文字部分仅一行结论，不在图表之外大段重复各维度数值
- **图表生成失败时**：重试 1 次；仍失败则降级为格式C（文字对比表格），并提示"图表生成异常，已切换为文字对比"
- **4+项目对比**：直接用格式C，不生成雷达图（多边形重叠后可读性差）

**降级到格式C的条件**：
- 项目数 > 3
- radar_chart.py 脚本执行失败（2次重试后）
- 脚本输出文件不存在或文件大小 < 100 字节
- **注意**: 30天/90天增量数据 GitHub API 不提供，main.py 只返回 `star_per_day`（总star/项目年龄）。格式D中的"30天增长"用 `star_per_day * 30` 估算，并标注"估算值"。

### 阶段 5: 交互跟进
- "看第N个" → 执行 `main.py analyze owner/repo`，输出格式B
- "和前N个对比" → 提取前N项信息，输出格式C
- "趋势如何" → 对该项输出格式D（基于 star_per_day 估算）
- "支持docker吗" → 执行 `main.py readme owner/repo`，分析后回答
- "还有吗" → 显示更多结果
- "HelloGitHub 有推荐的吗" → 执行 `main.py hellogithub "关键词"`
- "阮一峰有推荐的吗" / "周刊里有..." → 执行 `main.py ruanyf "关键词"`
- "有哪些 awesome 列表" → 执行 `main.py awesome "关键词"`
- "对比..." / "哪个好" → 2-3个项目时格式F（雷达图），4+项目时格式C（文字表格）
- "有没有类似的" / "替代品" → 从 projects_db.json 找标签重叠 ≥2 的同类项目，输出格式E
- "详细对比" → 格式C（文字对比表格）
- "想练手" / "想重写学习" → `learning rewrite` 模式
- "想参与开源" / "想提PR" → `learning contribute` 模式
- "本地库有哪些领域" / "能搜什么" → `db-stats` 命令
- "按...分类浏览" / "AI项目有哪些" → `discover` 命令

---

## 命令速查表

| 用户意图 | 调用命令 | 说明 |
|---------|---------|------|
| 搜索项目 | `python scripts/main.py search "关键词" [语言]` | 本地库 + GitHub API |
| 分析具体项目 | `python scripts/main.py analyze owner/repo` | 详情+README+趋势+star增量(30d/90d)+语言组成+项目类型+DeepWiki/Zread链接 |
| 仓库文档 | `python scripts/main.py docs owner/repo` | 技术栈+目录结构+模块划分+Quick Start |
| 信任评估 | `python scripts/main.py trust owner/repo` | Star质量/许可证风险/维护者健康度/依赖安全 |
| 查看 Trending | `python scripts/main.py trending [语言]` | 近期热门（独立命令） |
| HelloGitHub 精选 | `python scripts/main.py hellogithub "关键词" [期数]` | 社区人工推荐（默认10期） |
| 阮一峰周刊 | `python scripts/main.py ruanyf "关键词" [期数]` | 阮一峰周刊项目推荐（默认10期） |
| Awesome 列表 | `python scripts/main.py awesome "关键词" [语言]` | 按领域发现精选清单 |
| 智能体技能/工具 | `python scripts/main.py agent "关键词" [模式] [--region cn\|global\|all]` | 技能/MCP/框架搜索+安全评估+区域过滤 |
| 学习-重写 | `python scripts/main.py learning rewrite "关键词" [语言]` | 找简单项目换语言重写 |
| 学习-贡献 | `python scripts/main.py learning contribute "关键词" [语言]` | 找有 good-first-issue 的项目 |
| 获取 README | `python scripts/main.py readme owner/repo` | 回答部署/配置细节 |
| 雷达图对比 | `python scripts/radar_chart.py --data-file <json> --output <html>` | 2-3个项目可视化对比 |
| 本地库统计 | `python scripts/main.py db-stats` | 查看领域覆盖和标签分布 |
| 按标签浏览 | `python scripts/main.py discover "标签" [数量]` | 按领域/标签浏览本地库 |
| 纯本地搜索 | `python scripts/main.py search "关键词" --no-api` | 强制不调用 GitHub API |
| 区域过滤搜索 | `python scripts/main.py search "关键词" --region cn` | 仅国内适用项目（v4.2.0） |

---

## 错误处理

| 错误场景 | 处理方式 |
|---------|---------|
| GITHUB_TOKEN 未配置 | v4.3.0: 走未认证模式（60次/小时），所有功能可用，返回 `token_mode: "unauthenticated"` |
| API 速率限制 (403) | 有Token时提示"认证 API 速率限制"；无Token时提示"未认证限额已用完，配置 Token 可提升至 5000次/小时" |
| Token 无效/过期 (401) | v4.3.0: 返回 `error: invalid_token`，提示更新凭证，本地库功能不受影响 |
| 项目 404 | 标记状态为 deleted，提示"该项目已不可访问" |
| 网络超时 | 重试1次，仍失败则返回本地库结果 |
| 搜索结果为空 | main.py 自动放宽筛选条件后重试 |
| HelloGitHub 月刊解析失败 | 返回空列表，提示"月刊内容解析异常" |
| 阮一峰周刊解析失败 | 返回空列表，提示"周刊内容解析异常" |
| Agent Skills/AI Agents 解析失败 | 返回已获取的部分结果，提示"部分数据源解析异常" |
| GitHub Topics 搜索受限 | 跳过该 topic，继续搜索其他 topic |
| MCP Registry API 失败 | 静默跳过，继续搜索其他数据源 |
| Smithery 无 token 或 API 失败 | 静默跳过，继续搜索其他数据源 |
| Glama 网页解析失败 | 静默跳过，继续搜索其他数据源 |
| Hermes top100.json 获取失败 | 静默跳过，继续搜索其他数据源 |
| 虾评无 token 或 API 失败 | 静默跳过，继续搜索其他数据源 |
| SkillHub 网页解析失败 | 静默跳过，继续搜索其他数据源 |
| 源码扫描超限或失败 | 不影响基本安全评估，跳过源码扫描 |
| 安全评估 GitHub API 超限 | 使用已有数据进行评估，跳过额外 API 调用 |
| 区域过滤后结果为空 | 提示用户尝试 `--region all` 查看全部结果 |

---

## 数据来源

1. **本地库** (`data/projects_db.json`): Agent 直接读取，语义匹配，优先展示 ✅
2. **GitHub Search API**: `main.py search` 调用，实时搜索 ⏳
3. **GitHub Trending**: `main.py trending` 独立调用，按需使用 ⏳
4. **HelloGitHub 社区精选**: `main.py hellogithub` 调用，中文人工推荐 📖
5. **阮一峰周刊**: `main.py ruanyf` 调用，阮一峰科技爱好者周刊项目推荐 📰
6. **Awesome 列表**: `main.py awesome` 调用，按领域发现精选清单 📋
7. **Awesome Agent Skills**: `main.py agent` 调用，跨平台技能/MCP/工具目录 🤖
8. **Awesome AI Agents**: `main.py agent` 调用，AI agent 框架/平台列表 🤖
9. **GitHub Topics**: `main.py agent` 调用，按 topic 搜索 agent 相关仓库 🤖
10. **MCP Registry**（v4.0.0）: `main.py agent` 调用，官方 MCP 注册中心 🌐
11. **Smithery**（v4.0.0）: `main.py agent` 调用，MCP 服务器平台（需 token） 🌐
12. **Glama MCP**（v4.0.0）: `main.py agent` 调用，MCP 服务器目录 🌐
13. **Hermes Skills Hub**（v4.1.0）: `main.py agent` 调用，agentskills.io 验证技能榜 🌐
14. **虾评**（v4.1.0）: `main.py agent` 调用，Agent 技能评测平台（需 API Key） 🌐
15. **腾讯 SkillHub**（v4.1.0）: `main.py agent` 调用，OpenClaw 生态技能市场 🌐
16. **广义搜索**（v4.1.0）: `main.py agent` 调用，GitHub 广义搜索+适配检测

---

## 文件结构
```
github-project-search/
├── SKILL.md                    # 本文件
├── data/
│   └── projects_db.json        # 本地项目库（Agent直接读取）
├── scripts/
│   ├── main.py                 # 核心执行脚本
│   └── radar_chart.py          # 雷达图生成脚本（格式F）
└── references/
    ├── tag-guide.md            # 标签语义匹配指南
    ├── output-templates.md     # 输出格式模板
    └── filter-rules.md         # 筛选规则说明
```

---

## 使用示例

**示例 1: 搜索项目**
```
用户: 找一下 Python 的量化交易工具
→ 阶段1: 搜索类, 关键词="量化交易", 语言="python"
→ 阶段2A: Agent读取 projects_db.json，语义匹配"量化交易""金融"等
→ 阶段2B: 执行 main.py search "量化交易" python
→ 阶段3: 解析 merged 数组
→ 阶段4: 格式A快速列表
```

**示例 1b: 自然语言搜索**
```
用户: 我想找一个Python的Web框架来开发后端API服务
→ 阶段1: 搜索类, 提取核心词="Python Web框架 后端 API", 语言="python"
→ 阶段2A: Agent读取 projects_db.json，语义匹配"Web框架""API""后端"
→ 阶段2B: 执行 main.py search "Python的Web框架来开发后端API服务" python
         → expand_keywords 自动转换: "web framework backend server Python API"
→ 阶段3: 解析 merged 数组
→ 阶段4: 格式A快速列表
```

**示例 2: 分析项目**
```
用户: 分析一下 vnpy
→ 阶段1: 分析类, repo="vnpy/vnpy"
→ 阶段2: 执行 main.py analyze vnpy/vnpy
→ 阶段3: 解析 analyze JSON（含 project_type, languages_summary）
→ 阶段4: 格式B详细卡片 + 格式D趋势（star_per_day估算）
```

**示例 3: 查看 Trending（独立命令）**
```
用户: 最近有什么热门的 Python 项目
→ 阶段1: Trending类
→ 阶段2: 执行 main.py trending python
→ 阶段3: 解析结果
→ 阶段4: 格式A列表
```

**示例 4: HelloGitHub 社区精选**
```
用户: HelloGitHub 有推荐的游戏开发项目吗
→ 阶段1: 社区精选类, 关键词="游戏"
→ 阶段2: 执行 main.py hellogithub "游戏" 5
→ 阶段3: 解析返回的 projects 数组
→ 阶段4: 格式A列表，标注"第N期推荐"
```

**示例 4b: 阮一峰周刊推荐**
```
用户: 阮一峰周刊最近有什么好用的工具推荐
→ 阶段1: 社区精选类, 关键词="工具"
→ 阶段2: 执行 main.py ruanyf "工具" 10
→ 阶段3: 解析返回的 projects 数组（来自「工具」和「AI 相关」板块）
→ 阶段4: 格式A列表，标注"第N期·工具/AI相关"
```

**示例 5: Awesome 列表发现**
```
用户: 有哪些 deep-learning 的 awesome 列表
→ 阶段1: 领域发现类, 关键词="deep-learning"
→ 阶段2: 执行 main.py awesome "deep-learning"
→ 阶段3: 解析返回的 lists 数组
→ 阶段4: Awesome 列表格式，展示仓库名、⭐数、简介
```

**示例 5b: 智能体技能搜索**
```
用户: 有没有 MCP server 可以连接数据库
→ 阶段1: 智能体技能/工具类, 关键词="MCP database", mode="all"
→ 阶段2: 执行 main.py agent "MCP database"
→ 阶段3: 解析返回的 projects 数组，每个项目标注 is_skill/agent_integration/standalone
→ 阶段4: 格式A列表 + 分类标签（🏷️技能/🔌可接入/🖥️独立可用）
```

**示例 5c: 可独立使用的 agent 工具**
```
用户: 我不想接入 agent，有没有能直接用的 AI 工具
→ 阶段1: 智能体技能/工具类, 关键词="", mode="standalone"
→ 阶段2: 执行 main.py agent "" standalone
→ 阶段3: 过滤 is_skill=False 且 standalone=True 的项目
→ 阶段4: 格式A列表，仅展示🖥️独立可用的项目
```

**示例 5d: 区域过滤（v4.2.0）**
```
用户: 我在国内，没有VPN，帮我找能用的 agent 技能
→ 阶段1: 智能体技能/工具类, 关键词="agent", mode="all", region="cn"
→ 阶段2: 执行 main.py agent "agent" all --region cn
→ 阶段3: 过滤掉 region="international" 的项目，仅保留 domestic + universal
→ 阶段4: 格式A列表 + 区域标签（🇨🇳国内/🌐通用）
```

**示例 6: 学习-重写模式**
```
用户: 我想找一个简单的Python项目，用Rust重写来练手
→ 阶段1: 学习类(rewrite), 关键词="Python"
→ 阶段2: 执行 main.py learning rewrite "Python" python
→ 阶段3: 解析 merged 数组，按 _learning_score 排序
→ 阶段4: 格式G（rewrite），优先展示单语言、小代码量项目
```

**示例 7: 学习-贡献模式**
```
用户: 我想参与开源项目提PR，有推荐吗
→ 阶段1: 学习类(contribute), 关键词=""(无特定领域)
→ 阶段2: 执行 main.py learning contribute ""
→ 阶段3: 解析 merged 数组，按 _learning_score 排序
→ 阶段4: 格式G（contribute），展示有 good-first-issue 的活跃项目
```

**示例 8: 信任评估**
```
用户: 这个项目靠谱吗 m-ahmed-elbeskeri/Starguard
→ 阶段1: 信任评估类
→ 阶段2: 执行 main.py trust m-ahmed-elbeskeri/Starguard
→ 阶段3: 解析 trust_score、trust_badge、各维度分数
→ 阶段4: 展示信任评分卡片 + 风险提示
```

**示例 9: 分析项目（自动包含信任评估）**
```
用户: 分析一下 microsoft/markitdown
→ 阶段1: 分析类
→ 阶段2: 执行 main.py analyze microsoft/markitdown
→ 阶段3: 解析结果（已自动包含 trust_assessment 字段 + deepwiki_url + zread_url）
→ 阶段4: 格式B详细卡片 + 信任评估徽章 + 风险警告 + 深度阅读链接
```

**示例 10: 生成仓库文档**
```
用户: 帮我快速了解 vercel/next.js 这个项目
→ 阶段1: 理解类（快速了解项目）
→ 阶段2: 执行 main.py docs vercel/next.js
→ 阶段3: 解析 tech_stack / key_modules / quick_start
→ 阶段4: 输出技术栈 + 模块结构 + Quick Start + DeepWiki/Zread 链接
```