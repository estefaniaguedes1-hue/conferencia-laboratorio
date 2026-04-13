import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Conferência Dom Bosco", layout="wide")

st.title("📋 Sistema de Conferência de Amostras")
st.info("Suba os PDFs gerados pelos sistemas Autolac e DB para verificar o que não chegou.")

def extrair_autolac(arquivo):
    dados = []
    with pdfplumber.open(arquivo) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if not texto: continue
            
            linhas = texto.split('\n')
            paciente_atual = "Não identificado"
            
            for linha in linhas:
                # 1. Identifica o Protocolo (Ex: 28-013536 ou 67-028832)
                # O padrão é: dois dígitos, traço, seis dígitos
                match_prot = re.search(r'(\d{2}-\d{6})', linha)
                
                if match_prot:
                    protocolo_limpo = match_prot.group(1).replace('-', '')
                    # O nome costuma ser o que vem depois do protocolo na mesma linha
                    # ou o texto antes do protocolo. Vamos pegar a linha limpa:
                    paciente_atual = linha.replace(match_prot.group(1), '').replace('08/04/2026', '').strip()
                
                # 2. Identifica o Exame (Ex: D-ACU, D-CRE, D-TSH)
                if "D-" in linha:
                    partes = linha.split()
                    for p in partes:
                        if p.startswith("D-"):
                            dados.append({
                                'Protocolo': protocolo_limpo if match_prot else dados[-1]['Protocolo'] if dados else "S/P",
                                'Paciente': paciente_atual,
                                'Exame': p
                            })
    return pd.DataFrame(dados)

def extrair_db(arquivo):
    # No DB o atendimento é um número como 67028918
    atendimentos = []
    with pdfplumber.open(arquivo) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                # Busca números de 8 dígitos que comecem com 67 ou similares
                achados = re.findall(r'\b(\d{8})\b', texto)
                atendimentos.extend(achados)
    return list(set(atendimentos)) # Retorna lista sem duplicados

col1, col2 = st.columns(2)
with col1:
    f_autolac = st.file_uploader("Relatório Autolac (PDF)", type="pdf")
with col2:
    f_db = st.file_uploader("Relatório DB (PDF)", type="pdf")

if f_autolac and f_db:
    with st.spinner('Cruzando dados...'):
        df_a = extrair_autolac(f_autolac)
        list_d = extrair_db(f_db)
        
        if not df_a.empty:
            # Compara: quem está no Autolac mas o protocolo NÃO está na lista do DB
            pendentes = df_a[~df_a['Protocolo'].isin(list_d)]
            
            if pendentes.empty:
                st.success("✅ Excelente! Todas as amostras constam no laboratório DB.")
            else:
                st.error(f"⚠️ Atenção: {len(pendentes.drop_duplicates(subset=['Protocolo', 'Exame']))} exames pendentes encontrados.")
                
                # Formata a tabela para ficar bonita
                st.dataframe(pendentes[['Protocolo', 'Paciente', 'Exame']].drop_duplicates(), use_container_width=True)
                
                # Botão para baixar
                csv = pendentes.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Baixar Lista de Pendências", csv, "pendencias.csv", "text/csv")
        else:
            st.warning("Não consegui ler os dados do Autolac. Verifique se o PDF está correto.")
