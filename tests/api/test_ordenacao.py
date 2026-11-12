"""Casos da ordem interna da fila executados nas funções publicadas no Xano."""

import json
import os
import subprocess
import time
import unittest


PERFIL = os.getenv("XANO_TEST_PROFILE", "ps-impacta")


def ficha(identificador, cor, chegada, *, condicao="NENHUMA", fila_em=None, status="AGUARDANDO"):
    return {
        "id": identificador,
        "status": status,
        "prioridade_atual": cor,
        "condicao_prioritaria": condicao,
        "chegada_em": chegada,
        "fila_em": chegada if fila_em is None else fila_em,
        "senha": f"{cor[0]}-CAR-{identificador:03d}",
    }


def executar(nome, **entrada):
    # A instância Free também limita as chamadas do CLI (25 por 20 s nesta conta).
    for tentativa in range(4):
        time.sleep(2.5 if tentativa == 0 else 21)
        processo = subprocess.run(
            ["xano", "function", "run", nome, "--json", "-", "--branch", "v1", "-p", PERFIL],
            input=json.dumps(entrada),
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        resposta_cli = processo.stderr or processo.stdout
        if not processo.returncode or "plan only supports" not in resposta_cli.lower() or tentativa == 3:
            break
    if processo.returncode:
        raise AssertionError(f"{nome}: {processo.stderr or processo.stdout}")
    resposta = json.loads(processo.stdout)
    if resposta.get("status") != "ok":
        raise AssertionError(resposta)
    return resposta["result"]


def proxima(fichas, posicao=1, amarelas=2, azuis=1):
    return executar("fila/proxima_ficha", fichas=fichas, posicao=posicao, amarelas=amarelas, azuis=azuis)


def previsao(fichas, posicao=1, limite=5, amarelas=2, azuis=1):
    return executar("fila/prever_fila", fichas=fichas, posicao=posicao, amarelas=amarelas, azuis=azuis, limite=limite)


class OrdenacaoTest(unittest.TestCase):
    def test_vermelha_tardia_e_ciclo_preservado(self):
        resultado = proxima([ficha(1, "AMARELA", 100), ficha(2, "VERMELHA", 200)], posicao=2)
        self.assertEqual(resultado["ficha"]["id"], 2)
        self.assertEqual(resultado["proxima_posicao"], 2)

    def test_ciclo_amarela_amarela_azul(self):
        fichas = [ficha(i, "AMARELA", i) for i in range(1, 5)] + [ficha(i, "AZUL", i) for i in range(5, 7)]
        cores = [item["cor"] for item in previsao(fichas, limite=6)]
        self.assertEqual(cores, ["AMARELA", "AMARELA", "AZUL", "AMARELA", "AMARELA", "AZUL"])

    def test_ciclo_respeita_quantidades_configuradas(self):
        fichas = [ficha(i, "AMARELA", i) for i in range(1, 4)] + [ficha(i, "AZUL", i) for i in range(4, 8)]
        cores = [item["cor"] for item in previsao(fichas, limite=6, amarelas=1, azuis=2)]
        self.assertEqual(cores, ["AMARELA", "AZUL", "AZUL", "AMARELA", "AZUL", "AZUL"])

    def test_vermelha_intercalada_nao_avanca(self):
        fichas = [ficha(1, "VERMELHA", 300), ficha(2, "AMARELA", 100), ficha(3, "AZUL", 200)]
        self.assertEqual([item["cor"] for item in previsao(fichas, posicao=2, limite=3)], ["VERMELHA", "AMARELA", "AZUL"])

    def test_cor_alternativa_nao_avanca(self):
        resultado = proxima([ficha(1, "AZUL", 1)], posicao=1)
        self.assertEqual(resultado["ficha"]["id"], 1)
        self.assertEqual(resultado["proxima_posicao"], 1)
        resultado = proxima([ficha(2, "AMARELA", 2)], posicao=3)
        self.assertEqual(resultado["proxima_posicao"], 3)
        self.assertEqual(proxima([ficha(2, "AMARELA", 2), ficha(3, "AZUL", 3)], posicao=3)["ficha"]["id"], 3)

    def test_prioritarios_dentro_da_cor_sem_precedencia_entre_tipos(self):
        fichas = [
            ficha(1, "AZUL", 10),
            ficha(2, "AZUL", 40, condicao="IDOSO"),
            ficha(3, "AZUL", 30, condicao="CRIANCA"),
            ficha(4, "AZUL", 20, condicao="GESTANTE"),
        ]
        self.assertEqual([item["senha"] for item in previsao(fichas, posicao=3, limite=4)], [fichas[i]["senha"] for i in (3, 2, 1, 0)])

    def test_condicao_prioritaria_nao_ultrapassa_cor(self):
        resultado = proxima([ficha(1, "AZUL", 1, condicao="IDOSO"), ficha(2, "AMARELA", 2)])
        self.assertEqual(resultado["ficha"]["id"], 2)

    def test_empate_de_chegada_por_id(self):
        resultado = proxima([ficha(8, "AMARELA", 1), ficha(3, "AMARELA", 1)])
        self.assertEqual(resultado["ficha"]["id"], 3)

    def test_reentrada_vai_ao_fim_sem_mudar_chegada(self):
        resultado = proxima([ficha(1, "AMARELA", 1, fila_em=30), ficha(2, "AMARELA", 2, fila_em=20)])
        self.assertEqual(resultado["ficha"]["id"], 2)

    def test_estados_fora_da_fila_sao_excluidos(self):
        fichas = [ficha(i, "VERMELHA", i, status=estado) for i, estado in enumerate(("EM_TRIAGEM", "CHAMADO", "ATENDIDO", "DESISTENCIA", "CANCELADO"), 1)]
        fichas.append(ficha(9, "AZUL", 9))
        self.assertEqual(proxima(fichas)["ficha"]["id"], 9)

    def test_previsao_tres_e_sete_e_nova_vermelha(self):
        fichas = [ficha(i, "AMARELA" if i % 3 else "AZUL", i) for i in range(1, 8)]
        self.assertEqual(len(previsao(fichas[:3])), 3)
        self.assertEqual(len(previsao(fichas, limite=7)), 7)
        fichas.append(ficha(8, "VERMELHA", 8))
        self.assertEqual(previsao(fichas)[0]["senha"], fichas[-1]["senha"])

    def test_previsao_nao_retorna_dados_pessoais(self):
        paciente = ficha(1, "AMARELA", 1)
        paciente.update(nome="Nome privado", cpf="00000000000", paciente_id=5)
        resultado = previsao([paciente])
        self.assertEqual(set(resultado[0]), {"senha", "cor"})
        self.assertNotIn("Nome privado", json.dumps(resultado))


if __name__ == "__main__":
    unittest.main()
