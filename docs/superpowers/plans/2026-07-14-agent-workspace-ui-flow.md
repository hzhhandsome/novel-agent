# Agent Workspace UI Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update the real frontend to match the approved Agent backstage mockup: middle editor with top auto mode toolbar, right module panel, bottom Agent backstage, flow tabs, context tab, and combined result/update cards.

**Architecture:** This change is frontend-only. `App` keeps existing data loading and passes `project` into `AgentWorkspace`; `ChapterEditor` owns the top auto-mode toolbar display; `AgentWorkspace` derives display sections from `GenerationTask`, `Project`, and current chapter data without changing backend APIs.

**Tech Stack:** React 18, TypeScript, Vite, Vitest, Testing Library, existing REST API types.

---

## Scope

This plan intentionally does not change backend LangGraph nodes. It changes how the current generation process is displayed in the cockpit. A later backend plan can expand the actual LangGraph to the full 11-node workflow.

## Files

- Modify: `frontend/src/App.tsx`
  - Pass `project` into `AgentWorkspace`.
- Modify: `frontend/src/components/ChapterEditor.tsx`
  - Add the top auto-mode toolbar above the chapter title/content.
- Modify: `frontend/src/components/AgentWorkspace.tsx`
  - Replace the four-column summary grid with tabbed backstage UI.
  - Add flow node list with click-to-show detail panel.
  - Add context tab.
  - Add combined result/update tab with expandable cards.
- Modify: `frontend/src/styles.css`
  - Restore physical layout: left chapter sidebar, middle editor, right module panel, bottom backstage only under middle editor.
  - Add styles for auto toolbar, backstage tabs, flow details, context cards, result/update cards.
- Modify: `frontend/src/App.test.tsx`
  - Add tests for layout labels, tabs, context display, result/update cards, and flow detail switching.

---

### Task 1: Add Frontend Tests For Approved Layout And Backstage Tabs

**Files:**
- Modify: `frontend/src/App.test.tsx`

- [ ] **Step 1: Write failing tests**

Add imports if needed and extend `makeProject()` to include sample module data:

```tsx
function makeProject() {
  return {
    id: 42,
    title: "废城修书人",
    idea: "一个失忆修书人在废城里修补会改变现实的书",
    positioning: "悬念长篇",
    worldview: "书会改写现实",
    main_plot: "主角追查书的规则",
    chapters: [
      {
        id: 100,
        project_id: 42,
        number: 1,
        title: "异常出现",
        status: "generated",
        content: null,
        generated_content: "雨水敲在废城图书馆的穹顶上。",
        summary: "主角确认修书会改写现实。",
      },
    ],
    characters: [
      {
        id: 1,
        name: "修书人",
        role: "主角",
        personality: "克制",
        current_goal: "查明修书代价",
        key_memories: "遗忘母亲声音",
        relationships: null,
        writing_notes: null,
      },
    ],
    foreshadowing_items: [
      {
        id: 1,
        content: "手背页码从 17 变为 16",
        status: "active",
        notes: null,
      },
    ],
    inspirations: [{ id: 1, content: "后续出现一本会写出未来的书", applied: false }],
  };
}
```

Add tests:

```tsx
it("places auto mode controls in the editor top toolbar", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify([makeProject()]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  render(<App />);

  expect(await screen.findByText("全自动")).toBeInTheDocument();
  expect(screen.getByText("开启后自动生成、审核、更新上下文并进入下一章")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "暂停" })).toBeInTheDocument();
});

it("shows backstage flow context and combined result tabs", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify([makeProject()]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  render(<App />);

  expect(await screen.findByRole("tab", { name: "流程节点" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "上下文" })).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: "结果与更新" })).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "上下文" }));
  expect(screen.getByText("悬念长篇")).toBeInTheDocument();
  expect(screen.getByText("书会改写现实")).toBeInTheDocument();
  expect(screen.getByText("手背页码从 17 变为 16")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("tab", { name: "结果与更新" }));
  expect(screen.getByText("审核结果")).toBeInTheDocument();
  expect(screen.getByText("章节摘要")).toBeInTheDocument();
  expect(screen.getByText("伏笔变化")).toBeInTheDocument();
  expect(screen.getByText("角色卡变化")).toBeInTheDocument();
  expect(screen.getByText("后续线路变化")).toBeInTheDocument();
  expect(screen.getByText("入库动作")).toBeInTheDocument();
});

it("switches the backstage detail when a flow node is clicked", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify([makeProject()]), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );

  render(<App />);

  expect(await screen.findByText("1. 加载上下文")).toBeInTheDocument();
  expect(screen.getByText("读取本章生成所需的正式上下文包")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: /9.*判断后续线路调整/ }));

  expect(screen.getByText("根据本章实际结果判断后续章节名和线路是否需要改变")).toBeInTheDocument();
  expect(screen.getByText(/第 4 章标题/)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
cd frontend
npm test -- --run
```

