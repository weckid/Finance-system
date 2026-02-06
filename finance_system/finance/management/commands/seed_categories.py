"""
Создание базовых системных категорий расходов для всех пользователей.
"""
from django.core.management.base import BaseCommand
from finance.models import Category


DEFAULT_CATEGORIES = [
    {'name': 'Продукты', 'color': '#FF6B6B'},
    {'name': 'Еда', 'color': '#E57373'},
    {'name': 'Такси', 'color': '#45B7D1'},
    {'name': 'Транспорт', 'color': '#4FC3F7'},
    {'name': 'Коммунальные услуги', 'color': '#4ECDC4'},
    {'name': 'Здоровье', 'color': '#96CEB4'},
    {'name': 'Развлечения', 'color': '#FFEAA7'},
    {'name': 'Одежда и обувь', 'color': '#DDA0DD'},
    {'name': 'Связь', 'color': '#98D8C8'},
    {'name': 'Образование', 'color': '#F7DC6F'},
    {'name': 'Товары для дома', 'color': '#BB8FCE'},
    {'name': 'Кафе и рестораны', 'color': '#F8B500'},
    {'name': 'Прочее', 'color': '#95A5A6'},
]


class Command(BaseCommand):
    help = 'Создаёт базовые системные категории расходов (Еда, Коммунальные и т.д.)'

    def handle(self, *args, **options):
        created_count = 0
        for cat_data in DEFAULT_CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                is_system=True,
                owner=None,
                defaults={
                    'type': 'expense',
                    'color': cat_data['color'],
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Создана категория: {cat.name}"))
        self.stdout.write(self.style.SUCCESS(f'Готово. Создано категорий: {created_count}, всего системных: {len(DEFAULT_CATEGORIES)}'))
