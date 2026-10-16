import random

CUSTO_PEDAGIO = 3  # custo de uma ação feita em célula de pedágio (ajuste conforme o enunciado)

# Símbolos do grid: "." = livre, "#" = obstáculo, "$" = pedágio

def criar_grid(n):
    """Cria um grid n x n com obstáculos e pedágios sorteados."""
    grid = []
    for i in range(n):
        linha = []
        for j in range(n):
            sorteio = random.random()
            if sorteio < 0.25:
                linha.append("#")
            elif sorteio < 0.40:
                linha.append("$")
            else:
                linha.append(".")
        grid.append(linha)
    return grid


def contar_livres(grid):
    total = 0
    for linha in grid:
        for celula in linha:
            if celula != "#":
                total = total + 1
    return total


def sortear_posicao_livre(grid, ocupadas):
    """Sorteia uma célula que não é obstáculo e ainda não foi usada."""
    n = len(grid)
    while True:
        lin = random.randint(0, n - 1)
        col = random.randint(0, n - 1)
        if grid[lin][col] != "#" and (lin, col) not in ocupadas:
            return (lin, col)


def custo_da_acao(grid, lin, col):
    """Custo de qualquer ação feita na célula (lin, col)."""
    if grid[lin][col] == "$":
        return CUSTO_PEDAGIO
    return 1


def sucessores(grid, estado):
    """
    Estado = (linha do agente, coluna do agente, linha do pacote, coluna do pacote).
    Se o pacote está com o agente, a linha e a coluna do pacote valem -1.
    Retorna uma lista de (nome da ação, novo estado, custo).
    """
    n = len(grid)
    lin, col, plin, pcol = estado
    custo = custo_da_acao(grid, lin, col)
    lista = []

    # Movimentos
    movimentos = [("cima", -1, 0), ("baixo", 1, 0), ("esquerda", 0, -1), ("direita", 0, 1)]
    for nome, dl, dc in movimentos:
        nova_lin = lin + dl
        nova_col = col + dc
        if nova_lin >= 0 and nova_lin < n and nova_col >= 0 and nova_col < n:
            if grid[nova_lin][nova_col] != "#":
                lista.append((nome, (nova_lin, nova_col, plin, pcol), custo))

    # Pegar pacote
    if plin == lin and pcol == col:
        lista.append(("pegar pacote", (lin, col, -1, -1), custo))

    # Entregar pacote
    if plin == -1:
        lista.append(("entregar pacote", (lin, col, lin, col), custo))

    return lista


def montar_plano(anterior, estado):
    """Volta do estado final até o inicial para montar a lista de ações."""
    plano = []
    while anterior[estado] is not None:
        estado_anterior, acao, custo = anterior[estado]
        plano.insert(0, (acao, custo))
        estado = estado_anterior
    return plano


def buscar(grid, inicio, destino):
    """
    Busca de custo uniforme: sempre expande o estado de menor custo.
    Retorna a lista de (ação, custo) ou None se não existe solução.
    """
    custo_ate = {inicio: 0}
    anterior = {inicio: None}
    fronteira = [inicio]

    while len(fronteira) > 0:
        # escolhe o estado com menor custo
        atual = fronteira[0]
        for estado in fronteira:
            if custo_ate[estado] < custo_ate[atual]:
                atual = estado
        fronteira.remove(atual)

        # objetivo: pacote na célula de destino
        if atual[2] == destino[0] and atual[3] == destino[1]:
            return montar_plano(anterior, atual)

        for acao, novo, custo in sucessores(grid, atual):
            novo_custo = custo_ate[atual] + custo
            if novo not in custo_ate or novo_custo < custo_ate[novo]:
                custo_ate[novo] = novo_custo
                anterior[novo] = (atual, acao, custo)
                if novo not in fronteira:
                    fronteira.append(novo)

    return None #rodou tudo , sem solução


def desenhar(grid, agente, pacote, destino):
    n = len(grid)
    print("    " + " ".join(str(j % 10) for j in range(n)))
    for i in range(n):
        texto = ""
        for j in range(n):
            if (i, j) == agente:
                texto = texto + "A "
            elif (i, j) == pacote:
                texto = texto + "P "
            elif (i, j) == destino:
                texto = texto + "X "
            else:
                texto = texto + grid[i][j] + " "
        print(f"{i:3d} {texto}")
    print("A=agente  P=pacote  X=destino  #=obstáculo  $=pedágio")


def main():
    n = int(input("Dimensão do grid: "))

    grid = criar_grid(n)
    while contar_livres(grid) < 3:
        grid = criar_grid(n)

    agente = sortear_posicao_livre(grid, [])
    pacote = sortear_posicao_livre(grid, [agente])
    destino = sortear_posicao_livre(grid, [agente, pacote])

    desenhar(grid, agente, pacote, destino)

    inicio = (agente[0], agente[1], pacote[0], pacote[1])
    plano = buscar(grid, inicio, destino)

    if plano is None:
        print("\nNão existe solução para este mundo.")
        return

    total = 0
    for acao, custo in plano:
        total = total + custo
    print(f"\nPlano ótimo: {len(plano)} ações, custo total {total}")
    numero = 1
    for acao, custo in plano:
        print(f"{numero}. {acao} (custo {custo})")
        numero = numero + 1


if __name__ == "__main__":
    main()