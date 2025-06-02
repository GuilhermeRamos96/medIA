import streamlit as st
import tiktoken
import requests
import json
import os

# Configuração da página
st.set_page_config(page_title="Assistente de Diagnóstico", page_icon="🩺")

st.title("🔍 Assistente de Diagnóstico Médico")
st.caption("Versão com Groq API - compatível com modelos Llama")

# Link para gerar a chave API na Groq
st.markdown(
    "[🔑 Clique aqui para obter sua chave API da Groq](https://console.groq.com/keys)",
    unsafe_allow_html=True
)

# Criar um espaço para a chave API
api_key = st.text_input("Digite sua chave da API Groq:", type="password")

# Função para contar tokens - usando método mais seguro
def contar_tokens(texto):
    """Conta o número aproximado de tokens em um texto."""
    try:
        encoding = tiktoken.get_encoding("cl100k_base")  # Método mais seguro
        return len(encoding.encode(texto))
    except:
        # Estimativa aproximada se tiktoken falhar
        return len(texto.split()) * 1.3

# Função para fazer chamada à API Groq usando requests
def chamar_groq_api(api_key, prompt, max_tokens_resposta=500, temperatura=0.7):
    """
    Faz chamada para a API da Groq usando requests diretamente
    """
    url = "https://api.groq.com/openai/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "max_tokens": max_tokens_resposta,
        "temperature": temperatura
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        # Verificar se a requisição foi bem-sucedida
        if response.status_code == 200:
            response_data = response.json()
            return response_data['choices'][0]['message']['content']
        elif response.status_code == 401:
            raise Exception("Chave API inválida ou expirada")
        elif response.status_code == 429:
            raise Exception("Limite de requisições excedido. Tente novamente em alguns minutos")
        elif response.status_code == 400:
            error_data = response.json()
            error_message = error_data.get('error', {}).get('message', 'Erro na requisição')
            raise Exception(f"Erro na requisição: {error_message}")
        else:
            raise Exception(f"Erro HTTP {response.status_code}: {response.text}")
            
    except requests.exceptions.Timeout:
        raise Exception("Timeout na requisição. Tente novamente")
    except requests.exceptions.ConnectionError:
        raise Exception("Erro de conexão com a API da Groq")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Erro na requisição: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Erro ao decodificar resposta da API")
    except Exception as e:
        raise Exception(f"Erro inesperado: {str(e)}")

