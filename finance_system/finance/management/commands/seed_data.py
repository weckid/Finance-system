"""
Команда для заполнения БД тестовыми данными.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from finance.models import Category, Transaction, FinancialGoal, Family
from decimal import Decimal
import random
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        # Создаем тестового пользователя
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Иван',
                'last_name': 'Иванов',
                'monthly_income': 100000
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь'))

        # Создаем категории
        categories_data = [
            {'name': 'Продукты', 'type': 'expense', 'color': '#FF6B6B'},
            {'name': 'Кафе и рестораны', 'type': 'expense', 'color': '#4ECDC4'},
            {'name': 'Транспорт', 'type': 'expense', 'color': '#45B7D1'},
            {'name': 'Развлечения', 'type': 'expense', 'color': '#96CEB4'},
            {'name': 'Коммунальные услуги', 'type': 'expense', 'color': '#FFEAA7'},
            {'name': 'Зарплата', 'type': 'income', 'color': '#55EFC4'},
            {'name': 'Фриланс', 'type': 'income', 'color': '#81ECEC'},
            {'name': 'Инвестиции', 'type': 'income', 'color': '#A29BFE'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                user=user,
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = cat
            if created:
                self.stdout.write(f"Создана категория: {cat_data['name']}")

        # Создаем транзакции (минимум 10)
        transaction_descriptions = [
            ('Покупка в Магните', 'Продукты', 'expense'),
            ('Обед в кафе', 'Кафе и рестораны', 'expense'),
            ('Такси до работы', 'Транспорт', 'expense'),
            ('Поход в кино', 'Развлечения', 'expense'),
            ('Оплата интернета', 'Коммунальные услуги', 'expense'),
            ('Зарплата за январь', 'Зарплата', 'income'),
            ('Зарплата за февраль', 'Зарплата', 'income'),
            ('Проект для клиента', 'Фриланс', 'income'),
            ('Дивиденды по акциям', 'Инвестиции', 'income'),
            ('Продукты на неделю', 'Продукты', 'expense'),
            ('Кофе с друзьями', 'Кафе и рестораны', 'expense'),
            ('Бензин на АЗС', 'Транспорт', 'expense'),
        ]

        for i, (desc, cat_name, t_type) in enumerate(transaction_descriptions):
            amount = Decimal(random.randint(100, 5000)) if t_type == 'expense' else Decimal(
                random.randint(10000, 50000))

            Transaction.objects.create(
                user=user,
                amount=amount,
                type=t_type,
                category=categories[cat_name],
                description=desc,
                date=datetime.now() - timedelta(days=random.randint(0, 60))
            )

        self.stdout.write(self.style.SUCCESS(f'Создано {len(transaction_descriptions)} транзакций'))

        # Создаем финансовые цели
        FinancialGoal.objects.create(
            user=user,
            name='Новый ноутбук',
            target_amount=150000,
            current_amount=45000,
            monthly_contribution=15000,
            deadline=datetime.now() + timedelta(days=180)
        )

        FinancialGoal.objects.create(
            user=user,
            name='Отпуск на море',
            target_amount=80000,
            current_amount=20000,
            monthly_contribution=10000,
            deadline=datetime.now() + timedelta(days=120)
        )

        self.stdout.write(self.style.SUCCESS('Созданы финансовые цели'))

        # Создаем семью
        family = Family.objects.create(
            name='Семья Ивановых',
            created_by=user,
            budget=50000
        )
        family.members.add(user)

        self.stdout.write(self.style.SUCCESS('Создана семья'))

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена тестовыми данными!'))