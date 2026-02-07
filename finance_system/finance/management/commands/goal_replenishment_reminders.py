# management/commands/goal_replenishment_reminders.py
"""Создаёт уведомления о необходимости пополнения целей по графику (раз в день, раз в неделю и т.д.). Запускать по cron раз в день."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from finance.models import FinancialGoal, Notification, FamilyMember  # noqa: F401


FREQUENCY_DAYS = {
    'daily': 1,
    'every_2_days': 2,
    'every_3_days': 3,
    'weekly': 7,
    'monthly': 30,
}


class Command(BaseCommand):
    help = 'Создаёт уведомления о необходимости пополнения целей по графику.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Не создавать уведомления, только вывести список.')
        parser.add_argument('--verbose', action='store_true', help='Подробный вывод.')
        parser.add_argument('--test', action='store_true', help='Создать тестовое уведомление для первой подходящей цели (игнорируя срок).')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        verbose = options.get('verbose', False)
        test_mode = options.get('test', False)
        today = timezone.now().date()
        created = 0

        goals = FinancialGoal.objects.filter(
            status='active',
            replenishment_frequency__in=FREQUENCY_DAYS.keys(),
        ).exclude(replenishment_frequency='').select_related('family', 'user')

        if verbose:
            self.stdout.write(f'Найдено целей с графиком пополнения: {goals.count()}')

        for goal in goals:
            days = FREQUENCY_DAYS.get(goal.replenishment_frequency)
            if not days:
                continue
            # Сравниваем с последним пополнением или с датой создания цели
            ref_date = goal.last_replenishment_at or goal.start_date
            if not ref_date:
                ref_date = goal.created_at.date() if goal.created_at else today
            if hasattr(ref_date, 'date'):
                ref_date = ref_date.date()
            next_due = ref_date + timedelta(days=days)
            if not test_mode and today < next_due:
                if verbose:
                    self.stdout.write(f'  Пропуск «{goal.name}»: следующее напоминание {next_due} (сегодня {today})')
                continue
            # Нужно напомнить (или --test)
            if verbose:
                self.stdout.write(f'  Напоминание: «{goal.name}» (ref={ref_date}, next_due={next_due})')
            display_freq = dict(FinancialGoal.REPLENISHMENT_CHOICES).get(goal.replenishment_frequency) or goal.replenishment_frequency
            title = 'Напоминание: пополнение цели'
            message = f'Цель «{goal.name}»: по графику пополнение {display_freq}. Рекомендуется внести сумму.'

            if goal.family_id:
                # Семейная цель — уведомляем всех участников семьи
                users_to_notify = [goal.family.created_by_id]
                for m in FamilyMember.objects.filter(family=goal.family).select_related('user'):
                    if m.user_id not in users_to_notify:
                        users_to_notify.append(m.user_id)
                for user_id in users_to_notify:
                    if dry_run:
                        self.stdout.write(f'[dry-run] Уведомление пользователю {user_id}: {title} — {goal.name}')
                        created += 1
                        continue
                    Notification.objects.create(
                        user_id=user_id,
                        notification_type='goal_replenishment_reminder',
                        title=title,
                        message=message,
                        data={
                            'goal_id': str(goal.id),
                            'family_id': str(goal.family_id),
                            'goal_name': goal.name,
                        },
                    )
                    created += 1
            else:
                # Личная цель
                if not goal.user_id:
                    continue
                if dry_run:
                    self.stdout.write(f'[dry-run] Уведомление пользователю {goal.user_id}: {title} — {goal.name}')
                    created += 1
                    continue
                Notification.objects.create(
                    user=goal.user,
                    notification_type='goal_replenishment_reminder',
                    title=title,
                    message=message,
                    data={
                        'goal_id': str(goal.id),
                        'goal_name': goal.name,
                    },
                )
                created += 1

        if goals.count() == 0:
            self.stdout.write(self.style.WARNING('Нет целей с заданным графиком пополнения. Укажите «Обязательное пополнение» при создании/редактировании цели.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Создано уведомлений: {created}'))
