import { useMemo, useState } from "react";
import {
  acceptChapter,
  addInspiration,
  createProject,
  generateChapter,
  getProject,
  rejectChapter,
  retryTask,
  updateChapter,
} from "./api/client";
import { AgentWorkspace } from "./components/AgentWorkspace";
import { ChapterEditor } from "./components/ChapterEditor";
import { ChapterSidebar } from "./components/ChapterSidebar";
import { ModulePanel } from "./components/ModulePanel";
import type { Chapter, GenerationTask, Project } from "./types";
import "./styles.css";

export default function App() {
  const [project, setProject] = useState<Project | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);
  const [editorContent, setEditorContent] = useState("");
  const [idea, setIdea] = useState("");
  const [inspirationText, setInspirationText] = useState("");
  const [task, setTask] = useState<GenerationTask | null>(null);
  const [busy, setBusy] = useState(false);

  const selectedChapter = useMemo(
    () => project?.chapters.find((chapter) => chapter.id === selectedChapterId) ?? null,
    [project, selectedChapterId],
  );

  function selectChapter(chapter: Chapter) {
    setSelectedChapterId(chapter.id);
    setEditorContent(chapter.content ?? "");
  }

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
    try {
      await action();
    } finally {
      setBusy(false);
    }
  }

  function handleCreateProject() {
    void runBusy(async () => {
      const created = await createProject({ idea });
      setProject(created);
      const first = created.chapters[0] ?? null;
      setSelectedChapterId(first?.id ?? null);
      setEditorContent(first?.content ?? "");
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
      const generated = await generateChapter(selectedChapter.id);
      setTask(generated);
      await refreshProject(generated.project_id);
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
    <div className="app-shell">
      <ChapterSidebar
        chapters={project?.chapters ?? []}
        selectedChapterId={selectedChapterId}
        onSelect={selectChapter}
        onGenerate={handleGenerate}
      />
      <ChapterEditor
        chapter={selectedChapter}
        editorContent={editorContent}
        idea={idea}
        busy={busy}
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
      <AgentWorkspace task={task} busy={busy} onRetry={handleRetry} />
    </div>
  );
}
