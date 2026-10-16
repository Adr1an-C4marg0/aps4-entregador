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
Recomendo fortemente testar os 2 códigos!
