"""
Efeito da carga (37, 65, 89% da carga máxima) e do tipo de ação (con, exc) sobre as medidas de desempenho.

Delineamento: ANOVA de medidas repetidas 3 (carga) x 2 (ação: con, exc),
uma por variável dependente. Esfericidade corrigida por Greenhouse-Geisser,
post hoc pareado com correção de Holm (cargas dentro de cada ação e
ações dentro de cada carga). As variáveis em LOG (resíduos assimétricos) são
testadas em escala logarítmica; os descritivos ficam na unidade original.

As medidas vêm de dados_5pct.xlsx (medidas_brutas.py): início e fim do movimento a 5%
do pico de velocidade, recalculados dos traços brutos.

Uso: python3 analise_cargas.py   (rodar depois de medidas_brutas.py)
Saída: resultados_cargas.xlsx
"""
from itertools import combinations

import numpy as np
import pandas as pd
import pingouin as pg
from scipy import stats

from medidas_brutas import LOG  # variáveis testadas em log

ENTRADA = "dados_5pct.xlsx"
SAIDA = "resultados_cargas.xlsx"
CARGAS = [37, 65, 89]
# Variáveis analisadas, por dimensão
DIMENSOES = {
    "Precisão": ["EA_mean", "ETA_mean"],
    "Amplitude e tempos": ["AMP_mean", "TR_mean", "TM_mean"],
    "Consistência": ["EC_sd", "ETC_sd", "PV_cv"],
    "Medidas de processo": ["PV_mean", "TRPV_mean"],
}
VDS = [vd for vds in DIMENSOES.values() for vd in vds]


def carregar():
    largo = pd.read_excel(ENTRADA, sheet_name="medidas")
    longo = largo.melt(id_vars="sujeito", var_name="col", value_name="valor")
    partes = longo["col"].str.split("_", expand=True)
    longo["vd"] = partes[0] + "_" + partes[1]
    longo["carga"] = partes[2].astype(int)
    longo["acao"] = partes[3]
    # o EC já vem com EC > 0 = além do alvo nas duas ações
    return longo.drop(columns="col")


def pares_carga(d, familia):
    """Comparações pareadas entre cargas (d: sujeito x carga), Holm na família."""
    linhas = []
    for a, b in combinations(CARGAS, 2):
        dif = d[b] - d[a]
        t, p = stats.ttest_1samp(dif, 0)
        ic = stats.t.interval(0.95, len(dif) - 1, dif.mean(), stats.sem(dif))
        linhas.append({
            "familia": familia, "comparacao": f"{a} vs {b}", "n": len(dif),
            "dif_media": dif.mean(), "ic95_inf": ic[0], "ic95_sup": ic[1],
            "t": t, "gl": len(dif) - 1, "p": p, "dz": dif.mean() / dif.std(ddof=1),
        })
    out = pd.DataFrame(linhas)
    out["p_holm"] = pg.multicomp(out["p"].values, method="holm")[1]
    return out


def pares_acao(cubo):
    """Exc vs con: efeito principal (média das cargas) e efeitos simples por carga (Holm)."""
    con, exc = cubo.xs("con", axis=1, level="acao"), cubo.xs("exc", axis=1, level="acao")
    blocos = [("acao (média das cargas)", con.mean(axis=1), exc.mean(axis=1))]
    blocos += [(f"acao dentro de {c}", con[c], exc[c]) for c in CARGAS]
    linhas = []
    for familia, a, b in blocos:
        dif = b - a
        t, p = stats.ttest_1samp(dif, 0)
        ic = stats.t.interval(0.95, len(dif) - 1, dif.mean(), stats.sem(dif))
        linhas.append({
            "familia": familia, "comparacao": "con vs exc", "n": len(dif),
            "dif_media": dif.mean(), "ic95_inf": ic[0], "ic95_sup": ic[1],
            "t": t, "gl": len(dif) - 1, "p": p, "dz": dif.mean() / dif.std(ddof=1),
        })
    out = pd.DataFrame(linhas)
    out["p_holm"] = out["p"]
    out.loc[1:, "p_holm"] = pg.multicomp(out["p"].values[1:], method="holm")[1]
    return out


