"""Автопроверки для рабочих тетрадей курса «Введение в искусственный интеллект».

В тетради:
    from course_support.checks import check
    check('0.1', python_version)

Проверка печатает ✅ или ❌ с подсказкой, а результат запоминает в словаре RESULTS
(ничего не возвращает, чтобы Jupyter не печатал лишнего). Необязательные задания
могут ответить ℹ️ — это не ошибка.
Модуль использует только стандартную библиотеку и pandas.
"""

import os
import subprocess
from pathlib import Path

import pandas as pd

COURSE_DIR = Path(__file__).resolve().parent
DATA_DIR = COURSE_DIR / 'data'

_TASKS = {}
RESULTS = {}


def _task(task_id):
    def register(func):
        _TASKS[task_id] = func
        return func
    return register


def check(task_id, *args, **kwargs):
    """Запускает проверку задания task_id и печатает результат."""
    func = _TASKS.get(task_id)
    if func is None:
        print(f'❓ Проверка для задания {task_id} не найдена. Получите свежий course_support по инструкции docs/GIT.md; свои ответы не заменяйте')
        return
    try:
        ok, message = func(*args, **kwargs)
    except Exception as error:  # студенту важнее понятное сообщение, чем трассировка
        ok, message = False, f'проверка не смогла выполниться: {error!r}'
    RESULTS[task_id] = ok
    mark = 'ℹ️ ' if ok is None else ('✅ ' if ok else '❌ ')
    print(mark + f'Задание {task_id}: {message}')


# ---------- вспомогательные функции ----------

def _is_filled(value):
    return isinstance(value, str) and value.strip() != ''


def _git_env():
    """Запрещаем git спрашивать логин и пароль, иначе ячейка зависнет."""
    env = dict(os.environ)
    env['GIT_TERMINAL_PROMPT'] = '0'
    env['GIT_ASKPASS'] = ''
    return env


def _git(project_dir, *args):
    result = subprocess.run(
        ['git', '-C', str(project_dir), *args],
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=_git_env(), timeout=15,
    )
    return result.returncode, result.stdout.strip()


