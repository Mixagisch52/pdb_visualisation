import tkinter as tk
from tkinter import filedialog
import vtkplotlib as vpl

import numpy as np


class ProteinViewerVTK:
    def __init__(self, master):
        self.master = master
        self.master.title("VTK Viewer")
        self.master.geometry("800x600")

        self.setup_ui()
        self.pdb_data = None

    def setup_ui(self):
        # Кнопки
        self.load_btn = tk.Button(self.master, text="Load PDB", command=self.load_pdb)
        self.load_btn.pack(pady=10)

        self.view_btn = tk.Button(self.master, text="View in VTK", command=self.view_vtk, state=tk.DISABLED)
        self.view_btn.pack(pady=10)

        # Контейнер для VTK-рендерера (будет создан позже)
        self.vtk_frame = tk.Frame(self.master, width=700, height=500)
        self.vtk_frame.pack(fill=tk.BOTH, expand=True)

    def load_pdb(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDB Files", "*.pdb*  ")])
        if not filepath:
            return

        with open(filepath, 'r') as f:
            self.pdb_data = f.read()

        self.view_btn.config(state=tk.NORMAL)

    def view_vtk(self):
        # Парсинг PDB и подготовка данных (упрощённо)
        # Здесь нужно преобразовать PDB в массив точек/линий
        points = self.parse_pdb_to_points()  # Ваша реализация парсинга

        # Создаём 3D-модель
        vpl.figure()
        vpl.plot(points[:, 0], points[:, 1], points[:, 2], line_width=3)

        # Встраиваем VTK-рендерер в Tkinter
        vpl.show(block=False)
        vpl.embed_tkinter(self.vtk_frame)

    def parse_pdb_to_points(self):
        """Пример: извлечение CA-атомов из PDB"""
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
    app = ProteinViewerVTK(root)
    root.mainloop()