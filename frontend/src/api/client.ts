import type { AutoGenerationTask, Chapter, GenerationTask, InputReviewResult, Inspiration, ModelConfig, Project } from "../types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function createProject(payload: { idea: string; genre?: string; style?: string }): Promise<Project> {
  return request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listProjects(): Promise<Project[]> {
  return request<Project[]>("/api/projects");
}

export function getProject(projectId: number): Promise<Project> {
  return request<Project>(`/api/projects/${projectId}`);
}

export function updateChapter(chapterId: number, payload: { title?: string; content?: string }): Promise<Chapter> {
  return request<Chapter>(`/api/chapters/${chapterId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function generateChapter(chapterId: number): Promise<GenerationTask> {
  return request<GenerationTask>(`/api/chapters/${chapterId}/generate`, { method: "POST" });
}

export async function streamGenerateChapter(
  chapterId: number,
  onTask: (task: GenerationTask) => void,
): Promise<GenerationTask | null> {
  const response = await fetch(`/api/chapters/${chapterId}/generate/stream`, { method: "POST" });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let latest: GenerationTask | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice(6));
      if (payload.id) {
        latest = payload as GenerationTask;
        onTask(latest);
      }
    }
  }

  return latest;
}

export async function streamAutoGenerateChapters(
  projectId: number,
  chapterCount: number,
  onAutoTask: (task: AutoGenerationTask) => void,
): Promise<AutoGenerationTask | null> {
  const response = await fetch(`/api/projects/${projectId}/auto-generate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ chapter_count: chapterCount }),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (!response.body) {
    throw new Error("浏览器不支持流式响应");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let latest: AutoGenerationTask | null = null;

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice(6));
      if (payload.id) {
        latest = payload as AutoGenerationTask;
        onAutoTask(latest);
      }
    }
  }

  return latest;
}

export function acceptChapter(chapterId: number): Promise<Chapter> {
  return request<Chapter>(`/api/chapters/${chapterId}/accept`, { method: "POST" });
}

export function rejectChapter(chapterId: number): Promise<Chapter> {
  return request<Chapter>(`/api/chapters/${chapterId}/reject`, { method: "POST" });
}

export function addInspiration(projectId: number, content: string): Promise<Inspiration> {
  return request<Inspiration>(`/api/projects/${projectId}/inspirations`, {
    method: "POST",
    body: JSON.stringify({ content }),
  });
}

export function retryTask(taskId: number): Promise<GenerationTask> {
  return request<GenerationTask>(`/api/generation-tasks/${taskId}/retry`, { method: "POST" });
}

export function getModelConfig(): Promise<ModelConfig> {
  return request<ModelConfig>("/api/model-config");
}

export function updateModelConfig(payload: {
  provider?: string;
  base_url?: string;
  model?: string;
  max_tokens?: number;
  api_key?: string;
  routes?: Record<string, Partial<ModelConfig> | null>;
}): Promise<ModelConfig> {
  return request<ModelConfig>("/api/model-config", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function reviewProjectIdea(content: string): Promise<InputReviewResult> {
  return request<InputReviewResult>("/api/projects/input-review", {
    method: "POST",
    body: JSON.stringify({ input_kind: "project_idea", content }),
  });
}

export function reviewProjectInput(projectId: number, inputKind: string, content: string): Promise<InputReviewResult> {
  return request<InputReviewResult>(`/api/projects/${projectId}/input-review`, {
    method: "POST",
    body: JSON.stringify({ input_kind: inputKind, content }),
  });
}