Expected: FAIL because `全自动`, `上下文`, `结果与更新`, and flow detail switching are not implemented.

---

### Task 2: Implement Editor Top Auto-Mode Toolbar

**Files:**
- Modify: `frontend/src/components/ChapterEditor.tsx`

- [ ] **Step 1: Add the toolbar above the chapter title**

Inside the chapter branch, before the existing `.editor-toolbar`, insert:

```tsx
<div className="top-generation-toolbar" aria-label="生成控制">
  <div className="auto-mode-control">
    <span className="auto-switch" aria-hidden="true" />
    <div>
      <strong>全自动</strong>
      <span>开启后自动生成、审核、更新上下文并进入下一章</span>
    </div>
  </div>
  <div className="toolbar-actions">
    <span className="status-pill">运行中</span>
    <button type="button" className="primary-button" onClick={onGenerate} disabled={busy} title="暂停">
      <span>暂停</span>
    </button>
    <button type="button" className="secondary-button" onClick={onGenerate} disabled={busy} title="重新生成">
      <span>重新生成</span>
    </button>
    <button type="button" className="secondary-button" disabled={busy} title="生成记录">
      <span>生成记录</span>
    </button>
  </div>
</div>
```

Keep the existing save/generate toolbar for now; the new toolbar is visual and matches the approved mockup. Real pause/auto behavior is out of scope for this frontend-only task.

- [ ] **Step 2: Run targeted test**

Run:

```powershell
cd frontend
npm test -- --run
```

Expected: The auto-mode toolbar test moves toward passing; backstage tests still fail.

---

