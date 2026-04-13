import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Conferência Dom Bosco", layout="wide")

st.title("📋 Conferência de Amostras (Autolac vs DB)")

def extrair_dados_autolac(pdf_path):
    dados = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Encontra o padrão de Protocolo (ex: 01-815104) e o nome que vem antes/depois
            # Ajustado para o layout do seu PDF
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if "Protocolo" in line: continue
                # Procura por números no formato XX-XXXXXX
                match = re.search(r'(\d{2}-\d{6})', line)
                if match:
                    protocolo = match.group(1).replace('-', '')
                    # O nome do paciente geralmente está na mesma linha ou na anterior
                    paciente = line.replace(match.group(1), '').strip()
                    # Tenta pegar os exames nas linhas seguintes até o próximo paciente
                    exames = []
                    for j in range(i+1, min(i+10, len(lines))):
                        if "D-" in lines[j]: # Seus exames começam com D-
                            exames.append(lines[j].split()[0])
                        if re.search(r'\d{2}-\d{6}', lines[j]): break
                    
                    for ex em exames:
                        dados.append({'protocolo': protocolo, 'paciente': paciente, 'exame': ex})
    return pd.DataFrame(dados)

def extrair_dados_db(pdf_path):
    dados = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # No DB, o atendimento é um número sequencial longo
            # Procuramos por "Atendimento" e pegamos o número abaixo ou ao lado
            atendimentos = re.findall(r'(\d{8,10})', text)
            for at em atendimentos:
                dados.append({'atendimento': at})
    return pd.DataFrame(dados)

file_a = st.file_uploader("Suba o PDF do Autolac", type="pdf")
file_d = st.file_uploader("Suba o PDF do DB", type="pdf")

if file_a and file_d:
    with st.spinner('Processando relatórios...'):
        df_autolac = extrair_dados_autolac(file_a)
        df_db = extrair_dados_db(file_d)
        
        if not df_autolac.empty and not df_db.empty:
            # Compara
            pendentes = df_autolac[~df_autolac['protocolo'].isin(df_db['atendimento'])]
            
            if pendentes.empty:
                st.success("✅ Todas as amostras do Autolac foram encontradas no DB!")
            else:
                st.error(f"🚨 Encontradas {len(pendentes.drop_duplicates('protocolo'))} amostras pendentes!")
                st.dataframe(pendentes[['protocolo', 'paciente', 'exame']].drop_duplicates())
        else:
            st.warning("Não foi possível extrair dados. Verifique se os PDFs são os relatórios originais.")
