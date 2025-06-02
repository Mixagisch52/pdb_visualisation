import tkinter as tk
from tkinter import filedialog, ttk
import py3Dmol
import os
import tempfile
import webview
from threading import Thread


class ProteinViewer:
    def __init__(self, master):
        self.master = master
        self.master.title("3D Protein Viewer")
        self.master.geometry("900x700")

        self.pdb_data = None
        self.webview_window = None
        self.setup_ui()

    def setup_ui(self):
        # Control Panel
        control_frame = tk.Frame(self.master)
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Buttons
        self.load_btn = tk.Button(control_frame, text="Load PDB", command=self.load_pdb)
        self.load_btn.pack(side=tk.LEFT, padx=5)

        self.view_btn = tk.Button(
            control_frame,
            text="View Structure",
            command=self.launch_viewer,
            state=tk.DISABLED
        )
        self.view_btn.pack(side=tk.LEFT, padx=5)

        # Style selector
        self.style_var = tk.StringVar(value="cartoon")
        styles = ["cartoon", "stick", "sphere", "line"]
        style_menu = ttk.Combobox(
            control_frame,
            textvariable=self.style_var,
            values=styles,
            state="readonly"
        )
        style_menu.pack(side=tk.LEFT, padx=5)
        style_menu.bind("<<ComboboxSelected>>", self.update_style)

    def load_pdb(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("PDB Files", "*.pdb*"), ("All Files", "*.*")]
        )
        if not filepath:
            return

        with open(filepath, 'r') as f:
            self.pdb_data = f.read()

        self.view_btn.config(state=tk.NORMAL)
        self.master.title(f"3D Protein Viewer - {os.path.basename(filepath)}")

    def launch_viewer(self):
        if not self.pdb_data:
            return

        # Create HTML content
        html_content = self.create_3dmol_html()

        # Create and start webview in a separate thread
        def start_webview():
            self.webview_window = webview.create_window(
                "3D Protein Viewer",
                html=html_content,
                width=900,
                height=700,
                resizable=True
            )
            webview.start()

        Thread(target=start_webview, daemon=True).start()

    def create_3dmol_html(self):
        viewer = py3Dmol.view(width=800, height=600)
        viewer.addModel(self.pdb_data, 'pdb')
        viewer.setStyle({'cartoon': {'color': 'spectrum'}})
        viewer.zoomTo()

        # Add JavaScript controls
        js_controls = """
        <script>
            function updateStyle(style) {
                if (style === 'cartoon') {
                    viewer.setStyle({cartoon: {color: 'spectrum'}});
                } else if (style === 'stick') {
                    viewer.setStyle({stick: {}});
                } else if (style === 'sphere') {
                    viewer.setStyle({sphere: {radius: 0.5}});
                } else if (style === 'line') {
                    viewer.setStyle({line: {}});
                }
                viewer.zoomTo();
                viewer.render();
            }
        </script>
        """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>3D Protein Viewer</title>
            <style>body {{ margin: 0; overflow: hidden; }}</style>
        </head>
        <body>
            {viewer._make_html()}
            {js_controls}
        </body>
        </html>
        """

    def update_style(self, event=None):
        if not self.webview_window:
            return

        style = self.style_var.get()
        js_code = f"updateStyle('{style}');"

        try:
            self.webview_window.evaluate_js(js_code)
        except Exception as e:
            print(f"Style update error: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProteinViewer(root)
    root.mainloop()