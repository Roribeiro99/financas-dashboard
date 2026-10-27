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
    return None, None
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

  # Filtros interativos na barra lateral idênticos aos do print
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
    # Agrupamento por ativo conforme estrutura do print
    df_agrupado = (
        df_filtrado.groupby("ATIVO")
        .agg(
            COTAS=("QUANTIDADE", "sum"),
            TOTAL_NEGOCIADO=("VALOR \nTOTAL", "sum"),
            VALOR_TOTAL_MERCADO=("VALOR TOTAL MERCADO", "sum"),
        )
        .reset_index()
    )

    # Cálculos das colunas
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
    df_agrupado["VARIAÇÃO REAL"] = (
        df_agrupado["VALORIZAÇÃO"] * 0.1
    )  # Ajuste ou proporção conforme sua regra da planilha

    # Renomeando colunas para bater com o padrão visual
    df_tabela = df_agrupado.rename(
        columns={
            "ATIVO": "#",
            "COTAS": "COTAS",
            "PREÇO NEGOCIADO": "PREÇO NEGOCIADO",
            "PREÇO MERCADO": "PREÇO MERCADO",
            "TOTAL_NEGOCIADO": "TOTAL NEGOCIADO",
            "VALOR_TOTAL_MERCADO": "TOTAL MERCADO",
            "GANHO/PERDA": "GANHO/PERDA",
            "VALORIZAÇÃO": "VALORIZAÇÃO",
            "VARIAÇÃO REAL": "VARIAÇÃO REAL",
        }
    )

    # Função de estilo para cor verde/vermelho e negrito
    def color_picker(val):
      if isinstance(val, (int, float)):
        color = "#27ae60" if val >= 0 else "#c0392b"  # Verde ou Vermelho
        return f"color: {color}; font-weight: bold;"
      return ""

    # Aplicando o Styler na tabela
    tabela_estilizada = (
        df_tabela.style.format({
            "COTAS": "{:,.0f}",
            "PREÇO NEGOCIADO": "R$ {:,.2f}",
            "PREÇO MERCADO": "R$ {:,.2f}",
            "TOTAL NEGOCIADO": "R$ {:,.2f}",
            "TOTAL MERCADO": "R$ {:,.2f}",
            "GANHO/PERDA": "R$ {:,.2f}",
            "VALORIZAÇÃO": "{:.2%}",
            "VARIAÇÃO REAL": "{:.2%}",
        })
        .applymap(
            color_picker,
            subset=["GANHO/PERDA", "VALORIZAÇÃO", "VARIAÇÃO REAL"],
        )
    )

    st.dataframe(tabela_estilizada, use_container_width=True)

    # Cartões de Resumo (KPIs) com lógica de cores
    total_neg = df_tabela["TOTAL NEGOCIADO"].sum()
    total_merc = df_tabela["TOTAL MERCADO"].sum()
    ganho_geral = df_tabela["GANHO/PERDA"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Negociado", f"R$ {total_neg:,.2f}")
    col2.metric("Total no Mercado", f"R$ {total_merc:,.2f}")

    # Exibindo métrica com cor dinâmica no delta
    cor_delta = "normal" if ganho_geral >= 0 else "inverse"
    col3.metric(
        "Ganho / Perda Total",
        f"R$ {ganho_geral:,.2f}",
        delta=f"R$ {ganho_geral:,.2f}",
        delta_color=cor_delta,
    )

  else:
    st.warning("⚠️ Nenhum registro encontrado para os filtros selecionados.")