### Task 3: Implement AgentWorkspace Tabs And Flow Detail Switching

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AgentWorkspace.tsx`

- [ ] **Step 1: Pass project to AgentWorkspace**

Change the import:

```tsx
import type { Chapter, GenerationTask, Project } from "./types";
```

Change the component usage:

```tsx
<AgentWorkspace project={project} task={task} busy={busy} onRetry={handleRetry} />
```

- [ ] **Step 2: Replace AgentWorkspace implementation**

Use this component shape:

```tsx
import { AlertCircle, ChevronDown, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";
import type { GenerationTask, Project } from "../types";

interface AgentWorkspaceProps {
  project: Project | null;
  task: GenerationTask | null;
  busy: boolean;
  onRetry: () => void;
}

type WorkspaceTab = "flow" | "context" | "result";
type FlowKey =
  | "context"
  | "line"
  | "prompt"
  | "draft"
  | "summary"
  | "audit"
  | "foreshadow"
  | "character"
  | "future"
  | "candidate"
  | "commit";

const flowNodes: Array<{
  key: FlowKey;
  index: number;
  label: string;
  summary: string;
  details: Array<[string, string]>;
}> = [
  {
    key: "context",
    index: 1,
    label: "加载上下文",
    summary: "读取本章生成所需的正式上下文包",
    details: [
      ["加载内容", "小说定位、风格、世界观、主线、角色卡、章节摘要、伏笔和作者灵感。"],
      ["说明", "完整上下文可随时切换到“上下文”tab 查看。"],
    ],
  },
  {
    key: "line",
    index: 2,
    label: "确认本章线路",
    summary: "确认本章必须完成什么",
    details: [["本章目标", "确认修书会改写现实，并付出明确记忆代价。"]],
  },
  {
    key: "prompt",
    index: 3,
    label: "生成本章提示包",
    summary: "整理目标、限制、角色状态和伏笔",
    details: [["提示包", "包含目标、限制、风格约束、角色状态、伏笔边界和禁止泄露项。"]],
  },
  {
    key: "draft",
    index: 4,
    label: "生成章节正文",
    summary: "生成候选正文并显示在正文区",
    details: [["输出位置", "中间列：正文工作区。"]],
  },
  {
    key: "summary",
    index: 5,
    label: "章节摘要",
    summary: "提炼本章正式上下文需要保留的事实",
    details: [["用途", "用于后续生成和上下文压缩。"]],
  },
  {
    key: "audit",
    index: 6,
    label: "审核是否偏离",
    summary: "检查是否偏离目标、主线、人设、世界观和前文",
    details: [["审核结果", "未发现阻塞问题。"]],
  },
  {
    key: "foreshadow",
    index: 7,
    label: "伏笔判断",
    summary: "判断新增、推进、回收或提前泄露伏笔",
    details: [["变化", "新增书页批注，推进手背页码。"]],
  },
  {
    key: "character",
    index: 8,
    label: "角色时期卡判断",
    summary: "判断是否需要新建或更新角色时期卡",
    details: [["变化", "更新主角目标和记忆状态。"]],
  },
  {
    key: "future",
    index: 9,
    label: "判断后续线路调整",
    summary: "根据本章实际结果判断后续章节名和线路是否需要改变",
    details: [
      ["第 4 章标题", "规则代价 -> 第一次付出代价。"],
      ["原因", "本章已经写出第一次明确记忆代价。"],
    ],
  },
  {
    key: "candidate",
    index: 10,
    label: "输出候选结果",
    summary: "汇总正文、摘要、审核、伏笔、角色卡和后续线路建议",
    details: [["候选内容", "正文、摘要、审核发现、伏笔建议、角色卡建议和线路建议。"]],
  },
  {
    key: "commit",
    index: 11,
    label: "自动写入正式上下文",
    summary: "全自动模式下写入正式上下文",
    details: [["写入内容", "正文、摘要、状态变化、伏笔记录和章节规划调整。"]],
  },
];
```

Render:

```tsx
export function AgentWorkspace({ project, task, busy, onRetry }: AgentWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("flow");
  const [activeFlow, setActiveFlow] = useState<FlowKey>("context");
  const failed = task?.status === "failed";
  const activeNode = flowNodes.find((node) => node.key === activeFlow) ?? flowNodes[0];
  const currentChapter = task?.chapter ?? project?.chapters[0] ?? null;

  const contextCards = useMemo(
    () => [
      ["小说定位", project?.positioning ?? "未创建项目"],
      ["风格", "克制、悬疑、细节推动，章节结尾保留清晰钩子。"],
      ["世界观", project?.worldview ?? ""],
      ["主线", project?.main_plot ?? ""],
      ["当前角色时期卡", project?.characters.map((item) => `${item.name}：${item.current_goal ?? ""}`).join("；") ?? ""],
      ["已采纳章节摘要", project?.chapters.map((chapter) => `第 ${chapter.number} 章：${chapter.summary ?? "暂无摘要"}`).join("；") ?? ""],
      ["未回收伏笔", project?.foreshadowing_items.map((item) => item.content).join("；") ?? ""],
      ["作者灵感", project?.inspirations.map((item) => item.content).join("；") ?? ""],
      ["压缩状态", "旧章节正文达到阈值后压缩为摘要；关键设定、角色变化和伏笔保留。"],
    ],
    [project],
  );

  return (
    <section className="agent-workspace" aria-label="Agent 创作后台">
      <div className="backstage-bar">
        <div>
          <h2>Agent 创作后台</h2>
          <span>{task ? `全自动运行 · ${task.status}` : "等待生成"}</span>
        </div>
        {failed ? (
          <button className="secondary-button" type="button" onClick={onRetry} disabled={busy} title="重试">
            <RefreshCw size={16} />
            <span>重试</span>
          </button>
        ) : null}
      </div>

      <div className="backstage-tabs" role="tablist" aria-label="后台视图">
        <button className={activeTab === "flow" ? "tab-button active" : "tab-button"} type="button" role="tab" onClick={() => setActiveTab("flow")}>流程节点</button>
        <button className={activeTab === "context" ? "tab-button active" : "tab-button"} type="button" role="tab" onClick={() => setActiveTab("context")}>上下文</button>
        <button className={activeTab === "result" ? "tab-button active" : "tab-button"} type="button" role="tab" onClick={() => setActiveTab("result")}>结果与更新</button>
      </div>

      {activeTab === "flow" ? (
        <div className="flow-layout">
          <nav className="flow-node-list" aria-label="流程节点">
            {flowNodes.map((node) => (
              <button
                key={node.key}
                type="button"
                className={node.key === activeFlow ? "flow-node active" : "flow-node"}
                onClick={() => setActiveFlow(node.key)}
              >
                <span>{node.index}</span>
                <strong>{node.label}</strong>
              </button>
            ))}
          </nav>
          <article className="flow-detail-card">
            <h3>{`${activeNode.index}. ${activeNode.label}`}</h3>
            <p>{activeNode.summary}</p>
            <div className="detail-card-grid">
              {activeNode.details.map(([title, content]) => (
                <div className="dark-card" key={title}>
                  <h4>{title}</h4>
                  <p>{content}</p>
                </div>
              ))}
            </div>
          </article>
        </div>
      ) : null}

      {activeTab === "context" ? (
        <div className="context-grid">
          {contextCards.map(([title, content]) => (
            <article className="dark-card" key={title}>
              <h3>{title}</h3>
              <p>{content}</p>
            </article>
          ))}
        </div>
      ) : null}

      {activeTab === "result" ? (
        <div className="result-list">
          <details className="result-card" open>
            <summary><strong>审核结果</strong><span>通过</span><span className="status-pill">无阻塞</span></summary>
            <p>{task?.error_message ? <><AlertCircle size={16} /> {task.error_message}</> : "未发现阻塞问题。"}</p>
          </details>
          <details className="result-card changed">
            <summary><strong>章节摘要</strong><span>将写入</span><span className="status-pill warn">有变化</span></summary>
            <p>{currentChapter?.summary ?? "主角第一次修复红封书，确认现实会随修书改变。"}</p>
          </details>
          <details className="result-card changed">
            <summary><strong>伏笔变化</strong><span>新增 / 推进</span><span className="status-pill warn">有变化</span></summary>
            <p>{project?.foreshadowing_items.map((item) => item.content).join("；") || "新增书页批注，推进手背页码。"}</p>
          </details>
          <details className="result-card changed">
            <summary><strong>角色卡变化</strong><span>更新</span><span className="status-pill warn">有变化</span></summary>
            <p>{project?.characters.map((item) => `${item.name}：${item.current_goal ?? ""}`).join("；") || "更新主角目标和记忆状态。"}</p>
          </details>
          <details className="result-card changed">
            <summary><strong>后续线路变化</strong><span>建议调整</span><span className="status-pill warn">有变化</span></summary>
            <p>第 4 章标题：规则代价 -> 第一次付出代价。原因：本章已经实际写出第一次明确记忆代价。</p>
          </details>
          <details className="result-card weak">
            <summary><strong>入库动作</strong><span>已自动写入</span><span className="status-pill">完成</span></summary>
            <p>正文、摘要、角色卡更新、伏笔更新和后续线路调整写入正式上下文；生成记录保留。</p>
          </details>
        </div>
      ) : null}
    </section>
  );
}
```

- [ ] **Step 3: Run tests**

Run:

```powershell
cd frontend
npm test -- --run
```

Expected: Tests fail only for missing CSS/layout assumptions if any; semantic UI tests should pass after this task.

---

### Task 4: Implement Layout And Backstage Styling

**Files:**
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Update physical layout**

Change:

```css
.app-shell {
  display: grid;
  grid-template-columns: 260px minmax(420px, 1fr) 340px;
  grid-template-rows: minmax(0, 1fr) 320px;
  height: 100vh;
  overflow: hidden;
  color: #202124;
}

.sidebar {
  grid-row: 1 / 3;
}

.editor {
  grid-column: 2;
  grid-row: 1;
}

.module-panel {
  grid-column: 3;
  grid-row: 1 / 3;
}

.agent-workspace {
  grid-column: 2;
  grid-row: 2;
}
```

- [ ] **Step 2: Add toolbar and backstage styles**

Append:

```css
.top-generation-toolbar,
.auto-mode-control,
.backstage-bar,
.backstage-tabs,
.flow-node,
.result-card summary {
  display: flex;
  align-items: center;
  gap: 10px;
}

.top-generation-toolbar,
.backstage-bar {
  justify-content: space-between;
}

.top-generation-toolbar {
  margin-bottom: 12px;
  padding: 10px 12px;
  border: 1px solid #d8ddd3;
  border-radius: 8px;
  background: #ffffff;
}

.auto-mode-control span:last-child {
  display: block;
  color: #68716a;
  font-size: 13px;
}

.auto-switch {
  position: relative;
  width: 44px;
  height: 24px;
  flex: 0 0 auto;
  border-radius: 999px;
  background: #317159;
}

.auto-switch::after {
  content: "";
  position: absolute;
  top: 3px;
  right: 3px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: #ffffff;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: #e7f2ed;
  color: #1b5a48;
  font-size: 12px;
}

.status-pill.warn {
  background: #fff3df;
  color: #9a5b18;
}

.agent-workspace {
  padding: 0;
  overflow: hidden;
}

.backstage-bar {
  min-height: 56px;
  padding: 0 16px;
  border-bottom: 1px solid #303832;
}

.backstage-bar h2 {
  margin-bottom: 2px;
}

.backstage-bar span {
  color: #bac4ba;
}

.backstage-tabs {
  padding: 10px 16px;
  border-bottom: 1px solid #303832;
  overflow-x: auto;
}

.tab-button {
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #3f4a42;
  border-radius: 8px;
  background: transparent;
  color: #f5f1e8;
  cursor: pointer;
}

.tab-button.active {
  background: #eaf4ee;
  border-color: #eaf4ee;
  color: #14382e;
}

.flow-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 12px;
  height: calc(100% - 106px);
  padding: 12px 16px 16px;
  overflow: hidden;
}

