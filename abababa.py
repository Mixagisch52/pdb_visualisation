import tkinter as tk
from tkinter import filedialog
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from pyopengltk import OpenGLFrame
import numpy as np


class ProteinViewerOpenGL(OpenGLFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.master = master
        self.master.title("Protein Viewer (OpenGL)")
        self.master.geometry("800x600")

        self.pdb_data = None
        self.points = []
        self.setup_ui()

    def setup_ui(self):
        # Кнопки поверх OpenGL-холста
        self.load_btn = tk.Button(self.master, text="Load PDB", command=self.load_pdb)
        self.load_btn.pack(pady=10)

        self.view_btn = tk.Button(self.master, text="View 3D", command=self.view_3d, state=tk.DISABLED)
        self.view_btn.pack(pady=10)

    def load_pdb(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDB Files", "*.pdb*")])
        if not filepath:
            return

        with open(filepath, 'r') as f:
            self.pdb_data = f.read()

        self.points = self.parse_pdb_to_points()
        self.view_btn.config(state=tk.NORMAL)

    def initgl(self):
        """Инициализация OpenGL"""
        glClearColor(0.1, 0.1, 0.1, 1.0)
        glEnable(GL_DEPTH_TEST)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        glTranslatef(0.0, 0.0, -5.0)

    def redraw(self):
        """Отрисовка кадра"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Рисуем цепочку атомов
        glBegin(GL_LINE_STRIP)
        glColor3f(0, 0, 1)  # Синий цвет
        for point in self.points:
            glVertex3f(*point)
        glEnd()

        # Рисуем атомы как точки
        glPointSize(5)
        glBegin(GL_POINTS)
        glColor3f(1, 0, 0)  # Красный цвет
        for point in self.points:
            glVertex3f(*point)
        glEnd()

    def view_3d(self):
        """Запуск перерисовки"""
        self.redraw()

    def parse_pdb_to_points(self):
        """Извлекает координаты CA-атомов и нормализует их"""
        import re
        ca_pattern = re.compile(r"^ATOM\s+\d+\s+CA\s+")
        points = []

        for line in self.pdb_data.split('\n'):
            if ca_pattern.match(line):
                x = float(line[30:38])
                y = float(line[38:46])
                z = float(line[46:54])
                points.append([x / 10, y / 10, z / 10])  # Масштабирование

        return np.array(points)


if __name__ == "__main__":
    root = tk.Tk()
    app = ProteinViewerOpenGL(root)
    app.pack(fill=tk.BOTH, expand=True)
    root.mainloop()