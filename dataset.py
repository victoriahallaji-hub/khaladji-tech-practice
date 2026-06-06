import pandas as pd
import sys
import io

# Категориальные колонки датасета (выбор из фиксированного набора значений,
# сложение которых не имеет смысла)
CATEGORICAL_COLS = ['key', 'mode', 'time_signature']

# Счётные (числовые) колонки
NUMERIC_COLS = ['danceability', 'energy', 'loudness', 'speechiness',
                'acousticness', 'valence', 'tempo', 'duration_ms']

# Загружаем датасет при импорте модуля
df = pd.read_csv('dataset.csv')


def print_report():
    """Формирует отчёт и выводит его в консоль и файл report.txt."""
    output = io.StringIO()

    def p(text=''):
        print(text)
        print(text, file=output)

    # 1. Размер датасета
    p(df.shape)

    # 2. Типы данных
    buf = io.StringIO()
    df.info(buf=buf)
    info_str = buf.getvalue()
    print(info_str)
    print(info_str, file=output)

    # 3. Количество незаполненных ячеек
    p(df.isnull().sum().to_string())

    # 4. Статистика по счётным колонкам
    p()
    header = 'Колонка>\tсреднее\tмедиана\tотклонение'
    p(header)
    for col in NUMERIC_COLS:
        if col in df.columns:
            mean = df[col].mean()
            median = df[col].median()
            std = df[col].std()
            p(f'{col}>\t{mean:.2f};\t{median:.2f};\t{std:.2f}')

    # 5. Частоты категориальных колонок
    p()
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            p(col)
            p(df[col].value_counts().to_string())
            p(f'Name: count, dtype: int64')
            p()

    # Сохраняем в файл
    with open('report.txt', 'w', encoding='utf-8') as f:
        f.write(output.getvalue())


if __name__ == '__main__':
    print_report()