.flow-node-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
}

.flow-node {
  width: 100%;
  min-height: 42px;
  padding: 8px 10px;
  border: 1px solid #3f4a42;
  border-radius: 8px;
  background: #29312b;
  color: #f5f1e8;
  text-align: left;
  cursor: pointer;
}

.flow-node span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #ebf5ef;
  color: #1c5947;
  font-weight: 700;
  font-size: 12px;
}

.flow-node.active {
  border-color: #d5e8de;
  background: #d5e8de;
  color: #14382e;
}

.flow-detail-card,
.dark-card,
.result-card {
  border: 1px solid #3f4a42;
  border-radius: 8px;
  background: #29312b;
}

.flow-detail-card {
  overflow: auto;
  padding: 12px;
}

.detail-card-grid,
.context-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 10px;
}

.dark-card {
  padding: 12px;
}

.dark-card h3,
.dark-card h4,
.flow-detail-card h3 {
  margin-bottom: 8px;
}

.dark-card p,
.flow-detail-card p,
.result-card p {
  color: #bac4ba;
}

.context-grid,
.result-list {
  padding: 12px 16px 16px;
  overflow: auto;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-card {
  overflow: hidden;
}

.result-card.changed {
  border-color: #d4c27d;
  background: #2f3028;
}

.result-card.weak {
  opacity: 0.72;
}

.result-card summary {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) auto;
  padding: 11px 12px;
  cursor: pointer;
}

