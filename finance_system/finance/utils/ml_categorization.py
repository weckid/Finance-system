"""
Модуль для автоматической категоризации транзакций с помощью ML.
"""

import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from django.db.models import Count
import json


class TransactionCategorizer:
    def __init__(self):
        self.model = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000)),
            ('clf', MultinomialNB())
        ])
        self.is_trained = False

    def train(self, X, y):
        """Обучение модели на исторических данных"""
        self.model.fit(X, y)
        self.is_trained = True

    def predict(self, description):
        """Предсказание категории по описанию"""
        if not self.is_trained:
            return None, 0.0

        probas = self.model.predict_proba([description])
        max_idx = np.argmax(probas)
        confidence = probas[0][max_idx]
        category = self.model.classes_[max_idx]

        return category, confidence


def categorize_transaction(description, amount, user):
    """Основная функция категоризации"""
    # Загрузка обученной модели для пользователя
    # или использование общих правил

    # Пример простых правил
    keywords = {
        'продукты': ['магнит', 'пятерочка', 'перекресток', 'ашан', 'продукт'],
        'кафе': ['ресторан', 'кафе', 'кофе', 'столовая', 'бургер'],
        'транспорт': ['такси', 'метро', 'автобус', 'заправка', 'бензин'],
        'развлечения': ['кино', 'театр', 'концерт', 'клуб'],
        'коммуналка': ['квартплата', 'электричество', 'вода', 'газ', 'интернет'],
    }

    description_lower = description.lower()

    for category, words in keywords.items():
        for word in words:
            if word in description_lower:
                # Находим соответствующую категорию в БД
                from ..models import Category
                cat = Category.objects.filter(
                    user=user,
                    name__icontains=category,
                    type='expense'
                ).first()
                return cat, 0.8

    return None, 0.0