def analisar(longo, vd):
    d = longo[longo["vd"] == vd]
    cubo = d.pivot_table(index="sujeito", columns=["carga", "acao"], values="valor")
    cubo = cubo.dropna()  # casos completos
    n = len(cubo)
    dd = cubo.stack(["carga", "acao"], future_stack=True).rename("valor").reset_index()
    escala = "log" if vd in LOG else "original"
    cubo_t = np.log(cubo) if vd in LOG else cubo  # escala dos testes
    dd_t = cubo_t.stack(["carga", "acao"], future_stack=True).rename("valor").reset_index()

    aov = pg.rm_anova(data=dd_t, dv="valor", within=["carga", "acao"],
                      subject="sujeito", correction=True)
    aov.insert(0, "vd", vd)
    aov.insert(1, "n", n)
    aov.insert(2, "escala", escala)

    # descritivos
    desc = dd.groupby(["carga", "acao"])["valor"].agg(["mean", "std"]).reset_index()
    marg = dd.groupby(["sujeito", "carga"])["valor"].mean().groupby("carga").agg(["mean", "std"]).reset_index()
    marg["acao"] = "media(con,exc)"
    marg_a = dd.groupby(["sujeito", "acao"])["valor"].mean().groupby("acao").agg(["mean", "std"]).reset_index()
    marg_a["carga"] = "media(37,65,89)"
    desc = pd.concat([desc, marg, marg_a])
    desc.insert(0, "vd", vd)
    desc.insert(1, "n", n)

    # post hoc (na escala dos testes): efeito principal de carga e efeitos simples
    ph = [pares_carga(cubo_t.T.groupby(level="carga").mean().T, "carga (média das ações)")]
    for ac in ["con", "exc"]:
        ph.append(pares_carga(cubo_t.xs(ac, axis=1, level="acao"), f"carga dentro de {ac}"))
    ph.append(pares_acao(cubo_t))
    ph = pd.concat(ph)
    ph.insert(0, "vd", vd)
    ph.insert(1, "escala", escala)

    # checagem: normalidade dos resíduos (valor - célula - sujeito + média geral)
    res = (cubo_t.sub(cubo_t.mean(axis=1), axis=0).sub(cubo_t.mean(axis=0), axis=1)
           + cubo_t.values.mean()).values.ravel()
    chk = {"vd": vd, "n": n, "escala": escala, "assimetria": stats.skew(res),
           "curtose": stats.kurtosis(res), "shapiro_W": stats.shapiro(res)[0],
           "shapiro_p": stats.shapiro(res)[1]}
    return aov, desc, ph, chk


def rodar(longo, vds, saida):
    aovs, descs, phs, chks = zip(*(analisar(longo, vd) for vd in vds))
    aov, desc, ph, chk = pd.concat(aovs), pd.concat(descs), pd.concat(phs), pd.DataFrame(chks)

    aov = aov.rename(columns={"Source": "efeito", "ddof1": "gl1", "ddof2": "gl2",
                              "p-unc": "p", "p-GG-corr": "p_GG", "ng2": "eta2_g", "eps": "eps_GG"})
    aov["eta2_p"] = aov["SS"] / (aov["SS"] + aov["SS"] / aov["F"] * aov["gl2"] / aov["gl1"])
    aov = aov[["vd", "n", "escala", "efeito", "gl1", "gl2", "F", "p", "eps_GG", "p_GG", "eta2_p", "eta2_g"]]

    # resumo: uma linha por VD com o efeito de carga
    c = aov[aov["efeito"] == "carga"].set_index("vd")
    a = aov[aov["efeito"] == "acao"].set_index("vd")
    i = aov[aov["efeito"] == "carga * acao"].set_index("vd")
    resumo = pd.DataFrame({
        "n": c["n"], "escala": c["escala"], "F_carga": c["F"], "p_GG_carga": c["p_GG"], "eta2_p_carga": c["eta2_p"],
        "F_acao": a["F"], "p_acao": a["p"], "eta2_p_acao": a["eta2_p"],
        "F_interacao": i["F"], "p_GG_interacao": i["p_GG"], "eta2_p_interacao": i["eta2_p"],
    })
    resumo["p_carga_holm_entre_VDs"] = pg.multicomp(resumo["p_GG_carga"].values, method="holm")[1]
    resumo["p_acao_holm_entre_VDs"] = pg.multicomp(resumo["p_acao"].values, method="holm")[1]
    princ = ph[ph["familia"] == "carga (média das ações)"].pivot(index="vd", columns="comparacao", values="p_holm")
    resumo.insert(0, "dimensao", [d for d, v in DIMENSOES.items() for _ in v])
    resumo = resumo.join(princ.add_prefix("p_holm ")).join(chk.set_index("vd")[["assimetria", "shapiro_p"]]).reset_index()

    with pd.ExcelWriter(saida) as xl:
        resumo.to_excel(xl, sheet_name="resumo", index=False)
        aov.to_excel(xl, sheet_name="anova", index=False)
        ph.to_excel(xl, sheet_name="posthoc", index=False)
        desc.to_excel(xl, sheet_name="descritivos", index=False)
        chk.to_excel(xl, sheet_name="checagens", index=False)

    return resumo


def main():
    resumo = rodar(carregar(), VDS, SAIDA)
    pd.set_option("display.width", 250, "display.max_columns", 30, "display.float_format", "{:.4f}".format)
    print(resumo.to_string(index=False))


if __name__ == "__main__":
    main()
