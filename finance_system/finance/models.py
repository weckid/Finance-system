from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
import json

class CustomUser(AbstractUser):
    """Расширенная модель пользователя"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    block_reason = models.TextField(blank=True, null=True, verbose_name='Причина блокировки')
    phone = models.CharField(max_length=20, blank=True, null=True)
    telegram_id = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    default_currency = models.CharField(max_length=3, default='RUB')
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.username} ({self.email})"

class Family(models.Model):
    """Модель семьи для совместного управления финансами"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='families/', blank=True, null=True)
    family_currency = models.CharField(max_length=3, default='RUB')
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_families')
    created_at = models.DateTimeField(auto_now_add=True)
    # Настройки управления (для создателя/админа)
    members_can_create_goals = models.BooleanField(default=True, verbose_name='Участники могут создавать цели')
    members_can_invite = models.BooleanField(default=False, verbose_name='Участники могут приглашать')

    class Meta:
        verbose_name = 'Семья'
        verbose_name_plural = 'Семьи'

    def __str__(self):
        return self.name

class FamilyMember(models.Model):
    """Участники семьи с ролями и правами"""
    ROLE_CHOICES = [
        ('creator', 'Создатель'),
        ('admin', 'Администратор'),
        ('member', 'Участник'),
        ('viewer', 'Наблюдатель'),
    ]

    PERMISSION_CHOICES = [
        ('full', 'Полный доступ'),
        ('limited', 'Ограниченный доступ'),
        ('own', 'Только свои операции'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='family_memberships')
    display_name = models.CharField(max_length=80, blank=True, verbose_name='Отображаемое имя в семье')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    permission_level = models.CharField(max_length=20, choices=PERMISSION_CHOICES, default='full')
    can_add_transactions = models.BooleanField(default=True)
    can_edit_transactions = models.BooleanField(default=True)
    can_delete_transactions = models.BooleanField(default=False)
    can_manage_budget = models.BooleanField(default=False)
    can_manage_goals = models.BooleanField(default=False)
    can_invite_members = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Участник семьи'
        verbose_name_plural = 'Участники семьи'
        unique_together = ['family', 'user']

    def __str__(self):
        return f"{self.user.username} in {self.family.name}"

class Account(models.Model):
    """Счета и кошельки"""
    ACCOUNT_TYPES = [
        ('cash', 'Наличные'),
        ('debit', 'Дебетовая карта'),
        ('credit', 'Кредитная карта'),
        ('savings', 'Сберегательный счет'),
        ('investment', 'Инвестиционный счет'),
        ('loan', 'Кредит'),
        ('other', 'Другое'),
    ]

    OWNERSHIP_TYPES = [
        ('personal', 'Личный'),
        ('joint', 'Совместный'),
        ('family', 'Семейный'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES, default='debit')
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_TYPES, default='personal')
    currency = models.CharField(max_length=3, default='RUB')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    include_in_total = models.BooleanField(default=True)

    # Владелец или семья
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='accounts')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name='family_accounts')

    # Интеграция с банками
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_api_key = models.CharField(max_length=200, blank=True, null=True)
    last_sync = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Счет'
        verbose_name_plural = 'Счета'

    def __str__(self):
        return f"{self.name} ({self.get_account_type_display()})"


class Category(models.Model):
    """Категории операций с иерархической структурой"""
    CATEGORY_TYPES = [
        ('expense', 'Расход'),  # Только расходы как на картинке
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=CATEGORY_TYPES, default='expense')
    color = models.CharField(max_length=7, default='#007bff')

    # Принадлежность
    is_system = models.BooleanField(default=False)  # Системные категории
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True,
                              related_name='personal_categories')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return f"{self.name}"

    def save(self, *args, **kwargs):
        # Автоматически назначаем цвет если не задан или стандартный
        if not self.color or self.color == '#007bff':
            import random
            colors = [
                '#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2',
                '#EF476F', '#1B9AAA', '#06BCC1', '#F86624', '#662E9B',
                '#2A9D8F', '#E9C46A', '#F4A261', '#E76F51'
            ]
            self.color = random.choice(colors)
        super().save(*args, **kwargs)

class Transaction(models.Model):
    """Финансовые операции (транзакции)"""
    TRANSACTION_TYPES = [
        ('income', 'Доход'),
        ('expense', 'Расход'),
        ('transfer', 'Перевод между счетами'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Основная информация
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    currency = models.CharField(max_length=3, default='RUB')
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    description = models.TextField(blank=True)

    # Категоризация
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='transactions')
    auto_category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                      related_name='auto_categorized_transactions')
    ml_confidence = models.FloatField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(1)])

    # Счета
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='transactions')
    transfer_to_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transfers')

    # Владелец и семья
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    family = models.ForeignKey(Family, on_delete=models.SET_NULL, null=True, blank=True, related_name='family_transactions')

    # Дополнительная информация
    date = models.DateTimeField(default=timezone.now)
    location = models.CharField(max_length=255, blank=True, null=True)
    merchant = models.CharField(max_length=200, blank=True, null=True)
    mcc_code = models.CharField(max_length=4, blank=True, null=True)

    # Чек и приложения
    receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)
    attachments = models.JSONField(default=list, blank=True)  # Список прикрепленных файлов

    # Периодичность
    is_recurring = models.BooleanField(default=False)
    recurring_rule = models.CharField(max_length=100, blank=True, null=True)  # Например: "monthly", "weekly"
    next_occurrence = models.DateTimeField(null=True, blank=True)

    # Теги для поиска
    tags = models.JSONField(default=list, blank=True)

    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_via = models.CharField(max_length=20, default='manual')  # manual, import, api, scan

    class Meta:
        verbose_name = 'Транзакция'
        verbose_name_plural = 'Транзакции'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['type', 'date']),
            models.Index(fields=['category', 'date']),
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.date.strftime('%Y-%m-%d')}: {self.description} ({self.amount} {self.currency})"

