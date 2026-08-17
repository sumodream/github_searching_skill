# 标签语义匹配指南

## 设计原则
- **扁平化**: 无父子层级，所有标签平级
- **语义匹配**: AI 根据关键词推断相关标签，大覆盖小
- **多标签**: 一个项目可挂多个标签，避免以偏概全
- **灵活扩展**: 新标签随时添加，无需维护层级关系

## 现有标签库

### 技术形式（来自飞书表"形式"字段）
```
网页, 应用, docker, git, python库, 模型, 资源, 开源项目, 
Shell, JavaScript, 插件, 网站, 开源, javascript, 不开源, Python, Kotlin
```

### 领域类型（来自飞书表"类型"字段 + AI 扩展）
```
金融, 即时通讯, 低代码, 量化交易, 系统工具, 浏览器扩展, 
数据归档, 云桌面, 舆情分析, SSH工具, AI应用, Agent框架, 
多Agent, 爬虫, Web服务, 自托管, 数据库, 可视化, 
代码生成, 文档工具, 测试工具, 安全工具, 运维工具
```

### 部署方式（AI 扩展）
```
docker部署, 一键安装, 本地部署, 云端部署, 自托管, 
pip安装, npm安装, 源码编译
```

### 技术栈（AI 扩展）
```
React, Vue, Angular, Node.js, Django, Flask, FastAPI, 
Spring, Go, Rust, C++, 机器学习, 深度学习, NLP, 计算机视觉
```

## 语义匹配规则

### 规则 1: 关键词 → 标签扩展

| 用户关键词 | 匹配标签 |
|-----------|---------|
| 金融 | 金融, 金融终端, 量化交易, 金融数据源, 加密货币 |
| AI | AI应用, Agent框架, 多Agent, LLM应用, RAG, 模型 |
| 爬虫 | 爬虫, 数据采集, 网络请求, 自动化 |
| 部署 | docker部署, 一键安装, 本地部署, 自托管 |
| 聊天 | 即时通讯, 多Agent, Web服务 |
| 数据 | 数据归档, 数据库, 可视化, 量化交易 |
| 安全 | 安全工具, SSH工具, 系统工具 |
| 低代码 | 低代码, 代码生成, 可视化 |

### 规则 2: 组合查询扩展

| 用户输入 | 推断意图 | 匹配标签组合 |
|---------|---------|------------|
| "Python 金融工具" | Python + 金融 | python库, Python, 金融, 量化交易, 金融终端 |
| "docker 部署的 AI 项目" | AI + docker部署 | AI应用, Agent框架, docker部署, 自托管 |
| "开源的即时通讯" | 开源 + 即时通讯 | 开源, 即时通讯, Web服务, 应用 |
| "低代码平台" | 低代码 | 低代码, 代码生成, 可视化, 网页 |
| "数据采集工具" | 数据采集 | 爬虫, 数据归档, 系统工具, python库 |

### 规则 3: 否定排除

| 用户输入 | 排除标签 |
|---------|---------|
| "不要网页版的" | 排除: 网页, 网站 |
| "只要 Python 的" | 排除: JavaScript, Kotlin, Go, Rust... |
| "需要开源的" | 排除: 不开源 |
| "要能 docker 部署的" | 排除: 无 docker部署 标签的项目 |

## 标签匹配算法

```
function matchTags(userQuery, projectTags):
  score = 0
  
  // 1. 精确匹配
  for tag in projectTags:
    if tag in userQuery:
      score += 10
  
  // 2. 语义扩展匹配
  expandedTags = expandKeywords(userQuery)  // AI 扩展
  for tag in projectTags:
    if tag in expandedTags:
      score += 5
  
  // 3. 场景匹配（飞书表的"适合场景"字段）
  if project.scene in userQuery:
    score += 3
  
  // 4. 名称匹配
  if project.name in userQuery:
    score += 2
  
  return score
```

## 标签维护建议

1. **定期审查**: 每月检查标签覆盖度，补充缺失标签
2. **用户反馈**: 根据用户搜索失败案例，新增标签
3. **热点跟踪**: 新兴技术领域及时添加标签（如 MCP、AI Agent 等）
4. **去重合并**: 发现同义词标签时合并（如 "JavaScript" 和 "javascript"）

## 注意事项

1. 标签匹配以**召回率优先**，宁可多匹配不要漏匹配
2. 输出时按匹配分数排序，最相关的排在前面
3. 标签为空的项目，通过名称和场景字段补充匹配
4. 新入库项目（热点榜/GitHub搜索）AI 自动打标签，可能不准确，需人工复核
