"""End-to-end checks using Python Playwright and the system Chromium.

Run the application first, then: python3 tests/browser_smoke.py
Optional environment variables: BASE_URL and CHROMIUM_PATH.
All browser data lives in an isolated, disposable context.
"""
import json
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = os.environ.get('BASE_URL', 'http://127.0.0.1:5173')
STORAGE_KEY = 'gramly-progress-v1'


def stored(page):
    return page.evaluate('(key) => JSON.parse(localStorage.getItem(key))', STORAGE_KEY)


def select_answer(page, exercise, wrong=False):
    if exercise.get('options'):
        target = next((option for option in exercise['options'] if option != exercise['answer']), None) if wrong else exercise['answer']
        for option in page.get_by_role('radio').all():
            if option.text_content()[1:] == target:
                option.click()
                break
        else:
            raise AssertionError(f"Missing answer option: {target}")
    else:
        page.get_by_label('Twoja odpowiedź', exact=True).fill('incorrect answer' if wrong else exercise['answer'])
    page.get_by_role('button', name='Sprawdź odpowiedź', exact=True).click()
    expect(page.locator('.answer-feedback')).to_be_visible()
    expect(page.locator('.answer-feedback')).to_have_class(re.compile('incorrect' if wrong else r'(?<!in)correct'))


def complete_quiz(page, questions, wrong_first=False):
    for index, exercise in enumerate(questions):
        select_answer(page, exercise, wrong=wrong_first and index == 0)
        page.get_by_role('button', name='Zobacz wynik' if index + 1 == len(questions) else 'Następne pytanie', exact=True).click()
    expect(page.locator('.quiz-result')).to_be_visible()


def nav(page, title):
    page.locator('.sidebar').get_by_role('button', name=re.compile('^' + re.escape(title) + r'(?:\s+\d+)?$')).click()


