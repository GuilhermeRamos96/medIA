import streamlit as st
import openai  

# Configuração do título da página
st.set_page_config(page_title="Assistente de Diagnóstico", page_icon="🩺")

st.title("🔍 Assistente de Diagnóstico Médico")

# Link para gerar a chave API na OpenAI
st.markdown(
    "[🔑 Clique aqui para obter sua chave API da OpenAI](https://platform.openai.com/signup)",
    unsafe_allow_html=True
)

# Criar um espaço para a chave API
api_key = st.text_input("Digite sua chave da API OpenAI:", type="password")

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

    with st.form("diagnostico_form"):
        st.subheader("📋 Dados do Paciente")

        idade = st.number_input("Idade do paciente:", min_value=0, max_value=120, step=1)
        genero = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
        comorbidades = st.text_input("Comorbidades (ou 'sem comorbidades conhecidas'):")

        st.subheader("🩺 Queixa Principal e Sintomas")
        queixa_principal = st.text_area("Queixa principal e duração:")
        
        sintomas = st.text_area("Liste os sintomas associados (separados por vírgula):")

        sinais_vitais = st.text_area("Sinais vitais (se disponíveis):")
        exame_fisico = st.text_area("Achados relevantes no exame físico:")
        exames = st.text_area("Exames laboratoriais ou de imagem (se disponíveis):")

        enviar = st.form_submit_button("🔎 Analisar")

    if enviar:
        prompt = f"""
        Analise a seguinte constelação de sintomas para um possível diagnóstico diferencial:

        Paciente: {idade} anos, {genero}, com {comorbidades}.

        Queixa principal: {queixa_principal}.

        Sintomas associados:
        - {sintomas.replace(',', '\n    - ')}

        Sinais vitais: {sinais_vitais}

        Achados relevantes no exame físico:
        - {exame_fisico}

        Exames laboratoriais ou de imagem (se disponíveis):
        - {exames}

        Por favor:
        1. Liste os diagnósticos diferenciais organizados por PROBABILIDADE, do mais provável ao menos provável, considerando os dados epidemiológicos e a apresentação clínica. Para cada diagnóstico, forneça uma breve justificativa baseada nos sintomas e sinais apresentados.

        2. Em seguida, reorganize os mesmos diagnósticos por GRAVIDADE, do mais grave (potencialmente fatal ou com necessidade de intervenção imediata) ao menos grave. Para cada diagnóstico, indique o tempo estimado para intervenção e possíveis complicações caso não seja tratado adequadamente.

        3. Sugira os próximos passos diagnósticos mais apropriados para confirmar ou descartar cada uma das hipóteses principais.

        4. Indique se há sinais de alarme ou 'red flags' na apresentação que exigiriam atenção imediata ou encaminhamento para emergência.
        """

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
        
        except Exception as e:
            st.error(f"❌ Erro ao acessar a API: {e}")

else:
    st.warning("⚠️ Digite sua chave da API para começar.")
