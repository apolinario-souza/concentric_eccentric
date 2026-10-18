"""
Gráficos das variáveis por carga e tipo de ação (média ± IC 95% intra-sujeitos),
com * nas diferenças significativas do post hoc (Holm) e # quando as ações diferem
na média das cargas (efeito de ação sem interação).

Uso: python3 graficos_cargas.py   (rodar depois de analise_cargas.py)
Saída: graficos/precisao.png, amplitude_tempos.png, consistencia.png, processo.png
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from analise_cargas import CARGAS, DIMENSOES, SAIDA, carregar

PASTA = "graficos"
ARQUIVOS = {"Precisão": "precisao", "Amplitude e tempos": "amplitude_tempos",
            "Consistência": "consistencia", "Medidas de processo": "processo"}
# rótulos do eixo y (as figuras são em inglês, para o artigo)
PAINEIS = {
    "EA_mean": "Spatial absolute error (°)", "ETA_mean": "Temporal absolute error (ms)",
    "AMP_mean": "Movement amplitude (°)", "TM_mean": "Movement time (ms)",
    "EC_sd": "Spatial variable error (°)", "ETC_sd": "Temporal variable error (ms)",
    "PV_cv": "CV of peak velocity (%)",
    "PV_mean": "Peak velocity (°/s)", "TR_mean": "Reaction time (ms)",
    "TRPV_mean": "Relative time to peak velocity\n(% of movement time)",
}
ACOES = {"con": ("Concentric", "#2a78d6", "o", -1.2), "exc": ("Eccentric", "#eb6834", "s", 1.2)}
# % real da carga máxima em cada nível (halteres de 1 em 1 kg): média e amplitude dos 45
# participantes nas duas ações, de dados_sujeitos.xlsx (aba valores_percentuais)
PCT_REAL = {37: "33%\n(25–41)", 65: "68%\n(60–75)", 89: "91%\n(80–100)"}
ALFA = 0.05
TINTA, MUDO, EIXO, FUNDO = "#0b0b0b", "#555555", "#555555", "#ffffff"
DPI = 300
NCOL = 2  # painéis por linha


def ic_intra(cubo):
    """Meia-largura do IC 95% intra-sujeitos (Cousineau-Morey) por condição."""
    norm = cubo.sub(cubo.mean(axis=1), axis=0) + cubo.values.mean()
    k, n = cubo.shape[1], len(cubo)
    ep = norm.std(ddof=1) / np.sqrt(n) * np.sqrt(k / (k - 1))
    return ep * stats.t.ppf(0.975, n - 1)


def colchete(ax, x1, x2, y, alt, cor):
    ax.plot([x1, x1, x2, x2], [y - alt, y, y, y - alt], color=cor, linewidth=1.2,
            solid_capstyle="butt", zorder=2)
    ax.text((x1 + x2) / 2, y - alt * 1.0, "*", ha="center", va="bottom", fontsize=12, color=TINTA)


def marcar_diferencas(ax, ph, a, media, ic):
    """Asteriscos (p de Holm < 0,05), condicionados ao efeito correspondente na ANOVA;
    # no centro quando há só o efeito principal de ação (sem interação)."""
    topo, base = (media + ic).max(), (media - ic).min()
    passo = 0.12 * (topo - base)
    sig = ph[ph["p_holm"] < ALFA].set_index(["familia", "comparacao"]).index
    interacao = a.loc["carga * acao", "p_GG"] < ALFA

    # ação: com interação, * sobre a carga em que con e exc diferem; sem interação,
    # um único # no centro do painel (con e exc diferem na média das cargas)
    y = topo
    if not interacao and a.loc["acao", "p"] < ALFA:
        yc = (media + ic).xs(CARGAS[1], level="carga").max()
        ax.text(CARGAS[1], yc + passo * 0.3, "#", ha="center", va="bottom", fontsize=11, color=TINTA)
        y = max(y, yc + passo * 1.1)
    if interacao:
        for c in CARGAS:
            if (f"acao dentro de {c}", "con vs exc") in sig:
                yc = (media + ic).xs(c, level="carga").max()
                ax.text(c, yc + passo * 0.15, "*", ha="center", va="bottom", fontsize=13, color=TINTA)
                y = max(y, yc + passo * 0.9)

    # carga: colchetes; por ação se há interação, senão sobre a média das ações
    if interacao:
        grupos = [(f"carga dentro de {ac}", ACOES[ac][1], ACOES[ac][3]) for ac in ACOES]
    elif a.loc["carga", "p_GG"] < ALFA:
        grupos = [("carga (média das ações)", MUDO, 0)]
    else:
        grupos = []
    for familia, cor, desloc in grupos:
        for nivel in ([(37, 65), (65, 89)], [(37, 89)]):
            pares = [(c1, c2) for c1, c2 in nivel if (familia, f"{c1} vs {c2}") in sig]
            if pares:
                y += passo
                for c1, c2 in pares:
                    colchete(ax, c1 + desloc + 1.5, c2 + desloc - 1.5, y, passo * 0.3, cor)
    if y > topo:
        ax.set_ylim(top=y + passo * 1.1)


