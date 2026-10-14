import unittest
import urllib.request
import json
import time
import random

BASE_TRIAGEM = "https://x8ki-letl-twmt.n7.xano.io/api:ps-fila-prioritaria-triagem"
BASE_PACIENTES = "https://x8ki-letl-twmt.n7.xano.io/api:ps-fila-prioritaria-pacientes"

def _req(base_url, method, path, data=None):
    time.sleep(2.5)  # Respeita o rate limit do plano Free (10 reqs / 20s)
    url = f"{base_url}{path}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"raw": err_body}

def _gerar_cpf_valido() -> str:
    nove = [random.randint(0, 9) for _ in range(9)]
    # Evita repetidos
    if len(set(nove)) == 1:
        nove[0] = (nove[0] + 1) % 10
    s1 = sum(d * (10 - i) for i, d in enumerate(nove))
    v1 = (s1 * 10) % 11
    if v1 >= 10:
        v1 = 0
    s2 = sum(d * (11 - i) for i, d in enumerate(nove)) + v1 * 2
    v2 = (s2 * 10) % 11
    if v2 >= 10:
        v2 = 0
    return "".join(map(str, nove + [v1, v2]))

class TestXanoApiIntegration(unittest.TestCase):
    """
    Testes de integração com a API remota do Xano cobrindo:
    RF06, RN03, RF07, RN04.
    """

    def test_catalogo_sintomas_46_ativos(self):
        """Valida que GET /sintomas retorna exatamente 46 sintomas ativos com campos obrigatórios."""
        status, sintomas = _req(BASE_TRIAGEM, "GET", "/sintomas")
        self.assertEqual(status, 200)
        self.assertEqual(len(sintomas), 46)
        for s in sintomas:
            self.assertIn("id", s)
            self.assertIn("nome", s)
            self.assertIn("grupo", s)
            self.assertIn("pontuacao", s)
            self.assertIn(s["pontuacao"], [1, 2, 3])
            # Sem cor/prioridade fixa exposta
            self.assertNotIn("prioridade_padrao", s)
            self.assertNotIn("cor", s)

    def test_rf06_abertura_de_ficha(self):
        """RF06: Paciente válido cria ficha em EM_TRIAGEM com chegada_em gerado pelo backend."""
        cpf = _gerar_cpf_valido()
        status_p, paciente = _req(BASE_PACIENTES, "POST", "/pacientes", {
            "cpf": cpf,
            "nome": f"Paciente Teste {random.randint(1000, 9999)}",
            "data_nascimento": "1992-04-10"
        })
        self.assertEqual(status_p, 200, f"Falha ao cadastrar paciente: {paciente}")
        paciente_id = paciente["id"]

        # 1. Cria ficha sem ticket
        status_f, ficha = _req(BASE_TRIAGEM, "POST", "/fichas", {
            "paciente_id": paciente_id
        })
        self.assertEqual(status_f, 200, f"Falha ao criar ficha: {ficha}")
        self.assertEqual(ficha["paciente_id"], paciente_id)
        self.assertEqual(ficha["status"], "EM_TRIAGEM")
        self.assertIsNotNone(ficha.get("chegada_em"))
        self.assertIn(ficha.get("aberta_por"), [None, 0])
        self.assertIn(ficha.get("ticket_id"), [None, 0])
        self.assertTrue(ficha["chegada_em"] > 1700000000000)

    def test_rn03_bloqueio_segunda_ficha_ativa(self):
        """RN03: Bloqueia abertura de segunda ficha quando já existe ficha em EM_TRIAGEM."""
        # Paciente 1 já possui ficha 1 em EM_TRIAGEM
        status, res = _req(BASE_TRIAGEM, "POST", "/fichas", {"paciente_id": 1})
        self.assertEqual(status, 400)
        self.assertEqual(res.get("message"), "FICHA_NAO_FINALIZADA_EXISTENTE")

    def test_rf07_e_rn04_fluxo_completo_ficha(self):
        """
        RF07 e RN04:
        - Sintomas, observação, ambos;
        - Edição posterior com coleção final;
        - Recarga por GET /fichas/{id};
        - Validação de RN04 (aceite e recusa no estado resultante).
        """
        cpf = _gerar_cpf_valido()
        status_p, paciente = _req(BASE_PACIENTES, "POST", "/pacientes", {
            "cpf": cpf,
            "nome": f"Paciente Triagem {random.randint(1000, 9999)}",
            "data_nascimento": "1988-11-20"
        })
        self.assertEqual(status_p, 200)
        paciente_id = paciente["id"]

        # Criação inicial vazia em EM_TRIAGEM
        status_f, ficha = _req(BASE_TRIAGEM, "POST", "/fichas", {"paciente_id": paciente_id})
        self.assertEqual(status_f, 200)
        ficha_id = ficha["id"]

        # 1. RN04 inválida: ambos vazios
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "sintoma_ids": [],
            "observacao": ""
        })
        self.assertEqual(status, 400)
        self.assertEqual(res.get("message"), "FICHA_SEM_SINTOMA_OU_OBSERVACAO")

        # 2. RN04 inválida: observação apenas whitespace sem sintomas
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "observacao": "     "
        })
        self.assertEqual(status, 400)
        self.assertEqual(res.get("message"), "FICHA_SEM_SINTOMA_OU_OBSERVACAO")

        # 3. Aceitar somente sintomas (sem observação)
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "sintoma_ids": [1, 2]
        })
        self.assertEqual(status, 200)
        self.assertEqual(set(res["sintoma_ids"]), {1, 2})
        self.assertEqual(res["observacao"], "")

        # 4. Recarregar via GET /fichas/{ficha_id}
        status, res_get = _req(BASE_TRIAGEM, "GET", f"/fichas/{ficha_id}")
        self.assertEqual(status, 200)
        self.assertEqual(res_get["ficha"]["id"], ficha_id)
        self.assertEqual(res_get["paciente"]["id"], paciente_id)
        ids_carregados = [s["id"] for s in res_get["sintomas"]]
        self.assertEqual(set(ids_carregados), {1, 2})

        # 5. Adicionar observação preservando sintomas
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "observacao": "Paciente refere dor no peito e palpitações há 2 horas"
        })
        self.assertEqual(status, 200)
        self.assertEqual(res["observacao"], "Paciente refere dor no peito e palpitações há 2 horas")
        self.assertEqual(set(res["sintoma_ids"]), {1, 2})  # Sintomas preservados

        # 6. Atualizar sintomas com coleção final [2, 3] (remove 1, mantém 2, adiciona 3)
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "sintoma_ids": [2, 3]
        })
        self.assertEqual(status, 200)
        self.assertEqual(set(res["sintoma_ids"]), {2, 3})
        self.assertEqual(res["observacao"], "Paciente refere dor no peito e palpitações há 2 horas")  # Observação preservada

        # 7. Aceitar somente observação (remover todos os sintomas mantendo observação válida)
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "sintoma_ids": []
        })
        self.assertEqual(status, 200)
        self.assertEqual(res["sintoma_ids"], [])
        self.assertEqual(res["observacao"], "Paciente refere dor no peito e palpitações há 2 horas")

        # 8. Tentar remover a observação agora que sintomas estão vazios (RN04 deve recusar)
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "observacao": ""
        })
        self.assertEqual(status, 400)
        self.assertEqual(res.get("message"), "FICHA_SEM_SINTOMA_OU_OBSERVACAO")

        # 9. Confirmar ausência de persistência parcial após a recusa
        status, res_final = _req(BASE_TRIAGEM, "GET", f"/fichas/{ficha_id}")
        self.assertEqual(status, 200)
        self.assertEqual(res_final["ficha"]["observacao"], "Paciente refere dor no peito e palpitações há 2 horas")
        self.assertEqual(res_final["sintomas"], [])

        # 10. Recusar sintoma inativo ou inexistente
        status, res = _req(BASE_TRIAGEM, "PATCH", f"/fichas/{ficha_id}", {
            "sintoma_ids": [999999]
        })
        self.assertEqual(status, 400)
        self.assertEqual(res.get("message"), "SINTOMA_INEXISTENTE_OU_INATIVO")

if __name__ == "__main__":
    unittest.main()