def _git_all_output(project_dir, *args):
    """То же, но вместе с stderr: git часть сообщений печатает туда."""
    result = subprocess.run(
        ['git', '-C', str(project_dir), *args],
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=_git_env(), timeout=15,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def _check_committed(project_dir):
    """Проверяет файлы на диске; несохранённые изменения в интерфейсе Jupyter не видны."""
    code, status = _git(project_dir, 'status', '--porcelain', '--untracked-files=all')
    if code != 0:
        return False, 'не удалось проверить git status; проверьте Git и путь проекта'
    if status:
        return False, ('есть изменённые или новые файлы вне коммита. Сначала Ctrl+S, '
                       'затем git status и осознанное добавление нужных файлов в коммит')
    return True, ''


def _commit_count(project_dir):
    code, out = _git(project_dir, 'rev-list', '--count', 'HEAD')
    return int(out) if code == 0 and out.isdigit() else 0


def _is_server_url(url):
    return url.startswith(('https://', 'http://', 'ssh://', 'git@'))


def _where(url):
    """Где лежит удалённый репозиторий — словами, для сообщений проверок."""
    if _is_server_url(url):
        host = url.split('://', 1)[-1].split('@')[-1].split('/')[0].split(':')[0]
        return 'на ' + {'github.com': 'GitHub', 'gitverse.ru': 'GitVerse'}.get(host, host)
    if len(url) > 2 and url[0].isalpha() and url[1] == ':':
        return f'на диске {url[0].upper()}'
    return f'в папке {url}'


def _gost_classes():
    table = pd.read_csv(DATA_DIR / 'gost_59277_classes.csv', encoding='utf-8')
    return table.groupby('основание')['класс'].apply(list).to_dict()


# ---------- Занятие 1 ----------

PAIRS_TOTAL = 24  # 12 занятий по две пары
AI_TASK_KEYS = ['система', 'назначение', 'сфера', 'знания', 'время', 'данные']
KNOWLEDGE_VALUES = ['правила', 'данные', 'правила и данные']
TIME_VALUES = ['реальное время', 'пакетная обработка']
GOST_BASES = [
    'По степени автономности',
    'По степени автоматизации',
    'По архитектурному принципу',
    'По видам деятельности',
    'По специализации систем',
]
TRACKS = [
    'Рынок труда Коми',
    'Недвижимость Сыктывкара',
    'Наука региона',
    'Климат Коми',
    'Курсы валют',
    'ИИ в цифрах',
]
README_PLACEHOLDER = '<впишите трек>'


@_task('01.1.1')
def _check_pairs_total(pairs_total):
    if isinstance(pairs_total, bool) or not isinstance(pairs_total, int):
        return False, f'ожидалось целое число, а получен {type(pairs_total).__name__}'
    if pairs_total != PAIRS_TOTAL:
        return False, f'получилось {pairs_total}. Занятий 12, на каждом две пары — пересчитайте'
    return True, f'{PAIRS_TOTAL} пары, и первая уже идёт'


@_task('01.1.2')
def _check_python_version(python_version):
    import sys
    expected = f'{sys.version_info.major}.{sys.version_info.minor}'
    if not isinstance(python_version, str):
        return False, f'нужна строка, а получен {type(python_version).__name__}'
    if python_version.strip() != expected:
        return False, f'ожидалась строка вида "{expected}", а получено "{python_version}"'
    return True, f'у вас Python {expected}'


@_task('01.1.3')
def _check_project_created(project_dir):
    project_dir = Path(project_dir)
    if not project_dir.is_dir():
        return False, f'папка {project_dir} не найдена. Скопируйте project_template и проверьте путь'
    if not (project_dir / 'README.md').exists():
        return False, 'в папке проекта нет README.md — скопируйте заготовку project_template целиком'
    required = ['course_support/checks.py', 'workbooks']
    missing = [name for name in required if not (project_dir / name).exists()]
    if missing:
        return False, f'неполная копия проекта: отсутствует {missing}. Нужен весь project_template'
    return True, 'самостоятельная папка проекта на месте. Покажите свой README; Git необязателен весь семестр'



@_task('01.1.4')
@_task('01.2.5')
def _check_saved(project_dir):
    """Необязательная проверка состояния отправки Git по локальным сведениям.

    Смотрим только то, что git знает локально, поэтому интернет не нужен.
    """
    clean, message = _check_committed(project_dir)
    if not clean:
        return False, message
    project_dir = Path(project_dir)
    code, _ = _git(project_dir, 'rev-parse', '--is-inside-work-tree')
    if code != 0:
        return False, f'{project_dir} — не git-репозиторий. Проверьте путь PROJECT_DIR'
    code, upstream = _git(project_dir, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}')
    if code != 0 or not upstream:
        code, url = _git(project_dir, 'remote', 'get-url', 'origin')
        if code != 0 or not url:
            return None, ('удалённая копия Git не настроена. На первом блоке достаточно '
                          'проверенной копии файлов; GitHub подключайте по желанию (docs/СДАЧА.md)')
        return False, f'адрес {url} подключён, но отправки ещё не было: git push -u origin main'
    remote = upstream.split('/', 1)[0]
    code, url = _git(project_dir, 'remote', 'get-url', remote)
    if url.endswith('.bundle'):
        return None, ('проект восстановлен из файла, а в файл отправить нельзя. '
                      'Подключите свой GitHub: git remote set-url origin <адрес> (docs/GIT.md)')
    code, unpushed = _git(project_dir, 'log', '--oneline', '@{u}..HEAD')
    if code == 0 and unpushed:
        count = len(unpushed.splitlines())
        if _is_server_url(url):
            return False, (f'не отправлено {_where(url)} коммитов: {count}. '
                           'На GitHub отправляем дома или со своего ноутбука')
        return False, f'не отправлено коммитов: {count}. Выполните git push'
    return True, (f'рабочее дерево чистое; по локальным данным нет неотправленных коммитов {_where(url)}. '
                  'Доступность удалённой копии не проверялась. Ctrl+S и контроль открытия копии обязательны')


@_task('01.2.1')
def _check_ai_system(system):
    if not isinstance(system, dict):
        return False, 'нужен словарь'
    missing = [key for key in AI_TASK_KEYS if key not in system]
    if missing:
        return False, f'не хватает ключей: {missing}'
    empty = [key for key in AI_TASK_KEYS if not _is_filled(system[key])]
    if empty:
        return False, f'заполните значения (непустые строки): {empty}'
    if system['знания'].strip() not in KNOWLEDGE_VALUES:
        return False, f'для "знания" выберите одно из {KNOWLEDGE_VALUES}'
    if system['время'].strip() not in TIME_VALUES:
        return False, f'для "время" выберите одно из {TIME_VALUES}'
    if system['система'].strip().lower() == 'антиспам-фильтр почты':
        return False, 'это пример из ноутбука — опишите другую систему'
    return True, f'система «{system["система"]}» описана'


@_task('01.2.2')
def _check_gost_classes(answer):
    if not isinstance(answer, dict):
        return False, 'нужен словарь «основание: класс»'
    missing = [basis for basis in GOST_BASES if basis not in answer]
    if missing:
        return False, f'не хватает оснований: {missing}'
    classes = _gost_classes()
    for basis in GOST_BASES:
        value = answer[basis]
        allowed = classes[basis]
        normalized = {name.lower(): name for name in allowed}
        if not isinstance(value, str) or value.strip().lower() not in normalized:
            return False, f'для «{basis}» класс «{value}» не найден. Возможные: {allowed}'
    return True, 'все классы существуют. Сравним ответы с соседями?'


@_task('01.2.3')
def _check_project_choice(project):
    if not isinstance(project, dict):
        return False, 'нужен словарь'
    for key in ['трек', 'вариант', 'вопросы']:
        if key not in project:
            return False, f'не хватает ключа "{key}"'
    if not _is_filled(project['трек']):
        return False, 'напишите тему из меню или свою предварительную тему'
    if not _is_filled(project['вариант']):
        return False, 'укажите вариант внутри трека'
    questions = project['вопросы']
    if not isinstance(questions, list) or len(questions) < 1:
        return False, 'нужен список хотя бы из одного конкретного вопроса'
    for question in questions:
        if not _is_filled(question) or not question.strip().endswith('?'):
            return False, f'каждый вопрос — строка со знаком вопроса в конце: {question!r}'
        if len(question.strip()) < 15:
            return False, f'вопрос слишком короткий, сделайте его конкретнее: {question!r}'
    if len({question.strip().lower() for question in questions}) < len(questions):
        return False, 'вопросы повторяются'
    return True, f'трек «{project["трек"]}», вопросов: {len(questions)}'


@_task('01.2.4')
def _check_project_readme(project_dir, project):
    project_dir = Path(project_dir)
    readme = project_dir / 'README.md'
    if not readme.exists():
        return False, 'не найден README.md в папке проекта'
    text = readme.read_text(encoding='utf-8')
    if README_PLACEHOLDER in text:
        return False, 'в README.md осталась заготовка "<впишите трек>" — впишите свой трек'
    if isinstance(project, dict) and project.get('трек') and project['трек'] not in text:
        return False, f'в README.md не найден ваш трек «{project["трек"]}»'
    return True, 'предварительная тема записана в README. Обсудите вопрос и доступность данных с преподавателем'



@_task('01.2.6')
def _check_bundle(project_dir, bundle_path):
    clean, message = _check_committed(project_dir)
    if not clean:
        return False, message
    bundle_path = Path(bundle_path)
    if not bundle_path.exists():
        return False, f'файл {bundle_path.name} не создан — запустите ячейку с git bundle create'
    code, out = _git_all_output(project_dir, 'bundle', 'verify', str(bundle_path))
    if code != 0:
        first_line = out.splitlines()[0] if out else 'без сообщения'
        return False, f'файл не проходит проверку git: {first_line}'
    code, head = _git(project_dir, 'rev-parse', 'HEAD')
    code_heads, heads = _git_all_output(project_dir, 'bundle', 'list-heads', str(bundle_path))
    if code != 0 or code_heads != 0 or not head:
        return False, 'не удалось сравнить последний коммит и содержимое бандла'
    if head not in {line.split()[0] for line in heads.splitlines() if line.split()}:
        return False, 'в файле нет последнего коммита — сделайте бандл заново после коммита'
    size_kb = bundle_path.stat().st_size / 1024
    return True, f'файл {bundle_path.name} готов, {size_kb:.0f} КБ. Отправьте его себе, чтобы продолжить дома'


@_task('01.2.7')
def _check_github(project_dir):
    """Необязательное задание: проект отправлен на GitHub или GitVerse.

    Адрес сервера может быть записан под любым именем: origin дома, github в аудитории.
    Проверка работает без интернета: смотрим только то, что git знает локально.
    """
    project_dir = Path(project_dir)
    code, names = _git(project_dir, 'remote')
    servers = []
    for name in names.split():
        code, url = _git(project_dir, 'remote', 'get-url', name)
        if code == 0 and _is_server_url(url):
            servers.append((name, url))
    if not servers:
        return None, ('GitHub пока не подключён — это нормально: отправляем дома или со своего ноутбука, '
                      'обязательного срока подключения нет (docs/СДАЧА.md)')
    code, branch = _git(project_dir, 'rev-parse', '--abbrev-ref', 'HEAD')
    for name, url in servers:
        code, _ = _git(project_dir, 'rev-parse', '--verify', '--quiet', f'refs/remotes/{name}/{branch}')
        if code != 0:
            continue
        code, unpushed = _git(project_dir, 'log', '--oneline', f'{name}/{branch}..HEAD')
        if code == 0 and unpushed:
            count = len(unpushed.splitlines())
            return False, (f'{_where(url)} не отправлено коммитов: {count}. '
                           'Без доступа к сети это нормально: отправьте их дома или со своего ноутбука')
        return True, f'всё отправлено на {url}. Эту ссылку и кладите в резюме'
    name, url = servers[0]
    return False, f'{url} подключён, но туда ещё ничего не отправлено: git push -u {name} {branch}'


# Блок 2: проверки результатов, не выбранного способа решения.
@_task('02.1.1')
def _lab_points(value):
    expected = pd.Series([15,15,20,20,10,20], index=[f'ЛР{i}' for i in range(1,7)])
    ok = isinstance(value, pd.Series) and value.equals(expected)
    return ok, 'Шесть работ, сумма 100' if ok else 'Проверьте значения и индекс ЛР1…ЛР6'

@_task('02.1.2')
def _marks_selection(row, col, scalar):
    ok = list(row.index)==['Ivanov','Petrov','Sidorov'] and row.tolist()==[5,4,3] and col.tolist()==[4,3,5,4,5,5,4] and scalar==4
    return bool(ok), 'Строка, столбец и позиция согласованы' if ok else 'Проверьте выбор строки Algebra и столбца Petrov'

@_task('02.1.3')
def _alternating(value):
    expected = pd.DataFrame([[5,4,3],[4,5,3],[4,5,3],[4,4,5]], index=['Algebra','Chemistry','History','Literature'], columns=['Ivanov','Petrov','Sidorov'])
    ok = isinstance(value,pd.DataFrame) and value.equals(expected)
    return ok, 'Каждая вторая строка выбрана' if ok else 'Начните с первой строки, шаг 2; сохраните все столбцы'

@_task('02.2.1')
def _titanic_profile(shape, missing, counts):
    data = pd.read_csv(DATA_DIR/'titanic.csv',index_col='PassengerId')
    expected = data.Pclass.value_counts().sort_index()
    ok = tuple(shape)==data.shape and missing==data.isna().sum().idxmax() and counts.sort_index().equals(expected)
    return ok, 'Размер, пропуски и классы проверены' if ok else 'PassengerId — индекс; используйте isna().sum() и value_counts()'

@_task('02.2.2')
def _titanic_rates(rates, fare):
    data = pd.read_csv(DATA_DIR/'titanic.csv')
    expected = data.groupby('Sex').Survived.mean()
    ok = set(rates.index)==set(expected.index) and all(abs(rates[k]-expected[k])<1e-6 for k in expected.index) and abs(fare-data.Fare.max())<1e-6
    return bool(ok), 'Доли и максимум проверены; ограничения объясните сами' if ok else 'Нужны доли 0…1 отдельно по Sex и максимум Fare'
