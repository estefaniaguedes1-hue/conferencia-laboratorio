import streamlit as st
import pandas as pd
import pdfplumber
import re

st.set_page_config(page_title="Conferência Dom Bosco", layout="wide")

st.title("📋 Conferência de Amostras (Autolac vs DB)")
st.info("O sistema agora cruza Protocolo e Exame para garantir que nada foi esquecido.")

def extrair_dados(arquivo, tipo):
    dados = []
    with pdfplumber.open(arquivo) as pdf:
        texto_completo = ""
        for pagina in pdf.pages:
            texto_completo += pagina.extract_text() + "\n"
        
        if tipo == "autolac":
            # No Autolac, buscamos o padrão XX-XXXXXX e os exames D-XXXX
            blocos = re.split(r'(\d{2}-\d{6})', texto_completo)
            for i in range(1, len(blocos), 2):
                protocolo = blocos[i].replace('-', '')
                conteudo_bloco = blocos[i+1]
                
                # Pega o nome do paciente (geralmente as primeiras palavras após o protocolo)
                linhas_bloco = conteudo_bloco.strip().split('\n')
                nome_paciente = linhas_bloco[0].split('08/04')[0].strip() if linhas_bloco else "Paciente não identificado"
                
                # Busca todos os exames D- no bloco desse protocolo
                exames = re.findall(r'(D-\w+)', conteudo_bloco)
                for ex in exames:
                    dados.append({'ID': protocolo, 'Paciente': nome_paciente, 'Exame': ex.replace('D-', '')})
        
        else: # Tipo DB
            # No DB, o atendimento é um número (ex: 67028918) e os exames são siglas (TSH, T4L, etc)
            # Vamos extrair todos os números de 8 dígitos e as siglas próximas
            # Mas para ser mais seguro, vamos pegar apenas os Atendimentos e os Procedimentos citados
            atendimentos = re.findall(r'\b(\d{8})\b', texto_completo)
            # Extraímos siglas de exames (letras maiúsculas de 2 a 6 caracteres)
            exames_db = re.findall(r'\b([A-Z0-9]{2,8})\b', texto_completo)
            
            # Criamos um set de combinações encontradas no texto para busca rápida
            return texto_completo
            
    return pd.DataFrame(dados)

f_a = st.file_uploader("Relatório Autolac (Interno)", type="pdf")
f_d = st.file_uploader("Relatório DB (Terceiro)", type="pdf")

if f_a and f_d:
    with st.spinner('Cruzando informações...'):
        df_autolac = extrair_dados(f_a, "autolac")
        texto_db = extrair_dados(f_d, "db") # Texto bruto do DB para busca
        
        if not df_autolac.empty:
            pendencias = []
            for _, linha in df_autolac.iterrows():
                # Verifica se o Protocolo E o Exame aparecem no texto do DB
                # Removemos o "D-" do exame do Autolac para buscar no DB
                if linha['ID'] not in texto_db or linha['Exame'] not in texto_db:
                    pendencias.append(linha)
            
            df_pendencias = pd.DataFrame(pendencias)
            
            if df_pendencias.empty:
                st.success("✅ Tudo ok! Todos os pacientes e exames foram localizados no DB.")
            else:
                st.error(f"⚠️ Encontradas {len(df_pendencias)} pendências de exames:")
                st.dataframe(df_pendencias[['ID', 'Paciente', 'Exame']].drop_duplicates(), use_container_width=True)
                
                csv = df_pendencias.to_csv(index=False).encode('utf-8-sig')
                st.download_button("Baixar Lista de Pendências", csv, "pendencias.csv", "text/csv")
