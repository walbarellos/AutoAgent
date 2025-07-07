# agent_bot.py
import os
import time
import json
import yaml
import openai
from datetime import datetime
from pathlib import Path

# 🚨 Configure sua chave da OpenAI via variável de ambiente OPENAI_API_KEY
openai.api_key = os.getenv("OPENAI_API_KEY")

# 📁 Carga de configurações e estado
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

PROJECT_DIR = Path(config["salvar_em"]) / config["projeto"]
PROMPTS_FILE = Path("prompts.txt")
ESTADO_FILE = Path("estado.json")
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"{datetime.now().date()}.log"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

def carregar_estado():
    if ESTADO_FILE.exists():
        with open(ESTADO_FILE, "r") as f:
            return json.load(f)
    return {"proximo_prompt": 0, "ultimos_arquivos": []}

def salvar_estado(estado):
    with open(ESTADO_FILE, "w") as f:
        json.dump(estado, f, indent=2)

def detectar_extensao(conteudo):
    if "```python" in conteudo:
        return ".py"
    elif "```html" in conteudo:
        return ".html"
    elif "```" in conteudo:
        return ".txt"
    elif conteudo.strip().startswith("#") or conteudo.strip().startswith("##"):
        return ".md"
    return ".txt"

def limpar_codigo(resposta):
    linhas = resposta.strip().splitlines()
    if linhas[0].startswith("```"):
        linhas = linhas[1:]
    if linhas[-1].startswith("```"):
        linhas = linhas[:-1]
    return "\n".join(linhas)

def salvar_resposta(texto, nome_base):
    ext = detectar_extensao(texto)
    pasta = PROJECT_DIR / datetime.now().strftime("%Y-%m-%d")
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{nome_base.replace(' ', '_').lower()}{ext}"
    caminho = pasta / nome
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(limpar_codigo(texto))
    log(f"Arquivo salvo: {caminho}")
    return str(caminho)

def enviar_prompt(prompt):
    resposta = openai.ChatCompletion.create(
        model=config["modelo"],
        messages=[
            {"role": "system", "content": "Você é um assistente de programação avançado."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )
    return resposta.choices[0].message.content

def ciclo():
    estado = carregar_estado()

    with open(PROMPTS_FILE, "r") as f:
        prompts = [p.strip() for p in f.readlines() if p.strip()]

    while estado["proximo_prompt"] < len(prompts):
        prompt_atual = prompts[estado["proximo_prompt"]]
        print(f"\n🚀 Executando prompt: {prompt_atual}")

        resposta = enviar_prompt(prompt_atual)
        caminho = salvar_resposta(resposta, prompt_atual)

        estado["ultimos_arquivos"].append(caminho)
        estado["proximo_prompt"] += 1
        salvar_estado(estado)

        print(f"✅ Código salvo: {caminho}")
        print("⏳ Aguardando próximo ciclo... (use `.` no seu terminal para continuar)")
        aguardar_ponto()

def aguardar_ponto():
    while True:
        entrada = input("Digite '.' para prosseguir: ").strip()
        if entrada == ".":
            break
        else:
            print("⛔ Use apenas '.' para continuar.")

if __name__ == "__main__":
    print("🧠 Agent-Bot Caracol iniciado com Sabedoria, Força e Beleza.")
    ciclo()
