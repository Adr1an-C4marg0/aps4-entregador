"""Testes da modelagem do mundo (entregador/mundo.py)."""

import pytest

from entregador.mundo import CUSTO_BASE, CUSTO_PEDAGIO, MundoGrid


def mundo_simples():
    """Grid 3x3 sem obstáculos nem pedágios."""
    return MundoGrid(3, set(), set(), (0, 0), (0, 2), (2, 0))


def test_estado_inicial_e_objetivo():
    mundo = mundo_simples()
    estado = mundo.estado_inicial()
    assert estado == ((0, 0), (0, 2), False)
    assert not mundo.eh_objetivo(estado)
    assert mundo.eh_objetivo(((2, 0), (2, 0), False))


def test_dimensao_invalida():
    with pytest.raises(ValueError):
        MundoGrid(1, set(), set(), (0, 0), (0, 1), (1, 0))


def test_celulas_distintas_e_sem_obstaculo_sobre_peca():
    with pytest.raises(ValueError):
        MundoGrid(3, set(), set(), (0, 0), (0, 0), (1, 1))
    with pytest.raises(ValueError):
        MundoGrid(3, {(0, 0)}, set(), (0, 0), (0, 1), (1, 1))
    with pytest.raises(ValueError):
        MundoGrid(3, set(), set(), (5, 0), (0, 1), (1, 1))


def test_geracao_aleatoria_reproduzivel():
    a = MundoGrid.gerar(8, "semente-1")
    b = MundoGrid.gerar(8, "semente-1")
    c = MundoGrid.gerar(8, "semente-2")
    assert (a.obstaculos, a.pedagios, a.agente, a.pacote, a.destino) == (
        b.obstaculos, b.pedagios, b.agente, b.pacote, b.destino,
    )
    assert (a.obstaculos, a.pedagios, a.agente, a.pacote, a.destino) != (
        c.obstaculos, c.pedagios, c.agente, c.pacote, c.destino,
    )


@pytest.mark.parametrize("dimensao", [2, 3, 5, 10, 17, 25])
def test_mundos_gerados_sao_validos(dimensao):
    for semente in ("a", "b", "c"):
        mundo = MundoGrid.gerar(dimensao, semente)
        assert mundo.dentro(mundo.agente) and mundo.dentro(mundo.pacote) and mundo.dentro(mundo.destino)
        assert len({mundo.agente, mundo.pacote, mundo.destino}) == 3
        assert not (mundo.obstaculos & {mundo.agente, mundo.pacote, mundo.destino})


def test_movimentos_na_borda_ou_obstaculo_mantem_agente_parado():
    mundo = MundoGrid(3, {(0, 1)}, set(), (0, 0), (0, 2), (2, 0))
    sucessores = {acao: novo for acao, novo, _ in mundo.sucessores(mundo.estado_inicial())}
    assert sucessores["DIREITA"] == mundo.estado_inicial()  # obstáculo em (0, 1)
    assert sucessores["CIMA"] == mundo.estado_inicial()      # borda do grid
    assert sucessores["ESQUERDA"] == mundo.estado_inicial()  # borda do grid
    assert sucessores["BAIXO"][0] == (1, 0)


def test_custo_com_pedagio():
    mundo = MundoGrid(
        3, set(), {(0, 1)}, (0, 0), (0, 2), (2, 0)
    )
    acoes = {acao: custo for acao, _, custo in mundo.sucessores(mundo.estado_inicial())}
    assert acoes["BAIXO"] == CUSTO_BASE
    assert acoes["DIREITA"] == CUSTO_BASE + CUSTO_PEDAGIO  # (0, 1) é pedágio


def test_pegar_e_entregar():
    mundo = mundo_simples()
    estado = mundo.estado_inicial()
    assert "PEGAR" not in dict((a, True) for a, _, _ in mundo.sucessores(estado))

    # vai até o pacote e o pega
    agente_no_pacote = ((0, 2), (0, 2), False)
    nomes = {acao for acao, _, _ in mundo.sucessores(agente_no_pacote)}
    assert "PEGAR" in nomes
    carregando = mundo.aplicar(agente_no_pacote, "PEGAR")
    assert carregando == ((0, 2), (0, 2), True)

    # pacote anda junto com o agente
    andou = mundo.aplicar(carregando, "BAIXO")
    assert andou == ((1, 2), (1, 2), True)
    assert mundo.posicao_pacote(andou) == (1, 2)

    # só dá para entregar sobre o destino
    assert "ENTREGAR" not in {a for a, _, _ in mundo.sucessores(carregando)}
    no_destino = ((2, 0), (0, 2), True)
    entregue = mundo.aplicar(no_destino, "ENTREGAR")
    assert entregue == ((2, 0), (2, 0), False)
    assert mundo.eh_objetivo(entregue)


@pytest.mark.parametrize("dimensao,minimo,maximo", [(2, 1, 1), (3, 1, 2), (4, 1, 4), (10, 10, 25)])
def test_quantidade_de_obstaculos_tem_piso_nos_mapas_pequenos(dimensao, minimo, maximo):
    """Mapas pequenos precisam gerar obstáculos (antes 0-1 em N=3)."""
    for semente in ("x", "y", "z", "w", "v"):
        mundo = MundoGrid.gerar(dimensao, semente)
        assert minimo <= len(mundo.obstaculos) <= maximo
        # as 3 peças nunca ficam sem célula e nunca em cima de obstáculo
        assert len({mundo.agente, mundo.pacote, mundo.destino, *mundo.obstaculos}) == 3 + len(mundo.obstaculos)


def test_pedagios_nao_ocupam_pecas_nem_obstaculos():
    for dimensao in (3, 5, 9):
        for semente in ("a", "b", "c"):
            mundo = MundoGrid.gerar(dimensao, semente)
            assert not (mundo.pedagios & (mundo.obstaculos | {mundo.agente, mundo.pacote, mundo.destino}))


def test_sem_solucao_por_isolamento():
    mundo = MundoGrid(3, {(1, 0), (0, 1)}, set(), (2, 2), (0, 0), (2, 0))
    assert not mundo.solucionavel()
    assert len(mundo.alcancaveis((0, 0))) == 1


def test_solucionavel_quando_destino_esta_atras_de_obstaculo():
    # Destino (2,0) cercado: sem solução, embora o pacote seja alcançável.
    mundo = MundoGrid(3, {(1, 0), (2, 1)}, set(), (0, 0), (0, 1), (2, 0))
    assert not mundo.solucionavel()
