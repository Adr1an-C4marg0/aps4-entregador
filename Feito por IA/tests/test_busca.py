"""Testes da busca de plano ótimo (entregador/busca.py)."""

import pytest

from entregador.busca import busca, simular
from entregador.mundo import CUSTO_BASE, CUSTO_PEDAGIO, MundoGrid


def test_plano_otimo_sem_pedagio():
    """3x3 livre: agente(0,0) -> pacote(0,2) -> destino(2,0)."""
    mundo = MundoGrid(3, set(), set(), (0, 0), (0, 2), (2, 0))
    plano = busca(mundo)
    assert plano is not None
    # 2 movimentos até o pacote + PEGAR + 4 movimentos + ENTREGAR
    assert plano.custo_total == 8
    assert plano.acoes[-1] == "ENTREGAR"
    assert "PEGAR" in plano.acoes

    valido, custo, _ = simular(mundo, plano.acoes)
    assert valido and custo == plano.custo_total


def test_plano_otimo_com_pedagio():
    """O A* deve emparelhar com o UCS mesmo com pedágio no caminho.

    3x3, pedágio em (0,1): agente(0,0) -> pacote(0,2) -> destino(2,0).
    Melhor rota até o pacote custa 4 (atalho pelo pedágio: 3 + 1) e a
    volta até o destino custa 4, mais PEGAR e ENTREGAR: total 10.
    """
    mundo = MundoGrid(3, set(), {(0, 1)}, (0, 0), (0, 2), (2, 0))
    plano = busca(mundo)
    assert plano is not None
    assert plano.custo_total == 10

    ucs = busca(mundo, usar_heuristica=False)
    assert ucs is not None
    assert plano.custo_total == ucs.custo_total  # A* é ótimo

    valido, custo, estados = simular(mundo, plano.acoes)
    assert valido and custo == plano.custo_total
    assert estados[-1][0] == mundo.destino


def test_pedagio_vale_a_pena_quando_e_atalho():
    """Grid 5x5 com obstáculos em (1,1..3) e pedágio em (0,2).

    Passar pelo pedágio custa 3; contornar a parede custaria muito mais.
    Rota ótima: (0,0)->(0,2)->(0,4) [4 passos + 2 de pedágio] pegar,
    (0,4)->(4,4) [4 passos], entregar. Total = 4 + 2 + 1 + 4 + 1 = 12.
    """
    mundo = MundoGrid(
        5, {(1, 1), (1, 2), (1, 3)}, {(0, 2)}, (0, 0), (0, 4), (4, 4)
    )
    plano = busca(mundo)
    assert plano is not None
    assert plano.custo_total == 12
    # o agente realmente atravessa a célula de pedágio
    assert any(estado[0] == (0, 2) for estado in plano.estados)

    ucs = busca(mundo, usar_heuristica=False)
    assert ucs is not None
    assert plano.custo_total == ucs.custo_total


def test_sem_solucao_retorna_none():
    mundo = MundoGrid(3, {(1, 0), (0, 1)}, set(), (2, 2), (0, 0), (2, 0))
    assert busca(mundo) is None


def test_sem_solucao_destino_cercado():
    mundo = MundoGrid(3, {(1, 0), (2, 1)}, set(), (0, 0), (0, 1), (2, 0))
    assert busca(mundo) is None


@pytest.mark.parametrize("dimensao", [4, 6, 10, 15])
@pytest.mark.parametrize("semente", ["1", "2", "3", "4"])
def test_mundos_aleatorios_plano_valido_e_otimo(dimensao, semente):
    """Para todo mundo com solução, o plano do A* é válido, tem o mesmo
    custo do UCS e termina com o pacote no destino."""
    mundo = MundoGrid.gerar(dimensao, semente)
    plano = busca(mundo)
    if not mundo.solucionavel():
        assert plano is None
        return

    ucs = busca(mundo, usar_heuristica=False)
    assert plano is not None and ucs is not None
    assert plano.custo_total == ucs.custo_total

    valido, custo, estados = simular(mundo, plano.acoes)
    assert valido, "plano simulado não atinge o objetivo"
    assert custo == plano.custo_total
    assert estados[-1][1] == mundo.destino and estados[-1][2] is False
    # estados do plano começam no estado inicial e terminam no objetivo
    assert estados[0] == mundo.estado_inicial() or estados[0] == mundo.estado_inicial()
    assert plano.estados[0] == mundo.estado_inicial()
    assert mundo.eh_objetivo(plano.estados[-1])


def test_resumo_do_plano():
    mundo = MundoGrid(3, set(), set(), (0, 0), (0, 2), (2, 0))
    plano = busca(mundo)
    assert plano is not None
    assert "x2" in plano.resumir()  # há ações repetidas consecutivas
