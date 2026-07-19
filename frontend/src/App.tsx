import { useEffect, useMemo, useState } from "react";
import {
  acceptChapter,
  addInspiration,
  createProject,
  getProject,
  getModelConfig,
  listProjects,
  rejectChapter,
  reviewProjectIdea,
  reviewProjectInput,
  retryTask,
  streamAutoGenerateChapters,
  streamGenerateChapter,
  updateChapter,
  updateModelConfig,
} from "./api/client";
import { AgentWorkspace } from "./components/AgentWorkspace";
import { ChapterEditor } from "./components/ChapterEditor";
import { ChapterSidebar } from "./components/ChapterSidebar";
import { ModulePanel } from "./components/ModulePanel";
import type { AutoGenerationTask, Chapter, GenerationTask, InputReviewResult, ModelConfig, Project } from "./types";
import "./styles.css";

function getGeneratedContentFromTask(task: GenerationTask | null, chapterId: number | null): string | null {
  if (!task || task.chapter_id !== chapterId) return null;
  const proseStep = task.steps.find((step) => step.name === "generate_prose");
  const generated = proseStep?.output_snapshot?.generated_content;
  return typeof generated === "string" && generated.trim() ? generated : null;
}

const defaultModelConfig: ModelConfig = {
  provider: "mock",
  base_url: "https://api.deepseek.com/anthropic",
  model: "deepseek-v4-flash",
  max_tokens: 4096,
  api_key_set: false,
  routes: {},
};

