
from typing import Dict, Tuple, List

SCALES_CLASSIC = {
    "Idade": {"Jovem (18–30)": 10, "Adulto (31–50)": 40, "Idoso (51+)": 70},
    "Tipo físico": {"Ectomorfo": 50, "Mesomorfo": 20, "Endomorfo": 70},
    "Metabolismo basal": {"Alto": 10, "Médio": 40, "Baixo": 70},
    "Doenças crônicas": {"Nenhuma": 0, "Leve (controlada)": 20, "Moderada (ex.: DM2)": 50, "Grave (descompensada)": 80},
    "Calorias": {"Manutenção": 20, "Superávit": 40, "Déficit": 60},
    "Psicológico/ambiente": {"Favorável": 10, "Neutro": 30, "Desfavorável": 60},
}

WEIGHTS_CLASSIC = {
    "Idade": 20,
    "Tipo físico": 20,
    "Metabolismo basal": 15,
    "Doenças crônicas": 25,
    "Calorias": 15,
    "Psicológico/ambiente": 5,
}

SCALES_V2 = {
    "Idade": {"Jovem (18–30)": 10, "Adulto (31–50)": 40, "Idoso (51+)": 70},
    "Sexo biológico": {"Homem": 20, "Mulher": 30, "Mulher pós-menopausa": 50},
    "Composição corporal (% gordura)": {"<20%": 10, "20–30%": 40, ">30%": 70},
    "Condição metabólica/doenças": {"Saudável": 0, "Leve": 20, "Moderada": 50, "Grave": 80},
    "Nível de atividade física": {"Ativo": 10, "Moderado": 40, "Sedentário": 70},
    "Sono & recuperação": {"Bom": 10, "Regular": 40, "Ruim": 70},
    "Psicológico/ambiente": {"Favorável": 10, "Neutro": 30, "Desfavorável": 60},
}

WEIGHTS_V2 = {
    "Idade": 15,
    "Sexo biológico": 10,
    "Composição corporal (% gordura)": 20,
    "Condição metabólica/doenças": 20,
    "Nível de atividade física": 15,
    "Sono & recuperação": 10,
    "Psicológico/ambiente": 10,
}

def normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total == 0:
        return {k: 0 for k in weights}
    return {k: (v / total) * 100 for k, v in weights.items()}

def compute_ier(selections: Dict[str, str], scales: Dict[str, Dict[str, int]], weights: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
    w = normalize_weights(weights)
    contributions = {}
    ier = 0.0
    for factor, choice in selections.items():
        score = 0
        if factor in scales:
            score = scales[factor].get(choice, 0)
        contrib = score * (w.get(factor, 0) / 100.0)
        contributions[factor] = round(contrib, 2)
        ier += contrib
    return round(ier, 2), contributions

def batch_compute(df, model="v2"):
    if model == "classic":
        scales = SCALES_CLASSIC
        weights = WEIGHTS_CLASSIC
    else:
        scales = SCALES_V2
        weights = WEIGHTS_V2
    weights = normalize_weights(weights)
    out_rows = []
    for _, row in df.iterrows():
        selections = {}
        for factor in scales.keys():
            val = row.get(factor, None)
            if isinstance(val, str):
                selections[factor] = val
        ier, contribs = compute_ier(selections, scales, weights)
        out = {"IER": ier}
        out.update({f"Contrib:{k}": v for k, v in contribs.items()})
        out_rows.append(out)
    return out_rows
