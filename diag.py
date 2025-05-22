import streamlit as st
import tiktoken
import importlib.util
import pkg_resources

# Configuração da página
st.set_page_config(page_title="Assistente de Diagnóstico", page_icon="🩺")

st.title("🔍 Assistente de Diagnóstico Médico")
st.caption("Versão universal - compatível com qualquer versão do OpenAI SDK")

# Verificar versão do OpenAI
try:
    openai_version = pkg_resources.get_distribution("openai").version
    st.info(f"📦 Versão detectada da biblioteca OpenAI: {openai_version}")
    is_new_version = int(openai_version.split('.')[0]) >= 1
except:
    st.warning("⚠️ Não foi possível detectar a versão da biblioteca OpenAI. O código tentará se adaptar automaticamente.")
    is_new_version = True  # Assume versão nova por padrão

# Importar OpenAI
import openai

# Link para gerar a chave API na OpenAI
st.markdown(
    "[🔑 Clique aqui para obter sua chave API da OpenAI](https://platform.openai.com/signup)",
    unsafe_allow_html=True
)

# Criar um espaço para a chave API
api_key = st.text_input("Digite sua chave da API OpenAI:", type="password")

# Função para contar tokens - usando método mais seguro
def contar_tokens(texto):
    """Conta o número aproximado de tokens em um texto."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # Método mais seguro
        return len(encoding.encode(texto))
    except:
        # Estimativa aproximada se tiktoken falhar
        return len(texto.split()) * 1.3

# Função para fazer chamada à API (compatível com ambas versões)
def chamar_openai_api(api_key, prompt, max_tokens_resposta=500, temperatura=0.7):
    if is_new_version:
        # Versão nova (>=1.0.0)
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens_resposta,
                temperature=temperatura
            )
            return response.choices[0].message.content
        except Exception as e:
            # Se falhar, tenta método alternativo
            try:
                client = openai.Client(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens_resposta,
                    temperature=temperatura
                )
                return response.choices[0].message.content
            except Exception as e2:
                raise Exception(f"Erro na API (nova versão): {e}\nTentativa alternativa: {e2}")
    else:
        # Versão antiga (<1.0.0)
        try:
            openai.api_key = api_key
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens_resposta,
                temperature=temperatura
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Erro na API (versão antiga): {e}")

# Verifica se a chave foi inserida
if api_key:
    st.success("✅ Chave API inserida com sucesso!")
    
    # Definir modelo diretamente (sem verificação)
    modelo_escolhido = "gpt-3.5-turbo"
    st.success(f"🧠 Modelo: {modelo_escolhido}")

    # Opções de análise
    tipo_analise = st.radio(
        "Selecione o tipo de análise:",
        ["Análise Simplificada (Recomendado para contas gratuitas)", 
         "Análise Intermediária (Risco moderado de exceder limite)",
         "Análise Completa (Pode exceder limite de contas gratuitas)"]
    )
    
    # Exibir contador de tokens estimados
    st.info("ℹ️ Contas gratuitas têm limite de ~4000 tokens (entrada + resposta).")
    
    with st.form("diagnostico_form"):
        st.subheader("📋 Dados do Paciente")

        col1, col2 = st.columns(2)
        with col1:
            idade = st.number_input("Idade:", min_value=0, max_value=120, step=1)
        with col2:
            genero = st.selectbox("Gênero:", ["Masculino", "Feminino", "Outro"])
        
        # Campo opcional
        comorbidades = st.text_input("Comorbidades (opcional):", 
                                    placeholder="Deixe em branco se não houver")

        st.subheader("🩺 Queixa Principal e Sintomas")
        
        # Limitar caracteres para evitar excesso de tokens
        max_chars = 300 if tipo_analise == "Análise Simplificada (Recomendado para contas gratuitas)" else (
                    500 if tipo_analise == "Análise Intermediária (Risco moderado de exceder limite)" else 1000)
        
        queixa_principal = st.text_area("Queixa principal:", 
                                       placeholder="Descreva o problema principal",
                                       max_chars=max_chars)
        
        sintomas = st.text_area("Sintomas:", 
                               placeholder="Liste os sintomas principais",
                               max_chars=max_chars)

        # Campos opcionais - expandidos apenas se necessário
        with st.expander("Informações Adicionais (opcional)"):
            sinais_vitais = st.text_area("Sinais vitais:", 
                                        placeholder="Deixe em branco se não disponível",
                                        max_chars=200)
            exame_fisico = st.text_area("Achados no exame físico:", 
                                       placeholder="Deixe em branco se não disponível",
                                       max_chars=200)
            exames = st.text_area("Exames laboratoriais/imagem:", 
                                 placeholder="Deixe em branco se não disponível",
                                 max_chars=200)

        enviar = st.form_submit_button("🔎 Analisar")

    if enviar:
        # Construir prompt de acordo com o tipo de análise selecionado
        if tipo_analise == "Análise Simplificada (Recomendado para contas gratuitas)":
            prompt = f"""
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa: {queixa_principal}
            Sintomas: {sintomas}
            
            Forneça:
            1. Diagnósticos diferenciais mais prováveis
            2. Próximos passos recomendados
            """
            max_tokens_resposta = 300
        elif tipo_analise == "Análise Intermediária (Risco moderado de exceder limite)":
            prompt = f"""
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa: {queixa_principal}
            Sintomas: {sintomas}
            {f"Sinais vitais: {sinais_vitais}" if sinais_vitais else ""}
            
            Forneça:
            1. Diagnósticos diferenciais mais prováveis
            2. Próximos passos recomendados
            3. Sinais de alarme a observar
            """
            max_tokens_resposta = 500
        else:
            prompt = f"""
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa: {queixa_principal}
            Sintomas: {sintomas}
            {f"Sinais vitais: {sinais_vitais}" if sinais_vitais else ""}
            {f"Exame físico: {exame_fisico}" if exame_fisico else ""}
            {f"Exames: {exames}" if exames else ""}
            
            Forneça:
            1. Diagnósticos diferenciais do mais provável ao menos provável
            2. Gravidade dos diagnósticos e tempo estimado para intervenção
            3. Próximos passos recomendados (exames e procedimentos)
            4. Sinais de alarme que exigem atenção imediata
            """
            max_tokens_resposta = 800

        # Contar e exibir tokens
        tokens_estimados = contar_tokens(prompt)
        st.info(f"📊 Tokens estimados no prompt: {tokens_estimados}")
        
        # Aviso de limite para contas gratuitas
        if tokens_estimados > 1500:
            st.error("❌ Este prompt é muito longo para contas gratuitas. Use a análise simplificada.")
            st.stop()

        try:
            with st.spinner("🧠 Analisando..."):
                # Usando a função universal que se adapta à versão
                resposta = chamar_openai_api(
                    api_key=api_key,
                    prompt=prompt,
                    max_tokens_resposta=max_tokens_resposta,
                    temperatura=0.7
                )
            
            st.subheader("📄 Resultado da Análise:")
            st.markdown(resposta)
            
            # Exibir uso de tokens
            tokens_resposta = contar_tokens(resposta)
            st.info(f"📊 Tokens na resposta: {tokens_resposta}")
            st.success(f"📊 Total de tokens utilizados: {tokens_estimados + tokens_resposta}")
            
            if (tokens_estimados + tokens_resposta) > 3500:
                st.warning("⚠️ Esta análise consumiu muitos tokens. Considere usar a análise simplificada nas próximas consultas.")
        
        except Exception as e:
            st.error(f"❌ Erro ao acessar a API: {e}")
            st.info("""
            💡 Possíveis soluções:
            
            1. Se o erro for de quota insuficiente, use a análise simplificada ou reduza o tamanho dos campos.
            
            2. Se o erro for relacionado à versão da biblioteca OpenAI, você pode:
               - Para versão antiga: `pip install openai==0.28`
               - Para versão nova: `pip install --upgrade openai`
            
            3. Verifique se a chave API está correta e ativa.
            """)

else:
    st.warning("⚠️ Digite sua chave da API para começar.")
