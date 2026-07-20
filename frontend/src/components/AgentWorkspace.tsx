import { AlertCircle, CheckCircle2, ChevronDown, ChevronUp, Circle, LoaderCircle, RefreshCw, XCircle } from "lucide-react";
import { type MouseEvent, type ReactNode, useMemo, useState } from "react";
import type { BuiltinEvalReport, GenerationStep, GenerationTask, Project, TraceEvent } from "../types";

interface AgentWorkspaceProps {
  project: Project | null;
  task: GenerationTask | null;
  evalReport: BuiltinEvalReport | null;
  busy: boolean;
  collapsed: boolean;
  onResizeStart: (event: MouseEvent<HTMLButtonElement>) => void;
  onToggleCollapsed: () => void;
  onRetry: () => void;
  onRunEval: () => void;
}

type WorkspaceTab = "flow" | "context" | "result" | "trace";
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

function formatContextBudget(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  const budget = value as Record<string, unknown>;
  const used = stringifyValue(budget.used) || "0";
  const total = stringifyValue(budget.total_budget) || "0";
  const sections = Array.isArray(budget.sections) ? budget.sections : [];
  const sectionText = sections
    .map((section) => {
      if (!section || typeof section !== "object" || Array.isArray(section)) return "";
      const item = section as Record<string, unknown>;
      return `${stringifyValue(item.name)}：${stringifyValue(item.included_count)} 入选 / ${stringifyValue(item.omitted_count)} 裁剪`;
    })
    .filter(Boolean)
    .join("；");
  const omitted = getNestedRecord(budget, "omitted");
  const omittedText = Object.entries(omitted)
    .map(([name, items]) => `${name}：${stringifyValue(items)}`)
    .filter((item) => item.trim() !== "")
    .join("；");
  return [`${used} / ${total}`, sectionText, omittedText].filter(Boolean).join("；");
}

function formatContextBudgetHeader(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  const budget = value as Record<string, unknown>;
  const used = Number(budget.used ?? 0);
  const total = Number(budget.total_budget ?? 0);
  if (!total) return "";
  const percent = Math.round((used / total) * 100);
  return `上下文 ${used} / ${total}（${percent}%）`;
}

function formatRetrievalResults(value: unknown): string {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  const retrieval = value as Record<string, unknown>;
  const backend = stringifyValue(retrieval.backend);
  const query = stringifyValue(retrieval.query);
  const hits = Array.isArray(retrieval.hits) ? retrieval.hits : [];
  const hitText = hits
    .map((hit) => {
      if (!hit || typeof hit !== "object" || Array.isArray(hit)) return "";
      const item = hit as Record<string, unknown>;
      const source = stringifyValue(item.source);
      const score = stringifyValue(item.score);
      const text = stringifyValue(item.text);
      return [source, score ? `score=${score}` : "", text].filter(Boolean).join("：");
    })
    .filter(Boolean)
    .join("；");
  return [`backend=${backend}`, query ? `query=${query}` : "", hitText].filter(Boolean).join("；");
}

