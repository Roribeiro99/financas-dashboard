# --- Bloco Único de Código para Google Colab ---

# 1. Instalação e Importação de Bibliotecas
# Instala as bibliotecas necessárias, se não estiverem presentes
!pip install -q yfinance openpyxl pandas plotly ipywidgets

import pandas as pd
import yfinance as yf
import plotly.express as px
import ipywidgets as widgets
from IPython.display import display, clear_output
import datetime

# 2. Carregamento dos Dados (Adapte o nome do arquivo se necessário)
excel_filename = "Controle_planilha_v8_2024_financas_24 (2)111.xlsx"

try:
    print(f"Carregando planilha: {excel_filename}...")
    # Lendo as abas principais
    df_base = pd.read_excel(excel_filename, sheet_name="Base de dados", header=3)
    df_info = pd.read_excel(excel_filename, sheet_name="INFO AÇÕES")
    print("✅ Planilha carregada com sucesso!")
except FileNotFoundError:
    print(f"⚠️ Arquivo '{excel_filename}' não encontrado.")
    print("Por favor, faça o upload do arquivo para o ambiente do Colab (barra lateral esquerda) ou edite o nome do arquivo no código.")
    # Pausa para permitir upload manual se necessário (opcional)
    # from google.colab import files
    # uploaded = files.upload()
    # excel_filename = list(uploaded.keys())[0]
    # df_base = pd.read_excel(excel_filename, sheet_name="Base de dados", header=3)
    # df_info = pd.read_excel(excel_filename, sheet_name="INFO AÇÕES")
except Exception as e:
    print(f"Ocorreu um erro ao carregar a planilha: {e}")
    df_base = pd.DataFrame() # Cria dataframe vazio para evitar erros posteriores
    df_info = pd.DataFrame()

# 3. Definição das Funções do Painel

def atualizar_mercado():
    """Busca cotações atuais do mercado via yfinance."""
    col_ticker = 'Símbolo do ticker' if 'Símbolo do ticker' in df_info.columns else df_info.columns[4]
    tickers_orig = df_info[col_ticker].dropna().unique().tolist()

    tickers_b3 = [t + ".SA" if not t.endswith(".SA") and len(t) <= 6 else t for t in tickers_orig]
    dados_ao_vivo = {}
    for t_orig, t_b3 in zip(tickers_orig, tickers_b3):
        try:
            info_ticker = yf.Ticker(t_b3)
            hist = info_ticker.history(period="2d")
            if not hist.empty:
                preco_atual = hist['Close'].iloc[-1]
                preco_anterior = hist['Close'].iloc[-2] if len(hist) > 1 else preco_atual
                var_pct = ((preco_atual - preco_anterior) / preco_anterior) * 100
                dados_ao_vivo[t_orig] = {"Preço Atual": round(preco_atual, 2), "Variação %": round(var_pct, 2)}
        except:
            dados_ao_vivo[t_orig] = {"Preço Atual": 0, "Variação %": 0}
    return dados_ao_vivo

