import streamlit as st
import openai
import tiktoken  # Biblioteca para contar tokens

# Configuração do título da página
st.set_page_config(page_title="Assistente de Diagnóstico", page_icon="🩺")

st.title("🔍 Assistente de Diagnóstico Médico")
st.caption("Versão otimizada para economia de tokens")

# Link para gerar a chave API na OpenAI
st.markdown(
    "[🔑 Clique aqui para obter sua chave API da OpenAI](https://platform.openai.com/signup)",
    unsafe_allow_html=True
)

# Criar um espaço para a chave API
api_key = st.text_input("Digite sua chave da API OpenAI:", type="password")

# Função para contar tokens
def contar_tokens(texto):
    """Conta o número aproximado de tokens em um texto."""
    try:
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        return len(encoding.encode(texto))
    except:
        # Estimativa aproximada se tiktoken falhar
        return len(texto.split()) * 1.3

# Função para verificar os modelos disponíveis
def verificar_modelo(api_key):
    try:
        client = openai.OpenAI(api_key=api_key)
        modelos_disponiveis = [model.id for model in client.models.list().data]
        if "gpt-4" in modelos_disponiveis:
            return "gpt-4"
        elif "gpt-3.5-turbo" in modelos_disponiveis:
            return "gpt-3.5-turbo"
        else:
            return None
    except Exception as e:
        st.error(f"Erro ao verificar modelos: {e}")
        return None

# Verifica se a chave foi inserida
if api_key:
    st.success("✅ Chave API inserida com sucesso! Verificando modelos disponíveis...")

    modelo_escolhido = verificar_modelo(api_key)

    if modelo_escolhido:
        st.success(f"🧠 Modelo disponível: {modelo_escolhido}")
    else:
        st.error("❌ Erro: sua chave não tem acesso a modelos disponíveis.")
        st.stop()

    # Opções de análise
    tipo_analise = st.radio(
        "Selecione o tipo de análise:",
        ["Análise Simplificada (Economia de tokens)", "Análise Completa (Mais tokens)"]
    )
    
    # Exibir contador de tokens estimados
    st.info("ℹ️ Contas gratuitas têm limite de tokens. A análise completa pode exceder esse limite.")
    
    with st.form("diagnostico_form"):
        st.subheader("📋 Dados do Paciente")

        col1, col2 = st.columns(2)
        with col1:
            idade = st.number_input("Idade:", min_value=0, max_value=120, step=1)
        with col2:
            genero = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
        
        # Campo opcional
        comorbidades = st.text_input("Comorbidades (opcional):", placeholder="Deixe em branco se não houver")

        st.subheader("🩺 Queixa Principal e Sintomas")
        queixa_principal = st.text_area("Queixa principal:", placeholder="Descreva o problema principal")
        
        sintomas = st.text_area("Sintomas:", placeholder="Liste os sintomas principais")

        # Campos opcionais - expandidos apenas se necessário
        with st.expander("Informações Adicionais (opcional)"):
            sinais_vitais = st.text_area("Sinais vitais:", placeholder="Deixe em branco se não disponível")
            exame_fisico = st.text_area("Achados no exame físico:", placeholder="Deixe em branco se não disponível")
            exames = st.text_area("Exames laboratoriais/imagem:", placeholder="Deixe em branco se não disponível")

        enviar = st.form_submit_button("🔎 Analisar")

    if enviar:
        # Construir prompt de acordo com o tipo de análise selecionado
        if tipo_analise == "Análise Simplificada (Economia de tokens)":
            prompt = f"""
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa: {queixa_principal}
            Sintomas: {sintomas}
            
            Forneça:
            1. Diagnósticos diferenciais mais prováveis
            2. Próximos passos recomendados
            3. Sinais de alarme a observar
            """
        else:
            prompt = f"""
            Analise a seguinte constelação de sintomas para um possível diagnóstico diferencial:

            Paciente: {idade} anos, {genero}, com {comorbidades if comorbidades else "sem comorbidades relatadas"}.

            Queixa principal: {queixa_principal}.

            Sintomas associados: {sintomas}

            {f"Sinais vitais: {sinais_vitais}" if sinais_vitais else ""}
            {f"Achados relevantes no exame físico: {exame_fisico}" if exame_fisico else ""}
            {f"Exames laboratoriais ou de imagem: {exames}" if exames else ""}

            Analise os dados clínicos e forneça:

            1. Probabilidade: Liste os diagnósticos diferenciais do mais provável ao menos provável, com justificativa.
            2. Gravidade: Reorganize os diagnósticos do mais grave ao menos grave, indicando tempo para intervenção.
            3. Próximos Passos: Sugira exames e procedimentos para confirmar ou descartar as principais hipóteses.
            4. Sinais de Alarme: Identifique "red flags" que exigem atenção imediata.
            """

        # Contar e exibir tokens
        tokens_estimados = contar_tokens(prompt)
        st.info(f"📊 Tokens estimados no prompt: {tokens_estimados}")
        
        # Aviso de limite
        if tokens_estimados > 1000 and tipo_analise == "Análise Completa (Mais tokens)":
            st.warning("⚠️ Atenção: Este prompt pode consumir muitos tokens. Considere usar a análise simplificada se tiver uma conta gratuita.")
            continuar = st.button("Continuar mesmo assim")
            if not continuar:
                st.stop()

        try:
            with st.spinner("🧠 Analisando..."):
                client = openai.OpenAI(api_key=api_key)  

                response = client.chat.completions.create(
                    model=modelo_escolhido,
                    messages=[{"role": "user", "content": prompt}]
                )

                resposta = response.choices[0].message.content
            
            st.subheader("📄 Resultado da Análise:")
            st.markdown(resposta)
            
            # Exibir uso de tokens
            tokens_resposta = contar_tokens(resposta)
            st.info(f"📊 Tokens na resposta: {tokens_resposta}")
            st.success(f"📊 Total de tokens utilizados: {tokens_estimados + tokens_resposta}")
        
        except Exception as e:
            st.error(f"❌ Erro ao acessar a API: {e}")
            st.info("💡 Se o erro for de quota insuficiente, considere adicionar um método de pagamento ou usar a análise simplificada.")

else:
    st.warning("⚠️ Digite sua chave da API para começar.")
