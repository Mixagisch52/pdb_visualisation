import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
'''
Графическое приложение для визуализации 3D-структур белков из PDB-файлов. 
Использует Tkinter для GUI и Matplotlib для 3D-рендеринга. 
Поддерживает: 
- Загрузку PDB-файлов 
- Визуализацию CA-атомов белковой цепи 
- Базовое управление 3D-графикой 
Attributes: 
master (tk.Tk):Главное окно приложения 
pdb_data (str): Сырые данные загруженного PDB-файла 
fig (matplotlib.figure.Figure): Область для построения графиков 
canvas (FigureCanvasTkAgg): Холст для встраивания графики в Tkinter
'''


class ProteinViewerMatplotlib:
    '''
    Инициализирует приложение:
    Создаёт корневое окно Tkinter (master(tk.Tk)) с заголовком и размером
    Вызывает метод setup_ui() для создания интерфейса


    '''
    def __init__(self, master):
        self.master = master
        self.master.title("Protein Viewer (Matplotlib)")
        self.master.geometry("800x600")

        self.setup_ui()
        self.pdb_data = None

    def setup_ui(self):
        '''
        Создаёт пользовательский интерфейс.
        Добавляет:
        - Кнокпи «Load PDB» для загрузки файлов (вызов load_pdb())
        - Кнопки «View 3D» для визуализации (которая изначально неактивна) (вызов view-3d)
        - Область для отображения 3D-графики (холст) :
            • Figure(7x5 дюймов, 100 DPI)
            • Canvas для встраивания в Tkinter с авторасширением(Преобразует график в виджет на всю доступную область).
        Использует:
        - tk.Button для кнопок
        - FigureCanvasTkAgg для интеграции Matplotlib
        - pack() geometry manager

        «View 3D» активируется только после заргузки pdb файла.
        '''
        # Кнопки
        self.load_btn = tk.Button(self.master, text="Load PDB", command=self.load_pdb)
        self.load_btn.pack(pady=10)

        self.view_btn = tk.Button(self.master, text="View 3D", command=self.view_3d, state=tk.DISABLED)
        self.view_btn.pack(pady=10)

        # Контейнер для Matplotlib
        self.fig = Figure(figsize=(7, 5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def load_pdb(self):
        '''
        Заргужает PDB-файл через диалоговое окно под стиль Вашей операционной системы, подготовливая его таким образом к визуализации, вызовом других функций.
        Обновляет:
        - self.pdb_data() — сохраняет содержимое файла
        - Активрует кнопку «View 3D»
        Обрабатывает ошибки выбора
        :returns:
        None: данные сохраняются в self.pdb_data(), кнопка view_btn активируется.
        Если файл не выбран, то завершаает функцию.
        Ограничения:
        - Поддерживает только текстовые PDB-файлы.
        - Максимальный размер файла ограничен доступной памятью.
        '''
        filepath = filedialog.askopenfilename(filetypes=[("PDB Files", "*.pdb*")])
        if not filepath:
            return

        with open(filepath, 'r') as f:
            self.pdb_data = f.read()

        self.view_btn.config(state=tk.NORMAL)

    def view_3d(self):
        '''
        Визцализирует белковую цепь в 3D.
         Полный цикл работы метода:
        1. Извлекает координаты CA-атомов через функцию parse_pdb_to_points()
        2. Инициализирует 3D-пространство:
       - Очищает предыдущий график (fig.clf())
       - Создает 3D-оси (projection='3d')
        3. Выводит белковый остов:
       - Синяя сплошная линия между CA-атомами
       - Толщина линии 2px
       - Подпись 'Backbone' в легенде
        4. Настраивает отображение:
       - Доабвляет подписи для осей (X/Y/Z)
       - Автомасштабирование под данные
       - Добавляет легенду
        5. Обновляет холст для отображения (canvas.draw())

        Требования:
        - Предварительная загрузка данных через load_pdb()
        - Наличие альфа атомов в PDB.

        :return:
        Результат визуализируется на интерфейсе.
        '''
        # Парсинг PDB
        points = self.parse_pdb_to_points()

        # Очистка предыдущего графика
        self.fig.clf()

        # Создание 3D-осей
        ax = self.fig.add_subplot(111, projection='3d')

        # Визуализация цепочки CA-атомов
        ax.plot(points[:, 0], points[:, 1], points[:, 2],
                'b-', linewidth=2, label='Backbone')

        # Настройка графика
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.legend()

        # Обновление холста
        self.canvas.draw()

    def parse_pdb_to_points(self):
        """Извлекает координаты CA-атомов из PDB (игнорирует другие, в т.ч HETATM)
        На вход идёт файл по-сути
        Освуществляет парсинг следующим образом:
        1) Использует регулярное вырадение для посика строк с описание СА-атомов (регулярное выражение создаёт некий «паттерн» начала строки, которому соотвествуют строки с информацией о CA-атомах)
        2) Использует фиксированные позиции строки PDB-файла, всвязи с фиксированностью позиций координат, для их извлиечения:
        X — 31-38;
        Y — 39-46;
        Z — 47-57;
        (точность координат соответсвтует спецификации PDB — три знака после запятой)
        3) Конвертирует строки во float и формирует NumPy массив.
        :returns:
        Массив нампай координат СА-атомов формы (N, 3), где N — количество СА-атомов.
        """
        import re
        ca_pattern = re.compile(r"^ATOM\s+\d+\s+CA\s+")
        points = []

        for line in self.pdb_data.split('\n'):
            if ca_pattern.match(line):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                points.append([x, y, z])

        return np.array(points)



if __name__ == "__main__":
    '''
    Точка входа приложения. 
    Создёт приложение, соотвествующее class ProteinViewerApp
    Назначает root родителем для всех виджетов и кнопок.
    Запускает главный цикл обработки событий
    Запуск бесконечного цикла (mainloop()).
    '''
    root = tk.Tk()
    app = ProteinViewerMatplotlib(root)
    root.mainloop()