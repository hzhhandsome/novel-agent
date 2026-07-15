export type ChapterStatus = "not_generated" | "generating" | "generated" | "accepted";

export interface Chapter {
  id: number;
  project_id: number;
  number: number;
  title: string;
  status: ChapterStatus;
  content: string | null;
  generated_content: string | null;
  summary: string | null;
}

export interface Character {
  id: number;
  name: string;
  role: string | null;
  personality: string | null;
  current_goal: string | null;
  key_memories: string | null;
  relationships: string | null;
  writing_notes: string | null;
}

export interface Inspiration {
  id: number;
  content: string;
  applied: boolean;
}

export interface ForeshadowingItem {
  id: number;
  content: string;
  status: string;
  notes: string | null;
}

export interface Project {
  id: number;
  title: string;
  idea: string;
  positioning: string | null;
  worldview: string | null;
  main_plot: string | null;
  chapters: Chapter[];
  characters: Character[];
  foreshadowing_items: ForeshadowingItem[];
  inspirations: Inspiration[];
}

export interface GenerationStep {
  id: number;
  task_id: number;
  name: string;
  status: string;
  input_snapshot: Record<string, unknown> | null;
  output_snapshot: Record<string, unknown> | null;
  error_message: string | null;
}

export interface GenerationTask {
  id: number;
  project_id: number;
  chapter_id: number | null;
  kind: string;
  status: string;
  current_step: string | null;
  error_type: string | null;
  error_message: string | null;
  chapter: Chapter | null;
  steps: GenerationStep[];
}
