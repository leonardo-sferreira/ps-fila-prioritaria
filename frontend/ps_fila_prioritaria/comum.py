"""Utilidades compartilhadas: ambiente, mensagens de erro da API e formatação de datas, CPF e e-mail."""

import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

from ps_fila_prioritaria import api


ARQUIVO_ENV = Path(__file__).resolve().parents[1] / ".env"


# Fonte única do aviso de privacidade: a página mostra este arquivo sem alterá-lo (add-privacidade, D1).
ARQUIVO_AVISO_PRIVACIDADE = Path(__file__).resolve().parents[2] / "docs" / "aviso-de-privacidade.md"


def carregar_variaveis_ambiente() -> None:
    """Carrega o arquivo de ambiente do frontend sem depender do diretório atual."""
    load_dotenv(dotenv_path=ARQUIVO_ENV)


carregar_variaveis_ambiente()


# Códigos da API da ficha e da classificação traduzidos para a Recepção/Triagem.
MENSAGENS_ERRO_API = {
    "FICHA_NAO_FINALIZADA_EXISTENTE": "Este paciente já está na fila de atendimento (ficha aguardando ou chamada). Não é possível abrir outra ficha.",
    "FICHA_FORA_DA_TRIAGEM": "Esta ficha já foi chamada ou encerrada e não pode mais ser alterada.",
    "SINTOMA_LIVRE_DESCRICAO_INVALIDA": "Descreva o sintoma não listado com 3 a 80 caracteres.",
    "SINTOMA_LIVRE_PONTUACAO_INVALIDA": "Escolha a gravidade do sintoma não listado: 1, 2 ou 3.",
    "SINTOMA_LIVRE_DUPLICADO": "Há sintomas não listados repetidos.",
    "SINTOMA_LIVRE_EXISTE_NO_CATALOGO": "Um sintoma digitado já existe na lista: selecione-o na pesquisa.",
    "SINTOMAS_LIVRES_LIMITE": "Limite de 10 sintomas não listados por ficha.",
    "JUSTIFICATIVA_OBRIGATORIA": "A justificativa é obrigatória.",
    "PRIORIDADE_IGUAL_A_CALCULADA": "Essa já é a prioridade calculada. Escolha outra cor.",
    "PRIORIDADE_INVALIDA": "Escolha a prioridade.",
    "FICHA_SEM_PRIORIDADE": "Defina a cor antes de confirmar: salve os sinais vitais ou ajuste a prioridade manualmente.",
    "DESTINO_NAO_CONFIGURADO": "Não há especialidade de destino configurada. Avise o Administrador.",
    "SENHA_NAO_ATIVA": "Esta ficha não tem senha ativa para o comprovante.",
    "SENHA_NAO_GERADA": "Não foi possível gerar a senha. Tente confirmar de novo.",
    # Cadastros do Administrador (add-cadastros-administrador).
    "ESPECIALIDADE_COM_FICHAS": "Há fichas aguardando ou chamadas nesta especialidade. Desative depois que a fila esvaziar.",
    "MEDICO_COM_FICHA_CHAMADA": "O médico tem uma ficha chamada em andamento. Desative depois que ele concluir.",
    "PLANTAO_SOBREPOSTO": "Este horário se sobrepõe a outro plantão do mesmo médico.",
    "PLANTAO_INICIADO": "Plantão já iniciado: não pode ser removido nem ter o início alterado; só o fim pode mudar.",
    "PARAMETRO_NAO_EDITAVEL_AQUI": "Este parâmetro não pode ser alterado pela tela.",
    "PARAMETRO_FORA_DOS_LIMITES": "Valor fora dos limites permitidos para este parâmetro.",
    "IDADES_INCOERENTES": "As idades precisam ficar em ordem: criança < tabela adulta ≤ idoso.",
    "LIMIARES_INCOERENTES": "O limiar da Amarela precisa ser menor que o da Vermelha.",
    "FAIXA_SOBREPOSTA": "Esta faixa se sobrepõe a outra do mesmo sinal vital.",
}


MENSAGEM_LIMITE_XANO ="O sistema recebeu muitos acessos ao mesmo tempo. Aguarde alguns segundos e tente novamente."


def _codigo_erro(resposta: httpx.Response) -> str:
    """Código de negócio devolvido pela API (ex.: FICHA_SEM_PRIORIDADE), ou vazio."""
    try:
        corpo: Any = resposta.json()
    except ValueError:
        return ""
    if isinstance(corpo, dict):
        codigo = corpo.get("message") or corpo.get("error") or corpo.get("code")
        if isinstance(codigo, str):
            return codigo
    return ""