# Verifica se a chave foi inserida
if api_key:
    st.success("✅ Chave API da Groq inserida com sucesso!")
    
    # Definir modelo diretamente
    modelo_escolhido = "llama3-70b-8192"
    st.success(f"🧠 Modelo: {modelo_escolhido}")

    # Opções de análise
    tipo_analise = st.radio(
        "Selecione o tipo de análise:",
        ["Análise Simplificada (Recomendado para uso eficiente)", 
         "Análise Intermediária (Risco moderado de exceder limite)",
         "Análise Completa (Análise mais detalhada)"]
    )
    
    # Exibir contador de tokens estimados
    st.info("ℹ️ Monitore o uso de tokens para controlar custos e limites da API.")
    
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
        max_chars = 300 if tipo_analise == "Análise Simplificada (Recomendado para uso eficiente)" else (
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
        # Validar campos obrigatórios
        if not queixa_principal.strip():
            st.error("❌ Por favor, preencha a queixa principal.")
            st.stop()
        
        if not sintomas.strip():
            st.error("❌ Por favor, descreva os sintomas.")
            st.stop()
        
        # Construir prompt de acordo com o tipo de análise selecionado
        if tipo_analise == "Análise Simplificada (Recomendado para uso eficiente)":
            prompt = f"""
            Como assistente médico especializado, analise o seguinte caso clínico:
            
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa principal: {queixa_principal}
            Sintomas: {sintomas}
            
            Forneça uma análise concisa com:
            1. Diagnósticos diferenciais mais prováveis (máximo 3)
            2. Próximos passos recomendados
            
            Mantenha a resposta focada e objetiva.
            """
            max_tokens_resposta = 300
        elif tipo_analise == "Análise Intermediária (Risco moderado de exceder limite)":
            prompt = f"""
            Como assistente médico especializado, analise detalhadamente o seguinte caso clínico:
            
            Paciente: {idade} anos, {genero}.
            Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            Queixa principal: {queixa_principal}
            Sintomas: {sintomas}
            {f"Sinais vitais: {sinais_vitais}" if sinais_vitais else ""}
            
            Forneça uma análise estruturada com:
            1. Diagnósticos diferenciais mais prováveis (máximo 5)
            2. Próximos passos recomendados (exames e avaliações)
            3. Sinais de alarme a observar
            
            Justifique brevemente cada diagnóstico diferencial.
            """
            max_tokens_resposta = 500
        else:
            prompt = f"""
            Como assistente médico especializado, realize uma análise completa do seguinte caso clínico:
            
            Dados do Paciente:
            - Idade: {idade} anos
            - Gênero: {genero}
            - Comorbidades: {comorbidades if comorbidades else "Nenhuma relatada"}
            
            Apresentação Clínica:
            - Queixa principal: {queixa_principal}
            - Sintomas: {sintomas}
            {f"- Sinais vitais: {sinais_vitais}" if sinais_vitais else ""}
            {f"- Exame físico: {exame_fisico}" if exame_fisico else ""}
            {f"- Exames complementares: {exames}" if exames else ""}
            
            Forneça uma análise médica abrangente incluindo:
            1. Diagnósticos diferenciais ordenados por probabilidade
            2. Avaliação da gravidade e urgência de cada diagnóstico
            3. Próximos passos diagnósticos recomendados (exames laboratoriais, imagem, etc.)
            4. Sinais de alarme que exigem atenção médica imediata
            5. Orientações gerais para manejo inicial
            
            Justifique cada diagnóstico diferencial com base nos dados apresentados.
            """
            max_tokens_resposta = 800

        # Contar e exibir tokens
        tokens_estimados = contar_tokens(prompt)
        st.info(f"📊 Tokens estimados no prompt: {tokens_estimados}")
        
        # Aviso de limite para controle de uso
        if tokens_estimados > 2000:
            st.warning("⚠️ Este prompt contém muitos tokens. Considere usar a análise simplificada para economizar.")

        try:
            with st.spinner("🧠 Analisando com Groq AI..."):
                # Chamada para a API da Groq
                resposta = chamar_groq_api(
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
            
            # Aviso sobre disclaimers médicos
            st.warning("""
            ⚠️ **IMPORTANTE - Disclaimer Médico:**
            
            Esta análise é apenas para fins educacionais e informativos. 
            NÃO substitui consulta médica profissional, diagnóstico ou tratamento.
            Sempre procure orientação médica qualificada para questões de saúde.
            """)
            
            if (tokens_estimados + tokens_resposta) > 1500:
                st.info("💡 Esta análise consumiu muitos tokens. Considere usar a análise simplificada nas próximas consultas para otimizar o uso.")
        
        except Exception as e:
            st.error(f"❌ Erro ao acessar a API da Groq: {e}")
            st.info("""
            💡 Possíveis soluções:
            
            1. **Chave API**: Verifique se sua chave da Groq está correta e ativa
            
            2. **Limite de requisições**: Se excedeu o limite, aguarde alguns minutos antes de tentar novamente
            
            3. **Conexão**: Verifique sua conexão com a internet
            
            4. **Tamanho do prompt**: Se o erro for relacionado ao tamanho, use a análise simplificada
            
            5. **Conta Groq**: Verifique se sua conta está ativa em https://console.groq.com
            """)

else:
    st.warning("⚠️ Digite sua chave da API da Groq para começar.")
    st.info("""
    🔗 **Como obter sua chave API da Groq:**
    
    1. Acesse https://console.groq.com
    2. Faça login ou crie uma conta
    3. Navegue para a seção "API Keys"
    4. Gere uma nova chave API
    5. Cole a chave no campo acima
    """)
