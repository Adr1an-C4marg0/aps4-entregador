"""Modelagem do mundo do tipo grid para o problema do entregador.

O mundo é um grid quadrado ``N x N`` (``N >= 2``) contendo:

- um agente (boneco), que sabe ir para cima, baixo, esquerda, direita,
  pegar pacote e entregar pacote;
- células livres (brancas);
- células intransponíveis (obstáculos, pretas);
- células com pedágio (cinzas): executar uma ação nelas custa +2;
- uma célula com o pacote (caixa);
- uma célula de destino da entrega (X).

Estado do problema
------------------
Um estado é a tupla ``(agente, pacote, carregando)``:

- ``agente``: célula ``(linha, coluna)`` do agente;
- ``pacote``: célula em que o pacote está no chão. Enquanto o pacote
  está com o agente, continua registrando a célula em que ele foi
  pego (o pacote, de fato, "viaja" na célula do agente);
- ``carregando``: ``True`` se o pacote está com o agente.

O estado objetivo é o pacote na célula de destino, ou seja, ter
executado a ação ``ENTREGAR`` sobre o destino.

Convenção de custo
------------------
Toda ação custa ``CUSTO_BASE`` (1). Quando a ação é executada em uma
célula de pedágio, o custo real é ``custo + CUSTO_PEDAGIO`` (total 3).
Para as ações de movimento, considera-se que a ação é executada na
célula em que o agente passa a estar após o movimento; para ``PEGAR``
e ``ENTREGAR``, na célula atual do agente.

Se o agente tenta mover-se para fora do grid ou para cima de um
obstáculo, a consequência é permanecer na mesma célula. Como isso
nunca pode fazer parte de um plano ótimo, tais ações simplesmente não
são geradas como sucessoras.
"""

from __future__ import annotations

import random
from typing import Dict, Iterable, List, Optional, Set, Tuple

CUSTO_BASE = 1
CUSTO_PEDAGIO = 2  # custo adicional de uma ação executada em célula de pedágio

# Deslocamentos na forma (delta de linha, delta de coluna).
DESLOCAMENTOS: Dict[str, Tuple[int, int]] = {
    "CIMA": (-1, 0),
    "BAIXO": (1, 0),
    "ESQUERDA": (0, -1),
    "DIREITA": (0, 1),
}

Celula = Tuple[int, int]
Estado = Tuple[Celula, Celula, bool]  # (agente, pacote, carregando)


