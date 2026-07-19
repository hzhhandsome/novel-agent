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
  period_stage: string | null;
  period_summary: string | null;
  period_source_chapter_id: number | null;
}

export interface Inspiration {
  id: number;
  content: string;
  applied: boolean;
}

export interface StoryEvent {
  id: number;
  project_id: number;
  source_chapter_id: number | null;
  title: string;
  summary: string;
  characters: string | null;
  location: string | null;
  consequence: string | null;
}

export interface WorldRule {
  id: number;
  project_id: number;
  source_chapter_id: number | null;
  rule: string;
  limitation: string | null;
  exception: string | null;
  status: string;
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
  story_events: StoryEvent[];
  world_rules: WorldRule[];
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
  model_config_snapshot?: Record<string, unknown> | null;
  chapter: Chapter | null;
  steps: GenerationStep[];
}

export interface ModelConfig {
  provider: string;
  base_url: string;
  model: string;
  max_tokens: number;
  api_key_set: boolean;
  routes?: Record<string, ModelConfig>;
}

export interface AutoGenerationCompletedChapter {
  id: number;
  number: number;
  title: string;
}

export interface AutoGenerationTask {
  id: number;
  project_id: number;
  kind: "auto_chapter_generation";
  status: string;
  current_step: string | null;
  error_type: string | null;
  error_message: string | null;
  model_config_snapshot?: Record<string, unknown> | null;
  target_count: number;
  completed_count: number;
  current_chapter_id: number | null;
  current_chapter_task: GenerationTask | null;
  completed_chapters: AutoGenerationCompletedChapter[];
  steps: GenerationStep[];
}
