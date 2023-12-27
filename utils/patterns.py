from datetime import timedelta, date, time

date_pattern = r"\d{1,2}[./-]\d{1,2}[./-]\d{2,4}"
short_date_pattern = r"\d{1,2}[./-]\d{1,2}"
time_pattern = r"\d{1,2}:\d{2}"

time_triggers = {
    'утром': time (12, 0),
    '(к|до) утр': time (12, 0),
    '(к|до) полудн': time (12, 0),
    '(к|до) обед': time (14, 0),
    'в первой половин': time (14, 0),
    '(в|во) второй половин': time (21, 0),
    '(к|до) вечер': time (21, 0),
    'вечер': time (21, 0),
    'сегодня': time (21, 0)
    }


# возвращает триггеры для даты
def get_date_triggers(current_date: date) -> dict:
    return {
        'завтра': timedelta(days=1),
        'послезавтра': timedelta(days=2),
        'через день': timedelta(days=2),
        'через (\d+) (день|дня|дней)': 'days',
        '(к|до) (\d+) числ': 'days_1',
        'на эту недел': 'on_week',
        'через неделю': timedelta(weeks=1),
        'до конца недел': timedelta(days=(4 - current_date.weekday())),
        'понедельник': timedelta(days=(0 - current_date.weekday())),
        'вторник': timedelta(days=(1 - current_date.weekday())),
        'сред': timedelta(days=(2 - current_date.weekday())),
        'четверг': timedelta(days=(3 - current_date.weekday())),
        'пятниц': timedelta(days=(4 - current_date.weekday())),
        'суббот': timedelta(days=(5 - current_date.weekday())),
        'воскресень': timedelta(days=(6 - current_date.weekday())),
        'до конца месяц': 'end_month'
        }
