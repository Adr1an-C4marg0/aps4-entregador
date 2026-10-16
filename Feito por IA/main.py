"""Ponto de entrada da APS "Entregador em mundo grid".

- ``python main.py`` abre a interface gráfica.
- ``python main.py --cli -n 10 -s 42`` roda em modo texto (gera o mundo,
  busca o plano ótimo e imprime o resultado).
"""

from __future__ import annotations

import argparse
import sys

from entregador import cli


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Entregador em mundo grid — APS")
    parser.add_argument("--cli", action="store_true", help="executa em modo texto (sem interface)")
    parser.add_argument("-n", "--dimensao", type=int, default=10, help="dimensão do grid quadrado")
    parser.add_argument("-s", "--semente", default=None, help="semente aleatória (opcional)")
    args = parser.parse_args(argv)

    if args.cli:
        return cli.run(args.dimensao, args.semente)

    from entregador.interface import main as iniciar_interface

    iniciar_interface()
    return 0


if __name__ == "__main__":
    sys.exit(main())
