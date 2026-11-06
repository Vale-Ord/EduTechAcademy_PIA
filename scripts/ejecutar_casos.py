"""Ejecuta los casos del maestro y guarda la evidencia en docs/evidencias/.

Uso:  python scripts/ejecutar_casos.py
"""
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from src.application.casos_maestro import ejecutar_todo  # noqa: E402

if __name__ == "__main__":
    r = ejecutar_todo(salida=RAIZ / "docs" / "evidencias")
    print("Casos validar/beneficio:", dict(Counter(c["resultado"] for c in r["casos"])))
    print("Transiciones:", dict(Counter(t["resultado"] for t in r["transiciones"])))
    print("Evidencia en docs/evidencias/resultados_*.csv")
