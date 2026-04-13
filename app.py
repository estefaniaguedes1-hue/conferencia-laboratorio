import streamlit as st
import pandas as pd
import pdfplumber

st.set_page_config(page_title="Conferência de Amostras", layout="wide")

st.title("🧪 Verificação de Pendências (PDF ou Excel)")

def extrair_dados_pdf(arquivo):
    with pdfplumber.open(arquivo) as pdf:
        todas_as_linhas = []
        for pagina in pdf.pages:
            tabela = pagina.extract_table()
            if tabela:
                todas_as_linhas.extend(tabela)
        # Transforma a primeira linha em cabeçalho
        df = pd.DataFrame(todas_as_linhas[1:], columns=todas_as_linhas[0])
        return df

f_autolac = st.file_uploader("Relatório Autolac (PDF ou Excel)", type=["xlsx", "pdf"])
f_db = st.file_uploader("Relatório DB (PDF ou Excel)", type=["xlsx", "pdf"])

if f_autolac and f_db:
    try:
        # Lógica para ler Autolac (Excel ou PDF)
        if f_autolac.name.endswith('.pdf'):
            df_a = extrair_dados_pdf(f_autolac)
        else:
            df_a = pd.read_excel(f_autolac)

        # Lógica para ler DB (Excel ou PDF)
        if f_db.name.endswith('.pdf'):
            df_d = extrair_dados_pdf(f_db)
        else:
            df_d = pd.read_excel(f_db)
        
        # Padroniza colunas
        df_a.columns = [str(c).strip().lower() for c in df_a.columns]
        df_d.columns = [str(c).strip().lower() for c in df_d.columns]

        # Limpeza e Comparação
        df_d['atendimento_limpo'] = df_d['atendimento'].astype(str).str.replace('-', '', regex=False)
        df_a['protocolo_str'] = df_a['protocolo'].astype(str)

        pendentes = df_a[~df_a['protocolo_str'].isin(df_d['atendimento_limpo'])]

        if not pendentes.empty:
            st.error(f"Atenção: {len(pendentes)} amostras não encontradas no DB!")
            st.dataframe(pendentes[['protocolo', 'paciente', 'exame']])
        else:
            st.success("Tudo certo! Nenhuma pendência.")
            
    except Exception as e:
        st.error(f"Erro ao ler os arquivos. Verifique se os nomes das colunas estão visíveis no PDF. Detalhe: {e}")
