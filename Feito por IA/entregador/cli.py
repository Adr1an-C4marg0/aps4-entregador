"""Uso em linha de comando (para exemplos de execução e depuração)."""

from __future__ import annotations

import argparse
from typing import List, Optional

from .busca import busca
from .mundo import MundoGrid


def run(dimensao: int, semente: Optional[str] = None, saida=print) -> int:
    """Gera um mundo, busca o plano ótimo e imprime o resultado.

    Retorna 0 quando existe solução e 1 quando não existe.
    """
    mundo = MundoGrid.gerar(dimensao, semente)
    saida(f"Mundo gerado: {mundo.resumo()}")
    saida("")
    saida(mundo.descrever())
    saida("")
    saida("Legenda: A agente | P pacote | X destino | # obstáculo | $ pedágio")
    saida("")

    plano = busca(mundo)
    if plano is None:
        saida("SEM SOLUÇÃO: não existe plano que entregue o pacote no destino")
        saida("(o pacote ou o destino está cercado/inacessível para o agente).")
        return 1

    saida(f"Solução ótima encontrada em {getattr(plano, 'tempo_segundos', 0) * 1000:.1f} ms")
    saida(f"Número de ações: {len(plano)}")
    saida(f"Custo total: {plano.custo_total:g}")
    saida(f"Plano resumido: {plano.resumir()}")
    saida("")
    saida("Plano detalhado:")
    for numero, (acao, custo) in enumerate(zip(plano.acoes, plano.custos_passo), start=1):
        saida(f"  {numero:3d}. {acao:<9s} custo {custo:g}")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Entregador em mundo grid — modo texto")
    parser.add_argument("-n", "--dimensao", type=int, default=10, help="dimensão do grid quadrado")
    parser.add_argument("-s", "--semente", default=None, help="semente aleatória (opcional)")
    args = parser.parse_args(argv)
    return run(args.dimensao, args.semente)


if __name__ == "__main__":
    raise SystemExit(main())
