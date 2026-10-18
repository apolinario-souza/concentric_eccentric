"""
Recalcula as medidas de desempenho a partir dos traços brutos (dados/sujX/), com início
e fim do movimento definidos a 5% do pico de velocidade, e gera a planilha lida por
analise_cargas.py.

O limiar de 20% (critério do feedback na coleta) continua sendo calculado para duas
coisas: conferir cada tentativa com o arquivo-resumo do LabVIEW e estimar a posição-alvo
(EC registrado = alvo - posição no fim do movimento a 20%).

Uso: python3 medidas_brutas.py
Saída: dados_5pct.xlsx (abas: medidas, tentativas, conferencia)
"""
import glob
import os
import re

import numpy as np
import pandas as pd

PASTA = "dados"
SAIDA = "dados_5pct.xlsx"
CONDS = ["37con", "65con", "89con", "37exc", "65exc", "89exc"]
MS_FRAME = 5          # 200 Hz
FRAME_ESTIMULO = 800
TM_MINIMO = 150       # exclusão de antecipações do script original (TM a 20%)
AMP_MINIMA = 30       # graus; metade da amplitude da tarefa (o pico detectado não é o movimento)
LIMIAR = 0.05         # critério de análise
LIMIAR_COLETA = 0.20  # critério do feedback online (arquivos-resumo)
META_TM = 250
RESUMO = ["TR", "TM", "EA", "EC", "PV"]
# Medidas de variabilidade e TR: assimétricas à direita, testadas em log (analise_cargas.py)
LOG = ["EC_sd", "ETC_sd", "PV_cv", "TR_mean"]


def cruzamentos(v, k, frac):
    """Frames (interpolados) em que a velocidade cruza frac * pico, antes e depois do pico k."""
    lim = frac * v[k]
    a = k
    while a > 0 and v[a] > lim:
        a -= 1
    b = k
    while b < len(v) - 1 and v[b] > lim:
        b += 1
    # sem cruzamento dentro do traço (v ainda acima do limiar na borda): usa a borda
    ini = a + (lim - v[a]) / (v[a + 1] - v[a]) if v[a] <= lim < v[a + 1] else a
    fim = b - (lim - v[b]) / (v[b - 1] - v[b]) if v[b] <= lim < v[b - 1] else b
    return ini, fim


def arquivos(pasta, cond):
    """Traços da condição, na ordem das tentativas."""
    arqs = glob.glob(f"{pasta}/{cond}_tentativa_*.xls")
    return sorted(arqs, key=lambda a: int(re.search(r"_(\d+)\.xls$", a).group(1)))


def ler_resumo(pasta, cond):
    for arq in (f"{pasta}/{cond}.txt", f"{pasta}/{cond}"):
        if os.path.exists(arq):
            return pd.read_csv(arq, sep="\t", decimal=",", header=None, names=RESUMO)
    return None


def ler_tentativas():
    linhas = []
    pastas = sorted(glob.glob(f"{PASTA}/suj*"), key=lambda p: int(os.path.basename(p)[3:]))
    for pasta in pastas:
        for cond in CONDS:
            arqs, res = arquivos(pasta, cond), ler_resumo(pasta, cond)
            if res is not None and len(res) != len(arqs):
                res = None  # sem correspondência tentativa a tentativa
            for i, arq in enumerate(arqs):
                t = pd.read_csv(arq, sep="\t", decimal=",", header=None)
                t = t.dropna(axis=1, how="all").dropna().values
                acao = cond[2:]
                pos, vel = t[:, 3], t[:, 4] * (-1 if acao == "con" else 1)
                k = 700 + int(np.argmax(vel[700:]))
                d = {"sujeito": os.path.basename(pasta), "carga": int(cond[:2]), "acao": acao,
                     "tentativa": i + 1, "arquivo": os.path.basename(arq), "PV": vel[k]}
                for nome, frac in (("", LIMIAR), ("_20", LIMIAR_COLETA)):
                    ini, fim = cruzamentos(vel, k, frac)
                    d["TR" + nome] = (ini - FRAME_ESTIMULO) * MS_FRAME
                    d["TM" + nome] = (fim - ini) * MS_FRAME
                    d["pos_ini" + nome] = np.interp(ini, np.arange(len(pos)), pos)
                    d["pos_fim" + nome] = np.interp(fim, np.arange(len(pos)), pos)
                    d["na_borda" + nome] = ini <= 0 or fim >= len(vel) - 1
                    if frac == LIMIAR:  # tempo do início do movimento até o pico de velocidade
                        d["TPV"] = (k - ini) * MS_FRAME
                        d["TRPV"] = 100 * (k - ini) / (fim - ini)  # em % do TM
                if res is not None:
                    d.update({f"{c}_resumo": res.iloc[i][c] for c in RESUMO})
                linhas.append(d)
    d = pd.DataFrame(linhas)

    # posição-alvo de cada sujeito e ação, estimada das tentativas com resumo
    d["alvo"] = (d["EC_resumo"] + d["pos_fim_20"]).groupby([d["sujeito"], d["acao"]]).transform("median")
    sinal = np.where(d["acao"] == "exc", -1, 1)  # EC > 0 = além do alvo nas duas ações
    d["EC"] = (d["alvo"] - d["pos_fim"]) * sinal
    d["EA"] = d["EC"].abs()
    d["AMP"] = (d["pos_fim"] - d["pos_ini"]).abs()  # amplitude do movimento (início ao fim a 5%)
    d["ETC"] = d["TM"] - META_TM
    d["ETA"] = d["ETC"].abs()
    # mesma exclusão de antecipações do script original (TM a 20% < 150 ms); sai também a
    # tentativa cujo traço acaba antes de a velocidade cair a 5% do pico (TM truncado) e a
    # de amplitude menor que AMP_MINIMA
    d["valida"] = (d["TM_20"] >= TM_MINIMO) & ~d["na_borda"] & (d["AMP"] >= AMP_MINIMA)
    return d


