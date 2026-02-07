# GitHub, Git, PostgreSQL и DBeaver

## 1. Исправление ошибки Git push

Ошибка `src refspec main does not match any` возникает, потому что **коммит не был создан** (из‑за ошибки с email). Выполните:

```powershell
# 1. Настройте имя и email (обязательно)
git config --global user.email "ваш@email.com"
git config --global user.name "Ваше Имя"

# 2. Первый коммит
cd c:\Users\Пользователь\Desktop\PythonProject
git add .
git commit -m "Initial commit: финансовая система"

# 3. Отправка (если ветка master, используйте master вместо main)
git branch -M main
git push -u origin main
```

Если репозиторий на GitHub создан с веткой `master`:

```powershell
git push -u origin master
```

---

## 2. Подключение PostgreSQL

### Установка PostgreSQL

1. Скачайте: https://www.postgresql.org/download/windows/
2. Установите (запомните пароль пользователя `postgres`).
3. Создайте базу и пользователя (в pgAdmin или psql):

```sql
CREATE DATABASE finance_db;
CREATE USER finance_user WITH PASSWORD 'ваш_пароль';
GRANT ALL PRIVILEGES ON DATABASE finance_db TO finance_user;
ALTER DATABASE finance_db OWNER TO finance_user;
```

### Настройка Django (после создания .env)

1. Файл `.env` уже создан в папке `finance_system/`. Заполните его:

```
DB_ENGINE=postgresql
DB_NAME=finance_db
DB_USER=finance_user
DB_PASSWORD=ваш_пароль
DB_HOST=localhost
DB_PORT=5432
```

2. Установите драйвер:

```powershell
pip install psycopg2-binary
```

3. Миграции:

```powershell
cd finance_system
python manage.py migrate
python manage.py createsuperuser
```

---

## 3. Подключение к PostgreSQL через DBeaver

1. Установите DBeaver: https://dbeaver.io/download/

2. Запустите DBeaver → **База данных** → **Новое подключение** → **PostgreSQL**.

3. Параметры:
   - **Host:** `localhost`
   - **Port:** `5432`
   - **Database:** `finance_db`
   - **Username:** `finance_user` (или `postgres`)
   - **Password:** пароль пользователя
   - Можно включить **«Сохранить пароль»**.

4. Нажмите **Тест подключения** → **ОК**.

5. В левой панели откройте базу → **Схемы** → **public** → таблицы.

---

## 4. Шаги после создания .env

1. Установите драйвер PostgreSQL (если ещё не установлен):
   ```powershell
   pip install psycopg2-binary
   ```

2. Создайте базу в PostgreSQL (через pgAdmin или DBeaver):
   ```sql
   CREATE DATABASE finance_db;
   ```

3. Выполните миграции:
   ```powershell
   cd c:\Users\Пользователь\Desktop\PythonProject\finance_system
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Запустите сервер:
   ```powershell
   python manage.py runserver
   ```

5. **Важно:** `.env` уже в `.gitignore` — не коммитьте его (там пароли).

---

## 5. db.sqlite3 и PostgreSQL

**Удалять db.sqlite3 не обязательно.** При включённом PostgreSQL (через .env) Django использует PostgreSQL. Файл sqlite3 остаётся неиспользуемым — его можно удалить для порядка, но это не обязательно.

---

## 6. Не получается закоммитить

Чаще всего причина — не настроен Git или ещё не создан первый коммит.

1. Настройте имя и email:
   ```powershell
   git config --global user.email "ваш@email.com"
   git config --global user.name "Ваше Имя"
   ```

2. Сделайте первый коммит:
   ```powershell
   cd c:\Users\Пользователь\Desktop\PythonProject
   git add .
   git commit -m "Initial commit"
   ```

3. Отправьте на GitHub:
   ```powershell
   git push -u origin main
   ```
   Если основная ветка `master`:
   ```powershell
   git push -u origin master
   ```

---

## 7. Как коммитить дальше

```powershell
git add .
git commit -m "Описание изменений"
git push
```

Примеры сообщений:
- `Круговой график расходов, фикс накоплений`
- `Только полоса прогресса для расходов`

Либо через **Source Control** в Cursor: вкладка «Source Control», сообщение коммита и кнопка **Commit** + **Push**.
