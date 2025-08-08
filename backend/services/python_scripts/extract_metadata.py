import os
import json
import sys
import logging
from tools import Tools  # Importa la clase desde tools.py

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
                resultado = extract_and_preview(input_path)
                print(json.dumps(resultado, indent=4, ensure_ascii=False))
            except Exception as e:
                logger.error(f"Error procesando archivo {input_path}: {e}")
                sys.exit(1)
        else:
            logger.error("Solo se permiten archivos .xlsx, .xls, .csv o .pdf en esta ejecución.")
            sys.exit(1)
    else:
        logger.error("No se proporcionó la ruta del archivo.")
        sys.exit(1)

