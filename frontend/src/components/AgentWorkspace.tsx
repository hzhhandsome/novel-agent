import { AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Circle, LoaderCircle, RefreshCw, XCircle } from "lucide-react";
import { useMemo, useState } from "react";
import type { GenerationStep, GenerationTask, Project } from "../types";

interface AgentWorkspaceProps {
  project: Project | null;
  task: GenerationTask | null;
  busy: boolean;
  collapsed: boolean;
  onToggleCollapsed: () => void;
  onRetry: () => void;
}

type WorkspaceTab = "flow" | "context" | "result";
type FlowKey =
  | "load_context"
  | "build_chapter_target"
  | "build_prompt_package"
  | "generate_prose"
  | "audit_prose"
  | "summarize_chapter"
  | "judge_foreshadowing"
  | "judge_character_period"
  | "propose_future_plan_updates"
  | "build_candidate_result"
  | "persist_candidate_result";

interface FlowNode {
  key: FlowKey;
  index: number;
  label: string;
  summary: string;
  details: Array<[string, string]>;
}

const flowNodes: FlowNode[] = [
  {
    key: "load_context",
    index: 1,
    label: "加载上下文",
    summary: "读取本章生成所需的正式上下文包",
    details: [
      ["加载内容", "小说定位、风格、世界观、主线、角色卡、章节摘要、伏笔和作者灵感。"],
      ["说明", "完整上下文可随时切换到“上下文”tab 查看。"],
    ],
  },
  {
    key: "build_chapter_target",
    index: 2,
    label: "确认本章线路",
    summary: "确认本章必须完成什么",
    details: [["本章目标", "确认修书会改写现实，并付出明确记忆代价。"]],
  },
  {
    key: "build_prompt_package",
    index: 3,
    label: "生成本章提示包",
    summary: "整理目标、限制、角色状态和伏笔",
    details: [["提示包", "包含目标、限制、风格约束、角色状态、伏笔边界和禁止泄露项。"]],
  },
  {
    key: "generate_prose",
    index: 4,
    label: "生成章节正文",
    summary: "生成候选正文并显示在正文区",
    details: [["输出位置", "中间列：正文工作区。"]],
  },
  {
    key: "audit_prose",
    index: 5,
    label: "审核是否偏离",
    summary: "检查是否偏离目标、主线、人设、世界观和前文",
    details: [["审核结果", "未发现阻塞问题。"]],
  },
  {
    key: "summarize_chapter",
    index: 6,
    label: "章节摘要",
    summary: "提炼本章正式上下文需要保留的事实",
    details: [["用途", "用于后续生成和上下文压缩。"]],
  },
  {
    key: "judge_foreshadowing",
    index: 7,
    label: "伏笔判断",
    summary: "判断新增、推进、回收或提前泄露伏笔",
    details: [["变化", "新增书页批注，推进手背页码。"]],
  },
  {
    key: "judge_character_period",
    index: 8,
    label: "角色时期卡判断",
    summary: "判断是否需要新建或更新角色时期卡",
    details: [["变化", "更新主角目标和记忆状态。"]],
  },
  {
    key: "propose_future_plan_updates",
    index: 9,
    label: "判断后续线路调整",
    summary: "根据本章实际结果判断后续章节名和线路是否需要改变",
    details: [
      ["第 4 章标题", "规则代价 -> 第一次付出代价。"],
      ["原因", "本章已经写出第一次明确记忆代价。"],
    ],
  },
  {
    key: "build_candidate_result",
    index: 10,
    label: "输出候选结果",
    summary: "汇总正文、摘要、审核、伏笔、角色卡和后续线路建议",
    details: [["候选内容", "正文、摘要、审核发现、伏笔建议、角色卡建议和线路建议。"]],
  },
  {
    key: "persist_candidate_result",
    index: 11,
    label: "保存候选结果",
    summary: "保存候选正文、候选摘要、审核发现和节点快照",
    details: [["写入内容", "候选正文、候选摘要、审核发现、任务状态和节点快照。"]],
  },
];

function joinItems(items: Array<string | null | undefined>, fallback = "") {
  const text = items.filter(Boolean).join("；");
  return text || fallback;
}

function stringifyValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "";
  if (Array.isArray(value)) return joinItems(value.map((item) => stringifyValue(item)));
  if (typeof value === "object") return joinItems(Object.values(value).map((item) => stringifyValue(item)));
  return String(value);
}

function findStep(task: GenerationTask | null, name: string): GenerationStep | null {
  return task?.steps.find((step) => step.name === name) ?? null;
}

function getOutput(task: GenerationTask | null, name: string): Record<string, unknown> {
  return findStep(task, name)?.output_snapshot ?? {};
}

