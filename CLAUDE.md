# 项目规则

## 记忆系统（最高优先级）

你必须在每次会话中遵守以下记忆管理规则：

### 启动时
1. **检查记忆文件是否存在**（最高优先级）：
   - 检查 `docs/` 目录是否存在，不存在则创建
   - 检查以下文件是否存在，**不存在则按下方模板自动创建**，并告知用户"已自动初始化项目记忆系统"：
     - `docs/ARCHITECTURE.md`
     - `docs/PROGRESS.md`
     - `docs/DECISIONS.md`
     - `docs/ISSUES.md` 
     - `docs/LOG.md`
     - `docs/CHANGELOG.md`
   - 如果 `.gitignore` 不存在，按项目类型自动创建（排除 IDE、虚拟环境、敏感文件）
   - 如果 `.gitignore` 中缺少对敏感文件的排除规则，自动补充
2. 读取上述所有记忆文件，了解项目当前状态
3. 运行 `git log --oneline -20` 了解最近的提交历史
4. 运行 `git status` 了解当前工作区状态
5. 运行 `git branch -a` 了解分支结构

### 文件不存在时的自动创建模板

当检测到文件缺失时，使用以下模板创建（根据项目实际情况填充）：

**docs/ARCHITECTURE.md（缺失时创建）：**

    # 项目架构

    > 最后更新：[当前日期]
    > 本文件由 Agent 自动初始化，请根据实际情况补充

    ## 系统概览
    [待补充：用一段话描述这个项目是做什么的]

    ## 技术栈
    | 层级 | 技术 | 用途 |
    |---|---|---|
    | [待补充] | | |

    ## 目录结构
    [根据当前项目文件自动生成]

    ## 核心模块关系
    [待补充]

**docs/PROGRESS.md（缺失时创建）：**

    # 项目进度

    > 最后更新：[当前日期]
    > 本文件由 Agent 自动初始化

    ## 进行中
    - [ ] 当前无进行中的任务

    ## 待办
    - [ ] [根据用户需求或项目状态推断]

    ## 已完成
    - [x] [[当前日期]] 项目记忆系统初始化

**docs/DECISIONS.md（缺失时创建）：**

    # 技术决策记录

    > 记录所有重要的技术决策，确保项目方向一致

    ---
    （暂无记录，后续开发过程中自动追加）

**docs/ISSUES.md（缺失时创建）：**

    # 问题记录

    > 记录开发中遇到的 bug、坑、注意事项

    ---
    （暂无记录，后续开发过程中自动追加）

**docs/LOG.md（缺失时创建）：**

    # 会话日志

    > 每次会话结束前追加一条记录

    ---

    ## [当前日期] 会话

    **做了什么**：
    - 初始化项目记忆系统
    - 创建 docs/ 目录及所有记忆文件

    **下次继续**：
    - [根据用户需求填写]

