"""Algoritmos de busca para o problema do entregador.

A busca principal é o **A\\*** com a heurística admissível de
:mod:`entregador.mundo`, que garante um plano **ótimo** (menor custo
total, considerando os pedágios). Com ``usar_heuristica=False`` a mesma
rotina implementa a busca de custo uniforme (UCS), usada nos testes
para conferir a otimalidade do A*.
"""

from __future__ import annotations

import heapq
import time
from typing import Callable, List, Optional, Tuple

from .mundo import Estado, MundoGrid

Custo = float


class Plano:
    """Plano (solução) retornado pela busca."""

    def __init__(
        self,
        estados: List[Estado],
        acoes: List[str],
        custos_passo: List[Custo],
        expandidos: int,
    ) -> None:
        self.estados = estados          # estados do inicial ao objetivo
        self.acoes = acoes               # ações que ligam os estados
        self.custos_passo = custos_passo  # custo de cada ação (com pedágio)
        self.expandidos = expandidos      # nº de estados expandidos (para medir esforço)

    @property
    def custo_total(self) -> Custo:
        """Custo real do plano (soma dos custos das ações)."""
        return sum(self.custos_passo)

    def __len__(self) -> int:
        return len(self.acoes)

    def resumir(self) -> str:
        """Versão compacta do plano, agrupando ações repetidas."""
        blocos: List[Tuple[str, int]] = []
        for acao in self.acoes:
            if blocos and blocos[-1][0] == acao:
                blocos[-1] = (acao, blocos[-1][1] + 1)
            else:
                blocos.append((acao, 1))
        return ", ".join(f"{acao} x{qtd}" if qtd > 1 else acao for acao, qtd in blocos)


def busca(mundo: MundoGrid, usar_heuristica: bool = True) -> Optional[Plano]:
    """Retorna o plano ótimo do mundo ou ``None`` se não houver solução."""
    inicio = time.perf_counter()
    plano = _astar(mundo, mundo.heuristica if usar_heuristica else None)
    mundo_tempo = time.perf_counter() - inicio
    if plano is not None:
        plano.tempo_segundos = mundo_tempo  # type: ignore[attr-defined]
    return plano


def _astar(mundo: MundoGrid, heuristica: Optional[Callable[[Estado], float]]) -> Optional[Plano]:
    """A* / busca de custo uniforme genérica sobre o espaço de estados."""
    h: Callable[[Estado], float] = heuristica or (lambda estado: 0.0)
    inicial = mundo.estado_inicial()

    if mundo.eh_objetivo(inicial):
        return Plano([inicial], [], [], 0)

    # Fila de prioridade: tuplas (f, g, estado). Estados são comparáveis,
    # então o desempate do heap nunca falha.
    fila: List[Tuple[float, float, Estado]] = [(h(inicial), 0.0, inicial)]
    melhor_g = {inicial: 0.0}
    # Estado -> (estado anterior, ação, custo da ação).
    origem = {inicial: (None, None, 0.0)}
    expandidos = 0

    while fila:
        _, g, estado = heapq.heappop(fila)
        if g > melhor_g.get(estado, float("inf")):
            continue  # entrada obsoleta na fila

        if mundo.eh_objetivo(estado):
            return _montar_plano(origem, estado, expandidos)

        expandidos += 1
        for acao, novo, custo in mundo.sucessores(estado):
            novo_g = g + custo
            if novo_g < melhor_g.get(novo, float("inf")):
                melhor_g[novo] = novo_g
                origem[novo] = (estado, acao, custo)
                heapq.heappush(fila, (novo_g + h(novo), novo_g, novo))

    return None  # fronteira esgotada: não existe solução


def _montar_plano(
    origem: dict, objetivo: Estado, expandidos: int
) -> Plano:
    """Reconstrói estados, ações e custos do objetivo até o estado inicial."""
    estados_inv: List[Estado] = []
    acoes_inv: List[str] = []
    custos_inv: List[Custo] = []
    estado: Optional[Estado] = objetivo
    while estado is not None:
        estados_inv.append(estado)
        anterior, acao, custo = origem[estado]
        if anterior is None:
            break
        acoes_inv.append(acao)
        custos_inv.append(custo)
        estado = anterior
    return Plano(
        estados=list(reversed(estados_inv)),
        acoes=list(reversed(acoes_inv)),
        custos_passo=list(reversed(custos_inv)),
        expandidos=expandidos,
    )


def simular(mundo: MundoGrid, acoes: List[str]) -> Tuple[bool, Custo, List[Estado]]:
    """Executa as ``acoes`` no mundo; devolve (válido, custo, estados).

    Usado nos testes para conferir que um plano realmente entrega o
    pacote e que seu custo corresponde ao informado pela busca.
    """
    estado = mundo.estado_inicial()
    estados = [estado]
    custo_total: Custo = 0.0
    for acao in acoes:
        aplicaveis = {nome: (novo, c) for nome, novo, c in mundo.sucessores(estado)}
        if acao not in aplicaveis:
            return False, custo_total, estados
        estado, custo = aplicaveis[acao]
        custo_total += custo
        estados.append(estado)
    return mundo.eh_objetivo(estado), custo_total, estados
