# main.py
import os
import sys
import json
import time
import argparse
import logging
from typing import Optional, List, Dict, Any

from tools import Tools
import reports

# --------------------------
# Configuración de logging
# --------------------------
def setup_logging(level: str) -> None:
    numeric = getattr(logging, level.upper(), logging.INFO)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=numeric, format="%(asctime)s %(levelname)s %(message)s")
    else:
        logging.getLogger().setLevel(numeric)

logger = logging.getLogger(__name__)

# --------------------------
# Etapa Tools
# --------------------------
def extract_and_preview(filepath: str, trackman_csv: Optional[str], umbral: float) -> dict:
    tools = Tools()
    return tools.procesar_archivo(filepath, trackman_csv=trackman_csv, umbral=umbral)

# --------------------------
# Etapa Reports
# --------------------------
def run_reports(df: Optional[Any] = None,
                local_file: Optional[str] = None,
                batter_filter: Optional[List[str]] = None,
                pitcher_filter: Optional[List[str]] = None,
                work_dir: Optional[str] = None,
                clean_temp: bool = True) -> dict:
    return reports.main(
        df=df,
        local_file=local_file,
        batter_filter=batter_filter,
        pitcher_filter=pitcher_filter,
        work_dir=work_dir,
        clean_temp=clean_temp
    )

# --------------------------
# Utilidades
# --------------------------
def has_error_in_tools(result: dict) -> bool:
    if not isinstance(result, dict):
        return True
    try:
        _, payload = next(iter(result.items()))
    except StopIteration:
        return True
    return isinstance(payload, dict) and "error" in payload

def single_json_output(tools_result: Optional[dict],
                       reports_result: Optional[dict],
                       artefactos: Optional[dict],
                       run_id: str) -> dict:
    return {
        "run_id": run_id,
        "tools_result": tools_result,
        "reports_result": reports_result,
        "artefactos": artefactos,
    }

def collect_artefacts(reports_result: Optional[dict]) -> Dict[str, List[str]]:
    if not isinstance(reports_result, dict):
        return {"batter": [], "pitcher": []}
    return {
        "batter": reports_result.get("batter", {}).get("paths", []) or [],
        "pitcher": reports_result.get("pitcher", {}).get("paths", []) or [],
    }

# --------------------------
# CLI
# --------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Pipeline de extracción y reportes")
    p.add_argument("input_path", nargs="?", help="Ruta a .xlsx/.xls/.csv/.pdf")
    p.add_argument("--trackman-csv", default=None, help="CSV con columna 'nombre' para Tools")
    p.add_argument("--local-trackman", default=None, help="CSV/Parquet local para Reports (datos de juego)")
    p.add_argument("--umbral", type=float, default=90.0, help="Umbral de similitud (0-100) para Tools")
    p.add_argument("--batter", nargs="*", default=None, help="Lista de bateadores a filtrar en Reports")
    p.add_argument("--pitcher", nargs="*", default=None, help="Lista de pitchers a filtrar en Reports")
    p.add_argument("--work-dir", default=None, help="Directorio base para artefactos (PNG/PDF)")
    p.add_argument("--no-clean-temp", action="store_true", help="No limpiar PNG temporales al final de Reports")
    p.add_argument("--solo-tools", action="store_true", help="Ejecuta solo la etapa Tools")
    p.add_argument("--solo-reports", action="store_true", help="Ejecuta solo la etapa Reports")
    p.add_argument("--output", default=None, help="Archivo donde guardar el JSON final")
    p.add_argument("--log-level", default="INFO", help="Nivel de log: DEBUG|INFO|WARNING|ERROR|CRITICAL")
    return p.parse_args()

# --------------------------
# Main
# --------------------------
def main() -> int:
    args = parse_args()
    setup_logging(args.log_level)

    # Validaciones de entrada
    if not args.solo_reports:
        if not args.input_path:
            logger.error("Ruta de archivo no proporcionada")
            return 1
        ext = args.input_path.lower()
        if not ext.endswith((".xlsx", ".xls", ".csv", ".pdf")):
            logger.error("Solo .xlsx, .xls, .csv o .pdf permitidos")
            return 1
        if args.trackman_csv and not os.path.isfile(args.trackman_csv):
            logger.error(f"No existe --trackman-csv: {args.trackman_csv}")
            return 1
    if args.local_trackman and not os.path.isfile(args.local_trackman):
        logger.error(f"No existe --local-trackman: {args.local_trackman}")
        return 1

    run_id = time.strftime("%Y%m%d-%H%M%S")
    tools_result: Optional[dict] = None
    reports_result: Optional[dict] = None
    artefactos: Optional[dict] = None
    exit_code = 0

    # Etapa Tools
    if not args.solo_reports:
        try:
            tools_result = extract_and_preview(args.input_path, args.trackman_csv, args.umbral)
            if has_error_in_tools(tools_result):
                logger.warning("Etapa Tools finalizó con error reportado")
                exit_code = max(exit_code, 2)
        except Exception as e:
            logger.exception(f"Fallo en etapa Tools: {e}")
            tools_result = {"error": f"{type(e).__name__}: {e}"}
            exit_code = 2  # parcial

    # Etapa Reports
    if not args.solo_tools:
        try:
            reports_result = run_reports(
                df=None,  # si quieres pasar un DF precargado, reemplaza aquí
                local_file=args.local_trackman,
                batter_filter=args.batter,
                pitcher_filter=args.pitcher,
                work_dir=args.work_dir,
                clean_temp=not args.no_clean_temp
            )
        except Exception as e:
            logger.exception(f"Fallo en etapa Reports: {e}")
            reports_result = {"error": f"{type(e).__name__}: {e}"}
            exit_code = 2  # parcial

    # Artefactos desde Reports
    artefactos = collect_artefacts(reports_result)

    # Salida unificada
    final_obj = single_json_output(tools_result, reports_result, artefactos, run_id)

    if args.output:
        try:
            os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(final_obj, f, ensure_ascii=False, indent=4)
            print(args.output)
        except Exception as e:
            logger.exception(f"No se pudo escribir salida en {args.output}: {e}")
            print(json.dumps(final_obj, ensure_ascii=False, indent=4))
            exit_code = max(exit_code, 2)
    else:
        print(json.dumps(final_obj, ensure_ascii=False, indent=4))

    # Código de salida: 0 ok, 2 parcial, 1 fatal
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
