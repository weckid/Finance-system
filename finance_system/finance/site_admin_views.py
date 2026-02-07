# site_admin_views.py — кастомная админ-панель (только is_staff)
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from django.utils import formats
import json

from .models import Category, Transaction, FinancialGoal, GoalContribution, Family, CustomUser


def staff_required(view_func):
    """Доступ только для is_staff."""
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, 'Войдите в систему.')
            return redirect('auth')
        if not request.user.is_staff:
            messages.error(request, 'Доступ только для администратора.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapped


@login_required
@staff_required
def site_admin_dashboard(request):
    """Главная админки — большая статистика и доп. информация."""
    users_count = CustomUser.objects.count()
    users_active = CustomUser.objects.filter(is_active=True).count()
    users_blocked = CustomUser.objects.filter(is_active=False).count()
    families_count = Family.objects.count()
    goals_count = FinancialGoal.objects.count()
    goals_active = FinancialGoal.objects.filter(status='active').count()
    goals_completed = FinancialGoal.objects.filter(status='completed').count()
    categories_count = Category.objects.count()
    categories_system = Category.objects.filter(is_system=True).count()
    transactions_count = Transaction.objects.count()
    total_transactions_sum = Transaction.objects.aggregate(s=Sum('amount'))['s'] or 0
    total_expenses = Transaction.objects.filter(type='expense').aggregate(s=Sum('amount'))['s'] or 0
    total_income = Transaction.objects.filter(type='income').aggregate(s=Sum('amount'))['s'] or 0
    contributions_count = GoalContribution.objects.count()
    total_contributions = GoalContribution.objects.aggregate(s=Sum('amount'))['s'] or 0
    total_goals_target = FinancialGoal.objects.aggregate(s=Sum('target_amount'))['s'] or 0
    total_goals_current = FinancialGoal.objects.aggregate(s=Sum('current_amount'))['s'] or 0

    last_users = CustomUser.objects.all().order_by('-date_joined')[:5]
    last_families = Family.objects.all().select_related('created_by').order_by('-created_at')[:5]
    last_contributions = GoalContribution.objects.select_related('goal', 'user').order_by('-contributed_at')[:10]

    monthly = GoalContribution.objects.all().annotate(
        month=TruncMonth('contributed_at')
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    chart_labels = []
    chart_data = []
    for row in monthly:
        chart_labels.append(formats.date_format(row['month'], 'Y-m') if row['month'] else '')
        chart_data.append(float(row['total']))

    return render(request, 'finance/site_admin/dashboard.html', {
        'users_count': users_count,
        'users_active': users_active,
        'users_blocked': users_blocked,
        'families_count': families_count,
        'goals_count': goals_count,
        'goals_active': goals_active,
        'goals_completed': goals_completed,
        'categories_count': categories_count,
        'categories_system': categories_system,
        'transactions_count': transactions_count,
        'total_transactions_sum': total_transactions_sum,
        'total_expenses': total_expenses,
        'total_income': total_income,
        'contributions_count': contributions_count,
        'total_contributions': total_contributions,
        'total_goals_target': total_goals_target,
        'total_goals_current': total_goals_current,
        'last_users': last_users,
        'last_families': last_families,
        'last_contributions': last_contributions,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_data_json': json.dumps(chart_data),
    })


@login_required
@staff_required
def site_admin_categories(request):
    """Список всех категорий."""
    categories = Category.objects.all().select_related('owner').order_by('is_system', 'name')
    return render(request, 'finance/site_admin/categories.html', {'categories': categories})


@login_required
@staff_required
def site_admin_category_create(request):
    """Создание категории (можно системную)."""
    from .forms import CategoryForm
    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        is_system = request.POST.get('is_system') == 'on'
        if name:
            import random
            colors = [
                '#FF6B6B', '#4ECDC4', '#FFD166', '#06D6A0', '#118AB2',
                '#EF476F', '#1B9AAA', '#06BCC1', '#F86624', '#662E9B',
                '#2A9D8F', '#E9C46A', '#F4A261', '#E76F51'
            ]
            Category.objects.create(
                name=name,
                type='expense',
                color=random.choice(colors),
                is_system=is_system,
                owner=None if is_system else request.user,
            )
            messages.success(request, f'Категория «{name}» создана.')
            return redirect('admin_categories')
        messages.error(request, 'Введите название категории.')
    return render(request, 'finance/site_admin/category_form.html', {'form_title': 'Создать категорию'})


@login_required
@staff_required
def site_admin_category_delete(request, pk):
    """Удаление категории."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Категория «{name}» удалена.')
        return redirect('admin_categories')
    return render(request, 'finance/site_admin/category_confirm_delete.html', {'category': category})


@login_required
@staff_required
def site_admin_users(request):
    """Список пользователей (блокировка/разблокировка)."""
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'finance/site_admin/users.html', {'users': users})


@login_required
@staff_required
def site_admin_user_block(request, pk):
    """Заблокировать пользователя с указанием причины."""
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.error(request, 'Нельзя заблокировать себя.')
        return redirect('admin_users')
    if user.is_superuser:
        messages.error(request, 'Нельзя заблокировать суперпользователя.')
        return redirect('admin_users')
    if request.method == 'POST':
        reason = (request.POST.get('block_reason') or '').strip() or None
        user.is_active = False
        user.block_reason = reason
        user.save()
        messages.success(request, f'Пользователь {user.username} заблокирован.')
    return redirect('admin_users')


@login_required
@staff_required
def site_admin_user_unblock(request, pk):
    """Разблокировать пользователя."""
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.is_active = True
        user.block_reason = None
        user.save()
        messages.success(request, f'Пользователь {user.username} разблокирован.')
    return redirect('admin_users')
