export type Level = 'A1' | 'A2' | 'B1' | 'B2' | 'C1';
export type Category = 'tenses' | 'grammar';
export type Example = { title: string; text: string; en: string; pl: string };
export type Exercise = { prompt: string; sentence: string; answer: string; alternatives?: string[]; options?: string[]; explanation: string };
export type Lesson = {
  id: string; title: string; subtitle: string; level: Level; category: Category;
  group: string; minutes: number; intro: string; uses: Example[];
  forms: { label: string; pattern: string; example: string }[];
  markers: string[]; pitfalls: string[];
  comparison: { title: string; a: string; b: string; explanation: string };
  exercises: Exercise[];
};
export type Word = { id: string; word: string; translation: string; level: string; example: string; pl: string };
export type Review = { id: string; kind: 'lesson' | 'word'; due: number; interval: number; repetitions: number; lastScore: number };
export type Progress = {
  completed: Record<string, { score: number; date: number; attempts: number }>;
  reviews: Record<string, Review>; activity: Record<string, number>;
  savedWords: string[]; dailyGoal: number; lastLesson?: string;
};
