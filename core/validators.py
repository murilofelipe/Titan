"""Validadores automáticos de etapa (S4.3).

Rodam antes de liberar a próxima etapa; retornam a lista de falhas (vazia = ok).
Ponto de partida, não teto: só checam o que o step declara em `validation:`.
"""

import glob
import os
import subprocess
from typing import List

from core.parser import StepValidation


def run_validations(
    validations: List[StepValidation], base_dir: str = "."
) -> List[str]:
    """Executa as validações declaradas e devolve as mensagens de falha."""
    failures: List[str] = []
    for v in validations:
        if v.type == "file_exists":
            target = v.path if os.path.isabs(v.path or "") else os.path.join(base_dir, v.path or "")
            if not os.path.isfile(target):
                failures.append(f"file_exists: '{v.path}' não existe")

        elif v.type == "glob_nonempty":
            pattern = v.pattern if os.path.isabs(v.pattern or "") else os.path.join(base_dir, v.pattern or "")
            if not glob.glob(pattern, recursive=True):
                failures.append(f"glob_nonempty: nenhum arquivo casa '{v.pattern}'")

        elif v.type == "command_zero":
            if not v.cmd:
                failures.append("command_zero: 'cmd' vazio")
                continue
            try:
                proc = subprocess.run(
                    v.cmd, cwd=base_dir, shell=False,
                    capture_output=True, text=True, timeout=600,
                )
            except (OSError, subprocess.TimeoutExpired) as e:
                failures.append(f"command_zero: {' '.join(v.cmd)} — {e}")
                continue
            if proc.returncode != 0:
                failures.append(
                    f"command_zero: {' '.join(v.cmd)} saiu {proc.returncode}"
                )
    return failures
