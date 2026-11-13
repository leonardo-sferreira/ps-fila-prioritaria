"""Verifica a integridade do formato de evidências com resultados sintéticos do coletor.

Os dados desta suite testam apenas o gerador; não representam resultados do produto.
"""

from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests/api"))
from run_test_evidence import clean, collect_http_results, collect_pytest_results, controlled_gate, executar_teste_nativo, execution_status, github_summary_write, identifier, junit_write, markdown_write, native_cases, source_cases  # noqa: E402
from pytest_http_evidence import _route  # noqa: E402
from test_ordenacao import executar  # noqa: E402


class EvidenceRunnerTest(unittest.TestCase):
    def test_timeout_transitorio_do_cli_xano_repete_sem_mudar_o_caso(self):
        aprovado = SimpleNamespace(returncode=0, stdout='{"status":"ok","results":[{"status":"pass"}]}')
        with patch("run_test_evidence.subprocess.run", side_effect=[subprocess.TimeoutExpired("xano", 50), aprovado]) as cli, patch("run_test_evidence.time.sleep") as espera:
            proc, result = executar_teste_nativo("teste-1", "ps-impacta", {})
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(result["results"][0]["status"], "pass")
        self.assertEqual([call.kwargs["timeout"] for call in cli.call_args_list], [50, 90])
        espera.assert_called_once_with(2.5)

    def test_resultado_json_tem_texto_legivel_sem_alterar_rastreabilidade(self):
        root = Path(__file__).resolve().parents[1]
        source = source_cases(root / "frontend/tests/test_auth_state.py", "Reflex", "unitario", False)
        case = next(case for case in source if case["node"].endswith("test_senha_correta_vai_para_o_codigo_sem_token_e_sem_guardar_a_senha"))
        self.assertEqual(case["id"], identifier(case["node"], "Reflex"))
        self.assertEqual(case["nome"], "Senha correta vai para o código sem token e sem guardar a senha")
        self.assertEqual(case["resultado_esperado"], case["nome"] + ".")
        self.assertTrue(case["assertions"])
        self.assertNotIn("estado.token ==", case["resultado_esperado"])

        native = next(case for case in native_cases() if case["nome"].startswith("Bordas 1:"))
        self.assertEqual(native["id"], identifier(native["node"], "Xano"))
        self.assertTrue(native["resultado_esperado"].startswith(native["nome"] + ". Valores esperados: "))
        self.assertIn("PA sistólica = 3", native["resultado_esperado"])
        self.assertTrue(native["assertions"])
        self.assertNotIn("expect.to_equal", native["resultado_esperado"])

    def test_junit_representa_falha_erro_e_nao_execucao(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = Path(tmp) / "resultados.xml"
            cases = [
                {"id": f"CT-REFLEX-{i}", "nome": "teste", "componente": "Reflex", "tipo": "unitario", "status": status, "duracao_segundos": 0.1, "motivo": "bloqueado" if status == "NOT_RUN" else "falhou", "resultado_obtido": status}
                for i, status in enumerate(("PASS", "FAIL", "ERROR", "SKIPPED", "NOT_RUN"), 1)
            ]
            junit_write(cases, xml, "exemplo")
            suite = ET.parse(xml).getroot()
            self.assertEqual((suite.attrib["tests"], suite.attrib["failures"], suite.attrib["errors"], suite.attrib["skipped"]), ("5", "1", "1", "2"))
            self.assertEqual(len(suite.findall("failure")), 0)
            self.assertEqual(sum(len(case.findall("failure")) for case in suite), 1)
            self.assertEqual(sum(len(case.findall("error")) for case in suite), 1)
            self.assertEqual(sum(len(case.findall("skipped")) for case in suite), 2)

    def test_resumo_mantem_status_e_redige_segredos(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "resumo.md"
            case = {"id": "CT-XANO-1", "requisito": None, "resultado_esperado": "HTTP 401", "resultado_obtido": "Não executado", "status": "NOT_RUN", "duracao_segundos": 0.0, "motivo": "credencial ausente"}
            data = {"execucao_id": "local", "data_utc": "2026-11-10T00:00:00Z", "commit": "abc", "branch": "v1", "suite": "exemplo", "ambiente": "local", "casos": [case], "limitacoes": ["sem ambiente"]}
            markdown_write(data, path)
            content = path.read_text(encoding="utf-8")
            self.assertIn("NOT_RUN: 1", content)
            self.assertIn("CT-XANO-1", content)
            self.assertNotIn("529.982.247-25", clean("CPF 529.982.247-25"))
            self.assertNotIn("ana@example.com", clean("ana@example.com"))

    def test_coleta_falha_nao_gera_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pytest.xml").write_text('<testsuite><testcase classname="tests.test_x.TestA" name="test_falha" time="0.2"><failure message="401 != 200">token=secreto</failure></testcase></testsuite>', encoding="utf-8")
            cases = [{"id": "CT-REFLEX-1", "node": "frontend/tests/test_x.py::TestA.test_falha", "nome": "falha", "status": "NOT_RUN", "duracao_segundos": 0.0, "motivo": "", "resultado_obtido": "Não executado"}]
            collect_pytest_results(directory, cases)
            self.assertEqual(cases[0]["status"], "FAIL")
            self.assertEqual(cases[0]["motivo"], "401 != 200")
            self.assertNotIn("secreto", (directory / "pytest.xml").read_text(encoding="utf-8"))

    def test_coleta_resultado_playwright_com_sufixo_navegador(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pytest.xml").write_text(
                '<testsuite><testcase classname="tests.e2e.test_publico" '
                'name="test_login_abre_aviso_e_volta[chromium]" time="0.2"/></testsuite>',
                encoding="utf-8",
            )
            cases = [{"id": "CT-REFLEX-1", "node": "tests/e2e/test_publico.py::test_login_abre_aviso_e_volta", "status": "NOT_RUN", "duracao_segundos": 0.0, "motivo": "", "resultado_obtido": "Não executado"}]
            collect_pytest_results(directory, cases)
            self.assertEqual(cases[0]["status"], "PASS")

    def test_funcao_xano_repete_apos_limite_temporario(self):
        limitado = SimpleNamespace(returncode=2, stderr="Your plan only supports 25 requests per 20 seconds.", stdout="")
        aprovado = SimpleNamespace(returncode=0, stderr="", stdout='{"status":"ok","result":{"id":1}}')
        with patch("test_ordenacao.time.sleep") as espera, patch("test_ordenacao.subprocess.run", side_effect=[limitado, aprovado]) as cli:
            self.assertEqual(executar("fila/proxima_ficha", fichas=[]), {"id": 1})
        self.assertEqual(cli.call_count, 2)
        self.assertEqual([chamada.args[0] for chamada in espera.call_args_list], [2.5, 21])

    def test_guardiao_recusa_host_de_producao_e_sem_confirmacao(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIn("Confirmação", controlled_gate())
        with patch.dict("os.environ", {
            "XANO_ISOLATED_CONFIRMATION": "CONFIRMO_WORKSPACE_DESCARTAVEL",
            "XANO_ISOLATED_API_HOST": "isolado.example.test",
            "XANO_AUTH_API_URL": "https://producao.example.test/api:auth",
        }, clear=True):
            self.assertIn("XANO_AUTH_API_URL", controlled_gate())

    def test_http_registra_somente_rota_status_e_campos(self):
        self.assertEqual(_route("https://privado.example.test/api/fichas/123?token=segredo"), "/api/fichas/{id}")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "http-events.jsonl"
            path.write_text('{"node":"tests/test_x.py::test_http","eventos":[{"metodo":"GET","endpoint":"/fichas/{id}","status":403,"resposta":{"tipo":"objeto","campos":["message"]}}]}\n', encoding="utf-8")
            cases = [{"node": "frontend/tests/test_x.py::test_http", "resultado_obtido": "Assertion falhou"}]
            collect_http_results(Path(tmp), cases)
            self.assertEqual(cases[0]["status_http_real"], [403])
            self.assertIn("GET /fichas/{id} → 403", cases[0]["resultado_obtido"])

    def test_execucao_bloqueada_ou_parcial_nao_e_aprovada(self):
        self.assertEqual(execution_status([{"status": "NOT_RUN"}], False), "BLOQUEADA")
        self.assertEqual(execution_status([{"status": "PASS"}, {"status": "NOT_RUN"}], False), "PARCIAL")
        self.assertEqual(execution_status([{"status": "PASS"}], False), "APROVADA")
        self.assertEqual(execution_status([{"status": "PASS"}], True), "ERRO_INFRAESTRUTURA")

    def test_resumo_actions_e_curto_e_mostra_resultado(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            data = {
                "suite": "xano-safe", "status_execucao": "PARCIAL",
                "casos": [{"status": "PASS"}, {"status": "NOT_RUN"}],
                "limitacoes": ["Unit tests nativos sem credencial"],
            }
            github_summary_write(data, path)
            content = path.read_text(encoding="utf-8")
            self.assertIn("xano-safe: PARCIAL", content)
            self.assertIn("| 1 | 0 | 0 | 0 | 1 |", content)
            self.assertIn("Unit tests nativos sem credencial", content)


if __name__ == "__main__":
    unittest.main()
