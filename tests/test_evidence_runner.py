import json
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
from run_test_evidence import clean, collect_http_results, collect_pytest_results, controlled_gate, executar_teste_nativo, execution_status, github_summary_write, junit_write, markdown_write, native_cases, source_cases  # noqa: E402
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
        import hashlib
        from run_test_evidence import catalog
        case = next(c for c in catalog("reflex") if c["node"].endswith("test_senha_correta_vai_para_o_codigo_sem_token_e_sem_guardar_a_senha"))
        alias = "CT-REFLEX-" + hashlib.sha256(case["node"].encode()).hexdigest()[:10].upper()
        self.assertIn(alias, case["aliases_historicos"])
        self.assertEqual(case["nome"], "Senha correta vai para o código sem token e sem guardar a senha")
        self.assertEqual(case["resultado_esperado"], case["nome"] + ".")
        self.assertNotIn("assertions", case)
        self.assertNotIn("estado.token ==", case["resultado_esperado"])
        native = next(c for c in catalog("xano-safe") if c["nome"].startswith("Bordas 1:"))
        self.assertTrue(native["resultado_esperado"].startswith(native["nome"] + ". Valores esperados: "))
        self.assertIn("PA sistólica = 3", native["resultado_esperado"])
        self.assertNotIn("expect.to_equal", native["resultado_esperado"])

    def test_junit_representa_falha_erro_e_nao_execucao(self):
        with tempfile.TemporaryDirectory() as tmp:
            xml = Path(tmp) / "resultados.xml"
            cases = [
                {"id": f"CT-REFLEX-{i}", "nome": "teste", "componente": "Reflex", "tipo": "unitario", "status": status, "duracao_segundos": 0.1, "motivo": "bloqueado" if status == "NOT_RUN" else "falhou", "resultado_obtido": status}
                for i, status in enumerate(("PASSED", "FAILED", "ERROR", "SKIPPED", "NOT_RUN"), 1)
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
            (directory / "pytest.xml").write_text('<testsuite><testcase classname="tests.test_x.TestA" name="test_falha" time="0.2"><failure message="AssertionError: 401 != 200">token=secreto</failure></testcase></testsuite>', encoding="utf-8")
            cases = [{"id": "CT-REFLEX-1", "node": "frontend/tests/test_x.py::TestA.test_falha", "nome": "falha", "status": "NOT_RUN", "duracao_segundos": 0.0, "motivo": "", "resultado_obtido": "Não executado"}]
            collect_pytest_results(directory, cases)
            self.assertEqual(cases[0]["status"], "FAILED")
            self.assertEqual(cases[0]["motivo"], "Expectativa funcional não satisfeita")
            self.assertNotIn("secreto", (directory / "pytest.xml").read_text(encoding="utf-8"))

    def test_coleta_resultado_playwright_com_sufixo_navegador(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pytest.xml").write_text(
                '<testsuite><testcase classname="tests.e2e.test_publico" '
                'name="test_login_abre_aviso_e_volta[chromium]" time="0.2"/></testsuite>',
                encoding="utf-8",
            )
            cases = [{"id": "CT-REFLEX-1", "node": "tests/e2e/test_publico.py::test_login_abre_aviso_e_volta", "tipo": "E2E", "status": "NOT_RUN", "duracao_segundos": 0.0, "motivo": "", "resultado_obtido": "Não executado"}]
            collect_pytest_results(directory, cases)
            self.assertEqual(cases[0]["status"], "PASSED")

    def test_coleta_distingue_nomes_iguais_em_modulos_diferentes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "pytest.xml").write_text(
                '<testsuite><testcase classname="tests.test_expiracao_state" name="test_sessao_expirada" time="0.1"/>'
                '<testcase classname="tests.test_plantao_state" name="test_sessao_expirada" time="0.2"/></testsuite>',
                encoding="utf-8",
            )
            cases = [
                {"id": "CT-1", "node": "frontend/tests/test_expiracao_state.py::test_sessao_expirada", "status": "NOT_RUN", "motivo": ""},
                {"id": "CT-2", "node": "frontend/tests/test_plantao_state.py::test_sessao_expirada", "status": "NOT_RUN", "motivo": ""},
            ]
            collect_pytest_results(directory, cases)
            self.assertEqual([case["status"] for case in cases], ["PASSED", "PASSED"])

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
        self.assertEqual(execution_status([{"status": "NOT_RUN"}], False), "NAO_EXECUTADA")
        self.assertEqual(execution_status([{"status": "PASSED"}, {"status": "NOT_RUN"}], False), "PARCIAL")
        self.assertEqual(execution_status([{"status": "PASSED"}], False), "APROVADA")
        self.assertEqual(execution_status([{"status": "PASSED"}], True), "ERRO_INFRAESTRUTURA")

    def test_resumo_actions_e_curto_e_mostra_resultado(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "summary.md"
            data = {
                "suite": "xano-safe", "status_execucao": "PARCIAL",
                "casos": [{"status": "PASSED"}, {"status": "NOT_RUN"}],
                "limitacoes": ["Unit tests nativos sem credencial"],
            }
            github_summary_write(data, path)
            content = path.read_text(encoding="utf-8")
            self.assertIn("# Evidências: xano-safe", content)
            self.assertIn("PASSED: 1", content)
            self.assertIn("Unit tests nativos sem credencial", content)


if __name__ == "__main__":
    unittest.main()


class ModeloEColetaTest(unittest.TestCase):
    def test_seis_estados_eixos_e_gate(self):
        import run_test_evidence as ev
        for status,technical,level in [('PASSED','PASSED','COMPLETA'),('FAILED','FAILED','COMPLETA'),('ERROR','ERROR','BLOQUEADA'),('SKIPPED','PASSED','NAO_EXECUTADA'),('NOT_RUN','PASSED','NAO_EXECUTADA'),('BLOCKED','PASSED','BLOQUEADA')]:
            self.assertEqual(ev.axes([{'status':status}]),(technical,level))
        self.assertEqual(ev.axes([]),('PASSED','NAO_EXECUTADA'))
        self.assertEqual(ev.axes([{'status':'PASS'},{'status':'BLOCKED'}]),('PASSED','PARCIAL'))
        self.assertEqual(ev.axes([{'status':'FAIL'}]),('FAILED','COMPLETA'))
        with self.assertRaises(ValueError):ev.state('APROVADO')
        data={'casos':[{'status':'BLOCKED'}],'status_tecnico':'PASSED','nivel_validacao':'BLOQUEADA'}
        self.assertEqual(ev.gate(data),0)
        self.assertEqual(ev.gate(data,require_complete=True),1)
        self.assertEqual(ev.gate(data,require_execution=True),1)
        data={'casos':[{'status':'FAILED'}],'status_tecnico':'FAILED','nivel_validacao':'COMPLETA'}
        self.assertEqual(ev.gate(data,True,True),1)

    def test_catalogo_identidade_renomeacao_duplicacao_e_divergencia(self):
        import copy,json
        import run_test_evidence as ev
        payload=json.loads(ev.CATALOG_PATH.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'catalogo.json'
            original=copy.deepcopy(payload);record=payload['casos'][0]
            identity=record['id'];record['seletor']='frontend/tests/renomeado.py::test_novo'
            path.write_text(json.dumps(payload))
            self.assertEqual(ev.load_catalog(path)[0]['id'],identity)
            with self.assertRaises(ValueError):ev.catalog(record['suite'],path)
            for mutation in ('id','selector','variant','removed','remote'):
                payload=copy.deepcopy(original)
                if mutation=='id':payload['casos'].append(payload['casos'][0])
                elif mutation=='selector':payload['casos'][1]['seletor']=payload['casos'][0]['seletor']
                elif mutation=='variant':payload['casos'][0]['variantes']=[{'chave':'x','seletor':'a::x'},{'chave':'x','seletor':'a::y'}]
                elif mutation=='remote':payload['casos'][0]['modo_dependencia']='REAL'
                else:payload['casos'].pop(0)
                path.write_text(json.dumps(payload))
                with self.assertRaises(ValueError):ev.catalog('reflex',path)
        self.assertEqual(len(ev.catalog('xano-static')),len([c for c in json.loads(ev.CATALOG_PATH.read_text(encoding='utf-8'))['casos'] if c['suite']=='xano-static']))
        self.assertEqual(len(ev.catalog('controlled')),29)
        variants=[c for c in ev.catalog('reflex') if c['variante']]
        self.assertTrue(variants)
        self.assertEqual(len({(c['id'],c['variante']) for c in variants}),len(variants))

    def test_xml_identidades_modulo_classe_variante_setup_teardown_e_erro_call(self):
        import run_test_evidence as ev
        cases=[{'id':str(i),'variante':v,'node':node,'status':'NOT_RUN','duracao_segundos':0} for i,(v,node) in enumerate([
            ('a','tests/a/test_igual.py::QualquerClasse.test_mesmo[a]'),
            ('b','tests/a/test_igual.py::QualquerClasse.test_mesmo[b]'),
            ('','tests/b/test_igual.py::QualquerClasse.test_mesmo')])]
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);xml=out/'pytest.xml'
            xml.write_text('<testsuite><testcase classname="tests.a.test_igual.QualquerClasse" name="test_mesmo[a]"/><testcase classname="tests.a.test_igual.QualquerClasse" name="test_mesmo[b]"><failure message="RuntimeError: transporte"/></testcase><testcase classname="tests.b.test_igual.QualquerClasse" name="test_mesmo"><error message="setup"/></testcase><testcase classname="tests.b.test_igual.QualquerClasse" name="test_mesmo"><error message="teardown"/></testcase><testcase classname="desconhecido" name="x"/></testsuite>')
            diagnostics=ev.collect_pytest_results(out,cases)
            self.assertEqual([c['status'] for c in cases],['PASSED','ERROR','ERROR'])
            self.assertEqual({d['codigo'] for d in diagnostics},{'RESULTADO_REPETIDO','RESULTADO_SEM_ASSOCIACAO'})
            xml.write_text('<corrompido')
            self.assertEqual(ev.collect_pytest_results(out,cases)[0]['codigo'],'XML_INVALIDO')

    def test_destino_exclusivo_timeout_e_metadados_ci(self):
        import os
        from datetime import datetime,timezone
        import run_test_evidence as ev
        with tempfile.TemporaryDirectory() as tmp:
            out=ev.new_output(Path(tmp)/'saida');old=out/'pytest.xml';old.write_text('histórico')
            with self.assertRaises(FileExistsError):ev.new_output(out)
            self.assertEqual(old.read_text(),'histórico')
            old.unlink()
            case={**ev.load_catalog()[0],'status':'NOT_RUN'}
            with patch('run_test_evidence.subprocess.run',side_effect=subprocess.TimeoutExpired('pytest',600)):
                problem,code=ev.run_pytest('reflex',out,[case])
            self.assertEqual(code,124);self.assertIn('Timeout',problem)
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true','GITHUB_SHA':'abc','GITHUB_RUN_ID':'42','GITHUB_RUN_ATTEMPT':'2','GITHUB_REPOSITORY':'owner/repo','GITHUB_JOB':'reflex'},clear=True),patch('run_test_evidence.git',side_effect=lambda *args: 'abc' if args[0]=='rev-parse' else ''):
            data=ev.metadata('reflex',datetime.now(timezone.utc))
            self.assertEqual(data['github_url'],'https://github.com/owner/repo/actions/runs/42')
            self.assertEqual(data['sha_observado'],'abc');self.assertEqual(data['github_run_attempt'],'2')
        self.assertIsNone(ev.public_url('https://github.com/owner/repo/actions/runs/42?token=x'))
        self.assertIsNone(ev.public_url('https://privado.example.test'))
        self.assertIsNone(ev.public_url('https://['))

    def test_guardiao_funcoes_python_bloqueia_antes_do_cli(self):
        import run_test_evidence as ev
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'backend/xano/function/fila/proxima_ficha.xs';p.parent.mkdir(parents=True)
            for content in ('db.query pacientes {}','api.request {}','redis.get {}','function.run "nao/revisada" {}'):
                p.write_text(content)
                self.assertIsNotNone(ev.pure_guard(['fila/proxima_ficha'],root))
        with patch('scripts.run_test_evidence.pure_guard',return_value='Recurso proibido'),patch('test_ordenacao.subprocess.run') as cli,patch('test_ordenacao.time.sleep'):
            with self.assertRaises(RuntimeError):executar('fila/proxima_ficha')
            cli.assert_not_called()

    def test_helper_cli_separa_erros_e_preserva_assertions(self):
        import json
        for proc in [SimpleNamespace(returncode=1,stderr='transporte',stdout=''),SimpleNamespace(returncode=0,stderr='',stdout='invalido'),SimpleNamespace(returncode=0,stderr='',stdout='{"status":"erro"}')]:
            with patch('test_ordenacao.subprocess.run',return_value=proc),patch('test_ordenacao.time.sleep'):
                with self.assertRaises(RuntimeError):executar('fila/proxima_ficha')
        with patch('test_ordenacao.subprocess.run',side_effect=subprocess.TimeoutExpired('xano',30)),patch('test_ordenacao.time.sleep'):
            with self.assertRaises(subprocess.TimeoutExpired):executar('fila/proxima_ficha')

    def test_guardiao_controlado_nega_cada_precondicao_sem_escrita(self):
        import os
        import run_test_evidence as ev
        env={'XANO_ISOLATED_CONFIRMATION':'CONFIRMO_WORKSPACE_DESCARTAVEL','XANO_ISOLATED_API_HOST':'isolado.example.test'}
        env.update({k:'https://isolado.example.test/api' for k in ('XANO_AUTH_API_URL','XANO_TRIAGEM_API_URL','XANO_API_URL','XANO_CADASTROS_API_URL')})
        env.update({k:'fixture' for k in ('TEST_RECEPCAO_TOKEN','TOTEM_CHAVE','TEST_ADMIN_EMAIL','TEST_ADMIN_SENHA','TEST_RECEPCAO_EMAIL','TEST_RECEPCAO_SENHA','TEST_MEDICO_EMAIL','TEST_MEDICO_SENHA')})
        with patch.dict(os.environ,env,clear=True):self.assertIsNone(ev.controlled_gate())
        for key in env:
            missing={k:v for k,v in env.items() if k!=key}
            with patch.dict(os.environ,missing,clear=True),patch('run_test_evidence.run_pytest') as executor:
                self.assertIsNotNone(ev.controlled_gate());executor.assert_not_called()

    def test_estatica_seleciona_oito_sem_rede_ou_cli(self):
        import run_test_evidence as ev
        import importlib.util
        spec=importlib.util.spec_from_file_location('base',ev.ROOT/'tests/api/test_base_compartilhada.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
        with patch('httpx.get',side_effect=AssertionError('rede proibida')),patch('subprocess.run',side_effect=AssertionError('CLI proibido')):
            suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(cls) for cls in (base.AuditoriaTest,base.ParametrosTest)])
            result=unittest.TestResult();suite.run(result)
            esperados=[c for c in ev.catalog('xano-static') if '::AuditoriaTest.' in c['seletor'] or '::ParametrosTest.' in c['seletor']]
            self.assertEqual(result.testsRun,len(esperados));self.assertFalse(result.errors or result.failures)
        self.assertTrue(all(c['modo_dependencia']=='LOCAL' for c in ev.catalog('xano-static')))
