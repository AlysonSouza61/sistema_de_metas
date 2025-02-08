import streamlit as st
import pandas as pd
import plotly.express as px
import mysql.connector
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title="ZARAPLAST",
    page_icon=":bar_chart:",
    layout="wide",
)

st.header("ZARAPLAST - Departamento: Assistência Técnica")
st.markdown("---")

# Função para conectar ao MySQL e buscar dados
def get_mysql_data(query):
    conexao = mysql.connector.connect(
        host='162.241.103.245',
        user='datatech_zara',
        password='L$@8,oR]S6K=',
        database='datatech_mc_zaraplast',
    )
    cursor = conexao.cursor()
    cursor.execute(query)
    resultado = cursor.fetchall()
    cursor.close()
    conexao.close()
    return resultado

# Buscar dados do banco
tecnico = pd.DataFrame(get_mysql_data('SELECT * FROM tecnico'), columns=["id", "Nome"])
df3 = pd.DataFrame(get_mysql_data('SELECT * FROM NCA'), columns=["id", "Cliente", "Peso"])
df2 = pd.DataFrame(get_mysql_data('SELECT * FROM sd'), columns=["id", "Desvios", "Peso"])

# Upload do arquivo
uploaded_file = st.file_uploader("Selecione um arquivo CSV ou XLSM", type=["csv", "xlsm"])

if uploaded_file:
    file_extension = uploaded_file.name.split(".")[-1]
    if file_extension == "csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file, sheet_name='Dados Gerais RAC - Atualizado')
    
    # Processamento dos dados
    df['SD'] = df['Sigla Defeito'].map(df2.set_index('Desvios')['Peso']).fillna(0)
    df['NCA'] = df['Cliente'].map(df3.set_index('Cliente')['Peso']).fillna(0)
    df[['Qtde Devolvida', 'Qtde Reclamada']] = df[['Qtde Devolvida', 'Qtde Reclamada']].fillna(0)
    df['SN'] = df.apply(lambda row: 0 if row['Qtde Devolvida'] >= row['Qtde Reclamada'] or (row['Qtde Devolvida'] == 0 and row['Qtde Reclamada'] == 0)
                        else 1 if row['Qtde Devolvida'] == 0
                        else row['Qtde Devolvida'] / row['Qtde Reclamada'] if row['Qtde Reclamada'] != 0
                        else 0, axis=1)
    df['NPS'] = df['SD'] * df['NCA'] * df['SN']
    df['MC'] = 1000 * df['NPS']
    df['Mês'] = pd.to_datetime(df['Data Corte']).dt.strftime('%B')
    df['Ano'] = pd.to_datetime(df['Data Corte']).dt.year
    
    # Menu lateral para filtros
    st.sidebar.header("Filtros")
    mes_selecionado = st.sidebar.selectbox("Mês", options=["Todos"] + sorted(df['Mês'].unique().tolist()))
    ano_selecionado = st.sidebar.selectbox("Ano", options=["Todos"] + sorted(df['Ano'].unique().tolist()))
    cliente_selecionado = st.sidebar.selectbox("Cliente", options=["Todos"] + sorted(df['Cliente'].unique().tolist()))
    tecnico_selecionado = st.sidebar.selectbox("Nome do Técnico", options=["Todos"] + sorted(tecnico['Nome'].unique().tolist()))
    
    # Aplicação dos filtros
    if mes_selecionado != "Todos":
        df = df[df['Mês'] == mes_selecionado]
    if ano_selecionado != "Todos":
        df = df[df['Ano'] == ano_selecionado]
    if cliente_selecionado != "Todos":
        df = df[df['Cliente'] == cliente_selecionado]
    if tecnico_selecionado != "Todos":
        df = df[df['Iniciador'] == tecnico_selecionado]
    
    # Gráfico
    fig = px.bar(df, x='Mês', y='MC', title='MC por Mês', labels={'MC': 'MC (Mil Pontos)'}, text_auto=True)
    st.plotly_chart(fig, use_container_width=True)
    
    # Exibir dataframe filtrado
    st.dataframe(df)
