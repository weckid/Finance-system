"""Создание уведомлений о пополнении целей — вызывается при загрузке дашборда."""
from django.utils import timezone
from datetime import timedelta


FREQUENCY_DAYS = {
    'daily': 1,
    'every_2_days': 2,
    'every_3_days': 3,
    'weekly': 7,
    'monthly': 30,
}


def create_replenishment_reminders():
    """Создаёт уведомления о пополнении целей по графику. Не создаёт дубликаты за текущий день."""
    from finance.models import FinancialGoal, Notification, FamilyMember

    today = timezone.now().date()

    goals = FinancialGoal.objects.filter(
        status='active',
        replenishment_frequency__in=FREQUENCY_DAYS.keys(),
    ).exclude(replenishment_frequency='').select_related('family', 'user')

    for goal in goals:
        days = FREQUENCY_DAYS.get(goal.replenishment_frequency)
        if not days:
            continue

        ref_date = goal.last_replenishment_at or goal.start_date
        if not ref_date:
            ref_date = goal.created_at.date() if goal.created_at else today
        if hasattr(ref_date, 'date'):
            ref_date = ref_date.date()
        next_due = ref_date + timedelta(days=days)
        if today < next_due:
            continue

        # Проверка: не создавали ли уже уведомление для этой цели сегодня
        goal_id_str = str(goal.id)
        if goal.family_id:
            user_ids = [goal.family.created_by_id]
            for m in FamilyMember.objects.filter(family=goal.family).values_list('user_id', flat=True):
                if m not in user_ids:
                    user_ids.append(m)
        else:
            if not goal.user_id:
                continue
            user_ids = [goal.user_id]

        for user_id in user_ids:
            try:
                if Notification.objects.filter(
                    user_id=user_id,
                    notification_type='goal_replenishment_reminder',
                    created_at__date=today,
                    data__goal_id=goal_id_str,
                ).exists():
                    continue  # уже есть уведомление за сегодня
            except Exception:
                pass  # если БД не поддерживает data__goal_id, создаём без проверки дубликата

            display_freq = dict(FinancialGoal.REPLENISHMENT_CHOICES).get(goal.replenishment_frequency) or goal.replenishment_frequency
            Notification.objects.create(
                user_id=user_id,
                notification_type='goal_replenishment_reminder',
                title='Напоминание: пополнение цели',
                message=f'Цель «{goal.name}»: по графику пополнение {display_freq}. Рекомендуется внести сумму.',
                data={'goal_id': goal_id_str, 'goal_name': goal.name, 'family_id': str(goal.family_id) if goal.family_id else None},
            )
