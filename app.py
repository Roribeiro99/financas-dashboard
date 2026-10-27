import os
import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

# Configuração da página em modo expandido
st.set_page_config(
    page_title="Dashboard de Finanças & Investimentos",
    page_icon="📈",
    layout="wide",
)

st.title("🚀 Dashboard de Gestão Financeira & Mercado em Tempo Real")
st.markdown(
    "Painel interativo conectado à sua base de dados e cotações ao vivo da"
    " B3."
)

EXCEL_FILE = "Controle_planilha_v8_2024_financas_24 (2)111.xlsx"


@st.cache_data(ttl=600)
def carregar_dados(path):
  if not os.path.exists(path):
    return None, None, None
  df_base = pd.read_excel(path, sheet_name="Base de dados", header=3)
  df_info = pd.read_excel(path, sheet_name="INFO AÇÕES")
  return df_base, df_info


df_base, df_info = carregar_dados(EXCEL_FILE)

if df_base is None:
  st.error(
      f"⚠️ Arquivo '{EXCEL_FILE}' não encontrado. Certifique-se de que ele está"
      " na mesma pasta que o app.py no repositório do GitHub."
  )
else:
  st.sidebar.header("🔍 Filtros do Relatório")

  # Filtros interativos na barra lateral idênticos aos da imagem
  if (
      "TIPO MOVIMENTAÇÃO" in df_base.columns
      and "FEITO?" in df_base.columns
  ):
    tipos_mov = sorted(df_base["TIPO MOVIMENTAÇÃO"].dropna().unique())
    status_feito = sorted(df_base["FEITO?"].dropna().unique())

    filtro_tipo = st.sidebar.selectbox(
        "TIPO MOVIMENTAÇÃO",
        tipos_mov,
        index=tipos_mov.index("Aporte") if "Aporte" in tipos_mov else 0,
    )
    filtro_feito = st.sidebar.selectbox(
        "FEITO?",
        status_feito,
        index=status_feito.index("SIM") if "SIM" in status_feito else 0,
    )

    # Filtrar dados com base na seleção
    df_filtrado = df_base[
        (df_base["TIPO MOVIMENTAÇÃO"] == filtro_tipo)
        & (df_base["FEITO?"] == filtro_feito)
    ]
  else:
    df_filtrado = df_base

  st.subheader(
      f"📊 Relatório Consolidado (Filtro: {filtro_tipo} | Feito: {filtro_feito})"
  )

  if not df_filtrado.empty:
    # Agrupamento por ativo
    df_agrupado = (
        df_filtrado.groupby("ATIVO")
        .agg(
            COTAS=("QUANTIDADE", "sum"),
            TOTAL_NEGOCIADO=("VALOR \nTOTAL", "sum"),
            VALOR_TOTAL_MERCADO=("VALOR TOTAL MERCADO", "sum"),
        )
        .reset_index()
    )

    # Calculando métricas
    df_agrupado["PREÇO NEGOCIADO"] = (
        df_agrupado["TOTAL_NEGOCIADO"] / df_agrupado["COTAS"]
    )
    df_agrupado["PREÇO MERCADO"] = (
        df_agrupado["VALOR_TOTAL_MERCADO"] / df_agrupado["COTAS"]
    )
    df_agrupado["GANHO/PERDA"] = (
        df_agrupado["VALOR_TOTAL_MERCADO"] - df_agrupado["TOTAL_NEGOCIADO"]
    )
    df_agrupado["VALORIZAÇÃO"] = (
        df_agrupado["VALOR_TOTAL_MERCADO"] / df_agrupado["TOTAL_NEGOCIADO"]
    ) - 1

    # Exibindo a tabela interativa formatada
    st.dataframe(
        df_agrupado.style.format({
            "COTAS": "{:,.0f}",
            "PREÇO NEGOCIADO": "R$ {:,.2f}",
            "PREÇO MERCADO": "R$ {:,.2f}",
            "TOTAL NEGOCIADO": "R$ {:,.2f}",
            "VALOR_TOTAL_MERCADO": "R$ {:,.2f}",
            "GANHO/PERDA": "R$ {:,.2f}",
            "VALORIZAÇÃO": "{:.2%}",
        }),
        use_container_width=True,
    )

    # Métricas de resumo rápido (KPIs)
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Total Negociado", f"R$ {df_agrupado['TOTAL_NEGOCIADO'].sum():,.2f}"
    )
    col2.metric(
        "Total no Mercado", f"R$ {df_agrupado['VALOR_TOTAL_MERCADO'].sum():,.2f}"
    )
    ganho_total = df_agrupado["GANHO/PERDA"].sum()
    col3.metric(
        "Ganho / Perda Total",
        f"R$ {ganho_total:,.2f}",
        delta=f"R$ {ganho_total:,.2f}",
    )

  else:
    st.warning("⚠️ Nenhum registro encontrado para os filtros selecionados.")