def _mensagem_erro(resposta: httpx.Response) -> str:
    """Extrai a mensagem pública devolvida pela API sem expor detalhes internos."""
    try:
        corpo: Any = resposta.json()
    except ValueError:
        return "Não foi possível concluir a solicitação."

    if isinstance(corpo, dict):
        mensagem = corpo.get("message") or corpo.get("error") or corpo.get("code")
        # Limite de requisições do plano gratuito do Xano (429, texto em inglês). Os 429 do nosso backend
        # ("Aguarde N segundos...") já vêm em português e seguem abaixo sem alteração.
        if getattr(resposta, "status_code", None) == 429 and isinstance(mensagem, str) and "requests per" in mensagem:
            return MENSAGEM_LIMITE_XANO
        if mensagem == "CPF_DUPLICADO":
            return "Já existe paciente com este CPF (CPF_DUPLICADO). Pesquise novamente para carregar o cadastro."
        if mensagem == "FICHA_SEM_SINTOMA_OU_OBSERVACAO":
            return "Informe ao menos um sintoma ou uma observação."
        if isinstance(mensagem, str) and mensagem.startswith("SINAL_VITAL_INVALIDO:"):
            campo = mensagem.split(":", 1)[1]
            return f"Valor fora do aceito em {NOME_SINAL_VITAL.get(campo, campo)}. Confira o número digitado."
        if isinstance(mensagem, str) and mensagem in MENSAGENS_ERRO_API:
            return MENSAGENS_ERRO_API[mensagem]
        if isinstance(mensagem, str):
            return mensagem
    return "Não foi possível concluir a solicitação."


def _postar_publico(estado: Any, caminho: str, corpo: dict[str, Any]) -> httpx.Response | None:
    """Chama um endpoint público de autenticação; em falha de conexão ou configuração, avisa e devolve None."""
    try:
        return api.requisitar("POST", "XANO_AUTH_API_URL", caminho, json=corpo)
    except api.ConfiguracaoAusente:
        estado.mensagem = "Configure XANO_AUTH_API_URL para conectar o login à API do PS."
    except httpx.RequestError:
        estado.mensagem = "Não foi possível conectar à API de autenticação."
    return None


def _segundos_reenvio(resposta: httpx.Response) -> int:
    return int(resposta.json().get("reenvio_em_segundos") or 60)


async def _contar_reenvio(estado: Any) -> None:
    """Contador do botão "Reenviar código"; um único contador por vez em cada estado."""
    async with estado:
        if estado.contando:
            return
        estado.contando = True
    while True:
        await asyncio.sleep(1)
        async with estado:
            estado.segundos_reenvio = max(estado.segundos_reenvio - 1, 0)
            if estado.segundos_reenvio == 0:
                estado.contando = False
                return


def _texto_reenvio(segundos: int) -> str:
    return f"Reenviar código em {segundos // 60}:{segundos % 60:02d}"


def _mascarar_email(email: str) -> str:
    """a***@ps.com.br, como no Figma (tela A2)."""
    usuario, _, dominio = email.partition("@")
    return f"{usuario[:1]}***@{dominio}" if dominio else email


def mascarar_cpf(valor: object) -> str:
    """***.456.789-** nas telas internas; CPF ausente ou sem 11 dígitos não aparece em parte (spec privacidade)."""
    digitos = "".join(c for c in str(valor or "") if c.isdigit())
    if len(digitos) != 11:
        return "—"
    return f"***.{digitos[3:6]}.{digitos[6:9]}-**"


def _id_da_rota(caminho: str) -> str:
    """Último trecho do caminho (/recepcao/ficha/12 → "12"); substitui o `router.page.params` obsoleto no Reflex 0.8."""
    return str(caminho or "").rstrip("/").rsplit("/", 1)[-1]


def _timestamp_segundos(valor: Any) -> float | None:
    """Aceita timestamps Xano em milissegundos ou datas ISO."""
    if isinstance(valor, (int, float)):
        return valor / 1000 if valor > 100_000_000_000 else float(valor)
    if isinstance(valor, str):
        try:
            data = datetime.fromisoformat(valor.replace("Z", "+00:00"))
            return data.replace(tzinfo=timezone.utc).timestamp() if data.tzinfo is None else data.timestamp()
        except ValueError:
            return None
    return None


# O Brasil não tem horário de verão desde 2019: America/Sao_Paulo é sempre UTC-3. Evita depender do pacote tzdata no Windows.
FUSO_BRASILIA = timezone(timedelta(hours=-3))


PREFIXO_TICKET = {"PEDIATRICO": "C", "PREFERENCIAL": "P", "NORMAL": "N"}


def formatar_ticket(tipo: Any, numero: Any) -> str:
    """Ticket do Totem como aparece para o paciente: prefixo do tipo e número com 3 dígitos (C-004, N-031)."""
    return f"{PREFIXO_TICKET.get(str(tipo), '?')}-{int(numero or 0):03d}"


def _hora_brasilia(valor: Any, segundos: bool = False) -> str:
    instante = _timestamp_segundos(valor)
    if instante is None:
        return "—"
    return datetime.fromtimestamp(instante, FUSO_BRASILIA).strftime("%H:%M:%S" if segundos else "%H:%M")


NOME_SINAL_VITAL = {
    "pa_sistolica": "PA sistólica",
    "fc": "frequência cardíaca",
    "fr": "frequência respiratória",
    "temperatura": "temperatura",
    "spo2": "SpO2",
    "glicemia": "glicemia",
}


def _data_hora_brasilia(valor: Any) -> str:
    instante = _timestamp_segundos(valor)
    if instante is None:
        return "—"
    return datetime.fromtimestamp(instante, FUSO_BRASILIA).strftime("%d/%m/%Y %H:%M")
