import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk
import datetime
import dataset

# Студ. ID 70227160: рекурсивная сумма = 7, маркер = '*'
MARKER = '*'
# Буква Х → цветовая схема 'BuGn'
DEFAULT_CMAP = 'BuGn'

CMAPS = [
    'viridis', 'plasma', 'inferno', 'magma', 'cividis',
    'Greys', 'Purples', 'Blues', 'Greens', 'Oranges',
    'Reds', 'YlOrBr', 'YlOrRd', 'OrRd', 'PuRd',
    'RdPu', 'BuPu', 'GnBu', 'PuBu', 'YlGnBu',
    'PuBuGn', 'BuGn', 'YlGn', 'binary', 'gist_yarg',
    'spring', 'summer', 'autumn', 'winter',
]

NUMERIC_COLS = dataset.NUMERIC_COLS
CATEGORICAL_COLS = dataset.CATEGORICAL_COLS
ALL_COLS = NUMERIC_COLS + CATEGORICAL_COLS


class VisualApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Расширенная визуализация данных')
        self.resizable(False, False)

        self.x_col = tk.StringVar(value=ALL_COLS[0])
        self.y_col = tk.StringVar(value=ALL_COLS[1])
        self.cmap_var = tk.StringVar(value=DEFAULT_CMAP)

        self._build_ui()
        self._update_plot()

    def _build_ui(self):
        # Верхняя панель — выбор цветовой схемы
        top = tk.Frame(self, padx=6, pady=4)
        top.grid(row=0, column=0, columnspan=3, sticky='ew')
        tk.Label(top, text='Цветовая схема:',
                 font=('Arial', 9, 'bold')).pack(side='left')
        cb = ttk.Combobox(top, textvariable=self.cmap_var,
                          values=CMAPS, width=14, state='readonly')
        cb.pack(side='left', padx=6)
        cb.bind('<<ComboboxSelected>>', lambda e: self._update_plot())

        # Левая панель — выбор Y
        left = tk.Frame(self, padx=4, pady=4)
        left.grid(row=1, column=0, sticky='ns')
        tk.Label(left, text='Ось Y', font=('Arial', 9, 'bold')).pack(pady=(0, 4))
        for col in ALL_COLS:
            b = tk.Button(left, text=col, width=14,
                          command=lambda c=col: self._set_y(c))
            b.pack(pady=2)

        # Холст
        self.canvas_label = tk.Label(self)
        self.canvas_label.grid(row=1, column=1, padx=4, pady=4)

        # Нижняя панель — выбор X
        bottom = tk.Frame(self, padx=4, pady=4)
        bottom.grid(row=2, column=1, sticky='ew')
        tk.Label(bottom, text='Ось X:', font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 6))
        for col in ALL_COLS:
            b = tk.Button(bottom, text=col, width=14,
                          command=lambda c=col: self._set_x(c))
            b.pack(side='left', padx=2)

        # Кнопка сохранения
        tk.Button(self, text='Сохранить', command=self._save)\
            .grid(row=2, column=0, pady=4)

    def _set_x(self, col):
        self.x_col.set(col)
        self._update_plot()

    def _set_y(self, col):
        self.y_col.set(col)
        self._update_plot()

    def _make_figure(self):
        x_col = self.x_col.get()
        y_col = self.y_col.get()
        cmap = self.cmap_var.get()
        fig, ax = plt.subplots(figsize=(6, 5), dpi=96)

        x_is_num = x_col in NUMERIC_COLS
        y_is_num = y_col in NUMERIC_COLS

        if x_col == y_col and x_is_num:
            # Гистограмма
            vals = dataset.df[x_col]
            n, bins, patches = ax.hist(vals, bins=10)
            cm = plt.get_cmap(cmap)
            for i, patch in enumerate(patches):
                patch.set_facecolor(cm(i / len(patches)))
            ax.set_xlabel(x_col)
            ax.set_ylabel('Количество')
            ax.set_title(f'Гистограмма: {x_col}')

        elif x_col == y_col and not x_is_num:
            # Круговая диаграмма
            counts = dataset.df[x_col].value_counts()
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(counts)) for i in range(len(counts))]
            ax.pie(counts, labels=[str(k) for k in counts.index],
                   colors=colors, autopct='%1.1f%%')
            ax.set_title(f'Распределение: {x_col}')

        elif x_is_num and not y_is_num:
            # Коробочная диаграмма
            groups = dataset.df.groupby(y_col)[x_col].apply(list)
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(groups)) for i in range(len(groups))]
            bp = ax.boxplot(groups.values, labels=[str(k) for k in groups.index],
                            patch_artist=True)
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            ax.set_xlabel(y_col)
            ax.set_ylabel(x_col)
            ax.set_title(f'Коробочная: {x_col} по {y_col}')

        elif not x_is_num and y_is_num:
            # Столбчатая диаграмма
            counts = dataset.df[x_col].value_counts()
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(counts)) for i in range(len(counts))]
            ax.bar([str(k) for k in counts.index], counts.values, color=colors)
            ax.set_xlabel(x_col)
            ax.set_ylabel('Количество')
            ax.set_title(f'Столбчатая: количество по {x_col}')

        else:
            # Точечная диаграмма
            x = dataset.df[x_col]
            y = dataset.df[y_col]
            ax.scatter(x, y, marker=MARKER, color='steelblue', alpha=0.7)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(f'{y_col} vs {x_col}')

        fig.tight_layout()
        return fig

    def _update_plot(self):
        fig = self._make_figure()
        agg = FigureCanvasAgg(fig)
        agg.draw()
        w, h = agg.get_width_height()
        img = Image.frombytes('RGBA', (w, h), agg.buffer_rgba())
        self._tk_img = ImageTk.PhotoImage(img)
        self.canvas_label.configure(image=self._tk_img)
        plt.close(fig)

    def _save(self):
        fig = self._make_figure()
        now = datetime.datetime.now()
        fname = f'graph{now.strftime("%H")}_{now.strftime("%M")}_{now.strftime("%S")}.png'
        fig.savefig(fname, dpi=96)
        plt.close(fig)
        print(f'График сохранён: {fname}')


if __name__ == '__main__':
    app = VisualApp()
    app.mainloop()
