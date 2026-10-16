# APS — Entregador em mundo grid

## Mudanças e Melhorias
Inicialmente a forma feita na prova foi uma lista de listas com strings para criar uma matriz para representar o mundo.  
Então cada string estaria associada a um determiando valor, e como sucessors o agente conseguiria realizar as seguintes ações (Mover direita, esquerda, cima, baixo, pegar pacote, largar pacote)

Mas isso acaba gerando alguns problemas.
Inicialmente, acabei não definindo no init uma váriavel para representar se o agente está carregando o pacote ou não.
Outra questão era que o grid era criado aleatoriamente ao colocar as strings no mundo NxN. Entretanto, devido a isso, era impossível ocorrer que o agente começasse encima do destino, ou do pacote.
Então dessa vez, cada posição (x,y) associado a posição do agente, pacote, e destino são contabilizados em váriaveis separadas, corringo esse erro discreto e conseguindo conter todas as possibilidades.


## Aviso
Durante a criação dessa aps, fiz 2 formas, uma mais simples utilizando o conteúdo como base e outro código usando IA para a criação (Que por sinal ficou EXTREMAMENTE bem feito) 


## Descrição
Implementação de um agente que calcula o **plano ótimo** para pegar um
pacote e entregá-lo no destino em um mundo do tipo **grid quadrado**
com obstáculos e células de pedágio.

A solução vale para **qualquer dimensão quadrada** `N x N` (N ≥ 2): o
usuário escolhe `N`, e a posição do agente, do pacote, do destino, a
quantidade e a posição dos obstáculos e dos pedágios são **sorteadas**.
Quando o estado inicial gerado **não tem solução**, o programa diz isso
explicitamente (na interface e no modo texto).


## Requisitos
- Python 3.8+ (testado em 3.13)
- Tkinter (interface gráfica) — já vem instalado com o Python em
  Windows, macOS e na maioria das distribuições Linux
- `pytest` (apenas para rodar os testes): `pip install pytest`

## Como executar

### Interface gráfica

```
python "Feito por IA/main.py"
```

Na janela é possível:

1. definir a **dimensão (N)** do grid (sempre quadrada);
2. informar uma **semente** aleatória opcional (para reproduzir um
   cenário nos exemplos);
3. clicar em **Gerar mundo** — obstáculos, pedágios, agente, pacote e
   destino são sorteados; se o mundo for insolúvel, o status avisa;
4. clicar em **Resolver (A\*)** — aparece o plano ótimo, o custo total,
   o número de ações e de estados expandidos;
5. clicar em **Executar plano** — o agente é animado passo a passo, com
   a ação e o custo acumulado; **Parar** interrompe a animação.

### Visualizar mapas grandes (janela, tela cheia e arrastar)

- **Janela ou tela cheia**: a janela é redimensionável; o botão **Tela
  cheia (F11)** (ou a tecla F11) alterna para tela cheia e **Esc**
  volta para janela.
- **Arrastar**: pressione e arraste com o botão esquerdo do mouse sobre
  o mundo para movê-lo (também há barras de rolagem).
- **Rolagem**: rodinha do mouse (vertical) e Shift + rodinha
  (horizontal).
- **Zoom**: controle deslizante **Zoom**, teclas `+`/`-` ou
  Ctrl + rodinha.
- **Ajuste automático**: o tamanho das células é calculado pela área
  visível x zoom, então um grid 40x40 já nasce cabendo na janela; ao
  redimensionar, o tamanho é recalculado.

### Modo texto (útil para depuração e exemplos)

```
python "Feito por IA/main.py" --cli -n 10 -s ia2026
```

Imprime o desenho ASCII do mundo, o plano ótimo (resumido e detalhado,
com o custo de cada ação) e retorna código 1 quando não há solução.

### Testes

```
python -m pytest "Feito por IA/tests" -q
```

Os testes verificam: geração válida/reproduzível de mundos, custo de
pedágio, ações inválidas (borda/obstáculo), pegar/entregar, detecção de
"sem solução" e a **otimalidade** do A* (comparada com a busca de custo
uniforme) em vários mundos aleatórios.

## Estrutura do repositório

```
aps-entregador/
├── README.md
└── Feito por IA/
    ├── main.py                 # ponto de entrada (GUI ou --cli)
    ├── entregador/
    │   ├── __init__.py
    │   ├── mundo.py            # modelo: MundoGrid, estado, sucessores, custos
    │   ├── busca.py            # A* (ótimo), UCS e simulador do plano
    │   ├── interface.py        # interface gráfica Tkinter
    │   └── cli.py              # execução em linha de comando
    ├── tests/
    │   ├── test_mundo.py       # testes da modelagem
    │   └── test_busca.py       # testes da busca e da otimalidade
    └── docs/
        ├── modelagem.md        # documentação da solução
        └── exemplos.md         # exemplos de execução (com e sem solução)
```

## Resumo da solução

- **Estado**: `(posição do agente, posição do pacote, carregando?)`.
- **Ações**: CIMA, BAIXO, ESQUERDA, DIREITA, PEGAR, ENTREGAR.
- **Custo**: 1 por ação; +2 se a ação é executada em célula de pedágio
  (ou seja, 3 no total).
- **Busca**: A* com heurística admissível
  `distancia(agente, pacote) + distancia(pacote, destino) + 2`
  (as ações PEGAR e ENTREGAR são sempre necessárias), garantindo plano
  **ótimo**.
- **Sem solução**: detectada quando o pacote ou o destino está
  inacessível (obstáculos isolam regiões do grid).

Detalhes, justificativas e complexidade em
[docs/modelagem.md](<Feito por IA/docs/modelagem.md>); saídas reais de execução em
[docs/exemplos.md](<Feito por IA/docs/exemplos.md>).
