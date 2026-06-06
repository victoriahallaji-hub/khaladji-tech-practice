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

NUMERIC_COLS = dataset.NUMERIC_COLS


class ScatterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Точечная диаграмма')
        self.resizable(False, False)

        self.x_col = tk.StringVar(value=NUMERIC_COLS[0])
        self.y_col = tk.StringVar(value=NUMERIC_COLS[1])

        self._build_ui()
        self._update_plot()

    def _build_ui(self):
        # Левая панель — выбор Y
        left = tk.Frame(self, padx=4, pady=4)
        left.grid(row=0, column=0, sticky='ns')
        tk.Label(left, text='Ось Y', font=('Arial', 9, 'bold')).pack(pady=(0, 4))
        for col in NUMERIC_COLS:
            b = tk.Button(left, text=col, width=14,
                          command=lambda c=col: self._set_y(c))
            b.pack(pady=2)

        # Холст для графика
        self.canvas_label = tk.Label(self)
        self.canvas_label.grid(row=0, column=1, padx=4, pady=4)

        # Нижняя панель — выбор X
        bottom = tk.Frame(self, padx=4, pady=4)
        bottom.grid(row=1, column=1, sticky='ew')
        tk.Label(bottom, text='Ось X:', font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 6))
        for col in NUMERIC_COLS:
            b = tk.Button(bottom, text=col, width=14,
                          command=lambda c=col: self._set_x(c))
            b.pack(side='left', padx=2)

        # Кнопка сохранения
        tk.Button(self, text='Сохранить', command=self._save)\
            .grid(row=1, column=0, pady=4)

    def _set_x(self, col):
        self.x_col.set(col)
        self._update_plot()

    def _set_y(self, col):
        self.y_col.set(col)
        self._update_plot()

    def _make_figure(self):
        fig, ax = plt.subplots(figsize=(6, 5), dpi=96)
        x = dataset.df[self.x_col.get()]
        y = dataset.df[self.y_col.get()]
        ax.scatter(x, y, marker=MARKER, color='steelblue', alpha=0.7)
        ax.set_xlabel(self.x_col.get())
        ax.set_ylabel(self.y_col.get())
        ax.set_title(f'{self.y_col.get()} vs {self.x_col.get()}')
        fig.tight_layout()
        return fig

    def _update_plot(self):
        fig = self._make_figure()
        agg = FigureCanvasAgg(fig)
        agg.draw()
        buf, (w, h) = agg.print_to_buffer(), agg.get_width_height()
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
    app = ScatterApp()
    app.mainloop()
