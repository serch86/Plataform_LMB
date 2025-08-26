import os
import json
import sys
import logging

from tools import Tools  # Importa la clase desde tools.py
from backend.services.python_scripts.reports import main as reports_main  # Integración de reportes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

def extract_and_preview(filepath: str) -> dict:
    tools = Tools()
    return tools.procesar_archivo(filepath)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_path = sys.argv[1]
        ext = input_path.lower()

        if ext.endswith(('.xlsx', '.xls', '.csv', '.pdf')):
            try:
                # 1) Procesamiento inicial
                resultado = extract_and_preview(input_path)
                print(json.dumps(resultado, indent=4, ensure_ascii=False))

                # 2) Construcción de filtros a partir de coincidencias Trackman
                try:
                    base = os.path.basename(input_path)
                    datos = resultado.get(base, {}).get("datos_extraidos", {})
                    coincidencias = datos.get("coincidencias_trackman", []) or []

                    nombres_filtrados = sorted({
                        c.get("nombre_trackman")
                        for c in coincidencias
                        if c.get("coincidencia") and c.get("nombre_trackman")
                    })

                    if nombres_filtrados:
                        logger.info(f"Generando reportes para {len(nombres_filtrados)} coincidencias.")
                        # 3) Ejecución de reportes Batter y Pitcher
                        reports_main(
                            batter_filter=nombres_filtrados,
                            pitcher_filter=nombres_filtrados,
                        )
                    else:
                        logger.info("Sin coincidencias válidas. Se omite generación de reportes.")
                except Exception as e:
                    logger.error(f"Error al generar reportes: {e}")

            except Exception as e:
                logger.error(f"Error procesando archivo {input_path}: {e}")
                sys.exit(1)
        else:
            logger.error("Solo se permiten archivos .xlsx, .xls, .csv o .pdf en esta ejecución.")
            sys.exit(1)
    else:
        logger.error("No se proporcionó la ruta del archivo.")
        sys.exit(1)
