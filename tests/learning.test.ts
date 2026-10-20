import { test } from 'node:test';
import assert from 'node:assert/strict';
import { DAY, isCorrect, normalise, scheduleReview, streak, localDate, loadProgress, STORAGE_KEY } from '../src/learning.ts';
import { lessons, learningPath } from '../src/curriculum.ts';

test('successful reviews increase spacing; an incorrect recall resets it to one hour', () => {
  const now = 1_800_000_000_000;
  let review = scheduleReview(undefined, 'present-simple', 'lesson', 80, now);
  assert.equal(review.due, now + DAY);
  for (const interval of [3, 7, 14, 30, 60, 60]) {
    const reviewTime = review.due;
    review = scheduleReview(review, 'present-simple', 'lesson', 100, reviewTime);
    assert.equal(review.interval, interval);
    assert.equal(review.due, reviewTime + interval * DAY);
  }
  review = scheduleReview(review, 'present-simple', 'lesson', 79, now);
  assert.equal(review.repetitions, 0);
  assert.equal(review.due, now + 3_600_000);
  review = scheduleReview(review, 'present-simple', 'lesson', 100, now);
  assert.equal(review.interval, 1);
});

test('early successful practice does not falsely lengthen the recall interval', () => {
  const now = 1_800_000_000_000;
  const first = scheduleReview(undefined, 'alleviate', 'word', 100, now);
  const early = scheduleReview(first, 'alleviate', 'word', 100, now + 60_000);
  assert.equal(early.due, first.due);
  assert.equal(early.repetitions, first.repetitions);
  const failed = scheduleReview(early, 'alleviate', 'word', 0, now + 120_000);
  assert.equal(failed.repetitions, 0);
  assert.equal(failed.due, now + 120_000 + 3_600_000);
});

test('matching handles punctuation, typographic apostrophes and supported contractions without accepting wrong tense', () => {
  const exercise = { prompt: '', sentence: '', explanation: '', answer: 'does not eat' };
  assert.ok(isCorrect('  Doesn’t eat.  ', exercise));
  assert.ok(!isCorrect('does not eats', exercise));
  assert.ok(!isCorrect('did not eat', exercise));
  assert.equal(normalise("won't go"), normalise('will not go'));
  assert.equal(normalise("can't go"), normalise('cannot go'));
  assert.equal(normalise("we've been working"), normalise('we have been working'));
  assert.ok(isCorrect('will be traveling', { ...exercise, answer: 'will be travelling', alternatives: ['will be traveling'] }));
  assert.ok(isCorrect('is she not?', { ...exercise, answer: "isn't she" }));
  assert.ok(!isCorrect('is not she?', { ...exercise, answer: "isn't she" }));
});

test('streak crosses month boundaries and survives a not-yet-active current day', () => {
  const now = new Date(2026, 2, 2, 12).getTime();
  assert.equal(streak({ '2026-02-28': 3, '2026-03-01': 1 }, now), 2);
  assert.equal(streak({ '2026-02-28': 3, '2026-03-01': 1, '2026-03-02': 2 }, now), 3);
  assert.equal(streak({ '2026-02-27': 5 }, now), 0);
  assert.equal(localDate(new Date(2026, 0, 1, 12).getTime()), '2026-01-01');
});

test('corrupt stored progress does not crash startup or manufacture mastered lessons', () => {
  let value = '{broken';
  Object.defineProperty(globalThis, 'localStorage', { configurable: true, value: { getItem: (key: string) => key === STORAGE_KEY ? value : null } });
  assert.deepEqual(loadProgress().completed, {});
  value = JSON.stringify({ completed: { wrong: { score: '100' }, invalid: null, valid: { score: 83, date: Date.now(), attempts: 1 } }, dailyGoal: 999, savedWords: ['word', 42, 'word'] });
  const progress = loadProgress();
  assert.deepEqual(Object.keys(progress.completed), ['valid']);
  assert.equal(progress.dailyGoal, 5);
  assert.deepEqual(progress.savedWords, ['word']);
});

test('every multiple-choice answer is unambiguous and all topics can be practised', () => {
  assert.equal(lessons.filter(l => l.category === 'tenses').length, 12);
  assert.equal(lessons.filter(l => l.category === 'grammar').length, 24);
  assert.equal(new Set(lessons.map(l => l.id)).size, lessons.length);
  assert.equal(learningPath[0].id, 'sentence-basics');
  for (const lesson of lessons) {
    assert.ok(lesson.exercises.length >= 4, lesson.id);
    for (const exercise of lesson.exercises) {
      assert.ok(exercise.answer.trim() && exercise.explanation.trim(), lesson.id);
      if (exercise.options) assert.equal(exercise.options.filter(option => isCorrect(option, exercise)).length, 1, lesson.id);
    }
  }
});
