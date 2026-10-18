"""
Série temporal média do movimento (velocidade e deslocamento), do estímulo até o fim do
movimento: concêntrica e excêntrica comparadas dentro de cada carga.

As tentativas têm TR e TM diferentes; a média ponto a ponto alinhada no estímulo borraria
o perfil e rebaixaria o pico. Por isso cada tentativa é normalizada no tempo em três fases
(estímulo → início do movimento; início → pico de velocidade; pico → fim do movimento, com
início e fim a 5% do pico), e a média é feita ponto a ponto dentro de cada fase: primeiro
por participante, depois entre participantes. O eixo do tempo de cada curva é reescalado
para as durações médias das fases na condição; assim o início, o pico e o fim da curva
média caem no TR, no PV, no tempo até o pico e no TM médios.

Usa as tentativas válidas de dados_5pct.xlsx; saem também as com TR <= 0 (movimento
iniciado antes do estímulo), que não têm a primeira fase.

Uso: python3 serie_temporal.py   (rodar depois de medidas_brutas.py; precisa de dados/)
Saída: graficos/serie_temporal.png
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from graficos_cargas import DPI, EIXO, FUNDO, PASTA, TINTA
from medidas_brutas import FRAME_ESTIMULO, LIMIAR, SAIDA as ENTRADA, cruzamentos

N = 100  # pontos por fase
# % real da carga máxima: média (mínimo–máximo), como em graficos_cargas.PCT_REAL
CARGAS = {37: "33% (25–41)", 65: "68% (60–75)", 89: "91% (80–100)"}
ACOES = {"con": ("Concentric", "#2a78d6", "-"), "exc": ("Eccentric", "#eb6834", "--")}
LINHAS = {"vel": "Angular velocity (°/s)", "pos": "Angular displacement (°)"}
TEMPOS = ["TR", "TPV", "TM"]  # colunas de dados_5pct.xlsx (ms)


def fases(arq, acao):
    """Velocidade e deslocamento da tentativa reamostrados nas três fases; None se TR <= 0."""
    t = pd.read_csv(arq, sep="\t", decimal=",", header=None)
    t = t.dropna(axis=1, how="all").dropna().values
    pos, vel = t[:, 3], t[:, 4] * (-1 if acao == "con" else 1)
    k = 700 + int(np.argmax(vel[700:]))
    ini, fim = cruzamentos(vel, k, LIMIAR)
    if ini <= FRAME_ESTIMULO:
        return None
    x = np.concatenate([np.linspace(FRAME_ESTIMULO, ini, N, endpoint=False),
                        np.linspace(ini, k, N, endpoint=False), np.linspace(k, fim, N + 1)])
    frames = np.arange(len(vel))
    # deslocamento em relação à posição no estímulo, positivo nas duas ações
    desl = np.abs(np.interp(x, frames, pos) - pos[FRAME_ESTIMULO])
    return {"vel": np.interp(x, frames, vel), "pos": desl}


def eixo_tempo(c):
    """Tempo (ms desde o estímulo) dos pontos da curva média, com as durações médias das fases."""
    return np.concatenate([np.linspace(0, c["TR"], N, endpoint=False),
                           c["TR"] + np.linspace(0, c["TPV"], N, endpoint=False),
                           c["TR"] + np.linspace(c["TPV"], c["TM"], N + 1)])


def medias():
    """Curvas médias por condição (média das médias dos participantes) e durações médias."""
    t = pd.read_excel(ENTRADA, sheet_name="tentativas")
    t = t[t["valida"]]
    curvas, fora = {}, 0
    for (acao, carga), cond in t.groupby(["acao", "carga"]):
        por_suj = {nome: [] for nome in [*LINHAS, *TEMPOS]}
        for suj, d in cond.groupby("sujeito"):
            f = [fases(f"dados/{suj}/{a}", acao) for a in d["arquivo"]]
            ok = [x is not None for x in f]
            fora += len(f) - sum(ok)
            for nome in LINHAS:
                por_suj[nome].append(np.mean([x[nome] for x in f if x is not None], axis=0))
            for nome in TEMPOS:
                por_suj[nome].append(d.loc[ok, nome].mean())
        curvas[acao, carga] = {k: np.mean(v, axis=0) for k, v in por_suj.items()}
        curvas[acao, carga]["n"] = len(por_suj["TR"])
    return curvas, len(t), fora


def main():
    curvas, n_tent, fora = medias()
    alt = 0.2 + 3.0 * len(LINHAS)  # altura da figura (polegadas)
    fig, eixos = plt.subplots(len(LINHAS), 3, figsize=(12.4, alt), facecolor=FUNDO, sharex=True, sharey="row")
    for j, (carga, pct) in enumerate(CARGAS.items()):
        for i, (nome, titulo_y) in enumerate(LINHAS.items()):
            ax = eixos[i, j]
            ax.set_facecolor(FUNDO)
            for acao, (rotulo, cor, traco) in ACOES.items():
                c = curvas[acao, carga]
                tempo = eixo_tempo(c)
                ax.plot(tempo, c[nome], color=cor, linewidth=2, linestyle=traco, label=rotulo, zorder=3)
                # início e fim do movimento
                for k, marca in ((N, "o"), (-1, "s")):
                    ax.plot(tempo[k], c[nome][k], marca, color=cor, markersize=7,
                            markeredgecolor=FUNDO, markeredgewidth=1.5, zorder=4)
            ax.axvline(0, color=EIXO, linewidth=1, zorder=1)
            ax.tick_params(colors=TINTA, length=3, labelsize=9, labelleft=True)
            for lado in ["top", "right"]:
                ax.spines[lado].set_visible(False)
            for lado in ["left", "bottom"]:
                ax.spines[lado].set_color(EIXO)
            ax.set_ylabel(titulo_y, fontsize=10, color=TINTA)
            if i == 0:  # identificação da carga da coluna (não é título da figura)
                ax.text(0.5, 1.03, f"Load: {pct}", transform=ax.transAxes, ha="center", fontsize=10, color=TINTA)
            if i == len(LINHAS) - 1:
                ax.set_xlabel("Time from stimulus onset (ms)", fontsize=10, color=TINTA)
    eixos[0, 0].set_xlim(left=-15)
    eixos[0, 0].legend(loc="center left", frameon=False, fontsize=10, labelcolor=TINTA, handlelength=3)
    fig.tight_layout(h_pad=1.5, w_pad=2)
    fig.savefig(f"{PASTA}/serie_temporal.png", dpi=DPI, facecolor=FUNDO)
    plt.close(fig)

    print(f"{n_tent} tentativas válidas, {fora} fora por TR <= 0")
    for (acao, carga), c in curvas.items():
        print(f"{acao} {carga}: n = {c['n']}, TR = {c['TR']:.1f}, TM = {c['TM']:.1f}, "
              f"TPV = {c['TPV']:.1f}, pico da curva média = {c['vel'].max():.1f} °/s, deslocamento final = {c['pos'][-1]:.1f}°")
    print(f"arquivo salvo: {PASTA}/serie_temporal.png")


if __name__ == "__main__":
    main()
