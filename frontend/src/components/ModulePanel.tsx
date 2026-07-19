import { Send } from "lucide-react";
import type { Project } from "../types";

interface ModulePanelProps {
  project: Project | null;
  inspirationText: string;
  busy: boolean;
  onInspirationChange: (value: string) => void;
  onAddInspiration: () => void;
}

export function ModulePanel({
  project,
  inspirationText,
  busy,
  onInspirationChange,
  onAddInspiration,
}: ModulePanelProps) {
  return (
    <aside className="module-panel" aria-label="模块">
      <h2>模块</h2>
      <details open>
        <summary>小说定位</summary>
        <p>{project?.positioning ?? "未创建项目"}</p>
      </details>
      <details>
        <summary>世界观</summary>
        <p>{project?.worldview ?? ""}</p>
      </details>
      <details>
        <summary>主线</summary>
        <p>{project?.main_plot ?? ""}</p>
      </details>
      <details open>
        <summary>角色卡</summary>
        <div className="stack">
          {project?.characters.map((character) => (
            <article className="module-row" key={character.id}>
              <strong>{character.name}</strong>
              <span>{character.role}</span>
              <span>{character.period_stage ?? "未标注时期"}</span>
              <p>{character.current_goal}</p>
              {character.period_summary ? <p>{character.period_summary}</p> : null}
            </article>
          ))}
        </div>
      </details>
      <details open>
        <summary>事件时间线</summary>
        <div className="stack">
          {project?.story_events.map((item) => (
            <article className="module-row" key={item.id}>
              <strong>{item.title}</strong>
              <span>{item.characters}</span>
              <p>{item.summary}</p>
              {item.consequence ? <p>{item.consequence}</p> : null}
            </article>
          ))}
        </div>
      </details>
      <details open>
        <summary>世界观规则</summary>
        <div className="stack">
          {project?.world_rules.map((item) => (
            <article className="module-row" key={item.id}>
              <strong>{item.rule}</strong>
              <span>{item.status}</span>
              {item.limitation ? <p>{item.limitation}</p> : null}
              {item.exception ? <p>{item.exception}</p> : null}
            </article>
          ))}
        </div>
      </details>
      <details open>
        <summary>作者灵感</summary>
        <textarea
          aria-label="作者灵感输入"
          className="inspiration-input"
          value={inspirationText}
          onChange={(event) => onInspirationChange(event.target.value)}
          disabled={busy}
        />
        <button
          className="primary-button"
          type="button"
          onClick={onAddInspiration}
          disabled={busy || !project || !inspirationText.trim()}
          title="加入灵感"
        >
          <Send size={16} />
          <span>加入</span>
        </button>
        <div className="stack">
          {project?.inspirations.map((item) => (
            <p className="module-row" key={item.id}>{item.content}</p>
          ))}
        </div>
      </details>
      <details open>
        <summary>伏笔记录</summary>
        <div className="stack">
          {project?.foreshadowing_items.length ? (
            project.foreshadowing_items.map((item) => (
              <article className="module-row" key={item.id}>
                <strong>{item.content}</strong>
                <span>{item.status}</span>
                {item.notes ? <p>{item.notes}</p> : null}
              </article>
            ))
          ) : (
            <p className="module-row empty-state">暂无伏笔记录</p>
          )}
        </div>
      </details>
    </aside>
  );
}
