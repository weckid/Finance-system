from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from . import models
from .models import (
    CustomUser, Transaction, Category, Account,
    FinancialGoal, Budget, Family, CategorizationRule
)
import re
import random


class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с дополнительными полями"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'example@email.com'
    }))

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Простая валидация телефона
            phone_pattern = r'^\+?[1-9]\d{1,14}$'
            if not re.match(phone_pattern, phone.replace(' ', '').replace('(', '').replace(')', '').replace('-', '')):
                raise ValidationError("Введите корректный номер телефона.")
        return phone


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа с запоминанием"""
    remember_me = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={
        'class': 'form-check-input'
    }))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'placeholder': 'Имя пользователя или email'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})


class TransactionForm(forms.ModelForm):
    """Форма создания/редактирования транзакции"""

    class Meta:
        model = Transaction
        fields = ['amount', 'currency', 'type', 'category', 'description', 'date', 'account', 'merchant', 'location']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Описание операции...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'account': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'merchant': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Магазин/организация'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Место совершения операции'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q  # Добавить импорт
            from .models import Account, Category  # Добавить импорты
            # Фильтруем счета пользователя
            self.fields['account'].queryset = Account.objects.filter(
                Q(owner=user) | Q(family__members__user=user),
                is_active=True
            ).distinct()
            self.fields['category'].queryset = Category.objects.filter(
                Q(owner=user) | Q(is_system=True)
            ).distinct()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:
            raise ValidationError("Сумма должна быть больше 0.")
        return amount


class QuickTransactionForm(forms.Form):
    """Форма быстрого добавления транзакции (для мобильных устройств)"""
    AMOUNT_CHOICES = [(str(i * 100), f"{i * 100} ₽") for i in range(1, 11)]

    amount = forms.ChoiceField(choices=AMOUNT_CHOICES, widget=forms.Select(attrs={
        'class': 'form-control quick-amount'
    }))
    custom_amount = forms.DecimalField(required=False, max_digits=12, decimal_places=2, widget=forms.NumberInput(attrs={
        'class': 'form-control d-none',
        'placeholder': 'Другая сумма',
        'step': '0.01'
    }))
    category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control quick-category'})
    )
    description = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Краткое описание'
    }))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Показываем только часто используемые категории
            self.fields['category'].queryset = Category.objects.filter(
                models.Q(owner=user) | models.Q(is_system=True),
                type='expense'
            ).order_by('name')[:10]

    def clean(self):
        cleaned_data = super().clean()
        amount = cleaned_data.get('amount')
        custom_amount = cleaned_data.get('custom_amount')

        if custom_amount:
            cleaned_data['final_amount'] = custom_amount
        else:
            cleaned_data['final_amount'] = amount

        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Форма создания категории - упрощенная версия"""

    class Meta:
        model = Category
        fields = ['name']  # Только название
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название категории'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Ничего не добавляем - форма простая

    def save(self, commit=True, user=None):
        category = super().save(commit=False)
        # Устанавливаем тип по умолчанию (расход) и случайный цвет
        category.type = 'expense'
        category.color = self.get_random_color()

        if user:
            category.owner = user

        if commit:
            category.save()
        return category

    def get_random_color(self):
        """Генерирует случайный цвет для категории"""
        colors = [
            '#FF6B6B',  # Красный
            '#4ECDC4',  # Бирюзовый
            '#FFD166',  # Желтый
            '#06D6A0',  # Зеленый
            '#118AB2',  # Синий
            '#EF476F',  # Розовый
            '#1B9AAA',  # Голубой
            '#06BCC1',  # Бирюзовый 2
            '#F86624',  # Оранжевый
            '#662E9B',  # Фиолетовый
            '#2A9D8F',  # Зеленый морской
            '#E9C46A',  # Золотой
            '#F4A261',  # Оранжевый светлый
            '#E76F51',  # Коралловый
        ]
        return random.choice(colors)


class AccountForm(forms.ModelForm):
    """Форма создания/редактирования счета"""

    class Meta:
        model = Account
        fields = ['name', 'account_type', 'ownership', 'currency', 'balance', 'bank_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название счета'}),
            'account_type': forms.Select(attrs={'class': 'form-control'}),
            'ownership': forms.Select(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'balance': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название банка'}),
        }


class FinancialGoalForm(forms.ModelForm):
    """Форма создания/редактирования финансовой цели"""

    class Meta:
        model = FinancialGoal
        fields = ['name', 'goal_type', 'target_amount', 'deadline', 'description', 'replenishment_frequency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название цели'
            }),
            'goal_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'target_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '100000'
            }),
            'deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание цели...'
            }),
            'replenishment_frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def clean_target_amount(self):
        target_amount = self.cleaned_data.get('target_amount')
        if target_amount <= 0:
            raise ValidationError("Сумма цели должна быть больше 0.")
        return target_amount

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < date.today():
            raise ValidationError("Дата окончания не может быть в прошлом.")
        return deadline


class BudgetForm(forms.ModelForm):
    """Форма создания/редактирования бюджета"""

    class Meta:
        model = Budget
        fields = ['name', 'period', 'amount', 'category', 'start_date', 'end_date', 'notification_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название бюджета'}),
            'period': forms.Select(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notification_threshold': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '100'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if end_date and start_date and end_date < start_date:
            raise ValidationError("Дата окончания не может быть раньше даты начала.")

        return cleaned_data


class FamilyForm(forms.ModelForm):
    """Форма создания/редактирования семьи. Валюта всегда рубли."""

    class Meta:
        model = Family
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название семьи'}),
        }


class ImportTransactionsForm(forms.Form):
    """Форма импорта транзакций"""
    FORMAT_CHOICES = [
        ('csv', 'CSV файл'),
        ('xlsx', 'Excel файл'),
        ('qif', 'QIF файл'),
        ('ofx', 'OFX файл'),
    ]

    file = forms.FileField(
        label='Файл для импорта',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.csv,.xlsx,.qif,.ofx'})
    )
    file_format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Счет для импорта'
    )
    auto_categorize = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Автоматически категоризировать'
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['account'].queryset = Account.objects.filter(owner=user, is_active=True)


class PasswordResetRequestForm(forms.Form):
    """Форма запроса сброса пароля"""
    METHOD_CHOICES = [
        ('email', 'По электронной почте'),
        ('sms', 'По SMS (требуется номер телефона)'),
        ('telegram', 'По Telegram'),
    ]

    username_or_email = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя пользователя или email'})
    )
    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='email'
    )


class ProfileUpdateForm(forms.ModelForm):
    """Форма обновления профиля. Все подписи на русском. Валюта не редактируется (всегда рубли)."""

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'avatar', 'monthly_income']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Имя'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (999) 123-45-67'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'monthly_income': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': '0'}),
        }
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'phone': 'Телефон',
            'avatar': 'Аватар',
            'monthly_income': 'Месячный доход (₽)',
        }


# forms.py - исправляем ReceiptUploadForm
class ReceiptUploadForm(forms.ModelForm):
    """Форма загрузки чека"""

    class Meta:
        model = Transaction
        fields = ['receipt_image', 'amount', 'category', 'description', 'date']
        widgets = {
            'receipt_image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Описание покупки...'
            }),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            from django.db.models import Q  # Добавить импорт
            from .models import Category  # Добавить импорт
            self.fields['category'].queryset = Category.objects.filter(
                Q(owner=user) | Q(is_system=True),
                type='expense'
            ).distinct()