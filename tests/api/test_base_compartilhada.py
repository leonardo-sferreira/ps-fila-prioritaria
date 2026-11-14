"""Base compartilhada (add-base-compartilhada): auditoria, fuso e parâmetros.

Os testes estáticos leem o XanoScript versionado em backend/xano e rodam sem rede.
Os de integração só conferem o que dá para provar sem token (o login exige código por e-mail).
"""

import os
import re
import ssl
import unittest
from pathlib import Path

import httpx
from dotenv import dotenv_values

RAIZ = Path(__file__).resolve().parents[2]
XANO = RAIZ / "backend/xano"
API = XANO / "api"
URL_CADASTROS = os.getenv("XANO_CADASTROS_API_URL") or dotenv_values(RAIZ / "frontend/.env").get("XANO_CADASTROS_API_URL")

CHAMADA_AUDITORIA = re.compile(r'function\.run\s+"registrar_alteracao"\s*\{')
ESCRITA_HISTORICO = re.compile(r"db\.(add|edit|patch|del|delete|bulk\.\w+|truncate)\s+historico_alteracao\b")
PARAMETRO_PADRAO = re.compile(r'\{chave:\s*"(\w+)",\s*valor:\s*"([^"]*)"\}')
REGRA = re.compile(r"^\s*(\w+)\s*:\s*\{tipo:\s*\"(\w+)\",\s*minimo:\s*(-?\d+|null),\s*maximo:\s*(-?\d+|null)", re.M)


def _endpoints() -> list[Path]:
    return sorted(API.rglob("*.xs"))


def _fim_do_bloco(texto: str, abertura: int) -> int:
    """Posição da chave que fecha o bloco aberto em `abertura` (índice do '{')."""
    profundidade = 0
    for indice in range(abertura, len(texto)):
        if texto[indice] == "{":
            profundidade += 1
        elif texto[indice] == "}":
            profundidade -= 1
            if profundidade == 0:
                return indice
    raise AssertionError("bloco sem fechamento")


def _transacoes(texto: str) -> list[tuple[int, int]]:
    return [(m.end() - 1, _fim_do_bloco(texto, m.end() - 1)) for m in re.finditer(r"db\.transaction\s*\{", texto)]


def _parametros_iniciais() -> dict[str, str]:
    valores: dict[str, str] = {}
    for arquivo in XANO.glob("function/**/inicializar*.xs"):
        for chave, valor in PARAMETRO_PADRAO.findall(arquivo.read_text(encoding="utf-8")):
            valores[chave] = valor
    return valores


def _regras() -> dict[str, tuple[str, str, str]]:
    texto = (XANO / "function/cadastros/regra_parametro.xs").read_text(encoding="utf-8")
    return {chave: (tipo, minimo, maximo) for chave, tipo, minimo, maximo in REGRA.findall(texto)}


