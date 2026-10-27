import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
import os

st.set_page_config(page_title="Dashboard de Finanças & Investimentos", page_icon="📈", layout="wide")

st.title("🚀 Dashboard de Gestão Financeira & Mercado em Tempo Real")
st.markdown("Painel interativo conectado à sua base de dados e cotações ao vivo da B3.")

EXCEL_FILE = "Controle_planilha_v8_2024_financas_24 (2)111.xlsx"

@st.cache_data(ttl=600)
def carregar_dados(path):
    if not os.path.exists(path):
        return None, None, None
    df_base = pd.read_excel(path, sheet_name="Base de dados", header=3)
    df_resumo = pd.read_excel(path, sheet_name="RESUMO", header=1)
    df_info = pd.read_excel(path, sheet_name="INFO AÇÕES")
    return df_base, df_resumo, df_info

df_base, df_resumo, df_info = carregar_dados(EXCEL_FILE)

if df_base is None:
    st.error(f"⚠️ Arquivo '{EXCEL_FILE}' não encontrado. Certifique-se de que ele está na mesma pasta que o app.py.")
else:
    aba1, aba2, aba3 = st.tabs(["📊 Visão Geral & Planejamento", "💼 Carteira & Mercado (Tempo Real)", "🎯 Simulador de Aportes"])
    
    with aba1:
        st.subheader("Resumo de Entradas, Saídas e Aportes")
        if 'Ano' in df_base.columns:
            anos = sorted(df_base['Ano'].dropna().unique())
            ano_selecionado = st.selectbox("Selecione o Ano:", anos)
            df_filtrado = df_base[df_base['Ano'] == ano_selecionado]
        else:
            df_filtrado = df_base
            
        total_entradas = df_filtrado[df_filtrado['TIPO MOVIMENTAÇÃO'] == 'Entradas']['VALOR 
TOTAL'].sum()
        total_saidas = df_filtrado[df_filtrado['TIPO MOVIMENTAÇÃO'] == 'Saídas']['VALOR 
TOTAL'].sum()
        total_aportes = df_filtrado[df_filtrado['TIPO MOVIMENTAÇÃO'] == 'Aporte']['VALOR 
TOTAL'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Entradas Totais", f"R$ {total_entradas:,.2f}")
        col2.metric("💸 Saídas (Gastos)", f"R$ {total_saidas:,.2f}")
        col3.metric("📈 Aportes Realizados", f"R$ {total_aportes:,.2f}")
        taxa_poupanca = ((total_entradas - total_saidas) / total_entradas * 100) if total_entradas > 0 else 0
        col4.metric("📊 Taxa de Poupança", f"{taxa_poupanca:.1f}%")
        
        st.markdown("---")
        st.subheader("Top Despesas (Saídas)")
        saidas_df = df_filtrado[df_filtrado['TIPO MOVIMENTAÇÃO'] == 'Saídas']
        if not saidas_df.empty:
            gastos_cat = saidas_df.groupby('DESCRIÇÃO')['VALOR 
TOTAL'].sum().reset_index().sort_values(by='VALOR 
TOTAL', ascending=False).head(10)
            fig_gastos = px.bar(gastos_cat, x='VALOR 
TOTAL', y='DESCRIÇÃO', orientation='h', title="Top 10 Maiores Gastos", color='VALOR 
TOTAL', color_continuous_scale='Reds')
            fig_gastos.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_gastos, use_container_width=True)
            
    with aba2:
        st.subheader("📡 Cotações da Bolsa em Tempo Real (Aba INFO AÇÕES)")
        col_ticker = 'Símbolo do ticker' if 'Símbolo do ticker' in df_info.columns else df_info.columns[4]
        tickers_orig = df_info[col_ticker].dropna().tolist()
        
        if tickers_orig:
            tickers_b3 = [t + ".SA" if not t.endswith(".SA") and len(t) <= 6 else t for t in tickers_orig]
            dados_ao_vivo = []
            for t_orig, t_b3 in zip(tickers_orig, tickers_b3):
                try:
                    info_ticker = yf.Ticker(t_b3)
                    hist = info_ticker.history(period="2d")
                    if not hist.empty:
                        preco_atual = hist['Close'].iloc[-1]
                        preco_anterior = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
                        var_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
                        dados_ao_vivo.append({"Ticker": t_orig, "Preço Atual (R$)": round(preco_atual, 2), "Variação Diária (%)": round(var_pct, 2)})
                except:
                    pass
            if dados_ao_vivo:
                df_mercado = pd.DataFrame(dados_ao_vivo)
                st.dataframe(df_mercado, use_container_width=True)
                fig_var = px.bar(df_mercado, x='Ticker', y='Variação Diária (%)', title="Variação Diária dos Ativos (%)", color='Variação Diária (%)', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig_var, use_container_width=True)
            else:
                st.warning("Não foi possível carregar as cotações em tempo real.")
                
    with aba3:
        st.subheader("🎯 Simulador de Independência Financeira & Juros Compostos")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            aporte_mensal = st.number_input("Aporte Mensal (R$)", value=1500, step=100)
        with col_s2:
            patrimonio_inicial = st.number_input("Patrimônio Atual / Seed (R$)", value=5000, step=500)
        with col_s3:
            anos_proj = st.slider("Horizonte de Tempo (Anos)", 1, 30, 10)
        
        taxa_anual = st.slider("Rentabilidade Anual Esperada (%)", 4.0, 18.0, 10.0, 0.5)
        taxa_mensal = (1 + taxa_anual / 100)**(1/12) - 1
        
        meses = anos_proj * 12
        evolução = []
        patrimonio = patrimonio_inicial
        total_aportado = patrimonio_inicial
        
        for m in range(1, meses + 1):
            patrimonio = (patrimonio + aporte_mensal) * (1 + taxa_mensal)
            total_aportado += aporte_mensal
            if m % 12 == 0:
                evolução.append({"Ano": m // 12, "Patrimônio Total": round(patrimonio, 2), "Total Aportado": round(total_aportado, 2), "Juros Acumulados": round(patrimonio - total_aportado, 2)})
        
        df_sim = pd.DataFrame(evolução)
        if not df_sim.empty:
            fig_proj = px.area(df_sim, x='Ano', y=['Total Aportado', 'Juros Acumulados'], title="Evolução do Patrimônio")
            st.plotly_chart(fig_proj, use_container_width=True)
