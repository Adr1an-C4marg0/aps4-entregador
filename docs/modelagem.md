# Documentação da solução

## 1. Formulação do problema

- **Mundo**: grid quadrado `N x N` (`N >= 2`), com:
  - células livres (brancas);
  - **obstáculos** (pretos): intransponíveis;
  - **pedágios** (cinzas): células em que executar uma ação custa +2;
  - uma célula com o **pacote**;
  - uma célula de **destino** (X);
  - um único **agente** (o boneco).
- **Estado inicial**: agente em sua casa, pacote na célula de origem,
  agente sem o pacote.
- **Objetivo**: pacote na célula de destino.
- **Agente** (um só): move-se para cima, baixo, esquerda e direita
  (uma célula por ação), pode **pegar** o pacote (que passa a andar com
  o agente) e **entregar** o pacote (ele fica na célula onde o agente
  está).
- **Custo**: toda ação custa 1. Se a ação é executada em uma célula de
  pedágio, o custo real é `custo + 2` (ou seja, 3).
- **Obstáculo/borda**: mover-se para fora do grid ou contra um
  obstáculo tem como consequência permanecer na mesma célula. Como isso
  nunca reduz o custo de um plano ótimo, essas ações não são geradas
  pela função sucessora (o espaço de busca fica menor sem perder
  soluções).

### 1.1 Estado

Um estado é a tupla `(agente, pacote, carregando)`:

| campo       | significado                                                          |
|-------------|----------------------------------------------------------------------|
| `agente`    | célula `(linha, coluna)` do agente                                   |
| `pacote`    | célula em que o pacote está no chão (quando carregado, a célula em que foi pego) |
| `carregando`| `True` quando o pacote está com o agente — ele se move junto com ele |

O **teste de objetivo** é: `não carregando` e `pacote == destino`, ou
seja, a ação ENTREGAR foi executada sobre o destino.

### 1.2 Função sucessora

A partir de `(agente, pacote, carregando)`:

- **Movimentos** (CIMA/BAIXO/ESQUERDA/DIREITA): se a célula de destino
  está dentro do grid e não é obstáculo, gera
  `(nova_célula, nova_célula se carregando senão pacote, carregando)`
  com custo `1 (+2 se a célula de destino é pedágio)`.
- **PEGAR**: aplicável se `não carregando` e `agente == pacote`;
  resultado: `(agente, pacote, True)`, custo `1 (+2 se a célula atual
  é pedágio)`.
- **ENTREGAR**: aplicável se `carregando` e `agente == destino`;
  resultado: `(agente, destino, False)`, custo `1 (+2 se aplicável)`.

**Grau de ramificação**: até 6 (4 movimentos, PEGAR e ENTREGAR).
**Tamanho do espaço de estados**: `2 * N^2 * (N^2 - 1)` no máximo —
para `N = 20`, cerca de 320 mil estados, trivial para A*.

## 2. Busca do plano ótimo

A busca é o **A\\*** (`entregador/busca.py`), com fila de prioridade
(heap) sobre `f = g + h`. Com a heurística zerada, o mesmo código
implementa a **busca de custo uniforme (UCS)** — usada nos testes para
verificar a otimalidade.

### 2.1 Heurística admissível

```
h(estado) = dist(agente, posição_do_pacote)
          + dist(posição_do_pacote, destino)
          + 1  (se ainda falta PEGAR)
          + 1  (ENTREGAR é sempre necessária)
```

`dist` é a distância de Manhattan.

**Admissibilidade**: cada ação move o agente em no máximo uma célula,
logo são necessários ao menos `dist(agente, pacote)` movimentos para
alcançar o pacote e ao menos `dist(pacote, destino)` movimentos para
levá-lo ao destino; as ações PEGAR e ENTREGAR são obrigatórias em
qualquer plano. Como pedágios **aumentam** o custo real das ações,
`h` nunca superestima o custo ótimo. Como `h` também é consistente
(cada ação reduz `h` em no máximo o próprio custo), o A* encontra o
plano de **custo mínimo** sem reabrir estados.

## 3. Detecção de "sem solução"

Um estado inicial pode ser insolúvel — por exemplo, se obstáculos
isolam o pacote do agente, ou o destino do pacote. Duas proteções:

1. `MundoGrid.solucionavel()`: busca em largura de conectividade
   (ignorando pedágios, que custam caro mas não bloqueiam). Se o agente
   não alcança o pacote, ou do pacote não se alcança o destino, o mundo
   é insolúvel — a interface avisa já na geração.
2. A própria busca: se a fronteira é esvaziada sem atingir o objetivo,
   `busca()` retorna `None` e o programa informa **"SEM SOLUÇÃO"**.

## 4. Geração aleatória do mundo

`MundoGrid.gerar(dimensao, semente)`:

1. embaralha todas as `N^2` células com `random.Random(semente)`;
2. sorteia a **quantidade** de obstáculos e de pedágios e consome as
   primeiras células embaralhadas; as 3 células restantes seguintes
   viram agente, pacote e destino (nunca sobrepostas a nada).

Regra das quantidades (sempre garantindo as 3 células das peças):

| elemento   | faixa                                    | mapa pequeno (N=2) | mapa pequeno (N=3) |
|------------|------------------------------------------|--------------------|--------------------|
| obstáculos | entre `max(1, 10%)` e `25%` das células  | exatamente 1       | 1 ou 2             |
| pedágios   | entre `4%` e `10%` das células restantes | 0                  | 0                  |