def medidas(d):
    """Medidas por sujeito e condição, no formato largo (<vd>_<carga>_<acao>).

    As variáveis de LOG saem também em logaritmo natural (ln<vd>_<carga>_<acao>), para
    quem for repetir a análise em outro programa.
    """
    g = d[d["valida"]].groupby(["sujeito", "carga", "acao"], sort=False)
    m = pd.DataFrame({
        "EA_mean": g["EA"].mean(), "ETA_mean": g["ETA"].mean(),
        "EC_mean": g["EC"].mean(), "ETC_mean": g["ETC"].mean(),
        "EC_sd": g["EC"].std(), "ETC_sd": g["ETC"].std(),
        "PV_cv": 100 * g["PV"].std() / g["PV"].mean(),
        "PV_mean": g["PV"].mean(), "TR_mean": g["TR"].mean(),
        "TRPV_mean": g["TRPV"].mean(), "TRPV_cv": 100 * g["TRPV"].std() / g["TRPV"].mean(),
        "AMP_mean": g["AMP"].mean(), "TM_mean": g["TM"].mean(), "TPV_mean": g["TPV"].mean(),
        "n_tentativas": g["PV"].size(),
    })
    for vd in LOG:
        m["ln" + vd] = np.log(m[vd])
    largo = m.unstack(["carga", "acao"])
    largo.columns = [f"{vd}_{carga}_{acao}" for vd, carga, acao in largo.columns]
    return largo.loc[d["sujeito"].unique()].reset_index()


def conferir(d):
    """Concordância com os arquivos-resumo (limiar de 20%), por sujeito e condição."""
    c = d.dropna(subset=["PV_resumo"]).assign(
        pv_igual=lambda x: (x["PV"] - x["PV_resumo"]).abs() < 0.01,
        tm_igual=lambda x: (x["TM_20"] - x["TM_resumo"]).abs() <= MS_FRAME,
        tr_igual=lambda x: (x["TR_20"] - x["TR_resumo"]).abs() <= MS_FRAME)
    g = c.groupby(["sujeito", "carga", "acao"], sort=False)
    conf = g[["pv_igual", "tm_igual", "tr_igual"]].mean().mul(100).round(0)
    conf.insert(0, "tentativas", g.size())
    return conf.reset_index()


def main():
    d = ler_tentativas()
    conf = conferir(d)
    largo = medidas(d)
    with pd.ExcelWriter(SAIDA) as xl:
        largo.to_excel(xl, sheet_name="medidas", index=False)
        d.to_excel(xl, sheet_name="tentativas", index=False)
        conf.to_excel(xl, sheet_name="conferencia", index=False)

    n = d.groupby(["sujeito", "carga", "acao"]).size()
    print(f"{d['sujeito'].nunique()} participantes, {len(n)} condições, {len(d)} tentativas "
          f"({(d['TM_20'] < TM_MINIMO).sum()} excluídas por TM a 20% < {TM_MINIMO} ms, "
          f"{(d['na_borda'] & (d['TM_20'] >= TM_MINIMO)).sum()} por traço truncado, "
          f"{((d['AMP'] < AMP_MINIMA) & (d['TM_20'] >= TM_MINIMO) & ~d['na_borda']).sum()} "
          f"por amplitude < {AMP_MINIMA}°)")
    print(f"condições com resumo conferido: {len(conf)}; PV igual em {conf['pv_igual'].mean():.1f}% das "
          f"tentativas, TM em {conf['tm_igual'].mean():.1f}%, TR em {conf['tr_igual'].mean():.1f}%")
    ruins = conf[conf["pv_igual"] < 100]
    if len(ruins):
        print("PV diferente do resumo em:\n" + ruins.to_string(index=False))
    print(f"arquivo salvo: {SAIDA}")


if __name__ == "__main__":
    main()