def gerar_relatorio(tipo_mov, feito):
    """Filtra a base de dados e gera o relatório formatado."""
    if df_base.empty:
        return pd.DataFrame()

    # Aplica filtros
    df_filtrado = df_base[(df_base['TIPO MOVIMENTAÇÃO'] == tipo_mov) & (df_base['FEITO?'] == feito)]

    # Agrupa por ATIVO
    df_agrupado = df_filtrado.groupby('ATIVO').agg(
        COTAS=('QUANTIDADE', 'sum'),
        TOTAL_NEGOCIADO=('VALOR \nTOTAL', 'sum'),
        VALOR_TOTAL_MERCADO=('VALOR TOTAL MERCADO', 'sum')
    ).reset_index()

    # Busca dados de mercado em tempo real
    dados_mercado = atualizar_mercado()

    # Cria o DataFrame final com a estrutura desejada
    df_final = pd.DataFrame(columns=[
        '#', 'COTAS', 'PREÇO NEGOCIADO', 'PREÇO MERCADO',
        'TOTAL NEGOCIADO', 'TOTAL MERCADO', 'GANHO/PERDA',
        'VALORIZAÇÃO', 'VARIAÇÃO REAL'
    ])

    # Preenche o DataFrame (Lógica de classificação simplificada baseada nos dados de exemplo)
    acoes_conhecidas = ['BBAS3', 'BBSE3', 'EQTL3', 'ITSA3', 'SAPR4', 'SBSP3']

    # Ações
    acoes_df = df_agrupado[df_agrupado['ATIVO'].isin(acoes_conhecvidas)].copy()
    if not acoes_df.empty:
        df_final.loc[0] = ['Ações', acoes_df['COTAS'].sum(), 0, 0, acoes_df['TOTAL_NEGOCIADO'].sum(), acoes_df['VALOR_TOTAL_MERCADO'].sum(), acoes_df['GANHO/PERDA'].sum(), (acoes_df['VALOR_TOTAL_MERCADO'].sum()/acoes_df['TOTAL_NEGOCIADO'].sum())-1, 0]
        for index, row in acoes_df.iterrows():
            df_final.loc[len(df_final)] = [row['ATIVO'], row['COTAS'], row['TOTAL_NEGOCIADO']/row['COTAS'] if row['COTAS'] != 0 else 0, dados_mercado.get(row['ATIVO'], {}).get('Preço Atual', 0), row['TOTAL_NEGOCIADO'], row['VALOR_TOTAL_MERCADO'], row['VALOR_TOTAL_MERCADO'] - row['TOTAL_NEGOCIADO'], (row['VALOR_TOTAL_MERCADO']/row['TOTAL_NEGOCIADO'])-1 if row['TOTAL_NEGOCIADO'] != 0 else 0, 0]

    # FIIs
    fiis_df = df_agrupado[~df_agrupado['ATIVO'].isin(acoes_conhecvidas)].copy()
    if not fiis_df.empty:
        df_final.loc[len(df_final)] = ['FIIs', fiis_df['COTAS'].sum(), 0, 0, fiis_df['TOTAL_NEGOCIADO'].sum(), fiis_df['VALOR_TOTAL_MERCADO'].sum(), fiis_df['GANHO/PERDA'].sum(), (fiis_df['VALOR_TOTAL_MERCADO'].sum()/fiis_df['TOTAL_NEGOCIADO'].sum())-1, 0]
        for index, row in fiis_df.iterrows():
            df_final.loc[len(df_final)] = [row['ATIVO'], row['COTAS'], row['TOTAL_NEGOCIADO']/row['COTAS'] if row['COTAS'] != 0 else 0, dados_mercado.get(row['ATIVO'], {}).get('Preço Atual', 0), row['TOTAL_NEGOCIADO'], row['VALOR_TOTAL_MERCADO'], row['VALOR_TOTAL_MERCADO'] - row['TOTAL_NEGOCIADO'], (row['VALOR_TOTAL_MERCADO']/row['TOTAL_NEGOCIADO'])-1 if row['TOTAL_NEGOCIADO'] != 0 else 0, 0]

    # Total Geral
    if not df_final.empty:
        total_cotas_real = df_final[df_final['#'].apply(lambda x: x not in ['Ações', 'FIIs'])]['COTAS'].sum()
        total_negociado_real = df_final[df_final['#'].apply(lambda x: x not in ['Ações', 'FIIs'])]['TOTAL NEGOCIADO'].sum()
        total_mercado_real = df_final[df_final['#'].apply(lambda x: x not in ['Ações', 'FIIs'])]['TOTAL MERCADO'].sum()
        total_ganho_perda_real = df_final[df_final['#'].apply(lambda x: x not in ['Ações', 'FIIs'])]['GANHO/PERDA'].sum()
        df_final.loc[len(df_final)] = ['Total Geral', total_cotas_real, 0, 0, total_negociado_real, total_mercado_real, total_ganho_perda_real, (total_mercado_real/total_negociado_real)-1 if total_negociado_real != 0 else 0, 0]

    # Formatação
    df_formatado = df_final.copy()
    cols_to_format = ['PREÇO NEGOCIADO', 'PREÇO MERCADO', 'TOTAL NEGOCIADO', 'TOTAL MERCADO', 'GANHO/PERDA']
    for col in cols_to_format:
        df_formatado[col] = df_formatado[col].apply(lambda x: f"{x:,.2f}" if x != 0 else "-")
    cols_to_percent = ['VALORIZAÇÃO', 'VARIAÇÃO REAL']
    for col in cols_to_percent:
        df_formatado[col] = df_formatado[col].apply(lambda x: f"{x:.2%}" if x != 0 else "-")

    return df_formatado

# 4. Criação dos Widgets Interativos

# Obtém valores únicos para os dropdowns
if not df_base.empty:
    tipos_mov = sorted(df_base['TIPO MOVIMENTAÇÃO'].dropna().unique())
    status_feito = sorted(df_base['FEITO?'].dropna().unique())
else:
    tipos_mov = []
    status_feito = []

# Cria os widgets
dropdown_tipo = widgets.Dropdown(
    options=tipos_mov,
    value='Aporte' if 'Aporte' in tipos_mov else (tipos_mov[0] if tipos_mov else None),
    description='TIPO MOV:',
    style={'description_width': 'initial'}
)
dropdown_feito = widgets.Dropdown(
    options=status_feito,
    value='SIM' if 'SIM' in status_feito else (status_feito[0] if status_feito else None),
    description='FEITO?',
    style={'description_width': 'initial'}
)

btn_atualizar = widgets.Button(
    description='Atualizar Relatório',
    button_style='success', # 'success', 'info', 'warning', 'danger' or ''
    tooltip='Clique para aplicar os filtros e buscar cotações',
    icon='refresh'
)

output = widgets.Output()
data_atualizacao = widgets.Label(value=f"Última atualização: Nunca")

# 5. Lógica de Atualização do Painel

def on_update_button_clicked(b):
    with output:
        clear_output(wait=True)
        print("Processando dados e buscando cotações... ⏳")
        try:
            df_result = gerar_relatorio(dropdown_tipo.value, dropdown_feito.value)
            clear_output()
            if not df_result.empty:
                display(data_atualizacao)
                data_atualizacao.value = f"Última atualização: {datetime.datetime.now().strftime('%H:%M:%S')}"
                display(widgets.HBox([dropdown_tipo, dropdown_feito, btn_atualizar])) # Removi o display do botão para que ele não fique repetindo
                display(df_result.style.set_properties(**{'text-align': 'right'}).hide_index()) # Exibe o DataFrame formatado
            else:
                display(widgets.HBox([dropdown_tipo, dropdown_feito, btn_atualizar]))
                print("⚠️ Nenhum dado encontrado para os filtros selecionados.")
        except Exception as e:
            clear_output()
            display(widgets.HBox([dropdown_tipo, dropdown_feito, btn_atualizar]))
            print(f"❌ Ocorreu um erro ao gerar o relatório: {e}")

btn_atualizar.on_click(on_update_button_clicked)

# 6. Exibição Inicial do Painel

display(widgets.HBox([dropdown_tipo, dropdown_feito, btn_atualizar]))
display(output)

# Executa a atualização inicial para mostrar o relatório com os filtros pré-selecionados
on_update_button_clicked(None)
