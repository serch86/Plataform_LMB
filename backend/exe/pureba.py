import os
import sys
import pdfplumber
import pandas as pd
import numpy as np

def extraer_tablas_pdf_sin_normalizar(pdf_paths, output_dir="debug_tablas_pdf"):
    """
    Extrae tablas crudas de PDFs y las guarda como CSV para diagnóstico visual.
    No aplica ninguna transformación ni limpieza.
    """
    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    os.makedirs(output_dir, exist_ok=True)

    for path in pdf_paths:
        if not os.path.isfile(path):
            print(f"Archivo no encontrado: {path}")
            continue
        try:
            with pdfplumber.open(path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    tables = page.extract_tables({"horizontal_strategy": "text", "vertical_strategy": "text"}) or []
                    if not tables:
                        tables = page.extract_tables() or []

                    for i, table in enumerate(tables):
                        if not table or len(table) < 2:
                            continue

                        header = table[0]
                        rows = table[1:]
                        max_len = max(len(header), *(len(r) for r in rows))
                        header = list(header) + [f"col_{j}" for j in range(len(header), max_len)]
                        norm_rows = [list(r) + [np.nan] * (max_len - len(r)) for r in rows]

                        df = pd.DataFrame(norm_rows, columns=header)

                        base = os.path.splitext(os.path.basename(path))[0]
                        filename = f"{base}_p{page_num}_t{i}.csv"
                        full_path = os.path.join(output_dir, filename)
                        df.to_csv(full_path, index=False)

                        print(f"\nGuardado: {filename}")
                        print("Columnas detectadas:", df.columns.tolist())
        except Exception as e:
            print(f"Error procesando {path}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python prueba.py archivo.pdf")
        sys.exit(1)

    ruta_pdf = sys.argv[1]
    extraer_tablas_pdf_sin_normalizar(ruta_pdf)