def axe_check(page, label):
    page.add_script_tag(path=str(ROOT / 'node_modules/axe-core/axe.min.js'))
    violations = page.evaluate("""async () => (await axe.run(document, {
      runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}
    })).violations.map(v => ({id:v.id, nodes:v.nodes.map(n=>n.target)}))""")
    assert not violations, f'{label}: {json.dumps(violations)}'


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width': 1440, 'height': 1050}, reduced_motion='reduce')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(BASE_URL, wait_until='networkidle')
    expect(page).to_have_title('Gramly — angielski, który ma sens')
    data = page.evaluate("async () => { const d = await import('/src/curriculum.ts'); return {lessons:d.lessons, words:d.vocabulary}; }")
    lesson_data = data['lessons']
    assert len(lesson_data) == 36
    assert sum(len(l['exercises']) for l in lesson_data) == 168
    expect(page.locator('.lesson-card')).to_have_count(12)
    axe_check(page, 'desktop dashboard')
    print('PASS: dashboard, 12 tenses, accessibility', flush=True)

    # Real failed attempt: 3/4 must not be reported as mastery.
    page.get_by_role('button', name='Zacznij od podstaw', exact=True).click()
    expect(page.get_by_role('heading', name='Podstawy zdania.', exact=True)).to_be_visible()
    for step in ['Jak tworzymy?', 'Porównaj i zrozum']:
        page.get_by_role('button', name=re.compile(re.escape(step))).click()
    axe_check(page, 'lesson')
    page.get_by_role('button', name='Sprawdź się w praktyce', exact=True).click()
    basics = next(l for l in lesson_data if l['id'] == 'sentence-basics')
    axe_check(page, 'quiz')
    complete_quiz(page, basics['exercises'], wrong_first=True)
    expect(page.locator('.result-score > strong')).to_have_text('75%')
    saved = stored(page)
    assert saved['completed']['sentence-basics']['score'] == 75
    assert saved['reviews']['sentence-basics']['interval'] == 1 / 24
    page.reload(wait_until='networkidle')
    assert stored(page)['completed']['sentence-basics']['score'] == 75
    print('PASS: failed quiz, one-hour retry, persistence after reload', flush=True)

    nav(page, 'Biblioteka wiedzy')
    page.get_by_label('Szukaj tematu').fill('perfect')
    expect(page.locator('.lesson-card')).to_have_count(6)
    page.get_by_label('Szukaj tematu').fill('does-not-exist')
    expect(page.locator('.empty-state')).to_be_visible()
    page.get_by_role('button', name='Wyczyść filtry').click()
    page.get_by_role('button', name='A1', exact=True).click()
    expect(page.locator('.lesson-card')).to_have_count(3)
    page.get_by_role('button', name='Wszystkie', exact=True).click()
    page.get_by_role('tab', name=re.compile('Konstrukcje gramatyczne')).click()
    expect(page.locator('.lesson-card')).to_have_count(24)
    print('PASS: category tabs, search, level filters, empty results', flush=True)

    # Every curriculum exercise is answered through the rendered controls.
    for lesson in lesson_data:
        nav(page, 'Biblioteka wiedzy')
        page.get_by_role('tab', name=re.compile('Czasy angielskie' if lesson['category'] == 'tenses' else 'Konstrukcje gramatyczne')).click()
        page.locator('.lesson-card').filter(has=page.get_by_role('heading', name=lesson['title'], exact=True)).click()
        page.get_by_role('button', name='Przejdź do ćwiczeń', exact=True).click()
        complete_quiz(page, lesson['exercises'])
        expect(page.locator('.result-score > strong')).to_have_text('100%')
        assert stored(page)['completed'][lesson['id']]['score'] == 100
    assert len(stored(page)['completed']) == 36
    print('PASS: all 36 quizzes, 168 answers, mastery and scheduling', flush=True)

    nav(page, 'Mój pulpit')
    page.get_by_role('button', name='Rozpocznij trening', exact=True).click()
    question_count = int(page.locator('.quiz-progress-label').inner_text().split('z ')[1].split('\n')[0])
    for i in range(question_count):
        sentence = page.locator('.question-card h2').inner_text()
        exercise = next(e for lesson in lesson_data for e in lesson['exercises'] if e['sentence'] == sentence)
        select_answer(page, exercise)
        page.get_by_role('button', name='Zobacz wynik' if i + 1 == question_count else 'Następne pytanie', exact=True).click()
    expect(page.locator('.result-score > strong')).to_have_text('100%')
    print('PASS: mixed practice', flush=True)

    nav(page, 'Słownictwo')
    expect(page.locator('.word-card')).to_have_count(24)
    page.get_by_role('button', name='Zapisz słowo alleviate', exact=True).click()
    assert 'alleviate' in stored(page)['savedWords']
    page.get_by_role('button', name=re.compile('Moje słowa')).click()
    expect(page.locator('.word-card')).to_have_count(1)
    nav(page, 'Powtórki')
    page.locator('.review-row').filter(has=page.get_by_role('heading', name='alleviate', exact=True)).get_by_role('button', name='Powtórz').click()
    page.get_by_label('Wpisz angielskie słowo').fill('alleviate')
    page.get_by_role('button', name='Sprawdź', exact=True).click()
    page.get_by_role('button', name='Zapisz wynik', exact=True).click()
    assert stored(page)['reviews']['alleviate']['interval'] == 1
    axe_check(page, 'reviews')
    print('PASS: vocabulary bookmarks, written recall, daily scheduling', flush=True)

    # Simulate time passing using a test-only edit of this isolated context.
    page.evaluate("""key => { const p=JSON.parse(localStorage.getItem(key));p.reviews['present-simple'].due=Date.now()-1000;localStorage.setItem(key,JSON.stringify(p)); }""", STORAGE_KEY)
    page.reload(wait_until='networkidle')
    nav(page, 'Powtórki')
    page.locator('.review-row').filter(has=page.get_by_role('heading', name='Present Simple', exact=True)).get_by_role('button', name='Powtórz').click()
    complete_quiz(page, next(l for l in lesson_data if l['id'] == 'present-simple')['exercises'])
    assert stored(page)['reviews']['present-simple']['interval'] == 3
    nav(page, 'Moja ścieżka')
    expect(page.locator('.path-lesson')).to_have_count(36)
    expect(page.locator('.path-percentage')).to_have_text('100%')
    axe_check(page, 'learning path')

    page.get_by_role('button', name='Ustawienia nauki', exact=True).click()
    page.get_by_role('button', name='10 Dobry rytm', exact=True).click()
    assert stored(page)['dailyGoal'] == 10
    axe_check(page, 'settings dialog')
    with page.expect_download() as download_info:
        page.get_by_role('button', name='Pobierz kopię postępu').click()
    downloaded = json.loads(Path(download_info.value.path()).read_text())
    assert len(downloaded['completed']) == 36
    page.keyboard.press('Escape')
    expect(page.get_by_role('dialog')).to_have_count(0)
    print('PASS: due review, increased spacing, path, goal, export, modal keyboard', flush=True)

    nav(page, 'Jak się tutaj uczysz?')
    expect(page.locator('.method-card')).to_have_count(6)
    axe_check(page, 'methods')

    # Check the real mobile navigation and several compact breakpoints.
    nav(page, 'Mój pulpit')
    for width in [320, 390, 768, 1024, 1440]:
        page.set_viewport_size({'width': width, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
    page.set_viewport_size({'width': 390, 'height': 844})
    page.get_by_role('button', name='Otwórz menu').click()
    nav(page, 'Moja ścieżka')
    expect(page.locator('.sidebar')).not_to_have_class(re.compile('is-open'))
    expect(page.locator('.path-lesson')).to_have_count(36)
    axe_check(page, 'mobile path')
    page.get_by_role('button', name='Otwórz menu').click()
    nav(page, 'Słownictwo')
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    axe_check(page, 'mobile vocabulary')
    page.set_viewport_size({'width': 1440, 'height': 1050})
    page.get_by_role('button', name='Ustawienia nauki').click()
    page.get_by_role('button', name='Zacznij od nowa — wyzeruj postęp').click()
    page.get_by_role('button', name='Anuluj', exact=True).click()
    assert len(stored(page)['completed']) == 36
    page.get_by_role('button', name='Zacznij od nowa — wyzeruj postęp').click()
    page.get_by_role('button', name='Tak, wyzeruj postęp', exact=True).click()
    assert stored(page)['completed'] == {}
    assert stored(page)['savedWords'] == []
    assert not errors, errors
    print('PASS: methods, responsive layouts, mobile navigation, safe reset, no browser errors', flush=True)
    context.close()
    browser.close()
