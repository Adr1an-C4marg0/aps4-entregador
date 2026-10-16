# Exemplos de execução

Todos os exemplos abaixo são saídas **reais** de
`python main.py --cli -n <N> -s <semente>` na versão entregue. Use a
mesma semente para reproduzi-los.

Legenda do desenho ASCII:

| símbolo | significado          |
|---------|----------------------|
| `A`     | agente (boneco)      |
| `P`     | pacote (caixa)       |
| `X`     | destino da entrega   |
| `#`     | obstáculo (preto)    |
| `$`     | célula de pedágio    |
| `.`     | célula livre         |

---

## Exemplo 1 — grid 4x4 (semente `mini`)

```
Mundo gerado: grid 4x4 | obstáculos: 2 | pedágios: 0 | agente: (2, 1) | pacote: (1, 1) | destino: (3, 1)

    0 1 2 3
  0 . . . .
  1 # P . .
  2 # A . .
  3 . X . .

Solução ótima encontrada em 0.1 ms
Número de ações: 5
Custo total: 5
Plano resumido: CIMA, PEGAR, BAIXO x2, ENTREGAR

Plano detalhado:
    1. CIMA      custo 1
    2. PEGAR     custo 1
    3. BAIXO     custo 1
    4. BAIXO     custo 1
    5. ENTREGAR  custo 1
```

Sem pedágio, o custo é exatamente o número de ações (5): 3 movimentos
(Manhattan 1 + Manhattan 2) e as ações PEGAR e ENTREGAR.

---

## Exemplo 2 — grid 10x10 com obstáculos e pedágios (semente `ia2026`)

```
Mundo gerado: grid 10x10 | obstáculos: 15 | pedágios: 10 | agente: (0, 7) | pacote: (2, 2) | destino: (9, 7)

    0 1 2 3 4 5 6 7 8 9
  0 . . . . . . . A . .
  1 . . # # . . . $ . .
  2 . # P . # . # . . .
  3 . . . # . . . . # .
  4 . . . $ . . . . . .
  5 . $ # $ . . . . . #
  6 # . . . . . . $ . .
  7 . . . . . . . . $ $
  8 . $ . # # . # $ . .
  9 . # . . . $ # X . .

Solução ótima encontrada em 0.5 ms
Número de ações: 27
Custo total: 31
Plano resumido: ESQUERDA x6, BAIXO, ESQUERDA, BAIXO x2, DIREITA x2, CIMA, PEGAR, BAIXO x2, DIREITA x4, BAIXO x3, DIREITA, BAIXO x2, ENTREGAR
```

Repare nas ações de custo 3 do plano detalhado (trechos em `$`):

```
   17. DIREITA   custo 3   <- pedágio
   25. BAIXO     custo 3   <- pedágio
```

27 ações, mas custo total 31 = 27 ações + 2 pedágios (2 x 2). O plano
encontrado é o de **custo mínimo**: a busca avaliou inclusive desvios
maiores que evitam todos os pedágios.

---

## Exemplo 3 — grid 20x20 (semente `20x20`)