O **piso de 1 obstáculo** existe porque a porcentagem pura não gerava
nada em mapas pequenos: com `N = 3` (9 células), `10% = 0,9` e
`22% = 1,98` produziam 0 ou 1 obstáculo e `N = 2` nunca gerava nenhum.
Em `N = 2` ainda é impossível haver pedágio com sobra de células
(restaria apenas 1 célula, e ela é mais útil como obstáculo).

A **semente** é opcional: sem ela, cada execução gera um mundo novo; com
ela, o cenário é reproduzível (ótimo para testes e exemplos).

## 5. Interface gráfica

`entregador/interface.py` (Tkinter, sem dependências externas):

- campo da **dimensão** (2 a 60) e campo de **semente**;
- botões **Gerar mundo**, **Resolver (A\*)**, **Executar plano**,
  **Parar** e **Tela cheia**, além de controles de velocidade e de zoom;
- **canvas** com o grid: branco = livre, preto = obstáculo, cinza =
  pedágio (`$`), verde = agente, azul = pacote, vermelho = destino (X) e
  amarelo = trecho ainda não percorrido do plano;
- **lista do plano** (ação e custo de cada passo, destacando o passo
  atual), com custo acumulado e total;
- mensagem explícita de **sem solução** quando for o caso.

### 5.1 Visualização de mapas grandes

Problema: para `N` grande (ex.: 40), o mapa é maior que qualquer tela.
Solução adotada:

1. **Janela redimensionável + tela cheia**: `raiz.resizable(True, True)`
   com `minsize`, e `attributes("-fullscreen", ...)` alternado pelo
   botão **Tela cheia (F11)** (Esc volta para janela). O canvas usa
   `sticky="nsew"` com pesos de linha/coluna (`rowconfigure`/
   `columnconfigure`), então ocupa todo o espaço disponível.
2. **Tamanho automático das células** com zoom:
   `tam = clamp(min(largura/N, altura/N) * zoom, 6, 80)`, onde largura e
   altura vêm do canvas (`winfo_width/height`). Assim um grid 40x40 já
   nasce cabendo na janela, e o zoom amplia quando o usuário quiser
   detalhe (aí o mundo fica maior que a tela e a rolagem entra em ação).
3. **Rolagem nativa** com `scrollregion` e barras de rolagem ligadas a
   `xview`/`yview`.
4. **Arrastar com o mouse**: `<ButtonPress-1>` chama `scan_mark` e
   `<B1-Motion>` chama `scan_dragto` (mecanismo de pan do Tkinter sobre
   o `scrollregion`); o cursor vira `fleur` enquanto arrasta.
5. **Rodinha do mouse**: vertical (`yview_scroll`) e horizontal com
   Shift; **Ctrl + rodinha** aplica zoom.
6. **Redesenho econômico**: ao redimensionar a janela, o redesenho é
   reagendado com `after_idle` (uma vez por "respiro"), evitando
   redesenhar o mapa a cada pixel.

## 6. Verificação (testes automatizados)

`python -m pytest tests -q` — 37 testes, entre eles:

| teste                                       | o que garante                                  |
|---------------------------------------------|------------------------------------------------|
| `test_plano_otimo_sem_pedagio`              | custo mínimo = 8 no cenário simples 3x3        |
| `test_plano_otimo_com_pedagio`              | A* emparelha com UCS com pedágio no caminho    |
| `test_pedagio_vale_a_pena_quando_e_atalho`  | o A* opta por pagar pedágio quando compensa    |
| `test_sem_solucao_retorna_none`             | retorno `None` quando pacote fica isolado      |
| `test_sem_solucao_destino_cercado`          | retorno `None` quando o destino fica isolado   |
| `test_mundos_aleatorios_plano_valido_e_otimo` | em 16 mundos aleatórios: plano válido, custo igual ao do UCS e pacote no destino ao final |

Além disso, `busca.simular()` repete o plano em cima do modelo e
confere que o pacote termina no destino e que o custo informado é o
custo realmente pago.

## 7. Complexidade

- **Tempo** do A*: `O(E log V)`, com `V ≈ 2 N^4` estados e grau de
  ramificação ≤ 6. Medidas em CPU comum: ~1 ms para `N = 10` e ~1 ms
  para `N = 20` (ver `docs/exemplos.md`).
- **Espaço**: `O(V)` para as tabelas `g`, `origem` e a fronteira.
- A heurística forte (Manhattan) faz o A* expandir poucos estados:
  tipicamente apenas uma fração dos estados atingíveis.

## 8. Decisões de modelagem (registradas)

1. **Ação executada no destino do movimento**: o custo com pedágio é
   aplicado à célula em que o agente passa a estar (para PEGAR e
   ENTREGAR, a célula atual). O enunciado não fixa o detalhe; a escolha
   é uniforme para todas as ações.
2. **Movimentos inúteis não são gerados**: bater na borda ou no
   obstáculo deixaria o agente parado pagando custo — nunca ocorre em
   plano ótimo.
3. **ENTREGAR só sobre o destino**: deixar o pacote em outra célula
   nunca ajuda a atingir o objetivo, então essa ação só é gerada na
   célula de destino (reduz o espaço de busca sem perder otimalidade).
4. **Estado inclui a célula do pacote mesmo quando carregado**: mantém
   o estado canônico e evita ambiguidade na animação do plano.