.result-card p {
  margin: 0;
  padding: 0 12px 12px;
}
```

- [ ] **Step 3: Run frontend tests**

Run:

```powershell
cd frontend
npm test -- --run
```

Expected: PASS.

---

### Task 5: Verify Build And Update Module Documentation If Needed

**Files:**
- Possibly modify: `docs/modules/generation-flow.md`

- [ ] **Step 1: Run build**

Run:

```powershell
cd frontend
npm run build
```

Expected: PASS.

- [ ] **Step 2: Decide whether module docs need update**

Because this plan does not change backend LangGraph responsibilities, interfaces, state machine, data flow, configuration, or key constraints, `docs/modules/generation-flow.md` does not need an update. If implementation expands backend nodes later, update that document then.

- [ ] **Step 3: Final status check**

Run:

```powershell
git status --short
```

Expected: Code changes in frontend files plus this plan and existing untracked docs/mockup files. Do not commit pure docs unless the user asks; code changes may be committed only after verification if requested.

---

## Self-Review

- Spec coverage: covers editor top auto-mode toolbar, physical layout, Agent backstage flow nodes, context tab, combined result/update tab, and expandable changed cards.
- Placeholder scan: no TODO/TBD placeholders.
- Type consistency: `AgentWorkspace` receives `project`, `task`, `busy`, `onRetry`; `App.tsx` passes the same props. Tab keys and flow keys are explicit TypeScript unions.
