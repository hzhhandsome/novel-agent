import { Check, Save, X, Zap } from "lucide-react";
import type { AutoGenerationTask, Chapter, ModelConfig } from "../types";
import { ProjectCreator } from "./ProjectCreator";

interface ChapterEditorProps {
  chapter: Chapter | null;
  editorContent: string;
  liveGeneratedContent: string | null;
  autoChapterCount: string;
  autoTask: AutoGenerationTask | null;
  modelConfig: ModelConfig;
  modelApiKey: string;
  idea: string;
  busy: boolean;
  error: string | null;
  onIdeaChange: (value: string) => void;
  onAutoChapterCountChange: (value: string) => void;
  onModelConfigChange: (value: ModelConfig) => void;
  onModelApiKeyChange: (value: string) => void;
  onSaveModelConfig: () => void;
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
  modelConfig,
  modelApiKey,
  idea,
  busy,
  error,
  onIdeaChange,
  onAutoChapterCountChange,
  onModelConfigChange,
  onModelApiKeyChange,
  onSaveModelConfig,
  onCreateProject,
  onEditorChange,
  onSave,
  onGenerate,
  onAutoGenerate,
  onAccept,
  onReject,
}: ChapterEditorProps) {
  const candidateContent = liveGeneratedContent || chapter?.generated_content;
  function routeModel(route: "generation" | "audit" | "summary") {
    return modelConfig.routes?.[route]?.model ?? "";
  }

  function updateRouteModel(route: "generation" | "audit" | "summary", model: string) {
    onModelConfigChange({
      ...modelConfig,
      routes: {
        ...(modelConfig.routes ?? {}),
        [route]: {
          provider: modelConfig.provider,
          base_url: modelConfig.base_url,
          model,
          max_tokens: modelConfig.max_tokens,
          api_key_set: modelConfig.api_key_set,
          routes: {},
        },
      },
    });
  }

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
              <label className="compact-select-field">
                <span>模型供应商</span>
                <select
                  value={modelConfig.provider}
                  onChange={(event) => onModelConfigChange({ ...modelConfig, provider: event.target.value })}
                  disabled={busy}
                  aria-label="模型供应商"
                >
                  <option value="mock">mock</option>
                  <option value="deepseek">deepseek</option>
                </select>
              </label>
              <label className="compact-text-field">
                <span>模型 Base URL</span>
                <input
                  type="text"
                  value={modelConfig.base_url}
                  onChange={(event) => onModelConfigChange({ ...modelConfig, base_url: event.target.value })}
                  disabled={busy}
                  aria-label="模型 Base URL"
                />
              </label>
              <label className="compact-text-field">
                <span>模型名称</span>
                <input
                  type="text"
                  value={modelConfig.model}
                  onChange={(event) => onModelConfigChange({ ...modelConfig, model: event.target.value })}
                  disabled={busy}
                  aria-label="模型名称"
                />
              </label>
              <label className="compact-number-field">
                <span>模型最大 token</span>
                <input
                  type="number"
                  min="256"
                  max="32768"
                  value={modelConfig.max_tokens}
                  onChange={(event) =>
                    onModelConfigChange({ ...modelConfig, max_tokens: Number.parseInt(event.target.value, 10) || 4096 })
                  }
                  disabled={busy}
                  aria-label="模型最大 token"
                />
              </label>
              <label className="compact-text-field">
                <span>模型 API Key</span>
                <input
                  type="password"
                  value={modelApiKey}
                  onChange={(event) => onModelApiKeyChange(event.target.value)}
                  disabled={busy}
                  aria-label="模型 API Key"
                />
              </label>
              <span className="model-key-status">{modelConfig.api_key_set ? "密钥已设置" : "未设置密钥"}</span>
              <label className="compact-text-field route-model-field">
                <span>生成模型</span>
                <input
                  type="text"
                  value={routeModel("generation")}
                  onChange={(event) => updateRouteModel("generation", event.target.value)}
                  disabled={busy}
                  aria-label="生成模型"
                />
              </label>
              <label className="compact-text-field route-model-field">
                <span>审核模型</span>
                <input
                  type="text"
                  value={routeModel("audit")}
                  onChange={(event) => updateRouteModel("audit", event.target.value)}
                  disabled={busy}
                  aria-label="审核模型"
                />
              </label>
              <label className="compact-text-field route-model-field">
                <span>摘要模型</span>
                <input
                  type="text"
                  value={routeModel("summary")}
                  onChange={(event) => updateRouteModel("summary", event.target.value)}
                  disabled={busy}
                  aria-label="摘要模型"
                />
              </label>
              <button type="button" className="secondary-button" onClick={onSaveModelConfig} disabled={busy} title="保存模型">
                <span>保存模型</span>
              </button>
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
              {candidateContent ? (
                <>
                  <button type="button" className="primary-button" onClick={onAccept} disabled={busy} title="采纳">
                    <Check size={16} />
                    <span>采纳</span>
                  </button>
                  <button type="button" className="secondary-button" onClick={onReject} disabled={busy} title="拒绝">
                    <X size={16} />
                    <span>拒绝</span>
                  </button>
                </>
              ) : null}
            </div>
          </div>
          <textarea
            aria-label="章节正文"
            className="chapter-textarea"
            value={editorContent}
            disabled={busy}
            onChange={(event) => onEditorChange(event.target.value)}
          />
        </>
      )}
    </main>
  );
}
