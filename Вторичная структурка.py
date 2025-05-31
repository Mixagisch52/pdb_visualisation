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
        self.master.title("Вторичная структура")
        self.master.geometry("500x300")

        self.output_dir = Path("protein_views")
        self.output_dir.mkdir(exist_ok=True)
        self.html_file = self.output_dir / "secondary_structure.html"

        self.setup_ui()
        self.pdb_data = None

    def setup_ui(self):
        tk.Label(
            self.master,
            text="Secondary Structure Viewer",
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
    <title>Protein Secondary Structure Viewer</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
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
        #info {{
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(255,255,255,0.9);
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 0 5px rgba(0,0,0,0.1);
        }}
    </style>
</head>
<body>
    <div id="viewer"></div>
    <div id="loading">Loading secondary structure...</div>
    <div id="info">
        <div>α-helices: <span id="helices-count">0</span></div>
        <div>β-sheets: <span id="sheets-count">0</span></div>
    </div>

    <script>
        // Декодируем PDB данные
        const pdbData = `{self.pdb_data}`;

        // Основные переменные
        let scene, camera, renderer, controls;
        let proteinGroup = new THREE.Group();
        let helices = [], sheets = [], coils = [];

        // Цвета для вторичной структуры
        const COLORS = {{
            HELIX: 0xFF0000,    // Красный для α-спиралей
            SHEET: 0x0000FF,    // Синий для β-листов
            COIL: 0x00AA00      // Зеленый для петель
        }};

        // Инициализация
        function init() {{
            const container = document.getElementById('viewer');

            // Сцена
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf5f5f5);
            scene.add(proteinGroup);

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

            // Парсим PDB и строим структуру
            parsePDB();
            buildSecondaryStructure();

            // Центрируем камеру
            centerView();

            // Скрываем загрузчик
            document.getElementById('loading').style.display = 'none';

            // Обновляем информацию
            document.getElementById('helices-count').textContent = helices.length;
            document.getElementById('sheets-count').textContent = sheets.length;

            // Обработчики
            window.addEventListener('resize', onWindowResize);

            // Анимация
            animate();
        }}

        // Парсинг PDB файла
        function parsePDB() {{
            const lines = pdbData.split('\\n');
            let currentChain = '';
            let currentResidue = null;
            let residues = [];

            // Собираем информацию о остатках
            for (const line of lines) {{
                if (line.startsWith('HELIX ')) {{
                    // Парсим информацию о спиралях
                    const helixInfo = parseHelix(line);
                    helices.push(helixInfo);
                }}
                else if (line.startsWith('SHEET ')) {{
                    // Парсим информацию о листах
                    const sheetInfo = parseSheet(line);
                    sheets.push(sheetInfo);
                }}
                else if (line.startsWith('ATOM ')) {{
                    // Парсим атомы
                    const atom = parseAtom(line);

                    if (currentResidue === null || 
                        atom.resSeq !== currentResidue.resSeq || 
                        atom.chainID !== currentResidue.chainID) {{

                        if (currentResidue !== null) {{
                            residues.push(currentResidue);
                        }}

                        currentResidue = {{
                            resName: atom.resName,
                            chainID: atom.chainID,
                            resSeq: atom.resSeq,
                            atoms: []
                        }};
                    }}

                    currentResidue.atoms.push(atom);
                }}
            }}

            // Добавляем последний остаток
            if (currentResidue !== null) {{
                residues.push(currentResidue);
            }}

            // Классифицируем остатки по вторичной структуре
            classifyResidues(residues);
        }}

        // Парсинг информации о спирали
        function parseHelix(line) {{
            return {{
                startChain: line[19],
                startResSeq: parseInt(line.substr(21, 4)),
                endChain: line[31],
                endResSeq: parseInt(line.substr(33, 4)),
                type: parseInt(line.substr(38, 2))
            }};
        }}

        // Парсинг информации о листе
        function parseSheet(line) {{
            return {{
                startChain: line[21],
                startResSeq: parseInt(line.substr(22, 4)),
                endChain: line[32],
                endResSeq: parseInt(line.substr(33, 4)),
                sense: parseInt(line.substr(38, 2))
            }};
        }}

        // Парсинг атома
        function parseAtom(line) {{
            return {{
                serial: parseInt(line.substr(6, 5)),
                name: line.substr(12, 4).trim(),
                resName: line.substr(17, 3).trim(),
                chainID: line[21],
                resSeq: parseInt(line.substr(22, 4)),
                x: parseFloat(line.substr(30, 8)),
                y: parseFloat(line.substr(38, 8)),
                z: parseFloat(line.substr(46, 8))
            }};
        }}

        // Классификация остатков по вторичной структуре
        function classifyResidues(residues) {{
            // Помечаем остатки в спиралях
            for (const helix of helices) {{
                for (let i = helix.startResSeq; i <= helix.endResSeq; i++) {{
                    const residue = findResidue(residues, helix.startChain, i);
                    if (residue) residue.ssType = 'HELIX';
                }}
            }}

            // Помечаем остатки в листах
            for (const sheet of sheets) {{
                for (let i = sheet.startResSeq; i <= sheet.endResSeq; i++) {{
                    const residue = findResidue(residues, sheet.startChain, i);
                    if (residue) residue.ssType = 'SHEET';
                }}
            }}

            // Остальные - петли
            for (const residue of residues) {{
                if (!residue.ssType) residue.ssType = 'COIL';
            }}
        }}

        // Поиск остатка по номеру и цепи
        function findResidue(residues, chainID, resSeq) {{
            return residues.find(r => r.chainID === chainID && r.resSeq === resSeq);
        }}

        // Построение вторичной структуры
        function buildSecondaryStructure() {{
            const lines = pdbData.split('\\n');
            let caAtoms = [];

            // Собираем α-углероды
            for (const line of lines) {{
                if (line.startsWith('ATOM ') && line.substr(12, 4).trim() === 'CA') {{
                    const x = parseFloat(line.substr(30, 8));
                    const y = parseFloat(line.substr(38, 8));
                    const z = parseFloat(line.substr(46, 8));
                    const resSeq = parseInt(line.substr(22, 4));
                    const chainID = line[21];

                    // Находим тип вторичной структуры для этого остатка
                    let ssType = 'COIL';
                    for (const helix of helices) {{
                        if (chainID === helix.startChain && resSeq >= helix.startResSeq && resSeq <= helix.endResSeq) {{
                            ssType = 'HELIX';
                            break;
                        }}
                    }}
                    if (ssType === 'COIL') {{
                        for (const sheet of sheets) {{
                            if (chainID === sheet.startChain && resSeq >= sheet.startResSeq && resSeq <= sheet.endResSeq) {{
                                ssType = 'SHEET';
                                break;
                            }}
                        }}
                    }}

                    caAtoms.push({{ x, y, z, ssType }});
                }}
            }}

            // Строим каркас
            buildBackbone(caAtoms);

            // Добавляем спирали и листы
            buildHelicesAndSheets(caAtoms);
        }}

        // Построение остова
        function buildBackbone(caAtoms) {{
            const backboneGeometry = new THREE.BufferGeometry();
            const positions = [];
            const colors = [];

            for (let i = 0; i < caAtoms.length - 1; i++) {{
                const curr = caAtoms[i];
                const next = caAtoms[i + 1];

                // Позиции
                positions.push(curr.x, curr.y, curr.z);
                positions.push(next.x, next.y, next.z);

                // Цвета
                const color = new THREE.Color(COLORS[curr.ssType]);
                colors.push(color.r, color.g, color.b);
                colors.push(color.r, color.g, color.b);
            }}

            backboneGeometry.setAttribute('position', 
                new THREE.Float32BufferAttribute(positions, 3));
            backboneGeometry.setAttribute('color', 
                new THREE.Float32BufferAttribute(colors, 3));

            const backboneMaterial = new THREE.LineBasicMaterial({{
                vertexColors: true,
                linewidth: 3
            }});

            const backbone = new THREE.LineSegments(backboneGeometry, backboneMaterial);
            proteinGroup.add(backbone);
        }}

        // Построение спиралей и листов
        function buildHelicesAndSheets(caAtoms) {{
            // Группируем атомы по типам вторичной структуры
            const grouped = {{ HELIX: [], SHEET: [], COIL: [] }};
            for (const atom of caAtoms) {{
                grouped[atom.ssType].push(atom);
            }}

            // Строим спирали
            buildSSElements(grouped.HELIX, 0.8, COLORS.HELIX);

            // Строим листы
            buildSSElements(grouped.SHEET, 0.5, COLORS.SHEET);
        }}

        // Построение элементов вторичной структуры
        function buildSSElements(atoms, width, color) {{
            if (atoms.length < 2) return;

            const points = atoms.map(atom => new THREE.Vector3(atom.x, atom.y, atom.z));
            const path = new THREE.CatmullRomCurve3(points);

            const tubeGeometry = new THREE.TubeGeometry(
                path,
                points.length * 2,
                width,
                8,
                false
            );

            const material = new THREE.MeshPhongMaterial({{
                color: color,
                side: THREE.DoubleSide,
                transparent: true,
                opacity: 0.7
            }});

            const mesh = new THREE.Mesh(tubeGeometry, material);
            proteinGroup.add(mesh);
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