```
Mundo gerado: grid 20x20 | obstáculos: 58 | pedágios: 28 | agente: (14, 0) | pacote: (2, 1) | destino: (18, 3)

    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9
  0 . . . . $ . . . $ . # . . . . . . . . .
  1 . . . # . # . . . . # . . . . . # . . .
  2 $ P . . . . . . . . . . . . . $ . . # $
  3 . . . $ . . . . . . . . . . . . . . . #
  4 $ . . . . . . . . . # . . . . . . . . .
  5 . . . . . # . $ . . . . . . . . # # $
  6 . . . . # . # . # $ . $ . . $ . # . . .
  7 . . . # . . . . # # . $ . . . . . # . #
  8 . . . . . . # . . # . # . . . # . . . .
  9 . . . . . . . . . . . # . # . . . # # .
 10 # # . . # # . . $ . . $ # . . . # . . .
 11 $ . # . . . . $ . # # # . . # . . . . .
 12 . . . . . . . . . . . . . . . . . . . #
 13 # . . . . . . . . . . . . . . . . . . .
 14 A . . . . . # . . . $ . . . . $ # . . .
 15 . # . . . . . . $ . . # . . . . . . . .
 16 . . # $ . $ . $ . . . . # . . . . . $ #
 17 . . . . . . . . . . . # . # $ $ # . . .
 18 . . . X . . . $ . . # . . # # . . . . .
 19 # . . . . . # . . . . . # . $ . . . # .

Solução ótima encontrada em 0.8 ms
Número de ações: 37
Custo total: 39
Plano resumido: DIREITA, CIMA x2, DIREITA x2, CIMA x4, ESQUERDA, CIMA x6, ESQUERDA, PEGAR, DIREITA, BAIXO x6, DIREITA, BAIXO x10, ENTREGAR
```

Custo total 39 = 37 ações + 1 pedágio (a ação 34, `BAIXO`, custa 3).

---

## Exemplo 4 — estado **sem solução** (grid 8x8, semente `8-21`)

```
Mundo gerado: grid 8x8 | obstáculos: 14 | pedágios: 3 | agente: (6, 2) | pacote: (2, 2) | destino: (7, 7)

    0 1 2 3 4 5 6 7
  0 # . . . $ # # #
  1 . . . . # . . .
  2 . . P . . # . .
  3 . . . . # . # .
  4 $ . . . . . . .
  5 # $ . . . . . .
  6 # . A . # . # #
  7 . . . . . . # X

SEM SOLUÇÃO: não existe plano que entregue o pacote no destino
(o pacote ou o destino está cercado/inacessível para o agente).
```

O destino (7, 7) está cercado pelos obstáculos de (6, 7) e (7, 6), e o
pacote está em uma região que não se conecta a ele. O programa detecta a
inacessibilidade na geração do mundo (aviso no painel de status) e
confirma ao tentar resolver. Basta gerar outro mundo (ou aumentar a
dimensão) para obter um cenário solúvel.

---

## Exemplo 5 — interface gráfica

```
python main.py
```

Fluxo típico:

1. digite a dimensão (ex.: 12) e clique em **Gerar mundo** — o canvas
   desenha o grid sorteado; o status mostra a quantidade de obstáculos,
   pedágios e as posições das peças (com aviso "ATENÇÃO: estado sem
   solução" quando for o caso);
2. clique em **Resolver (A\*)** — o plano aparece na lista lateral, com
   o custo de cada passo, o custo total e o trecho restante destacado
   em amarelo no canvas;
3. clique em **Executar plano** — o agente se move no ritmo escolhido,
   mostrando a ação corrente e o custo acumulado; **Parar** interrompe.

## Exemplo 6 — mapas grandes (40x40)

Com dimensão 40, o mundo nasce com células pequenas o bastante para
caber na janela (o tamanho é `min(largura, altura) / N` × zoom):

```
$ python main.py
# dimensão = 40, semente = gigante, Gerar mundo
```

- **janela pequena (~360 px)**: célula 9 px → mapa 360 x 360 px, todo
  visível;
- **janela 1400 x 900**: célula 17 px → mapa 680 x 680 px, todo visível;
- **zoom 3,0x**: célula 52 px → mapa 2080 x 2080 px, maior que a tela —
  aí valem as **barras de rolagem** e o **arrastar com o mouse**;
- **Tela cheia (F11)**: o canvas ocupa o monitor inteiro; **Esc** volta
  para a janela;
- **rodinha** rola na vertical, **Shift + rodinha** na horizontal e
  **Ctrl + rodinha** (ou as teclas `+`/`-`) dá zoom.

Mesmo no mapa 40x40 (com 58 obstáculos e 28 pedágios), o A* resolve em
poucos ms e o plano é animado passo a passo.
