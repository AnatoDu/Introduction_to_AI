"""Локальный HTML-отчёт из уже рассчитанных срезов; без CDN и сервера.

Каждый срез: label, count, mean (число или None), note, image (путь к PNG).
Вычисления делает notebook, этот модуль только упаковывает результат.
"""
import base64
import html
import json
from pathlib import Path


def export_report(views, path, title='Проверяем вывод по срезам'):
    if not views:
        raise ValueError('Нужен хотя бы один срез')
    records = []
    for view in views:
        record = {key: view[key] for key in ('label', 'count', 'mean', 'note')}
        if record['count'] < 0:
            raise ValueError('Количество не может быть отрицательным')
        png = Path(view['image']).read_bytes()
        if not png.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Изображение должно быть PNG')
        record['image'] = 'data:image/png;base64,' + base64.b64encode(png).decode('ascii')
        records.append(record)
    data = json.dumps(records, ensure_ascii=False, allow_nan=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>
body{font:18px/1.5 system-ui,sans-serif;max-width:1000px;margin:30px auto;padding:0 18px;color:#213246;background:#f5f7fb}
main{background:white;padding:24px;border-radius:16px}select{font:inherit;padding:8px}img{width:100%;height:auto}
#metrics{font-size:1.15em;font-weight:600}footer{font-size:.9em;color:#526174}
</style><main><h1>__TITLE__</h1>
<p>Palmer Penguins. Выбор среза меняет расчёт и рисунок. Это наблюдения в наборе, не перепись популяции.</p>
<label for="slice">Срез по острову: </label><select id="slice"></select>
<p id="metrics" aria-live="polite"></p><p id="note"></p><img id="chart" alt="Масса птиц по видам в выбранном срезе">
<footer>Средняя масса посчитана по известным значениям; n — число использованных измерений.
Остров и вид связаны составом выборки. Отчёт не доказывает влияние острова на массу.
Источник: <a href="https://allisonhorst.github.io/palmerpenguins/">Palmer Penguins, CC0</a>.
Файл автономен; интернет нужен только для перехода по ссылке источника.</footer></main>
<script id="report-data" type="application/json">__DATA__</script>
<script>
const views = JSON.parse(document.getElementById('report-data').textContent);
const menu = document.getElementById('slice');
views.forEach((v, i) => {const o = document.createElement('option');o.value=i;o.textContent=v.label;menu.appendChild(o);});
function render() {
 const v=views[Number(menu.value)];
 document.getElementById('metrics').textContent='n = '+v.count+'; средняя масса = '+(v.mean === null ? 'нет данных' : v.mean.toFixed(1)+' г');
 document.getElementById('note').textContent=v.note;
 document.getElementById('chart').src=v.image;
}
menu.addEventListener('change', render);render();
</script></html>'''
    page = page.replace('__TITLE__', html.escape(title)).replace('__DATA__', data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding='utf-8')
    return path