**docs/CHANGELOG.md（缺失时创建）：**

    # 变更日志

    > 基于 Git 提交历史自动维护

    格式基于 [Keep a Changelog](https://keepachangelog.com/)

    ---

    ## [Unreleased]

    ### Added
    - [[当前日期]] 初始化项目记忆系统

### 工作过程中
- 每完成一个有意义的任务，立即更新 `docs/PROGRESS.md`
- 每做出一个技术决策（选型、架构、算法等），立即追加到 `docs/DECISIONS.md`
- 遇到 bug 或坑，记录到 `docs/ISSUES.md`
- 发现新的文件/模块关系，更新 `docs/ARCHITECTURE.md`
- 每完成一个功能模块，主动执行 `git add` + `git commit`（遵循提交规范）
- 每次 git commit 后，在 `docs/CHANGELOG.md` 的 `[Unreleased]` 下追加对应条目
- 如果用户明确要求推送，执行 `git push`

### 结束前
- 确认 `docs/PROGRESS.md` 的"进行中"和"待办"状态是最新的
- 在 `docs/LOG.md` 追加本次会话摘要（日期 + 做了什么 + 下一步 + git commit hash）
- 确认 `docs/CHANGELOG.md` 已记录本次会话的所有变更
- 检查是否有未提交的修改，提醒用户是否需要提交

### 记录格式要求
- 用简洁的中文
- 日期用 YYYY-MM-DD 格式
- 决策记录必须包含"为什么"，不能只记"是什么"
- 进度记录必须具体到文件路径和函数名

## Git 版本管理规范

### 分支策略
- `main` — 稳定版本，只通过 PR 合并
- `develop` — 开发主线，日常开发在此分支
- `feature/[功能名]` — 新功能分支，从 develop 创建
- `fix/[问题名]` — 修复分支，从 develop 创建
- `docs/[文档名]` — 文档更新分支

### 提交规范（Conventional Commits）
- `feat: 简短描述` — 新功能
- `fix: 简短描述` — Bug 修复
- `docs: 简短描述` — 文档更新
- `refactor: 简短描述` — 代码重构（不改变功能）
- `style: 简短描述` — 代码格式调整
- `test: 简短描述` — 测试相关
- `chore: 简短描述` — 构建/工具链/依赖更新

### 提交时机
- 完成一个完整的功能模块后立即提交
- 修复一个 bug 后立即提交
- 文档更新后立即提交
- 不要积攒大量修改后一次性提交
- 每次提交只做一件事，保持原子性

### 安全规则（严格遵守）
- 绝不执行 `git push --force` 到 main/master 分支
- 执行 `git reset --hard` 前必须与用户确认
- 绝不跳过 git hooks（不使用 `--no-verify`），除非用户明确要求
- 提交前检查 `.gitignore`，不提交敏感文件（.env, credentials, 密钥等）
- 推送前确认当前分支和目标分支

### 远程仓库
- 远程仓库地址：[https://github.com/WuChangqing1/ai-piano-companion.git]
- 默认推送分支：develop
- PR 目标分支：main

## 项目基本信息
- 项目名称：AI 琴伴（AI Piano Companion）
- 技术栈：FastAPI + SQLite + Flutter
- 开发语言：Python 3.11 / Dart 3.3+
- 包管理器：pip（后端）/ pub（前端）
- 虚拟环境：Conda 环境 `AIqinban`（Python 3.11，Miniconda）
- 远程仓库：[https://github.com/WuChangqing1/ai-piano-companion.git]

## 虚拟环境规范（最高优先级）

**所有 Python 命令必须在 Conda 环境 `AIqinban` 中运行，禁止使用全局环境。**

### 启动规则（每次会话必须执行）
1. 检查 Conda 环境是否存在：`conda env list | grep AIqinban`
2. 如不存在，创建：`conda create -n AIqinban python=3.11 -y`
3. **所有 Python 命令通过以下方式执行**：
   - 方式一（激活）：`conda activate AIqinban && <command>`
   - 方式二（推荐）：`conda run -n AIqinban python <script>` 或 `conda run -n AIqinban pip install <pkg>`
4. 安装依赖：`conda run -n AIqinban pip install -r backend/requirements.txt`
5. 后续所有 `python`、`pip`、`uvicorn` 命令均在 `AIqinban` 环境中执行

### 多环境管理
- **主环境** `AIqinban`：FastAPI 后端开发 + AI 模型（MediaPipe / basic-pitch / Oemer）——默认
- **模型环境** `AIqinban-models`（按需创建）：CosyVoice（PyTorch 全家桶，~3GB）
- 切换环境时明确告知用户当前使用的环境

### 规范
- 新增 Python 依赖后立即更新 `backend/requirements.txt`
- Conda 环境目录不在项目内，不会被提交到 git
- basic-pitch 走 ONNX 后端（轻量），不安装 TensorFlow

## 代码规范
- 文件名：驼峰命名法
- 变量名：不要使用中文拼音，使用英文易懂的单词或易懂的缩写
- 确保代码写完后是可维护、可扩展的