function isModelConfig(value: unknown): value is ModelConfig {
  if (!value || typeof value !== "object" || Array.isArray(value)) return false;
  const item = value as Record<string, unknown>;
  return typeof item.provider === "string" && typeof item.base_url === "string" && typeof item.model === "string";
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [autoChapterCount, setAutoChapterCount] = useState("3");
  const [modelConfig, setModelConfig] = useState<ModelConfig>(defaultModelConfig);
  const [modelApiKey, setModelApiKey] = useState("");
  const [inputReview, setInputReview] = useState<InputReviewResult | null>(null);
  const [idea, setIdea] = useState("");
  const [inspirationText, setInspirationText] = useState("");
  const [task, setTask] = useState<GenerationTask | null>(null);
  const [autoTask, setAutoTask] = useState<AutoGenerationTask | null>(null);
  const [backstageCollapsed, setBackstageCollapsed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedChapter = useMemo(
    () => project?.chapters.find((chapter) => chapter.id === selectedChapterId) ?? null,
    [project, selectedChapterId],
  );
  const liveGeneratedContent = useMemo(
    () => getGeneratedContentFromTask(task, selectedChapterId),
    [task, selectedChapterId],
  );

  function selectChapter(chapter: Chapter) {
    setSelectedChapterId(chapter.id);
    setEditorContent(chapter.content ?? chapter.generated_content ?? "");
  }

  function loadProject(next: Project) {
    setProject(next);
    const first = next.chapters[0] ?? null;
    setSelectedChapterId(first?.id ?? null);
    setEditorContent(first?.content ?? first?.generated_content ?? "");
  }

  useEffect(() => {
    if (liveGeneratedContent) {
      setEditorContent(liveGeneratedContent);
    }
  }, [liveGeneratedContent]);

  useEffect(() => {
    void runBusy(async () => {
      const projects = await listProjects();
      const latest = projects[0] ?? null;
      if (latest) {
        loadProject(latest);
      }
    });
    void getModelConfig()
      .then((config) => {
        if (isModelConfig(config)) {
          setModelConfig(config);
        }
      })
      .catch(() => undefined);
  }, []);

  async function refreshProject(
    projectId = project?.id,
    visibleTask: GenerationTask | null = task,
    preferredChapterId = selectedChapterId,
  ) {
    if (!projectId) return;
    const next = await getProject(projectId);
    setProject(next);
    const current = next.chapters.find((chapter) => chapter.id === preferredChapterId) ?? next.chapters[0] ?? null;
    if (current) {
      const liveContent = getGeneratedContentFromTask(visibleTask, current.id);
      setSelectedChapterId(current.id);
      setEditorContent(liveContent ?? current.content ?? current.generated_content ?? "");
    }
  }

  async function runBusy(action: () => Promise<void>) {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(err instanceof Error ? err.message : "操作失败");
    } finally {
      setBusy(false);
    }
  }

  function handleCreateProject() {
    void runBusy(async () => {
      const review = await reviewProjectIdea(idea.trim());
      setInputReview(review);
      if (review.decision === "block") return;
      const created = await createProject({ idea });
      loadProject(created);
    });
  }

  function handleSave() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      await updateChapter(selectedChapter.id, { content: editorContent });
      await refreshProject();
    });
  }

  function handleGenerate() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      const generated = await streamGenerateChapter(selectedChapter.id, setTask);
      if (generated) {
        await refreshProject(generated.project_id, generated, generated.chapter_id);
      }
    });
  }

  function handleAutoGenerate() {
    if (!project) return;
    const chapterCount = Number.parseInt(autoChapterCount, 10);
    if (!Number.isFinite(chapterCount) || chapterCount < 1) {
      setError("自动生成章数必须大于 0");
      return;
    }
    void runBusy(async () => {
      const generated = await streamAutoGenerateChapters(project.id, chapterCount, (nextAutoTask) => {
        setAutoTask(nextAutoTask);
        if (nextAutoTask.current_chapter_id) {
          setSelectedChapterId(nextAutoTask.current_chapter_id);
        }
        if (nextAutoTask.current_chapter_task) {
          setTask(nextAutoTask.current_chapter_task);
        }
      });
      if (generated) {
        const preferredChapterId = generated.current_chapter_id ?? generated.current_chapter_task?.chapter_id ?? selectedChapterId;
        await refreshProject(generated.project_id, generated.current_chapter_task, preferredChapterId);
      }
    });
  }

  function handleAccept() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      await acceptChapter(selectedChapter.id);
      await refreshProject(project?.id, null);
    });
  }

  function handleReject() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      await rejectChapter(selectedChapter.id);
      await refreshProject(project?.id, null);
    });
  }

  function handleAddInspiration() {
    if (!project || !inspirationText.trim()) return;
    void runBusy(async () => {
      const review = await reviewProjectInput(project.id, "inspiration", inspirationText.trim());
      setInputReview(review);
      if (review.decision === "block") return;
      await addInspiration(project.id, inspirationText.trim());
      setInspirationText("");
      await refreshProject(project.id);
    });
  }

  function handleSaveModelConfig() {
    void runBusy(async () => {
      const routes = Object.fromEntries(
        ["generation", "audit", "summary"].map((route) => {
          const routeConfig = modelConfig.routes?.[route];
          const model = routeConfig?.model?.trim();
          return [
            route,
            model
              ? {
                  provider: modelConfig.provider,
                  base_url: modelConfig.base_url,
                  model,
                  max_tokens: modelConfig.max_tokens,
                }
              : null,
          ];
        }),
      );
      const updated = await updateModelConfig({
        provider: modelConfig.provider,
        base_url: modelConfig.base_url,
        model: modelConfig.model,
        max_tokens: modelConfig.max_tokens,
        api_key: modelApiKey.trim() || undefined,
        routes,
      });
      setModelConfig(updated);
      setModelApiKey("");
    });
  }

  function handleRetry() {
    if (!task) return;
    void runBusy(async () => {
      const nextTask = await retryTask(task.id);
      setTask(nextTask);
      await refreshProject(nextTask.project_id, nextTask, nextTask.chapter_id);
    });
  }

  return (
    <div className={backstageCollapsed ? "app-shell backstage-collapsed" : "app-shell"}>
      <ChapterSidebar
        chapters={project?.chapters ?? []}
        selectedChapterId={selectedChapterId}
        onSelect={selectChapter}
        onGenerate={handleGenerate}
      />
      <ChapterEditor
        chapter={selectedChapter}
        editorContent={editorContent}
        liveGeneratedContent={liveGeneratedContent}
        autoChapterCount={autoChapterCount}
        autoTask={autoTask}
        modelConfig={modelConfig}
        modelApiKey={modelApiKey}
        inputReview={inputReview}
        idea={idea}
        busy={busy}
        error={error}
        onIdeaChange={setIdea}
        onAutoChapterCountChange={setAutoChapterCount}
        onModelConfigChange={setModelConfig}
        onModelApiKeyChange={setModelApiKey}
        onSaveModelConfig={handleSaveModelConfig}
        onCreateProject={handleCreateProject}
        onEditorChange={setEditorContent}
        onSave={handleSave}
        onGenerate={handleGenerate}
        onAutoGenerate={handleAutoGenerate}
        onAccept={handleAccept}
        onReject={handleReject}
      />
      <ModulePanel
        project={project}
        inspirationText={inspirationText}
        busy={busy}
        onInspirationChange={setInspirationText}
        onAddInspiration={handleAddInspiration}
      />
      <AgentWorkspace
        project={project}
        task={task}
        busy={busy}
        collapsed={backstageCollapsed}
        onToggleCollapsed={() => setBackstageCollapsed((value) => !value)}
        onRetry={handleRetry}
      />
    </div>
  );
}
