# 结构化记忆模块

## 模块职责

结构化记忆模块负责保存长篇生成中需要长期稳定引用的正式事实，避免所有记忆都挤在章节摘要里。

第一阶段包含：

- 角色当前时期/阶段。
- 事件时间线。
- 世界观规则表。

本模块只记录已采纳内容形成的正式记忆。候选生成结果、候选摘要和候选判断不得直接污染正式记忆。

## 入口文件

- `backend/app/models/character.py`：角色卡和当前时期字段。
- `backend/app/models/memory.py`：事件时间线和世界观规则模型。
- `backend/app/repositories/projects.py`：项目创建时初始化角色时期和基础世界观规则。
- `backend/app/agent/chapter_graph.py`：`load_context` 读取结构化记忆进入上下文包。
- `backend/app/services/chapter_service.py`：章节采纳后写入正式结构化记忆。
- `frontend/src/components/ModulePanel.tsx`：右侧模块栏展示角色时期、事件时间线和世界观规则。
- `frontend/src/components/AgentWorkspace.tsx`：后台上下文展示结构化记忆。

## 核心流程

1. 创建项目时，为角色初始化 `period_stage="初始时期"`，并用角色当前目标作为初始时期摘要。
2. 创建项目时，把项目世界观写入基础 `WorldRule`。
3. 生成章节时，`load_context` 加载角色时期、事件时间线和世界观规则；这些正式记忆会先参与 RAG 召回，再由上下文预算管理裁剪实际进入 prompt 的内容。
4. `persist_candidate_result` 仍然只保存候选正文、候选摘要、审核发现和任务快照。
5. 用户采纳或全自动采纳章节时，`accept_chapter_candidate` 写入正式记忆：
   - 根据章节摘要创建 `StoryEvent`。
   - 根据章节摘要创建章节来源的 `WorldRule` 约束记录。
   - 根据 `judge_character_period` 的判断结果更新角色时期摘要和来源章节。

## 数据和状态

### 角色时期

`Character` 额外保存：

- `period_stage`：当前时期/阶段名。
- `period_summary`：当前阶段下的目标、记忆、关系或状态摘要。
- `period_source_chapter_id`：最后一次改变时期信息的来源章节。

### 事件时间线

`StoryEvent` 保存：

- 事件标题和摘要。
- 来源章节。
- 涉及角色、地点和后果。

### 世界观规则

`WorldRule` 保存：

- 规则内容。
- 限制和例外。
- 来源章节。
- 当前状态。

## 扩展点

后续可以增加：

- 地点、物品、阵营等更多结构化实体。
- 用户逐条确认记忆变更。
- 结构化记忆编辑和废弃。
- RAG 检索对事件、规则、角色时期的召回质量优化。
- Eval 对摘要事实保留率和冲突检出率的评估。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_structured_memory.py -v
npm test -- --run src/App.test.tsx
```

相关生成流程验证：

```powershell
python -m pytest backend/tests/test_chapter_generation.py backend/tests/test_auto_generation.py -v
```

## 后续修改注意事项

- 正式记忆只能通过采纳路径写入，不能在候选保存节点直接写入。
- 新增记忆实体时，必须同步项目 API schema、前端类型和后台上下文展示。
- `load_context` 应读取结构化记忆，但必须交给 RAG 和上下文预算管理决定实际进入 prompt 的事件、规则等可变内容。
- 事件和规则当前是第一阶段基础实现，后续需要补更细的检索字段和评测样例。

## 2026-07-19 更新

- 采纳章节时会把 `judge_foreshadowing.foreshadowing_decisions` 写入正式 `ForeshadowingItem` 表。
- `new` 写为 `planted`，`advanced` 写为 `advanced`，`resolved` 写为 `recovered`；`notes` 保留为伏笔备注。
- 正式伏笔仍不能在 `persist_candidate_result` 候选保存阶段写入，避免未采纳内容污染长期记忆。
- 右侧模块栏的“伏笔记录”默认展开，展示内容、状态和备注；没有记录时显示空状态。
