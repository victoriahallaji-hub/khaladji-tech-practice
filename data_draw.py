import tkinter as tk
from tkinter import ttk, colorchooser
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image, ImageTk, ImageDraw
import datetime
import dataset

# Студ. ID 70227160
# Рекурсивная сумма = 7
# Толщина кисти: 7 // 2 + 5 = 8
# Цвет RGB из последних 6 цифр ID (227160): R=22, G=71, B=60 -> #16473C
DEFAULT_THICKNESS = 8
DEFAULT_COLOR = '#16473C'
MARKER = '*'
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


class DrawApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Рисование на графике')
        self.resizable(False, False)

        self.x_col = tk.StringVar(value=ALL_COLS[0])
        self.y_col = tk.StringVar(value=ALL_COLS[1])
        self.cmap_var = tk.StringVar(value=DEFAULT_CMAP)

        self.draw_mode = False
        self.pen_color = DEFAULT_COLOR
        self.pen_thickness = DEFAULT_THICKNESS

        # Слой рисования поверх графика (PIL Image)
        self._draw_layer = None
        self._last_line = []       # пиксели текущей линии
        self._prev_line = []       # пиксели предыдущей линии (для отмены)
        self._mouse_down = False
        self._canvas_pos = (0, 0)  # координаты холста внутри окна

        self._build_ui()
        self._update_plot()

    # ──────────────────────────────────────────────────────────────
    # UI
    # ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Верхняя панель
        top = tk.Frame(self, padx=6, pady=4)
        top.grid(row=0, column=0, columnspan=3, sticky='ew')

        tk.Label(top, text='Цветовая схема:', font=('Arial', 9, 'bold')).pack(side='left')
        cb = ttk.Combobox(top, textvariable=self.cmap_var,
                          values=CMAPS, width=12, state='readonly')
        cb.pack(side='left', padx=6)
        cb.bind('<<ComboboxSelected>>', lambda e: self._reset_and_update())

        tk.Label(top, text='   ').pack(side='left')

        # Кнопка режима рисования
        self._draw_btn = tk.Button(top, text='✏ Рисование',
                                   command=self._toggle_draw, relief='raised', bd=2)
        self._draw_btn.pack(side='left', padx=4)

        # Цвет кисти
        self._color_btn = tk.Canvas(top, width=24, height=24, bg=self.pen_color,
                                    cursor='hand2', relief='ridge', bd=1)
        self._color_btn.pack(side='left', padx=4)
        self._color_btn.bind('<Button-1>', lambda e: self._choose_color())

        # Толщина
        tk.Label(top, text='Толщина:').pack(side='left')
        self._thick_var = tk.IntVar(value=self.pen_thickness)
        tk.Spinbox(top, from_=1, to=30, textvariable=self._thick_var,
                   width=4, command=self._update_thickness).pack(side='left', padx=4)

        # Левая панель — Y
        left = tk.Frame(self, padx=4, pady=4)
        left.grid(row=1, column=0, sticky='ns')
        tk.Label(left, text='Ось Y', font=('Arial', 9, 'bold')).pack(pady=(0, 4))
        for col in ALL_COLS:
            b = tk.Button(left, text=col, width=14,
                          command=lambda c=col: self._set_y(c))
            b.pack(pady=2)

        # Холст
        self.canvas_widget = tk.Label(self, cursor='arrow')
        self.canvas_widget.grid(row=1, column=1, padx=4, pady=4)
        self.canvas_widget.bind('<ButtonPress-1>',   self._on_press)
        self.canvas_widget.bind('<B1-Motion>',       self._on_drag)
        self.canvas_widget.bind('<ButtonRelease-1>', self._on_release)
        self.canvas_widget.bind('<Button-3>',        self._exit_draw)

        # Нижняя панель — X
        bottom = tk.Frame(self, padx=4, pady=4)
        bottom.grid(row=2, column=1, sticky='ew')
        tk.Label(bottom, text='Ось X:', font=('Arial', 9, 'bold')).pack(side='left', padx=(0, 6))
        for col in ALL_COLS:
            b = tk.Button(bottom, text=col, width=14,
                          command=lambda c=col: self._set_x(c))
            b.pack(side='left', padx=2)

        # Кнопки сохранить / отмена
        side = tk.Frame(self, padx=4)
        side.grid(row=2, column=0)
        tk.Button(side, text='Сохранить', command=self._save).pack(pady=2)

        self.bind('<Control-z>', self._undo)

    # ──────────────────────────────────────────────────────────────
    # Управление данными и графиком
    # ──────────────────────────────────────────────────────────────
    def _set_x(self, col):
        self.x_col.set(col)
        self._exit_draw()
        self._reset_and_update()

    def _set_y(self, col):
        self.y_col.set(col)
        self._exit_draw()
        self._reset_and_update()

    def _reset_and_update(self):
        self._draw_layer = None
        self._last_line = []
        self._prev_line = []
        self._update_plot()

    def _make_figure(self):
        x_col = self.x_col.get()
        y_col = self.y_col.get()
        cmap = self.cmap_var.get()
        fig, ax = plt.subplots(figsize=(6, 5), dpi=96)
        x_is_num = x_col in NUMERIC_COLS
        y_is_num = y_col in NUMERIC_COLS

        if x_col == y_col and x_is_num:
            vals = dataset.df[x_col]
            n, bins, patches = ax.hist(vals, bins=10)
            cm = plt.get_cmap(cmap)
            for i, patch in enumerate(patches):
                patch.set_facecolor(cm(i / len(patches)))
            ax.set_xlabel(x_col); ax.set_ylabel('Количество')
            ax.set_title(f'Гистограмма: {x_col}')
        elif x_col == y_col and not x_is_num:
            counts = dataset.df[x_col].value_counts()
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(counts)) for i in range(len(counts))]
            ax.pie(counts, labels=[str(k) for k in counts.index],
                   colors=colors, autopct='%1.1f%%')
            ax.set_title(f'Распределение: {x_col}')
        elif x_is_num and not y_is_num:
            groups = dataset.df.groupby(y_col)[x_col].apply(list)
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(groups)) for i in range(len(groups))]
            bp = ax.boxplot(groups.values, labels=[str(k) for k in groups.index],
                            patch_artist=True)
            for patch, color in zip(bp['boxes'], colors):
                patch.set_facecolor(color)
            ax.set_xlabel(y_col); ax.set_ylabel(x_col)
            ax.set_title(f'Коробочная: {x_col} по {y_col}')
        elif not x_is_num and y_is_num:
            counts = dataset.df[x_col].value_counts()
            cm = plt.get_cmap(cmap)
            colors = [cm(i / len(counts)) for i in range(len(counts))]
            ax.bar([str(k) for k in counts.index], counts.values, color=colors)
            ax.set_xlabel(x_col); ax.set_ylabel('Количество')
            ax.set_title(f'Столбчатая: количество по {x_col}')
        else:
            x = dataset.df[x_col]; y = dataset.df[y_col]
            ax.scatter(x, y, marker=MARKER, color='steelblue', alpha=0.7)
            ax.set_xlabel(x_col); ax.set_ylabel(y_col)
            ax.set_title(f'{y_col} vs {x_col}')

        fig.tight_layout()
        return fig

    def _render_figure(self):
        """Возвращает PIL Image из текущей фигуры matplotlib."""
        fig = self._make_figure()
        agg = FigureCanvasAgg(fig)
        agg.draw()
        w, h = agg.get_width_height()
        img = Image.frombytes('RGBA', (w, h), agg.buffer_rgba()).convert('RGB')
        plt.close(fig)
        return img

    def _update_plot(self):
        """Перерисовывает холст: фигура + слой рисования."""
        base = self._render_figure()
        if self._draw_layer is None:
            self._draw_layer = Image.new('RGBA', base.size, (0, 0, 0, 0))

        composite = base.copy().convert('RGBA')
        composite.alpha_composite(self._draw_layer)
        self._display_img = composite.convert('RGB')
        self._tk_img = ImageTk.PhotoImage(self._display_img)
        self.canvas_widget.configure(image=self._tk_img)
        self._img_size = base.size

    def _composite_display(self):
        """Показывает текущее состояние без перерисовки фигуры."""
        if not hasattr(self, '_base_img'):
            return
        composite = self._base_img.copy().convert('RGBA')
        composite.alpha_composite(self._draw_layer)
        self._display_img = composite.convert('RGB')
        self._tk_img = ImageTk.PhotoImage(self._display_img)
        self.canvas_widget.configure(image=self._tk_img)

    # ──────────────────────────────────────────────────────────────
    # Режим рисования
    # ──────────────────────────────────────────────────────────────
    def _toggle_draw(self):
        if self.draw_mode:
            self._exit_draw()
        else:
            self._enter_draw()

    def _enter_draw(self):
        self.draw_mode = True
        self._draw_btn.configure(relief='sunken')
        self.canvas_widget.configure(cursor='pencil')
        # Кешируем базовый рисунок чтобы не перерисовывать matplotlib при каждом штрихе
        self._base_img = self._render_figure()
        if self._draw_layer is None:
            self._draw_layer = Image.new('RGBA', self._base_img.size, (0, 0, 0, 0))

    def _exit_draw(self, event=None):
        self.draw_mode = False
        self._draw_btn.configure(relief='raised')
        self.canvas_widget.configure(cursor='arrow')

    def _choose_color(self):
        color = colorchooser.askcolor(color=self.pen_color, title='Выбор цвета')[1]
        if color:
            self.pen_color = color
            self._color_btn.configure(bg=color)

    def _update_thickness(self):
        self.pen_thickness = self._thick_var.get()

    # ──────────────────────────────────────────────────────────────
    # Рисование мышью
    # ──────────────────────────────────────────────────────────────
    def _widget_to_img_coords(self, ex, ey):
        """Переводит координаты события в координаты изображения."""
        return ex, ey

    def _on_press(self, event):
        if not self.draw_mode:
            return
        self._mouse_down = True
        self._last_line = []
        self._draw_point(event.x, event.y)

    def _on_drag(self, event):
        if not self.draw_mode or not self._mouse_down:
            return
        self._draw_point(event.x, event.y)

    def _on_release(self, event):
        if not self.draw_mode:
            return
        self._mouse_down = False
        # Сохраняем текущую линию как предыдущую (для отмены)
        self._prev_line = list(self._last_line)
        self._last_line = []

    def _draw_point(self, x, y):
        """Рисует квадратик пикселей на слое рисования."""
        t = max(1, self._thick_var.get())
        half = t // 2
        draw = ImageDraw.Draw(self._draw_layer)

        # Конвертируем hex цвет в RGBA
        r = int(self.pen_color[1:3], 16)
        g = int(self.pen_color[3:5], 16)
        b = int(self.pen_color[5:7], 16)
        fill = (r, g, b, 255)

        x0, y0 = x - half, y - half
        x1, y1 = x + half, y + half
        draw.rectangle([x0, y0, x1, y1], fill=fill)
        self._last_line.append((x0, y0, x1, y1))

        # Обновляем экран без пересчёта matplotlib
        self._composite_display()

    def _undo(self, event=None):
        """Отменяет последнюю нарисованную линию (Ctrl+Z)."""
        if self._mouse_down or not self._prev_line:
            return
        draw = ImageDraw.Draw(self._draw_layer)
        # Стираем пиксели предыдущей линии
        for (x0, y0, x1, y1) in self._prev_line:
            draw.rectangle([x0, y0, x1, y1], fill=(0, 0, 0, 0))
        self._prev_line = []
        self._composite_display()

    # ──────────────────────────────────────────────────────────────
    # Сохранение
    # ──────────────────────────────────────────────────────────────
    def _save(self):
        now = datetime.datetime.now()
        fname = f'graph{now.strftime("%H")}_{now.strftime("%M")}_{now.strftime("%S")}.png'
        self._display_img.save(fname)
        print(f'График сохранён: {fname}')


if __name__ == '__main__':
    app = DrawApp()
    app.mainloop()
