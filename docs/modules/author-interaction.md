# 作者交互模块

## 模块职责

作者交互模块负责处理用户主动输入进入项目上下文前的边界检查。第一阶段重点是 AI 评判用户输入是否合理，避免过于模糊、提前泄露伏笔或破坏已有设定的内容直接写入项目。

## 入口文件

- `backend/app/services/input_review.py`：输入评判服务，组装项目上下文并调用审核模型。
- `backend/app/api/routes/projects.py`：`/api/projects/input-review` 和 `/api/projects/{project_id}/input-review`。
- `backend/app/services/model_provider.py`：`review_user_input` provider 方法。
- `frontend/src/api/client.ts`：输入评判 API client。
- `frontend/src/App.tsx`：在创建项目和加入作者灵感前调用评判。
- `frontend/src/components/ChapterEditor.tsx`：展示最近一次输入评判结果。

## 核心流程

### 项目想法

1. 用户输入小说想法并点击生成项目。
2. 前端先调用 `POST /api/projects/input-review`。
3. 结果为 `block` 时停止创建，并展示原因和建议。
4. 结果为 `pass` 或 `warning` 时继续走原有项目创建流程。

### 作者灵感

1. 用户在右侧模块栏输入作者灵感。
2. 前端先调用 `POST /api/projects/{project_id}/input-review`，类型为 `inspiration`。
3. 后端组装项目定位、世界观、主线、角色、已采纳摘要和伏笔作为评判上下文。
4. 结果为 `block` 时不写入灵感；其他结果继续写入。

## 数据和状态

输入评判结果不落库，当前只保存在前端状态中展示最近一次结果：

- `decision`：`pass`、`warning`、`block`。
- `reason`：原因。
- `suggestions`：修改建议。
- `input_kind`：输入类型。
- `project_id`：项目内输入时存在。

## 当前边界

- 不自动改写用户输入。
- 不持久化评判历史。
- 不处理已采纳章节重写或正文修改评判，因为第一版暂不开放用户修改已采纳章节的完整流程。
- `warning` 当前继续写入，只展示风险；后续可加用户确认弹窗。

## 测试方式

优先运行：

```powershell
python -m pytest backend/tests/test_input_review.py -v
npm test -- --run src/App.test.tsx
```

## 后续修改注意事项

- 扩展到正文修改前，必须先设计已采纳章节修改、后续章节影响判断和上下文重建边界。
- 不要让 `block` 输入写入项目正式上下文。
- 如果评判结果需要落库，应区分“用户审美偏好”和“事实/设定冲突”，避免污染后续 eval 或微调样本。