function getCandidateResult(task: GenerationTask | null): Record<string, unknown> {
  const output = getOutput(task, "build_candidate_result");
  const candidate = output.candidate_result;
  return candidate && typeof candidate === "object" && !Array.isArray(candidate)
    ? (candidate as Record<string, unknown>)
    : {};
}

function getNestedRecord(source: Record<string, unknown>, key: string): Record<string, unknown> {
  const value = source[key];
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function stepStatusText(status: string | undefined): string {
  if (status === "completed") return "完成";
  if (status === "running") return "执行中";
  if (status === "failed") return "失败";
  return "等待";
}

function stepStatusClass(status: string | undefined): string {
  if (status === "completed") return "completed";
  if (status === "running") return "running";
  if (status === "failed") return "failed";
  return "pending";
}

function StepStatusIcon({ status }: { status: string | undefined }) {
  if (status === "completed") return <CheckCircle2 size={16} aria-hidden="true" />;
  if (status === "running") return <LoaderCircle size={16} aria-hidden="true" />;
  if (status === "failed") return <XCircle size={16} aria-hidden="true" />;
  return <Circle size={16} aria-hidden="true" />;
}

export function AgentWorkspace({ project, task, busy, collapsed, onToggleCollapsed, onRetry }: AgentWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("flow");
  const [activeFlow, setActiveFlow] = useState<string>("load_context");
  const failed = task?.status === "failed";
  const realSteps = task?.steps ?? [];
  const realStepByName = new Map(realSteps.map((step) => [step.name, step]));
  const activeStep = realStepByName.get(activeFlow) ?? null;
  const activeNode = flowNodes.find((node) => node.key === activeFlow) ?? flowNodes[0];
  const currentChapter = task?.chapter ?? project?.chapters[0] ?? null;
  const loadContextOutput = getOutput(task, "load_context");
  const contextPackage = getNestedRecord(loadContextOutput, "context_package");
  const candidateResult = getCandidateResult(task);
  const auditResult = getNestedRecord(candidateResult, "audit");
  const foreshadowingResult = getNestedRecord(candidateResult, "foreshadowing");
  const characterPeriodResult = getNestedRecord(candidateResult, "character_period");
  const futurePlanResult = getNestedRecord(candidateResult, "future_plan");
  const persistenceResult = getOutput(task, "persist_candidate_result").persistence_result;

  const contextCards = useMemo<Array<[string, string]>>(
    () => [
      ["小说定位", stringifyValue(contextPackage.positioning) || project?.positioning || "未创建项目"],
      ["风格", "克制、悬疑、细节推动，章节结尾保留清晰钩子。"],
      ["世界观", stringifyValue(contextPackage.worldview) || project?.worldview || ""],
      ["主线", stringifyValue(contextPackage.main_plot) || project?.main_plot || ""],
      [
        "当前角色时期卡",
        stringifyValue(contextPackage.characters) ||
          joinItems(project?.characters.map((item) => `${item.name}：${item.current_goal ?? "暂无目标"}`) ?? []),
      ],
      [
        "已采纳章节摘要",
        stringifyValue(contextPackage.chapter_summaries) ||
          joinItems(
            project?.chapters.map((chapter) => `第 ${chapter.number} 章：${chapter.summary ?? "暂无摘要"}`) ?? [],
          ),
      ],
      [
        "未回收伏笔",
        stringifyValue(contextPackage.foreshadowing_items) ||
          joinItems(project?.foreshadowing_items.map((item) => item.content) ?? []),
      ],
      ["作者灵感", stringifyValue(contextPackage.inspirations) || joinItems(project?.inspirations.map((item) => item.content) ?? [])],
      ["压缩状态", "旧章节正文达到阈值后压缩为摘要；关键设定、角色变化和伏笔保留。"],
    ],
    [contextPackage, project],
  );
  const flowDisplayItems = flowNodes.map((node) => {
    const step = realStepByName.get(node.key);
    const status = step?.status;
    return {
      ...node,
      status,
      statusText: stepStatusText(status),
      statusClass: stepStatusClass(status),
    };
  });
  const activeTitle = `${activeNode.index}. ${activeNode.label}`;
  const activeSummary = activeStep
    ? stringifyValue(activeStep.output_snapshot) || activeStep.error_message || activeStep.status
    : activeNode.summary;
  const activeDetails = activeStep
    ? Object.entries(activeStep.output_snapshot ?? {}).map(([key, value]) => [key, stringifyValue(value)] as [string, string])
    : activeNode.details;

  return (
    <section className={collapsed ? "agent-workspace collapsed" : "agent-workspace"} aria-label="Agent 创作后台">
      <div className="backstage-bar">
        <div>
          <h2>Agent 创作后台</h2>
          <span>{task ? `全自动运行 · ${task.status}` : "等待生成"}</span>
        </div>
        <div className="toolbar-actions">
          {failed ? (
            <button className="secondary-button" type="button" onClick={onRetry} disabled={busy} title="重试">
              <RefreshCw size={16} />
              <span>重试</span>
            </button>
          ) : null}
          <button
            className="icon-text-button"
            type="button"
            onClick={onToggleCollapsed}
            title={collapsed ? "展开后台" : "收起后台"}
            aria-label={collapsed ? "展开后台" : "收起后台"}
          >
            {collapsed ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            <span>{collapsed ? "展开" : "收起"}</span>
          </button>
        </div>
      </div>

      {collapsed ? null : (
      <>
      <div className="backstage-tabs" role="tablist" aria-label="后台视图">
        <button
          className={activeTab === "flow" ? "tab-button active" : "tab-button"}
          type="button"
          role="tab"
          aria-selected={activeTab === "flow"}
          onClick={() => setActiveTab("flow")}
        >
          流程节点
        </button>
        <button
          className={activeTab === "context" ? "tab-button active" : "tab-button"}
          type="button"
          role="tab"
          aria-selected={activeTab === "context"}
          onClick={() => setActiveTab("context")}
        >
          上下文
        </button>
        <button
          className={activeTab === "result" ? "tab-button active" : "tab-button"}
          type="button"
          role="tab"
          aria-selected={activeTab === "result"}
          onClick={() => setActiveTab("result")}
        >
          结果与更新
        </button>
      </div>

      {activeTab === "flow" ? (
        <div className="flow-layout">
          <nav className="flow-node-list" aria-label="流程节点">
            {flowDisplayItems.map((node) => (
              <button
                key={node.key}
                type="button"
                className={node.key === activeFlow ? `flow-node active ${node.statusClass}` : `flow-node ${node.statusClass}`}
                aria-label={`${node.index}. ${node.label} ${node.statusText}`}
                onClick={() => setActiveFlow(node.key)}
              >
                <StepStatusIcon status={node.status} />
                <strong>{node.index}. {node.label}</strong>
              </button>
            ))}
          </nav>
          <article className="flow-detail-card">
            <h3>{activeTitle}</h3>
            <p>{activeSummary}</p>
            <div className="detail-card-grid">
              {activeDetails.map(([title, content]) => (
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
            <summary>
              <strong>审核结果</strong>
              <span>通过</span>
              <span className="status-pill">无阻塞</span>
            </summary>
            <p className={task?.error_message ? "error-line" : undefined}>
              {task?.error_message ? (
                <>
                  <AlertCircle size={16} />
                  <span>{task.error_message}</span>
                </>
              ) : (
                stringifyValue(auditResult.findings) || "未发现阻塞问题。"
              )}
            </p>
          </details>
          <details className="result-card changed">
            <summary>
              <strong>章节摘要</strong>
              <span>将写入</span>
              <span className="status-pill warn">有变化</span>
            </summary>
            <p>{stringifyValue(candidateResult.summary) || currentChapter?.summary || "主角第一次修复红封书，确认现实会随修书改变。"}</p>
          </details>
          <details className="result-card changed">
            <summary>
              <strong>伏笔变化</strong>
              <span>新增 / 推进</span>
              <span className="status-pill warn">有变化</span>
            </summary>
            <p>
              {stringifyValue(foreshadowingResult) ||
                joinItems(project?.foreshadowing_items.map((item) => item.content) ?? [], "新增书页批注，推进手背页码。")}
            </p>
          </details>
          <details className="result-card changed">
            <summary>
              <strong>角色卡变化</strong>
              <span>更新</span>
              <span className="status-pill warn">有变化</span>
            </summary>
            <p>
              {stringifyValue(characterPeriodResult) ||
                joinItems(
                  project?.characters.map((item) => `${item.name}：${item.current_goal ?? "暂无目标"}`) ?? [],
                  "更新主角目标和记忆状态。",
                )}
            </p>
          </details>
          <details className="result-card changed">
            <summary>
              <strong>后续线路变化</strong>
              <span>建议调整</span>
              <span className="status-pill warn">有变化</span>
            </summary>
            <p>{stringifyValue(futurePlanResult) || "第 4 章标题：规则代价 -> 第一次付出代价。原因：本章已经实际写出第一次明确记忆代价。"}</p>
          </details>
          <details className="result-card weak">
            <summary>
              <strong>入库动作</strong>
              <span>已自动写入</span>
              <span className="status-pill">完成</span>
            </summary>
            <p>{stringifyValue(persistenceResult) || "正文、摘要、角色卡更新、伏笔更新和后续线路调整写入正式上下文；生成记录保留。"}</p>
          </details>
        </div>
      ) : null}
      </>
      )}
    </section>
  );
}
