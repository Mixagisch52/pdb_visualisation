import tkinter as tk
from tkinter import filedialog, messagebox
import os
import sys
from pathlib import Path
import webbrowser
import base64


class ProteinViewerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Advanced Protein Viewer")
        self.master.geometry("500x300")

        self.output_dir = Path("protein_views")
        self.output_dir.mkdir(exist_ok=True)
        self.html_file = self.output_dir / "protein_viewer.html"

        self.setup_ui()
        self.pdb_data = None

    def setup_ui(self):
        tk.Label(
            self.master,
            text="Protein Structure Viewer",
            font=("Arial", 14, "bold"),
            pady=10
        ).pack()

        self.load_btn = tk.Button(
            self.master,
            text="1. Load PDB File",
            command=self.load_pdb,
            bg="#e3f2fd",
            width=25
        )
        self.load_btn.pack(pady=5)

        self.show_btn = tk.Button(
            self.master,
            text="2. View Structure",
            command=self.open_in_browser,
            bg="#ffebee",
            width=25,
            state=tk.DISABLED
        )
        self.show_btn.pack(pady=5)

        self.status = tk.Label(self.master, text="Waiting for PDB file...", fg="gray")
        self.status.pack(pady=10)

    def load_pdb(self):
        filepath = filedialog.askopenfilename(
            title="Select PDB File",
            filetypes=[("PDB Files", "*.pdb*"), ("All Files", "*.*")]
        )

        if not filepath:
            return

        try:
            with open(filepath, 'rb') as f:
                self.pdb_data = f.read().decode('utf-8', errors='replace')

            if not any(tag in self.pdb_data for tag in ["ATOM", "HETATM", "HEADER"]):
                raise ValueError("Invalid PDB file format")

            self.save_html()
            self.show_btn.config(state=tk.NORMAL, bg="#c8e6c9")
            self.status.config(text=f"Loaded: {os.path.basename(filepath)}", fg="green")

        except Exception as e:
            self.status.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")

    def save_html(self):
        pdb_encoded = base64.b64encode(self.pdb_data.encode('utf-8')).decode('utf-8')

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Protein Structure Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/PDBLoader.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <style>
        body {{
            margin: 0;
            overflow: hidden;
            font-family: Arial, sans-serif;
            background-color: #f5f5f5;
        }}
        #viewer {{
            width: 100vw;
            height: 100vh;
        }}
        #loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255,255,255,0.9);
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            z-index: 100;
        }}
        #controls {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }}
        button {{
            margin: 5px;
            padding: 5px 10px;
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 3px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div id="viewer"></div>
    <div id="loading">Loading protein structure...</div>
    <div id="controls">
        <button id="toggleStyle">Toggle Style</button>
        <button id="resetView">Reset View</button>
    </div>

    <script>
        // Декодируем PDB данные
        const pdbData = atob("{pdb_encoded}");

        // Основные переменные
        let scene, camera, renderer, controls;
        let proteinGroup, atoms, bonds;
        let currentStyle = 'cartoon';

        // Инициализация
        function init() {{
            const container = document.getElementById('viewer');
            const loading = document.getElementById('loading');

            // Сцена
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);

            // Камера
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 100;

            // Рендерер
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.setSize(window.innerWidth, window.innerHeight);
            container.appendChild(renderer.domElement);

            // Контролы
            controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.25;

            // Освещение
            const light1 = new THREE.DirectionalLight(0xffffff, 1);
            light1.position.set(1, 1, 1);
            scene.add(light1);

            const light2 = new THREE.DirectionalLight(0xffffff, 0.5);
            light2.position.set(-1, -1, 1);
            scene.add(light2);

            scene.add(new THREE.AmbientLight(0x404040));

            // Группа для белка
            proteinGroup = new THREE.Group();
            scene.add(proteinGroup);

            // Загрузка структуры
            loadStructure();

            // Обработчики
            window.addEventListener('resize', onWindowResize);
            document.getElementById('toggleStyle').addEventListener('click', toggleStyle);
            document.getElementById('resetView').addEventListener('click', resetView);

            // Анимация
            animate();
        }}

        // Загрузка структуры белка
        function loadStructure() {{
            const loader = new THREE.PDBLoader();
            const result = loader.parse(pdbData);

            // Создаем атомы и связи
            createAtoms(result);
            createBonds(result);

            // Центрируем камеру
            centerView();

            // Скрываем загрузчик
            document.getElementById('loading').style.display = 'none';
        }}

        // Создание атомов
        function createAtoms(result) {{
            const geometryAtoms = result.geometryAtoms;
            const json = result.json;

            const positions = geometryAtoms.attributes.position;
            const colors = geometryAtoms.attributes.color;

            // Создаем сферы для атомов
            for (let i = 0; i < positions.count; i++) {{
                const sphereGeometry = new THREE.SphereGeometry(0.4, 16, 16);
                const sphereMaterial = new THREE.MeshPhongMaterial({{
                    color: new THREE.Color(
                        colors.getX(i),
                        colors.getY(i),
                        colors.getZ(i)
                    ),
                    shininess: 30,
                    specular: 0x111111
                }});

                const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
                sphere.position.set(
                    positions.getX(i),
                    positions.getY(i),
                    positions.getZ(i)
                );

                proteinGroup.add(sphere);
            }}
        }}

        // Создание связей
        function createBonds(result) {{
            const geometryBonds = result.geometryBonds;

            // Материал для связей
            const bondMaterial = new THREE.LineBasicMaterial({{
                color: 0x333333,
                linewidth: 1,
                transparent: true,
                opacity: 0.7
            }});

            // Создаем линии связей
            const bonds = new THREE.LineSegments(geometryBonds, bondMaterial);
            proteinGroup.add(bonds);
        }}

        // Центрирование вида
        function centerView() {{
            const box = new THREE.Box3().setFromObject(proteinGroup);
            const center = box.getCenter(new THREE.Vector3());
            const size = box.getSize(new THREE.Vector3()).length();

            camera.position.copy(center);
            camera.position.z += size * 1.5;
            controls.target.copy(center);
            controls.update();
        }}

        // Переключение стиля отображения
        function toggleStyle() {{
            currentStyle = currentStyle === 'cartoon' ? 'ballstick' : 'cartoon';
            // Здесь можно добавить логику переключения стилей
        }}

        // Сброс вида
        function resetView() {{
            centerView();
        }}

        // Обработка изменения размера
        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        // Анимация
        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        }}

        // Запуск приложения
        window.onload = init;
    </script>
</body>
</html>"""

        try:
            with open(self.html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            self.status.config(text=f"Save error: {str(e)}", fg="red")
            messagebox.showerror("Error", f"Failed to save HTML:\n{str(e)}")

    def open_in_browser(self):
        if not self.html_file.exists():
            messagebox.showerror("Error", "HTML file not found!")
            return

        try:
            abs_path = os.path.abspath(self.html_file)

            if sys.platform == "win32":
                chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
                if os.path.exists(chrome_path):
                    os.system(f'"{chrome_path}" "{abs_path}"')
                else:
                    os.startfile(abs_path)
            else:
                webbrowser.open(f"file://{abs_path}")

        except Exception as e:
            self.status.config(text=f"Error: {str(e)}", fg="red")
            messagebox.showerror("Error", f"Failed to open in browser:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProteinViewerApp(root)
    root.eval('tk::PlaceWindow . center')
    root.mainloop()