def manhattan(a: Celula, b: Celula) -> int:
    """Distância de Manhattan entre duas células."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class MundoGrid:
    """Mundo quadrado ``N x N`` com obstáculos, pedágios, pacote e destino."""

    def __init__(
        self,
        dimensao: int,
        obstaculos: Iterable[Celula],
        pedagios: Iterable[Celula],
        agente: Celula,
        pacote: Celula,
        destino: Celula,
    ) -> None:
        if dimensao < 2:
            raise ValueError("A dimensão do grid deve ser >= 2.")

        self.dimensao = dimensao
        self.obstaculos: Set[Celula] = {tuple(c) for c in obstaculos}
        self.pedagios: Set[Celula] = {tuple(c) for c in pedagios}
        self.agente: Celula = tuple(agente)
        self.pacote: Celula = tuple(pacote)
        self.destino: Celula = tuple(destino)

        pecas = {"agente": self.agente, "pacote": self.pacote, "destino": self.destino}
        for nome, celula in pecas.items():
            self._validar_celula(celula, nome)
        if len(set(pecas.values())) != 3:
            raise ValueError("Agente, pacote e destino devem ocupar células distintas.")
        if self.obstaculos & set(pecas.values()):
            raise ValueError("Há obstáculo sobreposto ao agente, ao pacote ou ao destino.")

    # ------------------------------------------------------------------ #
    # Construção / geração aleatória
    # ------------------------------------------------------------------ #
    def _validar_celula(self, celula: Celula, nome: str) -> None:
        if not (0 <= celula[0] < self.dimensao and 0 <= celula[1] < self.dimensao):
            raise ValueError(f"A célula {nome} = {celula} está fora do grid.")

    @classmethod
    def gerar(cls, dimensao: int, semente: Optional[str] = None) -> "MundoGrid":
        """Gera um mundo aleatório de dimensão ``dimensao``.

        A quantidade e a posição dos obstáculos e dos pedágios, assim
        como as posições do agente, do pacote e do destino, são
        sorteadas. O mundo gerado pode ou não ter solução — use
        :meth:`solucionavel` ou a busca para verificar.

        Regra de sorteio das quantidades (sempre deixando 3 células
        livres para agente, pacote e destino):

        - **obstáculos**: entre ``max(1, 10%)`` e ``25%`` das células,
          com piso de 1 sempre que caibam ao menos 2 células extras
          (ou seja, ``N >= 3`` ganha no mínimo 1 obstáculo);
        - **pedágios**: entre ``4%`` e ``10%`` das células que sobrarem.
        """
        if dimensao < 2:
            raise ValueError("A dimensão do grid deve ser >= 2.")

        rng = random.Random() if semente is None else random.Random(semente)
        total = dimensao * dimensao
        celulas = [(i, j) for i in range(dimensao) for j in range(dimensao)]
        rng.shuffle(celulas)

        # Células disponíveis depois de reservar as 3 peças do problema.
        espacos = total - 3

        # Obstáculos: 10%-25% das células, com piso de 1 quando há pelo
        # menos uma célula de sobra além das 3 peças.
        teto_obstaculos = min(int(total * 0.25), espacos)
        piso_obstaculos = min(teto_obstaculos, max(1, int(total * 0.10))) if espacos >= 1 else 0
        n_obstaculos = rng.randint(piso_obstaculos, teto_obstaculos) if teto_obstaculos >= piso_obstaculos else 0
        espacos -= n_obstaculos

        # Pedágios: 4%-10% das células restantes.
        teto_pedagios = min(int(total * 0.10), espacos)
        piso_pedagios = min(teto_pedagios, int(total * 0.04))
        n_pedagios = rng.randint(piso_pedagios, teto_pedagios) if teto_pedagios >= piso_pedagios else 0

        obstaculos = celulas[:n_obstaculos]
        pedagios = celulas[n_obstaculos:n_obstaculos + n_pedagios]
        agente, pacote, destino = celulas[n_obstaculos + n_pedagios:n_obstaculos + n_pedagios + 3]

        return cls(dimensao, obstaculos, pedagios, agente, pacote, destino)

    # ------------------------------------------------------------------ #
    # Consultas sobre o mundo
    # ------------------------------------------------------------------ #
    def dentro(self, celula: Celula) -> bool:
        """``True`` se a célula está dentro dos limites do grid."""
        return 0 <= celula[0] < self.dimensao and 0 <= celula[1] < self.dimensao

    def custo_na_celula(self, celula: Celula) -> float:
        """Custo de executar uma ação cuja célula de execução é ``celula``."""
        custo = float(CUSTO_BASE)
        if celula in self.pedagios:
            custo += CUSTO_PEDAGIO
        return custo

    def estado_inicial(self) -> Estado:
        """Estado inicial: agente em sua casa, pacote na casa de origem."""
        return (self.agente, self.pacote, False)

    def eh_objetivo(self, estado: Estado) -> bool:
        """Objetivo alcançado: pacote (entregue) na célula de destino."""
        _, pacote, carregando = estado
        return (not carregando) and pacote == self.destino

    def posicao_pacote(self, estado: Estado) -> Celula:
        """Célula ocupada pelo pacote — com o agente, ele se move com ele."""
        agente, pacote, carregando = estado
        return agente if carregando else pacote

    def heuristica(self, estado: Estado) -> float:
        """Heurística admissível para o A*.

        Soma (1) a distância do agente até o pacote, (2) a distância do
        pacote até o destino e (3) as duas ações obrigatórias ``PEGAR``
        e ``ENTREGAR``. Pedágios só aumentam custos reais, portanto a
        heurística continua admissível e o A* encontra plano ótimo.
        """
        agente, pacote, carregando = estado
        pos_pacote = self.posicao_pacote(estado)
        estimativa = manhattan(agente, pos_pacote) + manhattan(pos_pacote, self.destino)
        if not carregando:
            estimativa += CUSTO_BASE  # ainda falta a ação PEGAR
        estimativa += CUSTO_BASE      # a ação ENTREGAR é sempre necessária
        return float(estimativa)

    # ------------------------------------------------------------------ #
    # Modelo de transição
    # ------------------------------------------------------------------ #
    def sucessores(self, estado: Estado) -> List[Tuple[str, Estado, float]]:
        """Ações aplicáveis em ``estado``, com o estado e o custo delas.

        Cada item da lista é ``(ação, estado_resultante, custo)``.
        Movimentos que bateriam na borda ou em um obstáculo não são
        gerados (a consequência seria ficar parado, o que nunca é útil).
        """
        agente, pacote, carregando = estado
        acoes: List[Tuple[str, Estado, float]] = []

        for nome, (di, dj) in DESLOCAMENTOS.items():
            destino = (agente[0] + di, agente[1] + dj)
            if not self.dentro(destino) or destino in self.obstaculos:
                continue
            custo = self.custo_na_celula(destino)
            pacote_novo = destino if carregando else pacote
            acoes.append((nome, (destino, pacote_novo, carregando), custo))

        if not carregando and agente == pacote:
            acoes.append(("PEGAR", (agente, pacote, True), self.custo_na_celula(agente)))

        if carregando and agente == self.destino:
            acoes.append(("ENTREGAR", (agente, self.destino, False), self.custo_na_celula(agente)))

        return acoes

    def aplicar(self, estado: Estado, acao: str) -> Estado:
        """Aplica ``acao`` em ``estado``; action inválida levanta ``ValueError``."""
        for nome, novo, _ in self.sucessores(estado):
            if nome == acao:
                return novo
        raise ValueError(f"A ação {acao!r} não é aplicável no estado {estado}.")

    # ------------------------------------------------------------------ #
    # Análise de conectividade (detecção rápida de "sem solução")
    # ------------------------------------------------------------------ #
    def vizinhas_livres(self, celula: Celula) -> List[Celula]:
        return [
            (celula[0] + di, celula[1] + dj)
            for di, dj in DESLOCAMENTOS.values()
            if self.dentro((celula[0] + di, celula[1] + dj))
            and (celula[0] + di, celula[1] + dj) not in self.obstaculos
        ]

    def alcancaveis(self, origem: Celula) -> Set[Celula]:
        """Células atingíveis a partir de ``origem`` ignorando pedágios."""
        vistas = {origem}
        fila = [origem]
        while fila:
            atual = fila.pop()
            for vizinha in self.vizinhas_livres(atual):
                if vizinha not in vistas:
                    vistas.add(vizinha)
                    fila.append(vizinha)
        return vistas

    def solucionavel(self) -> bool:
        """``True`` se o agente pode pegar o pacote e chegar ao destino."""
        do_agente = self.alcancaveis(self.agente)
        if self.pacote not in do_agente:
            return False
        do_pacote = self.alcancaveis(self.pacote)
        return self.destino in do_pacote

    # ------------------------------------------------------------------ #
    # Representação textual / ASCII
    # ------------------------------------------------------------------ #
    def resumo(self) -> str:
        return (
            f"grid {self.dimensao}x{self.dimensao} | obstáculos: {len(self.obstaculos)} | "
            f"pedágios: {len(self.pedagios)} | agente: {self.agente} | "
            f"pacote: {self.pacote} | destino: {self.destino}"
        )

    def descrever(self, estado: Optional[Estado] = None) -> str:
        """Desenho ASCII do mundo. ``.`` livre, `#` obstáculo, `$` pedágio,
        ``A`` agente, ``P`` pacote, ``X`` destino."""
        agente, pacote, carregando = estado if estado else self.estado_inicial()
        pos_pacote = self.posicao_pacote((agente, pacote, carregando))
        linhas = ["    " + " ".join(str(j % 10) for j in range(self.dimensao))]
        for i in range(self.dimensao):
            linha = []
            for j in range(self.dimensao):
                celula = (i, j)
                if celula == agente:
                    linha.append("A")
                elif celula == pos_pacote and carregando:
                    linha.append("A")  # pacote junto ao agente
                elif celula == pos_pacote:
                    linha.append("P")
                elif celula == self.destino:
                    linha.append("X")
                elif celula in self.obstaculos:
                    linha.append("#")
                elif celula in self.pedagios:
                    linha.append("$")
                else:
                    linha.append(".")
            linhas.append(f"{i:3d} " + " ".join(linha))
        return "\n".join(linhas)
