import { useEffect, useMemo, useState } from "react";
import {
  acceptChapter,
  addInspiration,
  createProject,
  getProject,
  listProjects,
  rejectChapter,
  retryTask,
  streamGenerateChapter,
  updateChapter,
} from "./api/client";
import { AgentWorkspace } from "./components/AgentWorkspace";
import { ChapterEditor } from "./components/ChapterEditor";
import { ChapterSidebar } from "./components/ChapterSidebar";
import { ModulePanel } from "./components/ModulePanel";
import type { Chapter, GenerationTask, Project } from "./types";
import "./styles.css";

function getGeneratedContentFromTask(task: GenerationTask | null, chapterId: number | null): string | null {
  if (!task || task.chapter_id !== chapterId) return null;
  const proseStep = task.steps.find((step) => step.name === "generate_prose");
  const generated = proseStep?.output_snapshot?.generated_content;
  return typeof generated === "string" && generated.trim() ? generated : null;
}

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [idea, setIdea] = useState("");
  const [inspirationText, setInspirationText] = useState("");
  const [task, setTask] = useState<GenerationTask | null>(null);
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
    setEditorContent(chapter.content ?? "");
  }

  function loadProject(next: Project) {
    setProject(next);
    const first = next.chapters[0] ?? null;
    setSelectedChapterId(first?.id ?? null);
    setEditorContent(first?.content ?? "");
  }

  useEffect(() => {
    void runBusy(async () => {
      const projects = await listProjects();
      const latest = projects[0] ?? null;
      if (latest) {
        loadProject(latest);
      }
    });
  }, []);

  async function refreshProject(projectId = project?.id) {
    if (!projectId) return;
    const next = await getProject(projectId);
    setProject(next);
    const current = next.chapters.find((chapter) => chapter.id === selectedChapterId) ?? next.chapters[0] ?? null;
    if (current) {
      setSelectedChapterId(current.id);
      setEditorContent(current.content ?? "");
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
        await refreshProject(generated.project_id);
      }
    });
  }

  function handleAccept() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      await acceptChapter(selectedChapter.id);
      await refreshProject();
    });
  }

  function handleReject() {
    if (!selectedChapter) return;
    void runBusy(async () => {
      await rejectChapter(selectedChapter.id);
      await refreshProject();
    });
  }

  function handleAddInspiration() {
    if (!project || !inspirationText.trim()) return;
    void runBusy(async () => {
      await addInspiration(project.id, inspirationText.trim());
      setInspirationText("");
      await refreshProject(project.id);
    });
  }

  function handleRetry() {
    if (!task) return;
    void runBusy(async () => {
      const nextTask = await retryTask(task.id);
      setTask(nextTask);
      await refreshProject(nextTask.project_id);
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
        idea={idea}
        busy={busy}
        error={error}
        onIdeaChange={setIdea}
        onCreateProject={handleCreateProject}
        onEditorChange={setEditorContent}
        onSave={handleSave}
        onGenerate={handleGenerate}
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
