import { Check, Save, X, Zap } from "lucide-react";
import type { AutoGenerationTask, Chapter } from "../types";
import { ProjectCreator } from "./ProjectCreator";

interface ChapterEditorProps {
  chapter: Chapter | null;
  editorContent: string;
  liveGeneratedContent: string | null;
  autoChapterCount: string;
  autoTask: AutoGenerationTask | null;
  idea: string;
  busy: boolean;
  error: string | null;
  onIdeaChange: (value: string) => void;
  onAutoChapterCountChange: (value: string) => void;
  onCreateProject: () => void;
  onEditorChange: (value: string) => void;
  onSave: () => void;
  onGenerate: () => void;
  onAutoGenerate: () => void;
  onAccept: () => void;
  onReject: () => void;
}

export function ChapterEditor({
  chapter,
  editorContent,
  liveGeneratedContent,
  autoChapterCount,
  autoTask,
  idea,
  busy,
  error,
  onIdeaChange,
  onAutoChapterCountChange,
  onCreateProject,
  onEditorChange,
  onSave,
  onGenerate,
  onAutoGenerate,
  onAccept,
  onReject,
}: ChapterEditorProps) {
  const candidateContent = liveGeneratedContent || chapter?.generated_content;

  return (
    <main className="editor" aria-label="正文">
      {error ? (
        <div className="app-alert" role="alert">
          {error}
        </div>
      ) : null}
      {!chapter ? (
        <ProjectCreator idea={idea} busy={busy} onIdeaChange={onIdeaChange} onCreate={onCreateProject} />
      ) : (
        <>
          <div className="top-generation-toolbar" aria-label="生成控制">
            <div className="auto-mode-control">
              <span className="auto-switch" aria-hidden="true" />
              <div>
                <strong>全自动</strong>
                <span>
                  {autoTask
                    ? `全自动：${autoTask.completed_count} / ${autoTask.target_count}`
                    : "开启后自动生成、审核、更新上下文并进入下一章"}
                </span>
              </div>
            </div>
            <div className="toolbar-actions">
              <label className="compact-number-field">
                <span>自动生成章数</span>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={autoChapterCount}
                  onChange={(event) => onAutoChapterCountChange(event.target.value)}
                  disabled={busy}
                  aria-label="自动生成章数"
                />
              </label>
              <button type="button" className="primary-button" onClick={onAutoGenerate} disabled={busy} title="开始全自动">
                <span>开始全自动</span>
              </button>
              <button type="button" className="secondary-button" onClick={onGenerate} disabled={busy} title="重新生成">
                <span>重新生成</span>
              </button>
              <button type="button" className="secondary-button" disabled={busy} title="生成记录">
                <span>生成记录</span>
              </button>
            </div>
          </div>
          <div className="editor-toolbar">
            <div>
              <h1>{chapter.title}</h1>
              <span>第 {chapter.number} 章</span>
            </div>
            <div className="toolbar-actions">
              <button type="button" className="icon-text-button" onClick={onSave} disabled={busy} title="保存正文">
                <Save size={16} />
                <span>保存</span>
              </button>
              <button type="button" className="primary-button" onClick={onGenerate} disabled={busy} title="生成章节">
                <Zap size={16} />
                <span>生成</span>
              </button>
            </div>
          </div>
          <textarea
            className="chapter-textarea"
            value={editorContent}
            onChange={(event) => onEditorChange(event.target.value)}
          />
          {candidateContent ? (
            <section className="candidate" aria-label="生成结果">
              <h2>生成结果</h2>
              <p>{candidateContent}</p>
              <div className="toolbar-actions">
                <button type="button" className="primary-button" onClick={onAccept} disabled={busy} title="采纳">
                  <Check size={16} />
                  <span>采纳</span>
                </button>
                <button type="button" className="secondary-button" onClick={onReject} disabled={busy} title="拒绝">
                  <X size={16} />
                  <span>拒绝</span>
                </button>
              </div>
            </section>
          ) : null}
        </>
      )}
    </main>
  );
}
