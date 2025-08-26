
import streamlit as st
import pandas as pd
from ier_core import (
    SCALES_CLASSIC, WEIGHTS_CLASSIC,
    SCALES_V2, WEIGHTS_V2,
    compute_ier, normalize_weights, batch_compute
)

st.set_page_config(page_title="IER — Índice de Esforço Relativo", layout="wide")

st.title("IER — Índice de Esforço Relativo")
st.caption("App simples para estimar o esforço relativo em dieta/treino considerando fatores individuais.")

tab_calc, tab_batch, tab_about = st.tabs(["Calcular", "Lote (Batch)", "Sobre"])

with tab_calc:
    colL, colR = st.columns([1,1])
    with colL:
        model = st.selectbox("Modelo", ["Versão 2 (objetiva — recomendado)", "Clássico (somatótipos)"])
        if model == "Clássico (somatótipos)":
            scales = SCALES_CLASSIC.copy()
            weights = WEIGHTS_CLASSIC.copy()
            model_key = "classic"
        else:
            scales = SCALES_V2.copy()
            weights = WEIGHTS_V2.copy()
            model_key = "v2"

        st.subheader("Pesos dos fatores (%)")
        weight_inputs = {}
        for factor, default_w in weights.items():
            weight_inputs[factor] = st.slider(factor, 0, 40, int(default_w))
        weights_norm = normalize_weights(weight_inputs)
        st.info("Os pesos são normalizados para somar 100%.")

    with colR:
        st.subheader("Seleção dos fatores")
        selections = {}
        for factor, options in scales.items():
            default = list(options.keys())[0]
            selections[factor] = st.selectbox(factor, list(options.keys()), index=0, key=factor)

    if st.button("Calcular IER", type="primary"):
        ier_score, contributions = compute_ier(selections, scales, weights_norm)
        st.metric("IER (0–100)", ier_score)
        if ier_score < 30:
            st.success("Esforço relativo **baixo**")
        elif ier_score < 60:
            st.warning("Esforço relativo **moderado**")
        else:
            st.error("Esforço relativo **alto**")

        st.markdown("#### Detalhamento por fator")
        df = pd.DataFrame({
            "Fator": list(contributions.keys()),
            "Contribuição": list(contributions.values()),
            "Peso (%)": [round(weights_norm[k], 1) for k in contributions.keys()],
            "Escolha": [selections[k] for k in contributions.keys()],
        })
        st.dataframe(df, use_container_width=True)

        st.markdown("---")
        st.subheader("Salvar / Exportar")
        name = st.text_input("Identificação do perfil (opcional)", "")
        if "saved" not in st.session_state:
            st.session_state["saved"] = []
        if st.button("Salvar perfil atual"):
            row = {"Perfil": name or "sem_nome", "IER": ier_score, "Modelo": model_key}
            row.update({f"Sel:{k}": v for k, v in selections.items()})
            row.update({f"Peso:{k}": round(weights_norm[k],1) for k in weights_norm})
            st.session_state["saved"].append(row)
            st.success("Perfil salvo na sessão!")

        if st.session_state.get("saved"):
            st.markdown("##### Perfis salvos (sessão)")
            df_saved = pd.DataFrame(st.session_state["saved"])
            st.dataframe(df_saved, use_container_width=True)
            st.download_button("Baixar CSV com perfis salvos", df_saved.to_csv(index=False).encode("utf-8"),
                               file_name="IER_perfis.csv", mime="text/csv")

with tab_batch:
    st.subheader("Processamento em lote (CSV/Excel)")
    st.write("Baixe o **template** correspondente ao modelo, preencha e reenvie. As colunas devem bater exatamente com os fatores.")

    template_choice = st.selectbox("Modelo do template", ["Versão 2 (objetiva — recomendado)", "Clássico (somatótipos)"])
    if template_choice == "Clássico (somatótipos)":
        scales_tpl = SCALES_CLASSIC
        model_key_tpl = "classic"
    else:
        scales_tpl = SCALES_V2
        model_key_tpl = "v2"

    df_tpl = pd.DataFrame({k: [""] for k in scales_tpl.keys()})
    st.download_button("Baixar template CSV", df_tpl.to_csv(index=False).encode("utf-8"),
                       file_name=f"IER_template_{model_key_tpl}.csv", mime="text/csv")

    up = st.file_uploader("Envie o arquivo preenchido (CSV ou XLSX)", type=["csv","xlsx"])
    if up is not None:
        if up.name.lower().endswith(".csv"):
            df_in = pd.read_csv(up)
        else:
            df_in = pd.read_excel(up)
        st.write("Pré-visualização do arquivo enviado:")
        st.dataframe(df_in.head(), use_container_width=True)

        out = batch_compute(df_in, model=model_key_tpl)
        df_out = pd.DataFrame(out)
        st.markdown("#### Resultados")
        st.dataframe(df_out, use_container_width=True)
        st.download_button("Baixar resultados (CSV)", df_out.to_csv(index=False).encode("utf-8"),
                           file_name=f"IER_resultados_{model_key_tpl}.csv", mime="text/csv")

with tab_about:
    st.markdown("""
**O que é o IER?**  
Uma heurística para **estratificar o esforço relativo** em resultados de dieta/treino considerando variáveis individuais.
Não é diagnóstico médico e não substitui avaliação clínica.

**Modelos:**  
- **Versão 2 (recomendada):** idade, sexo, % gordura, condição metabólica, nível de atividade, sono e fatores psicológicos/ambientais.  
- **Clássico:** idade, somatótipo, metabolismo basal, doenças crônicas, calorias, fatores psicológicos/ambientais.

**Uso profissional:** educação do paciente, metas realistas, estratificação de risco e direcionamento de programas de saúde.
""")

