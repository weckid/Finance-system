"""
AI/ML-анализ чека: автоматическое определение категории и названия магазина.

Цепочка: 1) OpenAI API (если OPENAI_API_KEY в .env), 2) ML-модель на ваших транзакциях (sklearn),
3) правила по ключевым словам.

Для OpenAI: добавьте в .env строку OPENAI_API_KEY=sk-...
"""
import json
import os
import re
from django.conf import settings


def _call_openai(raw_text, amount=None):
    """
    Вызов OpenAI для извлечения магазина и категории из текста чека.
    Возвращает (merchant, category_name) или (None, None).
    """
    api_key = os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', None)
    if not api_key or not raw_text or len(raw_text.strip()) < 10:
        return None, None

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        prompt = f"""Из текста чека извлеки:
1. Название магазина/продавца (кратко, без ООО/ИП если можно)
2. Категорию расхода на русском: Еда, Продукты, Кафе и рестораны, Здоровье, Транспорт, Такси, Развлечения, Одежда и обувь, Коммунальные услуги, Связь, Образование, Товары для дома, Прочее

Текст чека:
{raw_text[:2000]}

Ответ строго в формате JSON: {{"merchant": "название", "category": "категория"}}
"""
        response = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.1,
            max_tokens=150,
        )
        text = response.choices[0].message.content.strip()
        # Убираем markdown-блоки если есть
        if text.startswith('```'):
            text = re.sub(r'^```\w*\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
        obj = json.loads(text)
        merchant = (obj.get('merchant') or '').strip()[:100]
        category = (obj.get('category') or '').strip()
        return merchant if merchant else None, category if category else None
    except Exception:
        return None, None


def _get_ml_categorizer(user):
    """Получить обученный ML-категоризатор для пользователя."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.naive_bayes import MultinomialNB
        from sklearn.pipeline import Pipeline
        from ..models import Transaction, Category
    except ImportError:
        return None

    # Данные для обучения: транзакции пользователя с категориями
    txs = Transaction.objects.filter(
        user=user,
        type='expense',
        category__isnull=False
    ).select_related('category')[:2000]

    if txs.count() < 5:
        return None

    X, y = [], []
    for t in txs:
        parts = []
        if t.merchant:
            parts.append(str(t.merchant))
        if t.description:
            parts.append(str(t.description))
        if parts:
            X.append(' '.join(parts))
            y.append(t.category.name)

    if len(X) < 5 or len(set(y)) < 2:
        return None

    try:
        pipe = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=500, ngram_range=(1, 2))),
            ('clf', MultinomialNB())
        ])
        pipe.fit(X, y)
        return pipe
    except Exception:
        return None


def _predict_ml(text, user):
    """Предсказание категории по ML-модели."""
    pipe = _get_ml_categorizer(user)
    if pipe is None or not text or len(text.strip()) < 3:
        return None
    try:
        pred = pipe.predict([text[:500]])[0]
        return pred
    except Exception:
        return None


def _keyword_category(text):
    """Определение категории по ключевым словам."""
    if not text:
        return None
    t = text.lower()
    rules = [
        ('Развлечения', ['тур', 'море', 'путешеств', 'отдых', 'туризм', 'отель', 'авиа', 'билет', 'турагентств', 'круиз', 'экскурси', 'кино', 'театр', 'игр', 'концерт']),
        ('Здоровье', ['аптека', 'лекарств', 'клиника', 'врач', 'медицин']),
        ('Кафе и рестораны', ['кафе', 'ресторан', 'кофе', 'обед', 'ужин', 'бар', 'пиццерия', 'столовая']),
        ('Еда', ['продукты', 'молоко', 'хлеб', 'еда', 'супермаркет', 'магнит', 'пятерочка', 'перекресток', 'ашан', 'лента']),
        ('Продукты', ['продукты', 'молоко', 'хлеб']),
        ('Одежда и обувь', ['одежда', 'обувь', 'футболка']),
        ('Коммунальные услуги', ['жкх', 'коммунал', 'электр', 'газ', 'вода', 'интернет', 'связь']),
        ('Транспорт', ['азс', 'бензин', 'транспорт', 'метро', 'заправка']),
        ('Такси', ['такси', 'яндекс', 'uber']),
    ]
    for cat, words in rules:
        if any(w in t for w in words):
            return cat
    return None


def analyze_receipt(raw_text, merchant_from_ocr, amount, user):
    """
    Анализ текста чека с помощью AI/ML.
    Возвращает (merchant, suggested_category) — улучшенные значения.
    """
    merchant = merchant_from_ocr or ''
    category = None
    combined = f"{merchant} {raw_text}"[:1000] if raw_text else merchant

    # 1. OpenAI (если ключ задан)
    ai_merchant, ai_category = _call_openai(raw_text or combined, amount)
    if ai_merchant:
        merchant = ai_merchant
    if ai_category:
        category = ai_category

    # 2. Локальная ML-модель (если OpenAI не дал категорию)
    if not category and user and combined.strip():
        category = _predict_ml(combined, user)

    # 3. Ключевые слова
    if not category:
        category = _keyword_category(combined)

    # Приводим категорию к одному из стандартных названий
    if category:
        aliases = {
            'путешествия': 'Развлечения', 'путешествие': 'Развлечения', 'туризм': 'Развлечения',
            'отдых': 'Развлечения', 'продукты питания': 'Продукты', 'продукты': 'Еда',
            'кафе': 'Кафе и рестораны', 'ресторан': 'Кафе и рестораны', 'еда': 'Еда',
            'транспорт': 'Транспорт', 'здоровье': 'Здоровье', 'медицина': 'Здоровье',
            'коммунальные': 'Коммунальные услуги', 'жкх': 'Коммунальные услуги',
            'такси': 'Такси', 'одежда': 'Одежда и обувь', 'обувь': 'Одежда и обувь',
            'связь': 'Связь', 'образование': 'Образование', 'дом': 'Товары для дома',
        }
        cat_lower = category.lower().strip()
        category = aliases.get(cat_lower) or category

    return merchant, category
