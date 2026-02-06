# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    CustomUser, UserProfile, Family, FamilyMember, Account,
    Category, Transaction, Budget, FinancialGoal, GoalContribution, CategorizationRule,
    Forecast, ImportTemplate, Notification, FamilyInvitation,
    Report, MLModel
)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'phone', 'monthly_income', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация',
         {'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'monthly_income', 'default_currency')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'notification_email', 'notification_push')
    search_fields = ('user__username', 'user__email')

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'member_count')
    search_fields = ('name', 'created_by__username')

    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Количество участников'

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('family', 'user', 'role', 'permission_level', 'joined_at')
    list_filter = ('role', 'permission_level')
    search_fields = ('family__name', 'user__username')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_type', 'owner', 'balance', 'currency', 'is_active')
    list_filter = ('account_type', 'ownership', 'currency', 'is_active')
    search_fields = ('name', 'bank_name', 'owner__username')
    readonly_fields = ('balance',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'owner', 'color_display', 'is_system')
    list_filter = ('type', 'is_system')
    search_fields = ('name', 'owner__username')

    def color_display(self, obj):
        return format_html(
            '<span style="color: {};">⬤</span> {}',
            obj.color,
            obj.color
        )
    color_display.short_description = 'Цвет'

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('date', 'amount', 'currency', 'type', 'category', 'account', 'user', 'created_via')
    list_filter = ('type', 'currency', 'created_via', 'date')
    search_fields = ('description', 'merchant', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'date'

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'period', 'amount', 'spent_amount', 'remaining_amount', 'user')
    list_filter = ('period',)
    search_fields = ('name', 'user__username')
    readonly_fields = ('spent_amount', 'remaining_amount')

@admin.register(FinancialGoal)
class FinancialGoalAdmin(admin.ModelAdmin):
    list_display = ('name', 'goal_type', 'target_amount', 'current_amount', 'progress_percentage', 'deadline', 'status', 'replenishment_frequency')
    list_filter = ('goal_type', 'status')
    search_fields = ('name', 'user__username')
    readonly_fields = ('progress_percentage',)

    def progress_percentage_display(self, obj):
        return f"{obj.progress_percentage:.1f}%"
    progress_percentage_display.short_description = 'Прогресс'


@admin.register(GoalContribution)
class GoalContributionAdmin(admin.ModelAdmin):
    list_display = ('goal', 'amount', 'user', 'contributed_at')
    list_filter = ('contributed_at',)
    search_fields = ('goal__name', 'user__username')
    date_hierarchy = 'contributed_at'


@admin.register(CategorizationRule)
class CategorizationRuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'rule_type', 'pattern', 'category', 'priority', 'is_active')
    list_filter = ('rule_type', 'is_active')
    search_fields = ('name', 'pattern', 'user__username')

@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ('user', 'forecast_type', 'confidence', 'created_at', 'valid_until')
    list_filter = ('forecast_type',)
    search_fields = ('user__username',)

@admin.register(ImportTemplate)
class ImportTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'bank_name', 'file_format', 'user', 'is_active')
    list_filter = ('file_format', 'is_active')
    search_fields = ('name', 'bank_name', 'user__username')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'sent_via')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)

@admin.register(FamilyInvitation)
class FamilyInvitationAdmin(admin.ModelAdmin):
    list_display = ('family', 'inviter', 'invitee_email', 'status', 'created_at', 'expires_at')
    list_filter = ('status',)
    search_fields = ('invitee_email', 'family__name', 'inviter__username')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('name', 'report_type', 'format', 'created_at')
    list_filter = ('report_type', 'format')
    search_fields = ('name',)

@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ('user', 'accuracy', 'last_trained', 'training_samples', 'version')
    readonly_fields = ('last_trained',)