class Budget(models.Model):
    """Бюджеты на категории или группы категорий"""
    PERIOD_CHOICES = [
        ('daily', 'Ежедневный'),
        ('weekly', 'Еженедельный'),
        ('monthly', 'Ежемесячный'),
        ('quarterly', 'Квартальный'),
        ('yearly', 'Годовой'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])

    # Привязка к категории или группе категорий
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    categories = models.ManyToManyField(Category, blank=True, related_name='group_budgets')

    # Владелец
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='personal_budgets')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name='family_budgets')

    # Период действия
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    # Уведомления
    notification_threshold = models.IntegerField(default=80, validators=[MinValueValidator(1), MaxValueValidator(100)])
    notifications_enabled = models.BooleanField(default=True)

    # Статистика
    spent_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Бюджет'
        verbose_name_plural = 'Бюджеты'

    def save(self, *args, **kwargs):
        self.remaining_amount = self.amount - self.spent_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.get_period_display()})"

class FinancialGoal(models.Model):
    """Финансовые цели для накопления"""
    GOAL_TYPES = [
        ('savings', 'Накопления'),
        ('debt', 'Погашение долга'),
        ('investment', 'Инвестиции'),
        ('purchase', 'Крупная покупка'),
        ('travel', 'Путешествие'),
        ('education', 'Образование'),
        ('other', 'Другое'),
    ]

    REPLENISHMENT_CHOICES = [
        ('', 'Без обязательного графика'),
        ('daily', 'Раз в день'),
        ('every_2_days', 'Раз в 2 дня'),
        ('every_3_days', 'Раз в 3 дня'),
        ('weekly', 'Раз в неделю'),
        ('monthly', 'Раз в месяц'),
    ]

    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Выполнена'),
        ('paused', 'Приостановлена'),
        ('failed', 'Не выполнена'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES, default='savings')
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    current_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monthly_contribution = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Когда проводить пополнение (обязательное)
    replenishment_frequency = models.CharField(
        max_length=20, choices=REPLENISHMENT_CHOICES, default='', blank=True,
        verbose_name='Пополнение'
    )
    last_replenishment_at = models.DateField(null=True, blank=True, verbose_name='Последнее пополнение')

    # Сроки
    start_date = models.DateField(default=timezone.now)
    deadline = models.DateField()

    # Статус и прогресс
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    progress_percentage = models.FloatField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Владелец
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='personal_goals')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, null=True, blank=True, related_name='family_goals')

    # Привязанный счет
    linked_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='goals')

    # Изображение и описание
    image = models.ImageField(upload_to='goals/', blank=True, null=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_replenishment_display_short(self):
        """Краткое отображение графика пополнения для карточки."""
        d = dict(self.REPLENISHMENT_CHOICES)
        return d.get(self.replenishment_frequency) or 'Без графика'

    @property
    def remaining_amount(self):
        return max(0, self.target_amount - self.current_amount)

    class Meta:
        verbose_name = 'Финансовая цель'
        verbose_name_plural = 'Финансовые цели'
        ordering = ['deadline']

    def save(self, *args, **kwargs):
        if self.target_amount > 0:
            self.progress_percentage = (self.current_amount / self.target_amount) * 100
        else:
            self.progress_percentage = 0

        if self.progress_percentage >= 100:
            self.status = 'completed'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.current_amount}/{self.target_amount})"

class GoalContribution(models.Model):
    """Запись о пополнении цели (для графика по месяцам)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    goal = models.ForeignKey(FinancialGoal, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    contributed_at = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='goal_contributions')

    class Meta:
        verbose_name = 'Пополнение цели'
        verbose_name_plural = 'Пополнения целей'
        ordering = ['-contributed_at']

    def __str__(self):
        return f"{self.goal.name}: +{self.amount} ({self.contributed_at.date()})"


class Notification(models.Model):
    """Уведомления системы"""
    NOTIFICATION_TYPES = [
        ('budget_warning', 'Превышение бюджета'),
        ('bill_reminder', 'Напоминание о счете'),
        ('goal_progress', 'Прогресс цели'),
        ('goal_replenishment_reminder', 'Напоминание о пополнении цели'),
        ('family_invite', 'Приглашение в семью'),
        ('member_joined', 'Участник присоединился к семье'),
        ('transaction_added', 'Добавлена транзакция'),
        ('system', 'Системное уведомление'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)  # Дополнительные данные

    # Статус уведомления
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    sent_via = models.CharField(max_length=20, default='in_app')  # in_app, email, push, telegram

    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class FamilyInvitation(models.Model):
    """Приглашения в семью"""
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
        ('expired', 'Просрочено'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='invitations')
    inviter = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_invitations')
    invitee_email = models.EmailField()
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    # Права для приглашенного
    proposed_role = models.CharField(max_length=20, choices=FamilyMember.ROLE_CHOICES, default='member')
    proposed_permission = models.CharField(max_length=20, choices=FamilyMember.PERMISSION_CHOICES, default='full')

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Приглашение в семью'
        verbose_name_plural = 'Приглашения в семью'

    def __str__(self):
        return f"{self.invitee_email} → {self.family.name}"
