import type { Chapter, GenerationTask, Inspiration, Project } from "../types";

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
