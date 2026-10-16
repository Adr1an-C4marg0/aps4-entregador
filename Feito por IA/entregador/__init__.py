"""Pacote do entregador em mundo grid.

Módulos:
    mundo      -- modelagem do mundo quadrado N x N e do estado do problema
    busca      -- A* (ótimo) e busca de custo uniforme, para comparação
    interface  -- interface gráfica (Tkinter)
    cli        -- execução em linha de comando (para exemplos e depuração)
"""

from .mundo import CUSTO_BASE, CUSTO_PEDAGIO, Estado, MundoGrid

__all__ = ["CUSTO_BASE", "CUSTO_PEDAGIO", "Estado", "MundoGrid"]
__version__ = "1.0.0"