function modelUsageSummary(task: GenerationTask | null): string {
  const calls = (task?.steps ?? []).flatMap((step) =>
    Object.entries(step.output_snapshot ?? {})
      .filter(([key, value]) => key.endsWith("_model_usage") && value && typeof value === "object" && !Array.isArray(value))
      .map(([, value]) => value as Record<string, unknown>),
  );
  if (calls.length === 0) return "";

  const inputTokens = calls.reduce((sum, item) => sum + Number(item.estimated_input_tokens ?? 0), 0);
  const outputTokens = calls.reduce((sum, item) => sum + Number(item.estimated_output_tokens ?? 0), 0);
  const durationMs = calls.reduce((sum, item) => sum + Number(item.duration_ms ?? 0), 0);
  const cost = calls.reduce((sum, item) => sum + Number(item.estimated_cost ?? 0), 0);
  const totalTokens = inputTokens + outputTokens;
  return `估算 token：${totalTokens}；估算成本：${Number(cost.toFixed(6))}；耗时：${durationMs}ms`;
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

function formatEvalPercent(value: number | undefined): string {
  return `${Math.round((value ?? 0) * 100)}%`;
}

function evalCaseSummary(report: BuiltinEvalReport | null): string {
  if (!report) return "";
  const failedCases = [...report.summary.cases, ...report.audit.cases, ...(report.rag?.cases ?? [])].filter(
    (item) => !item.passed,
  );
  const judgeFailedCases = (report.judge?.cases ?? []).filter((item) => !item.passed);
  failedCases.push(...judgeFailedCases);
  if (failedCases.length === 0) return "所有内置样例通过";
  return failedCases
    .map((item) => {
      const missed =
        [...(item.missing ?? []), ...(item.missed ?? []), ...(item.blocking_findings ?? [])].join("、") ||
        item.reason ||
        "无";
      return `${item.case_id ?? item.case ?? "unknown_case"}：遗漏 ${missed}`;
    })
    .join("；");
}

function formatJson(value: unknown): string {
  return JSON.stringify(value ?? {}, null, 2);
}

function formatModelUsageFromOutput(output: Record<string, unknown>): string {
  const usages = Object.entries(output)
    .filter(([key, value]) => key.endsWith("_model_usage") && value && typeof value === "object" && !Array.isArray(value))
    .map(([, value]) => value as Record<string, unknown>);
  if (usages.length === 0) return "";

  const inputTokens = usages.reduce((sum, item) => sum + Number(item.estimated_input_tokens ?? 0), 0);
  const outputTokens = usages.reduce((sum, item) => sum + Number(item.estimated_output_tokens ?? 0), 0);
  const durationMs = usages.reduce((sum, item) => sum + Number(item.duration_ms ?? 0), 0);
  const cost = usages.reduce((sum, item) => sum + Number(item.estimated_cost ?? 0), 0);
  return `输入 ${inputTokens} / 输出 ${outputTokens} token；成本 ${Number(cost.toFixed(6))}；耗时 ${durationMs}ms`;
}

function formatPromptSummary(value: unknown): string {
  const text = stringifyValue(value);
  if (!text) return "";
  return text.length > 360 ? `${text.slice(0, 360)}...` : text;
}

function formatPromptMetadata(output: Record<string, unknown>): string {
  const direct = output.prompt_metadata;
  const metadata =
    direct && typeof direct === "object" && !Array.isArray(direct)
      ? (direct as Record<string, unknown>)
      : Object.entries(output)
          .filter(([key, value]) => key.endsWith("_prompt_metadata") && value && typeof value === "object" && !Array.isArray(value))
          .map(([, value]) => value as Record<string, unknown>)[0];
  if (!metadata) return "";
  return [
    stringifyValue(metadata.prompt_version),
    stringifyValue(metadata.context_builder_version),
    stringifyValue(metadata.prompt_hash),
  ]
    .filter(Boolean)
    .join("；");
}

function formatToolCalls(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value
    .map((call) => {
      if (!call || typeof call !== "object" || Array.isArray(call)) return "";
      const item = call as Record<string, unknown>;
      return [
        stringifyValue(item.tool_name),
        stringifyValue(item.status),
        stringifyValue(item.arguments),
        stringifyValue(item.result_summary),
        stringifyValue(item.error),
        stringifyValue(item.duration_ms) ? `${stringifyValue(item.duration_ms)}ms` : "",
      ]
        .filter(Boolean)
        .join("；");
    })
    .filter(Boolean)
    .join("\n");
}

function formatTraceMetadata(event: TraceEvent): string {
  const metadata = event.metadata ?? {};
  const items = [
    metadata.model ? `model=${stringifyValue(metadata.model)}` : "",
    metadata.route ? `route=${stringifyValue(metadata.route)}` : "",
    metadata.estimated_input_tokens || metadata.estimated_output_tokens
      ? `token=${Number(metadata.estimated_input_tokens ?? 0) + Number(metadata.estimated_output_tokens ?? 0)}`
      : "",
    metadata.query ? `query=${stringifyValue(metadata.query)}` : "",
    metadata.hit_count !== undefined ? `hits=${stringifyValue(metadata.hit_count)}` : "",
    metadata.tool_name ? `tool=${stringifyValue(metadata.tool_name)}` : "",
    metadata.error_message ? `error=${stringifyValue(metadata.error_message)}` : "",
    metadata.error ? `error=${stringifyValue(metadata.error)}` : "",
  ];
  return items.filter(Boolean).join("；");
}

function formatPersistenceResult(value: Record<string, unknown>): string {
  if (!Object.keys(value).length) return "";
  const items = [
    value.saved_candidate === true ? "候选正文已保存" : "候选正文未保存",
    value.saved_summary === true ? "候选摘要已保存" : "候选摘要未保存",
    value.official_content_committed === true ? "正式正文已写入" : "正式正文未写入",
  ];
  const reviewCount = Number(value.saved_review_findings ?? 0);
  if (reviewCount) items.push(`审核发现 ${reviewCount} 条`);
  return items.join("；");
}

function stepSummary(step: GenerationStep | null, node: FlowNode): string {
  if (!step) return node.summary;
  if (step.error_message) return step.error_message;
  if (step.name === "load_context") return "上下文包已加载，预算和召回信息可在下方查看。";
  if (step.name === "build_chapter_target") return "本章线路已确认。";
  if (step.name === "build_prompt_package") return "本章提示包已生成。";
  if (step.name === "generate_prose") return "正文节点已完成，正文内容显示在中间正文区。";
  if (step.name === "audit_prose") return "正文审核已完成。";
  if (step.name === "summarize_chapter") return "章节摘要已生成。";
  if (step.name === "judge_foreshadowing") return "伏笔新增、推进、回收和泄露判断已完成。";
  if (step.name === "judge_character_period") return "角色时期卡判断已完成。";
  if (step.name === "propose_future_plan_updates") return "后续章节线路调整建议已生成。";
  if (step.name === "build_candidate_result") return "候选结果已汇总，摘要、审核、伏笔和角色卡建议进入结果区。";
  if (step.name === "persist_candidate_result") return "候选结果、节点快照和写入状态已保存。";
  return node.summary;
}

function stepHighlights(step: GenerationStep | null, node: FlowNode): Array<[string, string]> {
  if (!step) return node.details;

  const input = step.input_snapshot ?? {};
  const output = step.output_snapshot ?? {};
  const items: Array<[string, string]> = [["节点状态", stepStatusText(step.status)]];
  const usageText = formatModelUsageFromOutput(output);
  if (usageText) items.push(["模型用量", usageText]);
  const promptText = formatPromptMetadata(output);
  if (promptText) items.push(["Prompt 版本", promptText]);
  const toolCallText = formatToolCalls(output.tool_calls);
  if (toolCallText) items.push(["工具调用", toolCallText]);

  if (step.name === "load_context") {
    const contextPackage = getNestedRecord(output, "context_package");
    const budgetText = formatContextBudget(contextPackage.context_budget);
    const retrievalText = formatRetrievalResults(contextPackage.retrieval_results);
    if (budgetText) items.push(["上下文预算", budgetText]);
    if (retrievalText) items.push(["RAG 召回", retrievalText]);
  }

  if (step.name === "build_chapter_target") {
    const target = stringifyValue(output.chapter_target);
    if (target) items.push(["本章线路", target]);
  }

  if (step.name === "build_prompt_package") {
    const target = stringifyValue(input.chapter_target);
    const prompt = formatPromptSummary(output.prompt_package);
    if (target) items.push(["本章线路", target]);
    if (prompt) items.push(["提示包摘要", prompt]);
  }

  if (step.name === "generate_prose") {
    const content = stringifyValue(output.generated_content);
    items.push(["正文输出", content ? `已生成 ${content.length} 字，正文显示在中间正文区。` : "正文内容显示在中间正文区。"]);
  }

  if (step.name === "audit_prose") {
    const audit = getNestedRecord(output, "audit_result");
    const findings = stringifyValue(audit.findings ?? output.review_findings);
    items.push(["审核发现", findings || "未发现阻塞问题。"]);
    if ("blocking" in audit) items.push(["是否阻塞", audit.blocking ? "有阻塞" : "无阻塞"]);
  }

  if (step.name === "summarize_chapter") {
    const summary = stringifyValue(output.summary) || stringifyValue(getNestedRecord(output, "summary_result").summary);
    if (summary) items.push(["章节摘要", summary]);
  }

  if (step.name === "judge_foreshadowing") {
    const decisions = getNestedRecord(output, "foreshadowing_decisions");
    items.push(["新增伏笔", stringifyValue(decisions.new) || "无"]);
    items.push(["推进伏笔", stringifyValue(decisions.advanced) || "无"]);
    items.push(["回收伏笔", stringifyValue(decisions.resolved) || "无"]);
    items.push(["提前泄露", stringifyValue(decisions.leaked) || "无"]);
    if (decisions.notes) items.push(["备注", stringifyValue(decisions.notes)]);
  }

  if (step.name === "judge_character_period") {
    const decisions = getNestedRecord(output, "character_period_decisions");
    items.push(["角色更新", stringifyValue(decisions.updates) || "无"]);
    items.push(["新时期卡", stringifyValue(decisions.new_period_cards) || "无"]);
    items.push(["记忆变化", stringifyValue(decisions.memory_changes) || "无"]);
    items.push(["关系变化", stringifyValue(decisions.relationship_changes) || "无"]);
    if ("stage_changed" in decisions) items.push(["阶段变化", decisions.stage_changed ? "发生阶段变化" : "未发生阶段变化"]);
    if (decisions.skipped) items.push(["跳过原因", stringifyValue(decisions.error) || "模型返回不可用，已跳过非关键角色判断。"]);
  }

  if (step.name === "propose_future_plan_updates") {
    const updates = getNestedRecord(output, "future_plan_updates");
    items.push(["后续线路建议", stringifyValue(updates.suggestions) || stringifyValue(updates) || "无调整建议"]);
  }

  if (step.name === "build_candidate_result") {
    const candidate = getNestedRecord(output, "candidate_result");
    const summary = stringifyValue(candidate.summary);
    if (summary) items.push(["章节摘要", summary]);
    const audit = stringifyValue(getNestedRecord(candidate, "audit"));
    if (audit) items.push(["审核结果", audit]);
  }

  if (step.name === "persist_candidate_result") {
    const persistence = formatPersistenceResult(getNestedRecord(output, "persistence_result")) || stringifyValue(output.persistence_result);
    if (persistence) items.push(["入库动作", persistence]);
  }

  return items.length > 1 ? items : node.details;
}

function StepStatusIcon({ status }: { status: string | undefined }) {
  if (status === "completed") return <CheckCircle2 size={16} aria-hidden="true" />;
  if (status === "running") return <LoaderCircle size={16} aria-hidden="true" />;
  if (status === "failed") return <XCircle size={16} aria-hidden="true" />;
  return <Circle size={16} aria-hidden="true" />;
}

interface ResultCardProps {
  title: string;
  summary: string;
  pill: string;
  className?: string;
  pillClassName?: string;
  children: ReactNode;
}

function ResultCard({ title, summary, pill, className = "", pillClassName = "", children }: ResultCardProps) {
  const [open, setOpen] = useState(false);
  const cardClassName = ["result-card", className].filter(Boolean).join(" ");
  const pillClasses = ["status-pill", pillClassName].filter(Boolean).join(" ");

  return (
    <article className={cardClassName}>
      <button
        className="result-card-summary"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <strong>{title}</strong>
        <span>{summary}</span>
        <span className={pillClasses}>{pill}</span>
      </button>
      {open ? <div className="result-card-body">{children}</div> : null}
    </article>
  );
}

export function AgentWorkspace({
  project,
  task,
  evalReport,
  busy,
  collapsed,
  onResizeStart,
  onToggleCollapsed,
  onRetry,
  onRunEval,
}: AgentWorkspaceProps) {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("flow");
  const [activeFlow, setActiveFlow] = useState<string>("load_context");
  const [rawSnapshotOpen, setRawSnapshotOpen] = useState(false);
  const failed = task?.status === "failed";
  const realSteps = task?.steps ?? [];
  const realStepByName = new Map(realSteps.map((step) => [step.name, step]));
  const activeStep = realStepByName.get(activeFlow) ?? null;
  const activeNode = flowNodes.find((node) => node.key === activeFlow) ?? flowNodes[0];
  const currentChapter = task?.chapter ?? project?.chapters[0] ?? null;
  const loadContextOutput = getOutput(task, "load_context");
  const contextPackage = getNestedRecord(loadContextOutput, "context_package");
  const contextBudgetText = formatContextBudget(contextPackage.context_budget);
  const contextBudgetHeaderText = formatContextBudgetHeader(contextPackage.context_budget);
  const retrievalText = formatRetrievalResults(contextPackage.retrieval_results);
  const candidateResult = getCandidateResult(task);
  const auditResult = getNestedRecord(candidateResult, "audit");
  const foreshadowingResult = getNestedRecord(candidateResult, "foreshadowing");
  const characterPeriodResult = getNestedRecord(candidateResult, "character_period");
  const futurePlanResult = getNestedRecord(candidateResult, "future_plan");
  const persistenceResult = getOutput(task, "persist_candidate_result").persistence_result;
  const usageSummary = modelUsageSummary(task);
  const traceEvents = task?.trace?.events ?? [];

  function handleRunEval() {
    setActiveTab("result");
    onRunEval();
  }

  const contextCards = useMemo<Array<[string, string]>>(
    () => [
      ["小说定位", stringifyValue(contextPackage.positioning) || project?.positioning || "未创建项目"],
      ["风格", "克制、悬疑、细节推动，章节结尾保留清晰钩子。"],
      ["世界观", stringifyValue(contextPackage.worldview) || project?.worldview || ""],
      ["主线", stringifyValue(contextPackage.main_plot) || project?.main_plot || ""],
      [
        "当前角色时期卡",
        stringifyValue(contextPackage.characters) ||
          joinItems(
            project?.characters.map(
              (item) =>
                `${item.name}：${item.period_stage ?? "未标注时期"}；${item.period_summary ?? item.current_goal ?? "暂无目标"}`,
            ) ?? [],
          ),
      ],
      [
        "事件时间线",
        stringifyValue(contextPackage.story_events) ||
          joinItems(project?.story_events.map((item) => `${item.title}：${item.summary}`) ?? []),
      ],
      [
        "世界观规则",
        stringifyValue(contextPackage.world_rules) ||
          joinItems(project?.world_rules.map((item) => `${item.rule}；${item.limitation ?? ""}`) ?? []),
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
      ["RAG 召回", retrievalText || "尚未生成召回报告。"],
      ["上下文预算", contextBudgetText || "尚未生成预算报告。"],
      ["压缩状态", "旧章节正文达到阈值后压缩为摘要；关键设定、角色变化和伏笔保留。"],
    ],
    [contextBudgetText, contextPackage, project, retrievalText],
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
  const activeSummary = stepSummary(activeStep, activeNode);
  const activeDetails = stepHighlights(activeStep, activeNode);
  const rawSnapshotText = activeStep
    ? formatJson({
        input_snapshot: activeStep.input_snapshot,
        output_snapshot: activeStep.output_snapshot,
      })
    : "";

  return (
    <section className={collapsed ? "agent-workspace collapsed" : "agent-workspace"} aria-label="Agent 创作后台">
      {!collapsed ? (
        <button
          className="backstage-resize-handle"
          type="button"
          aria-label="拖拽调整后台高度"
          title="拖拽调整后台高度"
          onMouseDown={onResizeStart}
        />
      ) : null}
      <div className="backstage-bar">
        <div>
          <h2>Agent 创作后台</h2>
          <span>{task ? `全自动运行 · ${task.status}` : "等待生成"}</span>
          {usageSummary ? <span>{usageSummary}</span> : null}
          {contextBudgetHeaderText ? <span className="context-budget-pill">{contextBudgetHeaderText}</span> : null}
        </div>
        <div className="toolbar-actions">
          <button className="secondary-button" type="button" onClick={handleRunEval} disabled={busy} title="运行 Eval">
            <span>运行 Eval</span>
          </button>
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
        <button
          className={activeTab === "trace" ? "tab-button active" : "tab-button"}
          type="button"
          role="tab"
          aria-selected={activeTab === "trace"}
          onClick={() => setActiveTab("trace")}
        >
          Trace
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
                onClick={() => {
                  setActiveFlow(node.key);
                  setRawSnapshotOpen(false);
                }}
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
            {activeStep ? (
              <div className="raw-snapshot-card">
                <button
                  type="button"
                  aria-expanded={rawSnapshotOpen}
                  onClick={() => setRawSnapshotOpen((value) => !value)}
                >
                  <strong>原始输出</strong>
                  <span>输入/输出快照</span>
                </button>
                {rawSnapshotOpen ? <pre>{rawSnapshotText}</pre> : null}
              </div>
            ) : null}
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
          {evalReport ? (
            <article className="result-card eval-report-card">
              <header className="eval-report-header">
                <div>
                  <strong>Eval 评测</strong>
                  <span>通过 {evalReport.overall.passed_count} / {evalReport.overall.case_count}</span>
                </div>
                <span className="status-pill">内置样例</span>
              </header>
              <div className="eval-metric-grid">
                <span>摘要事实保留率 {formatEvalPercent(evalReport.summary.average_retention_rate)}</span>
                <span>审核冲突检出率 {formatEvalPercent(evalReport.audit.average_recall_rate)}</span>
                {evalReport.rag ? <span>RAG 召回率 {formatEvalPercent(evalReport.rag.average_recall_at_k)}</span> : null}
                {evalReport.rag ? <span>RAG MRR {formatEvalPercent(evalReport.rag.average_mrr)}</span> : null}
                {evalReport.judge ? <span>Judge 语义分 {formatEvalPercent(evalReport.judge.average_score)}</span> : null}
                {evalReport.judge ? (
                  <span>
                    Judge 通过 {evalReport.judge.passed_count} / {evalReport.judge.case_count}
                  </span>
                ) : null}
                {evalReport.prompt_versions?.groups[0] ? (
                  <span>Prompt 版本 {evalReport.prompt_versions.groups[0].prompt_version}</span>
                ) : null}
              </div>
              <p>{evalCaseSummary(evalReport)}</p>
            </article>
          ) : null}
          <ResultCard title="审核结果" summary="通过" pill="无阻塞">
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
          </ResultCard>
          <ResultCard title="章节摘要" summary="将写入" pill="有变化" className="changed" pillClassName="warn">
            <p>{stringifyValue(candidateResult.summary) || currentChapter?.summary || "主角第一次修复红封书，确认现实会随修书改变。"}</p>
          </ResultCard>
          <ResultCard title="伏笔变化" summary="新增 / 推进" pill="有变化" className="changed" pillClassName="warn">
            <p>
              {stringifyValue(foreshadowingResult) ||
                joinItems(project?.foreshadowing_items.map((item) => item.content) ?? [], "新增书页批注，推进手背页码。")}
            </p>
          </ResultCard>
          <ResultCard title="角色卡变化" summary="更新" pill="有变化" className="changed" pillClassName="warn">
            <p>
              {stringifyValue(characterPeriodResult) ||
                joinItems(
                  project?.characters.map((item) => `${item.name}：${item.current_goal ?? "暂无目标"}`) ?? [],
                  "更新主角目标和记忆状态。",
                )}
            </p>
          </ResultCard>
          <ResultCard title="后续线路变化" summary="建议调整" pill="有变化" className="changed" pillClassName="warn">
            <p>{stringifyValue(futurePlanResult) || "第 4 章标题：规则代价 -> 第一次付出代价。原因：本章已经实际写出第一次明确记忆代价。"}</p>
          </ResultCard>
          <ResultCard title="入库动作" summary="已自动写入" pill="完成" className="weak">
            <p>{stringifyValue(persistenceResult) || "正文、摘要、角色卡更新、伏笔更新和后续线路调整写入正式上下文；生成记录保留。"}</p>
          </ResultCard>
        </div>
      ) : null}

      {activeTab === "trace" ? (
        <div className="result-list">
          <article className="result-card eval-report-card">
            <header className="eval-report-header">
              <div>
                <strong>Trace</strong>
                <span>{task?.trace?.trace_id ?? "尚未生成 trace"}</span>
              </div>
              <span className="status-pill">{traceEvents.length} events</span>
            </header>
          </article>
          {traceEvents.map((event) => {
            const metadataText = formatTraceMetadata(event);
            return (
              <article className="dark-card" key={event.span_id}>
                <h3>
                  {event.event_type} · {event.name}
                </h3>
                <p>{event.summary || event.status}</p>
                <p>
                  {[
                    `status=${event.status}`,
                    event.duration_ms !== null ? `${event.duration_ms}ms` : "",
                    metadataText,
                  ]
                    .filter(Boolean)
                    .join("；")}
                </p>
              </article>
            );
          })}
        </div>
      ) : null}
      </>
      )}
    </section>
  );
}
