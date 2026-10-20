import type { Exercise, Progress, Review } from './types';

export const STORAGE_KEY = 'gramly-progress-v1';
export const DAY = 86_400_000;
export const emptyProgress = (): Progress => ({ completed: {}, reviews: {}, activity: {}, savedWords: [], dailyGoal: 5 });

export function localDate(time = Date.now()): string {
  const date = new Date(time);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

export function loadProgress(): Progress {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return emptyProgress();
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return emptyProgress();
    const base = emptyProgress();
    if (parsed.completed && typeof parsed.completed === 'object') {
      for (const [id, value] of Object.entries(parsed.completed)) {
        const item = value as { score?: unknown; date?: unknown; attempts?: unknown } | null;
        if (item && typeof item.score === 'number' && item.score >= 0 && item.score <= 100 && typeof item.date === 'number' && Number.isFinite(item.date) && typeof item.attempts === 'number') base.completed[id] = item as Progress['completed'][string];
      }
    }
    if (parsed.reviews && typeof parsed.reviews === 'object') {
      for (const [id, value] of Object.entries(parsed.reviews)) {
        const item = value as Review | null;
        if (item && item.id === id && ['lesson', 'word'].includes(item.kind) && [item.due, item.interval, item.repetitions, item.lastScore].every(n => typeof n === 'number' && Number.isFinite(n))) base.reviews[id] = item;
      }
    }
    if (parsed.activity && typeof parsed.activity === 'object') {
      for (const [date, count] of Object.entries(parsed.activity)) if (/^\d{4}-\d{2}-\d{2}$/.test(date) && typeof count === 'number' && count >= 0 && Number.isFinite(count)) base.activity[date] = count;
    }
    if (Array.isArray(parsed.savedWords)) base.savedWords = [...new Set(parsed.savedWords.filter((id: unknown): id is string => typeof id === 'string'))] as string[];
    if ([5, 10, 15].includes(parsed.dailyGoal)) base.dailyGoal = parsed.dailyGoal;
    if (typeof parsed.lastLesson === 'string') base.lastLesson = parsed.lastLesson;
    return base;
  } catch { return emptyProgress(); }
}

export function normalise(value: string): string {
  return value.trim().toLowerCase()
    .replace(/[’‘`]/g, "'")
    .replace(/[.,!?;:]+$/g, '').trim().replace(/\s+/g, ' ')
    // In full negative tags the pronoun precedes not: "is she not?".
    // Do not accidentally teach the ungrammatical "is not she?".
    .replace(/^(is|are|was|were|do|does|did|have|has|had|could|would|should|must)n't (i|you|he|she|it|we|they)$/, '$1 $2 not')
    .replace(/^won't (i|you|he|she|it|we|they)$/, 'will $1 not')
    .replace(/\bwon't\b/g, 'will not').replace(/\bcan't\b/g, 'cannot')
    .replace(/\bcannot\b/g, 'can not').replace(/\bshan't\b/g, 'shall not')
    .replace(/n't\b/g, ' not').replace(/\bi'm\b/g, 'i am')
    .replace(/\b(you|we|they)'re\b/g, '$1 are')
    .replace(/\b(i|you|we|they)'ve\b/g, '$1 have')
    .replace(/\b(i|you|he|she|it|we|they)'ll\b/g, '$1 will');
}

export const isCorrect = (answer: string, exercise: Exercise): boolean => [exercise.answer, ...(exercise.alternatives ?? [])].some(value => normalise(answer) === normalise(value));

export function scheduleReview(previous: Review | undefined, id: string, kind: Review['kind'], score: number, now = Date.now()): Review {
  const successful = score >= 80;
  // Early practice is welcome, but it is not evidence of recall after a delay.
  if (successful && previous && previous.repetitions > 0 && previous.due > now) return { ...previous, lastScore: score };
  const repetitions = successful ? (previous?.repetitions ?? 0) + 1 : 0;
  const intervals = [1, 3, 7, 14, 30, 60];
  const interval = successful ? intervals[Math.min(repetitions - 1, intervals.length - 1)] : 1 / 24;
  return { id, kind, lastScore: score, repetitions, interval, due: now + interval * DAY };
}

export function streak(activity: Progress['activity'], now = Date.now()): number {
  const cursor = new Date(now);
  if (!activity[localDate(cursor.getTime())]) cursor.setDate(cursor.getDate() - 1);
  let result = 0;
  while (activity[localDate(cursor.getTime())]) {
    result++;
    cursor.setDate(cursor.getDate() - 1);
  }
  return result;
}

export function shuffle<T>(items: readonly T[]): T[] {
  const result = [...items];
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [result[i], result[j]] = [result[j], result[i]];
  }
  return result;
}