class AuditoriaTest(unittest.TestCase):
    def test_nenhum_endpoint_grava_no_historico_diretamente(self) -> None:
        violacoes = [p.relative_to(XANO).as_posix() for p in _endpoints() if ESCRITA_HISTORICO.search(p.read_text(encoding="utf-8"))]
        self.assertEqual(violacoes, [], "só a função registrar_alteracao pode gravar em historico_alteracao")

    def test_so_a_funcao_de_auditoria_grava_no_historico(self) -> None:
        gravam = {p.relative_to(XANO).as_posix() for p in XANO.rglob("*.xs") if ESCRITA_HISTORICO.search(p.read_text(encoding="utf-8"))}
        self.assertEqual(gravam, {"function/registrar_alteracao.xs"})

    def test_auditoria_dos_endpoints_fica_dentro_da_transacao(self) -> None:
        fora = []
        total = 0
        for arquivo in _endpoints():
            texto = arquivo.read_text(encoding="utf-8")
            transacoes = _transacoes(texto)
            for chamada in CHAMADA_AUDITORIA.finditer(texto):
                total += 1
                if not any(inicio < chamada.start() < fim for inicio, fim in transacoes):
                    linha = texto.count("\n", 0, chamada.start()) + 1
                    fora.append(f"{arquivo.relative_to(XANO).as_posix()}:{linha}")
        self.assertGreater(total, 0)
        self.assertEqual(fora, [], "registrar_alteracao precisa estar no db.transaction da alteração")

    def test_responsavel_vem_da_sessao(self) -> None:
        """O usuário auditado é sempre o autenticado, nunca um valor vindo do corpo da requisição."""
        suspeitos = []
        for arquivo in _endpoints():
            texto = arquivo.read_text(encoding="utf-8")
            for chamada in CHAMADA_AUDITORIA.finditer(texto):
                bloco = texto[chamada.end() - 1 : _fim_do_bloco(texto, chamada.end() - 1)]
                if "$input.usuario_id" in bloco or "usuario_id" not in bloco:
                    linha = texto.count("\n", 0, chamada.start()) + 1
                    suspeitos.append(f"{arquivo.relative_to(XANO).as_posix()}:{linha}")
        self.assertEqual(suspeitos, [])


class ParametrosTest(unittest.TestCase):
    VALORES_DA_BASELINE = {
        "IDADE_MINIMA_IDOSO": "60",
        "IDADE_MAXIMA_CRIANCA": "11",
        "amarelas_por_ciclo": "2",
        "azuis_por_ciclo": "1",
        "CICLO_PRE_TRIAGEM_PRIORITARIOS": "2",
        "CICLO_PRE_TRIAGEM_NORMAIS": "1",
        "tamanho_previsao": "5",
        "INTERVALO_CHAMADA_SEGUNDOS": "30",
        "TENTATIVAS_CHAMADA": "3",
        "HORAS_EXPIRACAO": "24",
    }

    def test_valores_iniciais_da_baseline(self) -> None:
        iniciais = _parametros_iniciais()
        for chave, valor in self.VALORES_DA_BASELINE.items():
            with self.subTest(chave=chave):
                self.assertEqual(iniciais.get(chave), valor)

    def test_todo_parametro_inicial_tem_regra_e_respeita_os_limites(self) -> None:
        regras = _regras()
        for chave, valor in _parametros_iniciais().items():
            if chave == "POSICAO_CICLO_PRE_TRIAGEM":
                continue  # interno, não editável
            with self.subTest(chave=chave):
                self.assertIn(chave, regras)
                tipo, minimo, maximo = regras[chave]
                if tipo == "INTEIRO":
                    self.assertLessEqual(int(minimo), int(valor))
                    self.assertLessEqual(int(valor), int(maximo))

    def test_fuso_nao_e_parametro(self) -> None:
        self.assertNotIn("FUSO_HORARIO", _parametros_iniciais())
        self.assertNotIn("FUSO_HORARIO", _regras())

    def test_fuso_fixo_em_sao_paulo(self) -> None:
        fusos = set()
        for arquivo in XANO.rglob("*.xs"):
            fusos.update(re.findall(r'(?:to_timestamp|format_timestamp|transform_timestamp)[^\n]*?"((?:America|UTC|Etc)[\w/+-]*)"', arquivo.read_text(encoding="utf-8")))
        self.assertEqual(fusos, {"America/Sao_Paulo"})


class ConsultaSemTokenTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not URL_CADASTROS:
            raise unittest.SkipTest("Configure XANO_CADASTROS_API_URL para a integração")

    def test_parametros_sem_token_e_com_token_adulterado(self) -> None:
        for cabecalho in ({}, {"Authorization": "Bearer token-adulterado"}):
            with self.subTest(cabecalho=bool(cabecalho)):
                resposta = httpx.get(f"{URL_CADASTROS.rstrip('/')}/parametros", headers=cabecalho, timeout=20, verify=ssl.create_default_context())
                self.assertEqual(resposta.status_code, 401)


if __name__ == "__main__":
    unittest.main()
