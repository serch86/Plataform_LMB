# gui_main.py
import os
os.environ["MPLBACKEND"] = "Agg"
import matplotlib
matplotlib.use("Agg")

import platform
import json
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, TclError

import sys
from tools import Tools, _rol_desde_title
import reports
from google.cloud import bigquery

# borrar log
print("DEBUG: Inicio de ejecución de gui_main.py") # borrar log

SERVICE_ACCOUNT_INFO = {  
}
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.is_busy = False
        
        # borrar log
        print("DEBUG: Entrando a App.__init__") # borrar log
        
        self.title("Roster Reports")
        self.geometry("980x620")

        # Estado interno de nombres encontrados
        self.batters_matched, self.pitchers_matched = [], []
        self.batters_unmatched, self.pitchers_unmatched = [], []
        self.staff_matched, self.staff_unmatched = [], []
        self.current_file = None

        # Parámetros de configuración
        self.umbral = 90.0
        self.work_dir = None
        self.clean_temp = True

        # Inicialización de credenciales embebidas
        self.creds_ok = False
        # borrar log
        print("DEBUG: Llamando a _install_embedded_credentials") # borrar log
        self._install_embedded_credentials()

        # Construcción de layout gráfico
        # borrar log
        print("DEBUG: Llamando a _build_layout") # borrar log
        self._build_layout()
        # borrar log
        print("DEBUG: Salida de App.__init__") # borrar log

    # Inicializa las credenciales de BigQuery desde un JSON embebido
    def _install_embedded_credentials(self):
        # borrar log
        print("DEBUG: Entrando a _install_embedded_credentials") # borrar log
        try:
            # borrar log
            print("DEBUG: Verificando SERVICE_ACCOUNT_INFO") # borrar log
            if not SERVICE_ACCOUNT_INFO or "private_key" not in SERVICE_ACCOUNT_INFO:
                raise RuntimeError("Faltan datos en SERVICE_ACCOUNT_INFO.")

            tmp_path = os.path.join(tempfile.gettempdir(), "bq_sa_embedded.json")
            # borrar log
            print(f"DEBUG: Creando archivo temporal en {tmp_path}") # borrar log
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(SERVICE_ACCOUNT_INFO, f)
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp_path

            client = bigquery.Client()
            # borrar log
            print("DEBUG: Ejecutando consulta de prueba en BigQuery") # borrar log
            client.query("SELECT 1 AS ok").result()
            self.creds_ok = True
            # borrar log
            print("DEBUG: BigQuery inicializado correctamente") # borrar log
        except Exception as e:
            self.creds_ok = False
            messagebox.showerror("Error de credenciales", f"No fue posible inicializar BigQuery: {e}")
            # borrar log
            print(f"ERROR: Fallo al inicializar BigQuery: {e}") # borrar log
        # borrar log
        print("DEBUG: Salida de _install_embedded_credentials") # borrar log

    # Crea todos los componentes visuales de la ventana principal
    def _build_layout(self):
        # borrar log
        print("DEBUG: Entrando a _build_layout") # borrar log
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Button(top, text="Seleccionar archivo", command=self.on_select_file).pack(side="left")
        self.lbl_file = ttk.Label(top, text="Archivo: ninguno")
        self.lbl_file.pack(side="left", padx=10)

        lbl_creds = "Credenciales: ok" if self.creds_ok else "Credenciales: error"
        self.lbl_creds = ttk.Label(top, text=lbl_creds)
        self.lbl_creds.pack(side="left", padx=20)

        mid = ttk.Frame(self, padding=10)
        mid.pack(fill="both", expand=True)

        cols = ("nombre", "rol", "score", "estado")
        self.tree = ttk.Treeview(mid, columns=cols, show="headings", height=16)
        for c, w in zip(cols, (360, 180, 80, 140)):
            self.tree.heading(c, text=c.capitalize())
            self.tree.column(c, width=w)
        self.tree.pack(side="left", fill="both", expand=True)

        yscroll = ttk.Scrollbar(mid, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side="left", fill="y")

        right = ttk.Frame(self, padding=10)
        right.pack(fill="x", side="top")

        self.var_pct_b = tk.StringVar(value="% capturados (Bateadores): 0.00%")
        self.var_pct_p = tk.StringVar(value="% capturados (Pitchers): 0.00%")
        ttk.Label(right, textvariable=self.var_pct_b).pack(anchor="w")
        ttk.Label(right, textvariable=self.var_pct_p).pack(anchor="w")

        bottom = ttk.Frame(self, padding=10)
        bottom.pack(fill="x", side="bottom")

        self.btn_gen_b = ttk.Button(bottom, text="Generar reportes Bateadores",
                                     command=self.on_generate_b, state="disabled")
        self.btn_gen_p = ttk.Button(bottom, text="Generar reportes Pitchers",
                                     command=self.on_generate_p, state="disabled")
        self.btn_gen_b.pack(side="left")
        self.btn_gen_p.pack(side="left", padx=10)

        self.txt_log = tk.Text(self, height=8, state='disabled')
        self.txt_log.pack(fill="both", expand=False, padx=10, pady=(0, 10))
        self._log("Listo.")

        # Conectar logs de reportes al cuadro de log de la GUI
        try:
            reports.set_gui_logger(self._log)
        except Exception as e:
            self._log(f"No se pudo conectar el logger de reportes: {e}")

        # borrar log
        print("DEBUG: Salida de _build_layout") # borrar log

    # Procesa los archivos seleccionados y detecta nombres y roles
    def on_select_file(self):
        # borrar log
        print("DEBUG: Entrando a on_select_file") # borrar log
        paths = filedialog.askopenfilenames(
            title="Seleccionar Archivos de Roster",
            filetypes=[
                ("Todos soportados", "*.pdf *.xls *.xlsx *.csv"),
                ("PDF", "*.pdf"),
                ("Excel", "*.xls *.xlsx"),
                ("CSV", "*.csv")
            ]
        )
        if not paths:
            # borrar log
            print("DEBUG: No se seleccionaron archivos") # borrar log
            return

        self.current_file = list(paths)
        self.lbl_file.config(text=f"Archivos seleccionados: {len(self.current_file)}")
        self._clear_table()
        self._set_busy(True)
        self._log("Iniciando procesamiento de archivos...")

        try:
            tools = Tools()
            all_batters_matched, all_pitchers_matched = [], []
            all_batters_unmatched, all_pitchers_unmatched = [], []
            all_roles_by_name = {}

            # borrar log
            print(f"DEBUG: Procesando {len(self.current_file)} archivos") # borrar log
            for path in self.current_file:
                # borrar log
                print(f"DEBUG: Procesando archivo: {os.path.basename(path)}") # borrar log
                try:
                    res = tools.procesar_archivo(
                        path,
                        umbral=getattr(self, "umbral", 90.0)
                    ) or {}
                    # borrar log
                    print(f"DEBUG: Resultado de procesar_archivo para {os.path.basename(path)}: {res}") # borrar log

                    for _, payload in res.items():
                        if not isinstance(payload, dict):
                            self._log(f"Error en el payload de {os.path.basename(path)}: tipo inválido ({type(payload).__name__})")
                            # borrar log
                            print(f"ERROR: Payload inválido para {os.path.basename(path)}") # borrar log
                            continue
                        if "error" in payload:
                            self._log(f"Error en el payload de {os.path.basename(path)}: {payload.get('error') or 'desconocido'}")
                            # borrar log
                            print(f"ERROR: Error en payload de {os.path.basename(path)}: {payload.get('error')}") # borrar log
                            continue

                        tables = payload.get("tables", []) or []
                        coincidencias = (payload.get("datos_extraidos", {}) or {}).get("coincidencias_trackman", []) or []
                        # borrar log
                        print(f"DEBUG: Encontradas {len(coincidencias)} coincidencias en {os.path.basename(path)}") # borrar log

                        nombre_a_rol = payload.get("roles_by_name", {}) or {}
                        if not nombre_a_rol:
                            tmp = {}
                            for row in tables:
                                nombre = str(row.get("raw_name", "")).strip()
                                title = str(row.get("title", "")).strip().lower()
                                rol = _rol_desde_title(title)
                                if nombre:
                                    tmp[nombre] = rol
                            nombre_a_rol = tmp
                        all_roles_by_name.update(nombre_a_rol)

                        for c in coincidencias:
                            nombre_roster = str(c.get("nombre_roster", "")).strip()
                            if not nombre_roster:
                                # borrar log
                                print("DEBUG: Nombre de roster vacío, omitiendo") # borrar log
                                continue

                            rol = all_roles_by_name.get(nombre_roster, "Unknown")
                            rol_l = str(rol or "").lower()
                            if rol_l.startswith("staff"):
                                continue

                            if c.get("coincidencia"):
                                item = {
                                    "extraido": nombre_roster,
                                    "canonico": c.get("nombre_trackman"),
                                    "score": float(c.get("similitud", 0.0)),
                                    "rol": rol
                                }
                                # borrar log
                                print(f"DEBUG: Coincidencia encontrada: {nombre_roster} -> {c.get('nombre_trackman')} con score {item['score']}") # borrar log
                                if rol_l.startswith("pitcher"):
                                    all_pitchers_matched.append(item)
                                else:
                                    all_batters_matched.append(item)
                            else:
                                # borrar log
                                print(f"DEBUG: Sin coincidencia para: {nombre_roster}") # borrar log
                                if rol_l.startswith("pitcher"):
                                    all_pitchers_unmatched.append(nombre_roster)
                                else:
                                    all_batters_unmatched.append(nombre_roster)

                    self._log(f"Procesado: {os.path.basename(path)}")

                except Exception as e:
                    self._log(f"Error en Tools con {os.path.basename(path)}: {e}")
                    # borrar log
                    print(f"ERROR: Fallo de Tools con {os.path.basename(path)}: {e}") # borrar log

            # Guardar resultados
            self.batters_matched = all_batters_matched
            self.pitchers_matched = all_pitchers_matched
            self.batters_unmatched = all_batters_unmatched
            self.pitchers_unmatched = all_pitchers_unmatched

            # Mostrar resultados en tabla
            # borrar log
            print("DEBUG: Llenando tabla con resultados matched y unmatched") # borrar log
            for m in self.batters_matched:
                self.tree.insert("", "end", values=(
                    m.get("canonico") or m.get("extraido") or "",
                    m.get("rol", "Batter"),
                    f"{m.get('score', 0):.2f}",
                    "Matched"
                ))
            for m in self.pitchers_matched:
                self.tree.insert("", "end", values=(
                    m.get("canonico") or m.get("extraido") or "",
                    m.get("rol", "Pitcher"),
                    f"{m.get('score', 0):.2f}",
                    "Matched"
                ))
            for n in self.batters_unmatched:
                self.tree.insert("", "end", values=(n, all_roles_by_name.get(n, "Unknown"), "-", "Unmatched"))
            for n in self.pitchers_unmatched:
                self.tree.insert("", "end", values=(n, all_roles_by_name.get(n, "Unknown"), "-", "Unmatched"))
            # borrar log
            print("DEBUG: Tabla llenada") # borrar log

            # Cálculo de porcentajes
            mb = len(self.batters_matched)
            mp = len(self.pitchers_matched)
            tb = mb + len(self.batters_unmatched)
            tp = mp + len(self.pitchers_unmatched)

            pct_b = (mb / tb * 100) if tb > 0 else 0.0
            pct_p = (mp / tp * 100) if tp > 0 else 0.0
            self.var_pct_b.set(f"% capturados (Bateadores): {pct_b:.2f}%")
            self.var_pct_p.set(f"% capturados (Pitchers): {pct_p:.2f}%")

            # Finaliza
            self._update_buttons()
            self._log(f"Archivos procesados: {len(self.current_file)}")
            self._log(f"Bateadores: {tb} | Matched: {mb} | Unmatched: {len(self.batters_unmatched)}")
            self._log(f"Pitchers: {tp} | Matched: {mp} | Unmatched: {len(self.pitchers_unmatched)}")
            total_coincidencias = mb + mp + len(self.batters_unmatched) + len(self.pitchers_unmatched)
            self._log(f"Total coincidencias evaluadas: {total_coincidencias}")
            # borrar log
            print("DEBUG: Finalizó el procesamiento de archivos") # borrar log

        except Exception as e:
            messagebox.showerror("Error", f"Error general durante el procesamiento: {e}")
            self._log(f"Error general: {e}")
            # borrar log
            print(f"ERROR: Error general en on_select_file: {e}") # borrar log
        finally:
            self._set_busy(False)
            # borrar log
            print("DEBUG: Saliendo de on_select_file") # borrar log

    # Genera reportes PDF de pitchers
    def on_generate_b(self):
        # borrar log
        print("DEBUG: Entrando a on_generate_b") # borrar log
        if not self.creds_ok:
            messagebox.showerror("Faltan credenciales", "Inicializa las credenciales embebidas.")
            # borrar log
            print("ERROR: Credenciales no válidas para generar reportes") # borrar log
            return
        self._set_busy(True)
        try:
            nombres = [x.get("canonico") for x in self.batters_matched if x.get("canonico")]
            if not nombres:
                self._log("No hay bateadores para generar.")
                # borrar log
                print("DEBUG: No hay bateadores matched, regresando") # borrar log
                return
            # borrar log
            print(f"DEBUG: Llamando a run_batter_reports con {len(nombres)} nombres") # borrar log
            res = reports.run_batter_reports(nombres)
            processed = res.get("processed", 0)
            generated = res.get("generated", 0)
            paths = res.get("paths", [])
            self._log(f"Bateadores procesados: {processed} | generados: {generated}")
            if paths:
                self._log(f"Primer archivo: {paths[0]}")
            # borrar log
            print(f"DEBUG: Reportes de bateadores: procesados={processed}, generados={generated}") # borrar log
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Error: {e}")
            # borrar log
            print(f"ERROR: Fallo al generar reportes de bateadores: {e}") # borrar log
        finally:
            self._set_busy(False)
            # borrar log
            print("DEBUG: Saliendo de on_generate_b") # borrar log

    # Genera reportes PDF de pitchers
    def on_generate_p(self):
        # borrar log
        print("DEBUG: Entrando a on_generate_p") # borrar log
        if not self.creds_ok:
            messagebox.showerror("Faltan credenciales", "Inicializa las credenciales embebidas.")
            # borrar log
            print("ERROR: Credenciales no válidas para generar reportes") # borrar log
            return
        self._set_busy(True)
        try:
            nombres = [x.get("canonico") for x in self.pitchers_matched if x.get("canonico")]
            if not nombres:
                self._log("No hay pitchers para generar.")
                # borrar log
                print("DEBUG: No hay pitchers matched, regresando") # borrar log
                return
            # borrar log
            print(f"DEBUG: Llamando a run_pitcher_reports con {len(nombres)} nombres") # borrar log
            res = reports.run_pitcher_reports(nombres)
            processed = res.get("processed", 0)
            generated = res.get("generated", 0)
            paths = res.get("paths", [])
            self._log(f"Pitchers procesados: {processed} | generados: {generated}")
            if paths:
                self._log(f"Primer archivo: {paths[0]}")
            # borrar log
            print(f"DEBUG: Reportes de pitchers: procesados={processed}, generados={generated}") # borrar log
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self._log(f"Error: {e}")
            # borrar log
            print(f"ERROR: Fallo al generar reportes de pitchers: {e}") # borrar log
        finally:
            self._set_busy(False)
            # borrar log
            print("DEBUG: Saliendo de on_generate_p") # borrar log

    # Limpia los datos de la tabla
    def _clear_table(self):
        # borrar log
        print("DEBUG: Entrando a _clear_table") # borrar log
        for i in self.tree.get_children():
            self.tree.delete(i)
        # borrar log
        print("DEBUG: Tabla limpiada") # borrar log

    # Escribe mensajes en el cuadro de log
    def _log(self, msg):
        try:
            if getattr(self, "txt_log", None) and self.txt_log.winfo_exists():
                self.txt_log.config(state='normal')
                self.txt_log.insert('end', msg + '\n')
                self.txt_log.config(state='disabled')
                self.txt_log.see('end')
        except TclError:
            pass
        # borrar log
        print(f"LOG: {msg}") # borrar log

    def _set_busy(self, busy: bool):
        # borrar log
        print(f"DEBUG: Cambiando estado de ocupado a {busy}") # borrar log
        self.is_busy = busy
        
        def _safe_config(w, **kw):
            try:
                if w and hasattr(w, "winfo_exists") and w.winfo_exists():
                    w.config(**kw)
                    return True
            except TclError:
                pass
            except Exception:
                pass
            return False
        
        try:
            cursor_busy = "wait" if platform.system() == "Windows" else "watch"
            cur = cursor_busy if busy else ""
            
            # Cursor en los widgets relevantes (si siguen vivos)
            for w in (
                getattr(self, "root", None),
                self,
                getattr(self, "tree", None),
                getattr(self, "btn_gen_b", None),
                getattr(self, "btn_gen_p", None),
                getattr(self, "txt_log", None),
            ):
                _safe_config(w, cursor=cur)
            
            # update_idletasks solo si la ventana existe
            try:
                root = getattr(self, "root", None)
                if root and hasattr(root, "winfo_exists") and root.winfo_exists():
                    root.update_idletasks()
                elif hasattr(self, "winfo_exists") and self.winfo_exists():
                    self.update_idletasks()
            except TclError:
                pass
            
            if busy:
                _safe_config(getattr(self, "btn_gen_b", None), state="disabled")
                _safe_config(getattr(self, "btn_gen_p", None), state="disabled")
            else:
                try:
                    # Llama a _update_buttons solo si la UI sigue viva
                    root = getattr(self, "root", None)
                    if (not root) or (root and root.winfo_exists()):
                        self._update_buttons()
                except TclError:
                    pass
            
        except Exception as e:
            # Evita romper si el logger también está destruido
            try:
                if hasattr(self, "_log"):
                    self._log(f"Error en _set_busy: {e}")
            except Exception:
                pass
        # borrar log
        print("DEBUG: Saliendo de _set_busy") # borrar log
        
    # Habilita botones solo si hay datos matched
    def _update_buttons(self):
        # borrar log
        print("DEBUG: Entrando a _update_buttons") # borrar log
        if not (self and self.winfo_exists()):
            return
        for btn in [getattr(self, "btn_gen_b", None),
                        getattr(self, "btn_gen_p", None)]:
            if btn and btn.winfo_exists():
                btn.config(state='normal' if not self.is_busy else 'disabled')
        # borrar log
        print("DEBUG: Estado de botones actualizado") # borrar log
    

if __name__ == "__main__":
    App().mainloop()