def painel(ax, longo, aov, ph, vd, titulo=None):
    d = longo[longo["vd"] == vd]
    cubo = d.pivot_table(index="sujeito", columns=["carga", "acao"], values="valor").dropna()
    media, ic = cubo.mean(), ic_intra(cubo)
    for ac, (rotulo, cor, marca, desloc) in ACOES.items():
        x = np.array(CARGAS) + desloc
        y, e = media.xs(ac, level="acao").values, ic.xs(ac, level="acao").values
        ax.errorbar(x, y, yerr=e, color=cor, marker=marca, markersize=7, linewidth=2,
                    elinewidth=1.2, capsize=3, markeredgecolor=FUNDO, markeredgewidth=1.5,
                    label=rotulo, zorder=3)
    if media.min() < 0 < media.max():
        ax.axhline(0, color=EIXO, linewidth=1, zorder=1)

    a = aov[aov["vd"] == vd].set_index("efeito")
    marcar_diferencas(ax, ph[ph["vd"] == vd], a, media, ic)
    ax.set_ylabel(titulo or vd.split("_")[0], fontsize=10, color=TINTA)
    ax.set_xticks(CARGAS, [PCT_REAL[c] for c in CARGAS], linespacing=1.3)
    ax.set_xlim(28, 98)
    ax.tick_params(colors=TINTA, length=3, labelsize=9)
    ax.tick_params(axis="x", length=0)
    for lado in ["top", "right"]:
        ax.spines[lado].set_visible(False)
    for lado in ["left", "bottom"]:
        ax.spines[lado].set_color(EIXO)
    return len(cubo)


def figura(longo, aov, ph, arquivo, vds, ncol=NCOL):
    nlin = -(-len(vds) // ncol)
    alt = 3.0 * nlin + 0.4  # painéis + faixa fixa da legenda (polegadas)
    fig, eixos = plt.subplots(nlin, ncol, figsize=(4.2 * ncol, alt), facecolor=FUNDO)
    eixos = np.ravel(eixos)
    for ax, letra, (vd, tit) in zip(eixos, "ABCDEFGH", vds.items()):
        ax.set_facecolor(FUNDO)
        painel(ax, longo, aov, ph, vd, tit)
        # letra do painel, para a legenda da figura no manuscrito
        ax.set_title(letra, loc="left", fontsize=12, fontweight="bold", color=TINTA)
    for ax in eixos[len(vds):]:
        ax.set_visible(False)
    marcas, rotulos = eixos[0].get_legend_handles_labels()
    fig.legend(marcas, rotulos, loc="upper right", bbox_to_anchor=(0.99, 1 - 0.02 / alt), ncol=2,
               frameon=False, fontsize=10, labelcolor=TINTA)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.32 / alt), h_pad=2.5, w_pad=2)
    fig.savefig(f"{PASTA}/{arquivo}.png", dpi=DPI, facecolor=FUNDO)
    plt.close(fig)


def main():
    os.makedirs(PASTA, exist_ok=True)
    longo = carregar()
    aov = pd.read_excel(SAIDA, sheet_name="anova")
    ph = pd.read_excel(SAIDA, sheet_name="posthoc")
    for dim, vds in DIMENSOES.items():
        figura(longo, aov, ph, ARQUIVOS[dim], {vd: PAINEIS[vd] for vd in vds})


if __name__ == "__main__":
    main()
