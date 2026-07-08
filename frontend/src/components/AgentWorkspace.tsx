import { AlertCircle, RefreshCw } from "lucide-react";
import type { GenerationTask } from "../types";

interface AgentWorkspaceProps {
  task: GenerationTask | null;
  busy: boolean;
  onRetry: () => void;
}

export function AgentWorkspace({ task, busy, onRetry }: AgentWorkspaceProps) {
  const failed = task?.status === "failed";

  return (
    <section className="agent-workspace" aria-label="Agent 创作后台">
      <div className="panel-heading">
        <h2>Agent 创作后台</h2>
        {failed ? (
          <button className="secondary-button" type="button" onClick={onRetry} disabled={busy} title="重试">
            <RefreshCw size={16} />
            <span>重试</span>
          </button>
        ) : null}
      </div>
      <div className="workspace-grid">
        <div>
          <h3>当前状态</h3>
          <p>{task ? `${task.status}${task.current_step ? ` / ${task.current_step}` : ""}` : "等待生成"}</p>
        </div>
        <div>
          <h3>节点步骤</h3>
          <ol>
            {task?.steps.map((step) => (
              <li key={step.id}>
                <span>{step.name}</span>
                <small>{step.status}</small>
              </li>
            ))}
          </ol>
        </div>
        <div>
          <h3>章节摘要</h3>
          <p>{task?.chapter?.summary ?? ""}</p>
        </div>
        <div>
          <h3>审核发现</h3>
          {task?.error_message ? (
            <p className="error-line">
              <AlertCircle size={16} />
              <span>{task.error_message}</span>
            </p>
          ) : (
            <p>{task ? "基础审核已完成" : ""}</p>
          )}
        </div>
      </div>
    </section>
  );
}
