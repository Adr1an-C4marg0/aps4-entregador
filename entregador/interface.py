"""Interface gráfica (Tkinter) do problema do entregador em mundo grid.

Permite ao usuário:
- definir a dimensão (sempre quadrada) do grid;
- gerar um mundo aleatório (obstáculos, pedágios, agente, pacote e
  destino sorteados), com semente opcional para reproduzir um cenário;
- calcular o plano ótimo com o A*;
- executar o plano passo a passo, vendo o custo acumulado;
- ser informado quando o estado inicial gerado **não tem solução**.

Visualização (grades grandes):
- janela redimensionável e **tela cheia** (botão ou tecla F11; Esc sai);
- **arrastar com o mouse** (botão esquerdo) para mover o mundo, rodinha
  do mouse para rolar (Shift + rodinha rola na horizontal);
- **zoom** pelo controle deslizante, pelas teclas +/- ou por
  Ctrl + rodinha do mouse;
- o tamanho inicial das células se ajusta à área visível, então um grid
  40x40 já nasce cabendo na janela.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import List, Optional, Set, Tuple

from .busca import Plano, busca
from .mundo import Celula, Estado, MundoGrid

CORES = {
    "livre": "#ffffff",
    "obstaculo": "#212121",
    "pedagio": "#9e9e9e",
    "agente": "#2e7d32",
    "pacote": "#0d47a1",
    "destino": "#b71c1c",
    "rota": "#fff59d",
    "grade": "#cfd8dc",
    "texto": "#37474f",
    "fundo": "#eceff1",
}

TAMANHO_MINIMO_CELULA = 6
TAMANHO_MAXIMO_CELULA = 80


class Aplicativo:
    """Janela principal da aplicação."""

    def __init__(self, raiz: tk.Tk) -> None:
        self.raiz = raiz
        raiz.title("APS — Entregador em mundo grid (plano ótimo com pedágios)")
        raiz.resizable(True, True)
        raiz.minsize(760, 560)
        raiz.configure(padx=8, pady=8, background=CORES["fundo"])

        self.mundo: Optional[MundoGrid] = None
        self.plano: Optional[Plano] = None
        self.estado_atual: Optional[Estado] = None
        self.indice = 0                # passo atual da execução do plano
        self.agendado = None           # id retornado por root.after
        self.tela_cheia = False
        self.reagendado: Optional[str] = None

        self.var_dimensao = tk.IntVar(value=10)
        self.var_semente = tk.StringVar()
        self.var_velocidade = tk.DoubleVar(value=4.0)
        self.var_zoom = tk.DoubleVar(value=1.0)
        self.var_status = tk.StringVar(value="Clique em 'Gerar mundo'.")
        self.var_acao = tk.StringVar(value="")
        self.var_custo = tk.StringVar(value="")
        self.var_tamanho = tk.StringVar(value="")

        self._montar_controles()
        self._montar_area()
        self._montar_rodape()
        self._atalhos()
        self.gerar_mundo()

    # ------------------------------------------------------------------ #
    # Montagem da interface
    # ------------------------------------------------------------------ #
    def _montar_controles(self) -> None:
        quadro = ttk.LabelFrame(self.raiz, text="Configuração do mundo", padding=8)
        quadro.grid(row=0, column=0, columnspan=2, sticky="ew")

        ttk.Label(quadro, text="Dimensão (N):").grid(row=0, column=0)
        ttk.Spinbox(quadro, from_=2, to=60, width=5, textvariable=self.var_dimensao).grid(
            row=0, column=1, padx=(2, 12)
        )

        ttk.Label(quadro, text="Semente:").grid(row=0, column=2)
        ttk.Entry(quadro, width=8, textvariable=self.var_semente).grid(row=0, column=3, padx=(2, 12))

        ttk.Button(quadro, text="Gerar mundo", command=self.gerar_mundo).grid(row=0, column=4)
        ttk.Button(quadro, text="Resolver (A*)", command=self.resolver).grid(row=0, column=5, padx=4)
        ttk.Button(quadro, text="Executar plano", command=self.executar_plano).grid(row=0, column=6)
        ttk.Button(quadro, text="Parar", command=self.parar).grid(row=0, column=7, padx=4)
        ttk.Button(quadro, text="Tela cheia (F11)", command=self.alternar_tela_cheia).grid(
            row=0, column=8, padx=4
        )

        ttk.Label(quadro, text="Velocidade:").grid(row=1, column=0, pady=(8, 0))
        ttk.Scale(
            quadro, from_=1, to=20, orient="horizontal", length=170,
            variable=self.var_velocidade,
        ).grid(row=1, column=1, columnspan=3, sticky="w", pady=(8, 0))

        ttk.Label(quadro, text="Zoom:").grid(row=1, column=4, pady=(8, 0))
        # tk.Scale (e não ttk.Scale) para poder usar resolução de 0.1 no zoom.
        tk.Scale(
            quadro, from_=0.4, to=6.0, orient="horizontal", length=140, resolution=0.1,
            variable=self.var_zoom, command=lambda _v: self.desenhar(),
            sliderlength=18, showvalue=False,
        ).grid(row=1, column=5, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Label(quadro, textvariable=self.var_tamanho, foreground=CORES["texto"]).grid(
            row=1, column=7, columnspan=2, pady=(8, 0)
        )

    def _montar_area(self) -> None:
        """Canvas do mundo dentro de um frame com barras de rolagem."""
        moldura = ttk.Frame(self.raiz, padding=(0, 10, 0, 0))
        moldura.grid(row=1, column=0, sticky="nsew")
        self.raiz.rowconfigure(1, weight=1)
        self.raiz.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(moldura, bg=CORES["grade"], highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        barra_v = ttk.Scrollbar(moldura, orient="vertical", command=self.canvas.yview)
        barra_h = ttk.Scrollbar(moldura, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=barra_h.set, yscrollcommand=barra_v.set)
        barra_v.grid(row=0, column=1, sticky="ns")
        barra_h.grid(row=1, column=0, sticky="ew")
        moldura.rowconfigure(0, weight=1)
        moldura.columnconfigure(0, weight=1)

        # Arrastar o mundo com o mouse.
        self.canvas.bind("<ButtonPress-1>", self._iniciar_arraste)
        self.canvas.bind("<B1-Motion>", self._arrastar)
        self.canvas.bind("<ButtonRelease-1>", self._fim_arraste)
        # Rodinha do mouse: vertical; Shift + rodinha: horizontal; Ctrl + rodinha: zoom.
        self.canvas.bind("<MouseWheel>", self._roda_do_mouse)
        self.canvas.bind("<Shift-MouseWheel>", self._roda_do_mouse)
        self.canvas.bind("<Control-MouseWheel>", self._roda_do_mouse)
        # Reajusta o tamanho das células quando a janela muda de tamanho.
        self.canvas.bind("<Configure>", self._ao_redimensionar)

        # Painel lateral: status + plano.
        lateral = ttk.Frame(self.raiz, padding=(10, 10, 0, 0))
        lateral.grid(row=1, column=1, sticky="nsew")
        lateral.rowconfigure(2, weight=1)
        lateral.columnconfigure(0, weight=1)
        ttk.Label(
            lateral, textvariable=self.var_status, wraplength=320, justify="left",
            foreground=CORES["texto"],
        ).grid(row=0, column=0, sticky="ew")

        ttk.Label(lateral, text="Plano ótimo (A*):").grid(row=1, column=0, sticky="w", pady=(12, 4))
        barra = ttk.Scrollbar(lateral, orient="vertical")
        self.lista_plano = tk.Listbox(
            lateral, width=30, height=30, yscrollcommand=barra.set, font=("Consolas", 9)
        )
        barra.config(command=self.lista_plano.yview)
        self.lista_plano.grid(row=2, column=0, sticky="nsew")
        barra.grid(row=2, column=1, sticky="ns")

    def _montar_rodape(self) -> None:
        rodape = ttk.Frame(self.raiz, padding=(0, 8, 0, 0))
        rodape.grid(row=2, column=0, columnspan=2, sticky="ew")
        rodape.columnconfigure(0, weight=1)
        rodape.columnconfigure(1, weight=1)

        ttk.Label(rodape, textvariable=self.var_acao, foreground=CORES["agente"]).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(rodape, textvariable=self.var_custo, foreground=CORES["destino"]).grid(
            row=0, column=1, sticky="e"
        )

        legenda = ttk.Frame(rodape)
        legenda.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        itens = [
            ("agente", "agente"), ("pacote", "pacote"), ("destino", "destino (X)"),
            ("obstaculo", "obstáculo"), ("pedagio", "pedágio (+2)"), ("rota", "rota do plano"),
        ]
        for coluna, (chave, texto) in enumerate(itens):
            tk.Label(legenda, bg=CORES[chave], width=2, relief="solid").grid(
                row=0, column=coluna * 2, padx=(0, 3)
            )
            ttk.Label(legenda, text=texto).grid(row=0, column=coluna * 2 + 1, padx=(0, 12))

    def _atalhos(self) -> None:
        """Atalhos de teclado da janela."""
        self.raiz.bind("<F11>", self.alternar_tela_cheia)
        self.raiz.bind("<Escape>", lambda _e: self.sair_da_tela_cheia())
        for tecla in ("<plus>", "<KP_Add>", "<equal>"):
            self.raiz.bind(tecla, lambda _e: self._zoom_relativo(1.25))
        for tecla in ("<minus>", "<KP_Subtract>"):
            self.raiz.bind(tecla, lambda _e: self._zoom_relativo(0.8))

    # ------------------------------------------------------------------ #
    # Visualização: arrastar, rolar, zoom, tela cheia
    # ------------------------------------------------------------------ #
    def _iniciar_arraste(self, evento: tk.Event) -> None:
        self.canvas.scan_mark(evento.x, evento.y)
        self.canvas.configure(cursor="fleur")

    def _arrastar(self, evento: tk.Event) -> None:
        self.canvas.scan_dragto(evento.x, evento.y, gain=1)

    def _fim_arraste(self, _evento: tk.Event) -> None:
        self.canvas.configure(cursor="")

    def _roda_do_mouse(self, evento: tk.Event) -> None:
        if self.mundo is None:
            return
        if evento.state & 0x4:  # Ctrl pressionado: zoom
            self._zoom_relativo(1.25 if getattr(evento, "delta", 0) > 0 else 0.8)
            return
        voltas = int(getattr(evento, "delta", 0) / 120) or (1 if getattr(evento, "num", 0) == 5 else -1)
        if evento.state & 0x1:  # Shift pressionado: rolagem horizontal
            self.canvas.xview_scroll(-voltas, "units")
        else:
            self.canvas.yview_scroll(-voltas, "units")

    def _zoom_relativo(self, fator: float) -> None:
        novo = min(6.0, max(0.4, self.var_zoom.get() * fator))
        self.var_zoom.set(round(novo, 2))
        self.desenhar()

    def alternar_tela_cheia(self, _evento=None) -> None:
        self.tela_cheia = not self.tela_cheia
        self.raiz.attributes("-fullscreen", self.tela_cheia)
        self._atualizar_indicador()

    def sair_da_tela_cheia(self) -> None:
        if self.tela_cheia:
            self.tela_cheia = False
            self.raiz.attributes("-fullscreen", False)
        self._atualizar_indicador()

    def _atualizar_indicador(self) -> None:
        modo = "tela cheia" if self.tela_cheia else "janela"
        self.var_tamanho.set(f"({modo})")

    def _ao_redimensionar(self, _evento=None) -> None:
        """Reagenda o redesenho para não fazê-lo a cada pixel redimensionado."""
        if self.reagendado is None:
            self.reagendado = self.raiz.after_idle(self._reajustar)

    def _reajustar(self) -> None:
        self.reagendado = None
        if self.mundo is not None:
            self.desenhar()

    # ------------------------------------------------------------------ #
    # Ações do usuário
    # ------------------------------------------------------------------ #
    def gerar_mundo(self) -> None:
        self.parar()
        try:
            dimensao = int(self.var_dimensao.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Dimensão inválida", "Informe um número inteiro >= 2.")
            return

        semente = self.var_semente.get().strip() or None
        try:
            self.mundo = MundoGrid.gerar(dimensao, semente)
        except ValueError as erro:
            messagebox.showerror("Mundo inválido", str(erro))
            return

        self.plano = None
        self.indice = 0
        self.lista_plano.delete(0, tk.END)
        self.estado_atual = self.mundo.estado_inicial()
        self.var_acao.set("")
        self.var_custo.set("")

        aviso = ""
        if not self.mundo.solucionavel():
            aviso = "   |   ATENÇÃO: estado sem solução"
        self.var_status.set(self.mundo.resumo() + aviso)
        self._atualizar_indicador()
        self.desenhar()

    def resolver(self) -> None:
        if self.mundo is None:
            messagebox.showinfo("Nada a resolver", "Gere um mundo primeiro.")
            return
        self.parar()

        self.plano = busca(self.mundo)
        self.indice = 0
        self.estado_atual = self.mundo.estado_inicial()
        self.lista_plano.delete(0, tk.END)

        if self.plano is None:
            self.var_status.set(
                "SEM SOLUÇÃO: não existe plano para entregar o pacote no destino. "
                "O pacote e/ou o destino estão inacessíveis (cercados por obstáculos "
                "ou isolados na borda). Gere outro mundo ou mude a dimensão."
            )
            messagebox.showinfo(
                "Sem solução",
                "O estado inicial gerado não possui solução:\n"
                "o agente não consegue alcançar o pacote ou o destino.",
            )
            self.desenhar()
            return

        tempo = getattr(self.plano, "tempo_segundos", 0.0) * 1000
        for numero, (acao, custo) in enumerate(zip(self.plano.acoes, self.plano.custos_passo), start=1):
            self.lista_plano.insert(tk.END, f"{numero:3d}. {acao:<9s} custo {custo:g}")
        self.var_status.set(
            f"{self.mundo.resumo()}\n"
            f"Solução ótima: {len(self.plano)} ações, custo total {self.plano.custo_total:g} "
            f"({self.plano.expandidos} estados expandidos, {tempo:.1f} ms).\n"
            f"Plano: {self.plano.resumir()}"
        )
        self.var_custo.set(f"Custo do plano: {self.plano.custo_total:g}")
        self.desenhar()

    def executar_plano(self) -> None:
        if self.plano is None:
            self.resolver()
        if self.plano is None:
            return
        if self.indice >= len(self.plano.estados) - 1:
            self.indice = 0
            self.estado_atual = self.plano.estados[0]
            self.var_acao.set("")
            self.var_custo.set(f"Custo do plano: {self.plano.custo_total:g}")
            self.desenhar()
        self._agendar()

    def parar(self) -> None:
        if self.agendado is not None:
            self.raiz.after_cancel(self.agendado)
            self.agendado = None

    def _agendar(self) -> None:
        if self.plano is None or self.indice >= len(self.plano.estados) - 1:
            return
        velocidade = max(1.0, float(self.var_velocidade.get()))
        self.agendado = self.raiz.after(int(1000.0 / velocidade), self._passo)

    def _passo(self) -> None:
        if self.plano is None:
            return
        if self.indice >= len(self.plano.estados) - 1:
            self.agendado = None
            return

        self.indice += 1
        acao = self.plano.acoes[self.indice - 1]
        custo = self.plano.custos_passo[self.indice - 1]
        acumulado = sum(self.plano.custos_passo[: self.indice])
        self.estado_atual = self.plano.estados[self.indice]
        self.var_acao.set(f"Passo {self.indice}: {acao} (custo {custo:g})")
        self.var_custo.set(f"Custo acumulado: {acumulado:g} / {self.plano.custo_total:g}")

        self.lista_plano.selection_clear(0, tk.END)
        self.lista_plano.selection_set(self.indice - 1)
        self.lista_plano.see(self.indice - 1)
        self.desenhar()
        self._agendar()

    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    # Desenho
    # ------------------------------------------------------------------ #
    def _tamanho_celula(self) -> int:
        """Tamanho da célula: ajuste automático à área visível x zoom."""
        if self.mundo is None:
            return getattr(self, "tam_celula", TAMANHO_MAXIMO_CELULA)
        n = self.mundo.dimensao
        largura = max(self.canvas.winfo_width() - 4, 120)
        altura = max(self.canvas.winfo_height() - 4, 120)
        base = min(largura / n, altura / n)
        zoom = max(0.4, float(self.var_zoom.get()))
        return int(max(TAMANHO_MINIMO_CELULA, min(TAMANHO_MAXIMO_CELULA, base * zoom)))

    def _celulas_rota(self) -> Set[Celula]:
        """Células ainda não visitadas do plano (para destacar o caminho)."""
        if self.plano is None:
            return set()
        return {estado[0] for estado in self.plano.estados[self.indice:]}

    def desenhar(self) -> None:
        """Redesenha o mundo inteiro no canvas e ajusta a área de rolagem."""
        self.canvas.delete("all")
        mundo, estado = self.mundo, self.estado_atual
        if mundo is None or estado is None:
            return

        n = mundo.dimensao
        tam = self._tamanho_celula()
        self.tam_celula = tam
        modo = "tela cheia" if self.tela_cheia else "janela"
        self.var_tamanho.set(f"célula {tam}px | zoom {self.var_zoom.get():.1f}x | {modo}")
        lado = n * tam
        self.canvas.configure(scrollregion=(0, 0, lado, lado))

        rota = self._celulas_rota()
        agente, pacote, carregando = estado
        pos_pacote = mundo.posicao_pacote(estado)
        mostrar_texto = tam >= 13

        for i in range(n):
            for j in range(n):
                celula = (i, j)
                x0, y0 = j * tam, i * tam
                x1, y1 = x0 + tam, y0 + tam

                cor = CORES["livre"]
                if celula in mundo.obstaculos:
                    cor = CORES["obstaculo"]
                elif celula in mundo.pedagios:
                    cor = CORES["pedagio"]
                elif celula in rota:
                    cor = CORES["rota"]
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=cor, outline=CORES["grade"])

                if celula in mundo.pedagios and celula not in mundo.obstaculos and mostrar_texto:
                    self.canvas.create_text(
                        (x0 + x1) / 2, (y0 + y1) / 2, text="$", fill="#ffffff",
                        font=("TkDefaultFont", max(7, tam // 3), "bold"),
                    )

                if celula == mundo.destino:
                    self._desenhar_x(x0, y0, x1, y1)

                if celula == pos_pacote and not (carregando and celula == agente):
                    self._desenhar_caixa(x0, y0, x1, y1)

        # Agente por cima de tudo; se carrega o pacote, a caixa vem junto.
        i, j = agente
        x0, y0 = j * tam, i * tam
        x1, y1 = x0 + tam, y0 + tam
        self._desenhar_agente(x0, y0, x1, y1)
        if carregando:
            self._desenhar_caixa(x0, y0, x1, y1)

    def _desenhar_x(self, x0: float, y0: float, x1: float, y1: float) -> None:
        margem = max(2.0, self.tam_celula / 5)
        self.canvas.create_line(
            x0 + margem, y0 + margem, x1 - margem, y1 - margem,
            fill=CORES["destino"], width=3,
        )
        self.canvas.create_line(
            x0 + margem, y1 - margem, x1 - margem, y0 + margem,
            fill=CORES["destino"], width=3,
        )

    def _desenhar_caixa(self, x0: float, y0: float, x1: float, y1: float) -> None:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        lado = self.tam_celula * 0.5
        self.canvas.create_rectangle(
            cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2,
            fill=CORES["pacote"], outline="#082a5e", width=2,
        )

    def _desenhar_agente(self, x0: float, y0: float, x1: float, y1: float) -> None:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        r = self.tam_celula * 0.32
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r, fill=CORES["agente"],
            outline="#14431a", width=2,
        )


def main() -> None:
    raiz = tk.Tk()
    Aplicativo(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()


