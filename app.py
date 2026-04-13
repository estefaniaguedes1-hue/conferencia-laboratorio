import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(page_title="Conferência de Amostras", layout="wide")

st.title("🧪 Sistema de Verificação de Pendências")
st.markdown("Compare o relatório **Autolac** com o relatório **DB** para identificar extravios.")

# Upload dos arquivos
col1, col2 = st.columns(2)

with col1:
    file_autolac = st.file_uploader("Upload Relatório Autolac (Interno)", type=["xlsx", "xls", "csv"])

with col2:
    file_db = st.file_uploader("Upload Relatório DB (Terceiro)", type=["xlsx", "xls", "csv"])

if file_autolac and file_db:
    try:
        # Lendo os arquivos
        df_autolac = pd.read_excel(file_autolac) if "xls" in file_autolac.name else pd.read_csv(file_autolac)
        df_db = pd.read_excel(file_db) if "xls" in file_db.name else pd.read_csv(file_db)

        # --- TRATAMENTO DOS DADOS ---
        
        # 1. Autolac: protocolo, paciente e exame
        # Nota: Ajuste os nomes das colunas entre aspas se houver diferença no arquivo real
        autolac_selecionado = df_autolac[['protocolo', 'paciente', 'exame']].copy()
        
        # 2. DB: atendimento (limpar "-"), nome do paciente e procedimento
        db_selecionado = df_db[['atendimento', 'nome do paciente', 'procedimento']].copy()
        
        # Limpeza do traço no atendimento
        db_selecionado['atendimento_limpo'] = db_selecionado['atendimento'].astype(str).str.replace('-', '', regex=False)

        # --- CRUZAMENTO (Lógica de Pendência) ---
        # Verificamos quem está no Autolac mas o protocolo NÃO está no atendimento_limpo do DB
        pendencias = autolac_selecionado[~autolac_selecionado['protocolo'].astype(str).isin(db_selecionado['atendimento_limpo'])]

        # --- EXIBIÇÃO ---
        st.divider()
        if not pendencias.empty:
            st.error(f"⚠️ Foram encontradas {len(pendencias)} amostras pendentes!")
            st.dataframe(pendencias, use_container_width=True)
            
            # Botão para baixar as pendências
            csv = pendencias.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="Baixar Lista de Pendências (CSV)",
                data=csv,
                file_name="amostras_pendentes.csv",
                mime="text/csv",
            )
        else:
            st.success("✅ Nenhuma pendência encontrada! Todas as amostras chegaram ao destino.")

    except Exception as e:
        st.error(f"Erro ao processar os arquivos: {e}")
        st.info("Dica: Verifique se os nomes das colunas nos arquivos são exatamente: protocolo, paciente, exame, atendimento, nome do paciente e procedimento.")
