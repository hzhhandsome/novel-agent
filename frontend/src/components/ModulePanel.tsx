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
              <p>{character.current_goal}</p>
            </article>
          ))}
        </div>
      </details>
      <details open>
        <summary>作者灵感</summary>
        <textarea
          className="inspiration-input"
          value={inspirationText}
          onChange={(event) => onInspirationChange(event.target.value)}
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
      <details>
        <summary>伏笔记录</summary>
        <div className="stack">
          {project?.foreshadowing_items.map((item) => (
            <p className="module-row" key={item.id}>{item.content}</p>
          ))}
        </div>
      </details>
    </aside>
  );
}
