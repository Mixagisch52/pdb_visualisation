import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np


class ProteinViewerMatplotlib:
    def __init__(self, master):
        self.master = master
        self.master.title("Protein Viewer (Matplotlib)")
        self.master.geometry("800x600")

        self.setup_ui()
        self.pdb_data = None

    def setup_ui(self):
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
        filepath = filedialog.askopenfilename(filetypes=[("PDB Files", "*.pdb*")])
        if not filepath:
            return

        with open(filepath, 'r') as f:
            self.pdb_data = f.read()

        self.view_btn.config(state=tk.NORMAL)

    def view_3d(self):
        # Парсинг PDB (упрощённый пример)
        points = self.parse_pdb_to_points()

        # Очистка предыдущего графика
        self.fig.clf()

        # Создание 3D-оси
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
        """Извлекает координаты CA-атомов из PDB"""
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
    root = tk.Tk()
    app = ProteinViewerMatplotlib(root)
    root.mainloop()