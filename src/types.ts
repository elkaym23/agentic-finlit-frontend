export type Role = "Student" | "Teacher";
export type LevelSlug = "beginner" | "intermediate" | "advanced";

export interface User {
  user_id: number; name: string; email: string; role: Role; title?: string | null;
  level_slug: LevelSlug; avatar: string; xp: number; rank: number;
  xp_into_rank: number; xp_per_rank: number; streak: number;
}

export interface PathLesson {
  lesson_id: number; level: LevelSlug; position: number; title: string; emoji: string; description: string;
  minutes: number; quiz_id: number; pass_pct: number; status: "locked" | "available" | "in_progress" | "completed";
  best_pct: number | null;
}
export interface PathGame { slug: string; name: string; emoji: string; blurb: string; won: boolean; status: "locked" | "available" | "completed"; }
export interface PathLevel {
  slug: LevelSlug; name: string; emoji: string; ages: string; blurb: string; color: string;
  unlocked: boolean; completed: boolean; progress: number; lessons: PathLesson[]; games: PathGame[];
}
export type NextStep =
  | { type: "lesson"; lesson_id: number; title: string; level?: LevelSlug }
  | { type: "game"; slug: string; title: string; level: LevelSlug }
  | { type: "retry"; lesson_id?: number; quiz_id?: number }
  | { type: "class" } | { type: "path" };
export interface LearningPath { levels: PathLevel[]; continue: NextStep | null; current_level: LevelSlug; graduated: boolean; }

export interface Section { position: number; title: string; content: string; }
export interface Lesson {
  lesson_id: number; title: string; description: string; emoji?: string; minutes?: number; level: LevelSlug;
  is_core: boolean; sections: Section[]; quiz_id: number | null; level_name?: string; level_emoji?: string;
  position?: number; lesson_count?: number; best_pct?: number | null; doc_name?: string | null;
  progress?: { status: string; current_pos: number } | null;
}

export interface QuizItem {
  item_id: number; position: number; kind: "mcq" | "short"; question: string; options: string[]; points: number;
  answer_key?: string | null; explanation?: string | null; rubric?: string | null;
}
export interface Quiz {
  quiz_id: number; title: string; description?: string | null; level: LevelSlug; pass_pct: number; is_core: boolean;
  lesson_id: number | null; lesson_title?: string | null; items: QuizItem[];
  last_attempt?: { submission_id: number; percent: number; passed: boolean } | null;
}

export interface ItemResult {
  item_id: number; kind: "mcq" | "short"; question: string; answer: string; points: number; earned: number;
  correct: boolean | null; explanation?: string; answer_text?: string; correct_text?: string; feedback?: string;
}
export interface ChatMsg { role: "user" | "assistant"; content: string; created_at?: string; }
export interface Submission {
  submission_id: number; quiz_id: number; quiz_title: string; lesson_title?: string | null; is_core: boolean;
  score: number; total: number; percent: number; passed: boolean; xp: number; feedback: string;
  results: ItemResult[]; chat: ChatMsg[]; next?: NextStep; user?: User; quiz_lesson_id?: number | null;
  submitted_at: string;
}

export interface LeaderRow { user_id: number; name: string; avatar: string; xp: number; rank: number; position: number;
  lessons_done: number; games_won: number; streak: number; }
export interface Assignment {
  assignment_id: number; lesson_id: number | null; quiz_id: number | null; due_at: string | null; created_at: string;
  title: string; description?: string | null; level: LevelSlug; lesson_status: string; best_pct: number | null; attempts: number;
}
export interface MyClass {
  class_id: number; name: string; code: string; joined_at: string; teacher_name: string;
  assignments: Assignment[]; my_position: number | null; size: number;
}
