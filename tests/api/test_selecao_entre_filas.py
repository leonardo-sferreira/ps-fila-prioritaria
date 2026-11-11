"""Política de escolha entre especialidades contra a função publicada no Xano."""

import unittest

from test_ordenacao import executar, ficha, proxima


def candidata(especialidade, identificador, cor, chegada, *, descoberta=False, condicao="NENHUMA"):
    return {
        "especialidade_id": especialidade,
        "descoberta": descoberta,
        "ficha": ficha(identificador, cor, chegada, condicao=condicao),
    }


def selecionar(candidatas, proprias, ultima=None):
    return executar(
        "fila/selecionar_entre_filas",
        candidatas=candidatas,
        especialidades_proprias=proprias,
        ultima_propria=ultima,
    )


class SelecaoEntreFilasTest(unittest.TestCase):
    def test_cobertura_exclui_pausa_ausencia_e_inativos(self):
        medicos = [
            {"id": i, "medico_ativo": ativo, "usuario_ativo": True, "plantao_vigente": True, "sessao_ativa": True, "status": status, "especialidade_ids": [i]}
            for i, ativo, status in [(1, True, "PAUSA"), (2, True, "AUSENTE"), (3, True, "EM_ATENDIMENTO"), (4, True, "DISPONIVEL"), (5, False, "DISPONIVEL")]
        ]
        resultado = executar("fila/avaliar_cobertura", medicos=medicos)
        self.assertEqual(resultado["especialidade_ids"], [3, 4])

    def test_cobertura_exige_plantao_sessao_e_usuario_ativos(self):
        base = {"medico_ativo": True, "usuario_ativo": True, "plantao_vigente": True, "sessao_ativa": True, "status": "DISPONIVEL"}
        medicos = [dict(base, id=1, especialidade_ids=[1]), dict(base, id=2, especialidade_ids=[2], plantao_vigente=False), dict(base, id=3, especialidade_ids=[3], sessao_ativa=False), dict(base, id=4, especialidade_ids=[4], usuario_ativo=False)]
        self.assertEqual(executar("fila/avaliar_cobertura", medicos=medicos)["especialidade_ids"], [1])

    def test_matriz_cor_propria_contra_descoberta(self):
        casos = [
            ("VERMELHA", "VERMELHA", "PROPRIA"),
            ("VERMELHA", "AMARELA", "PROPRIA"),
            ("AMARELA", "VERMELHA", "DESCOBERTA"),
            ("AMARELA", "AMARELA", "PROPRIA"),
            ("AZUL", "AMARELA", "DESCOBERTA"),
            ("AZUL", "AZUL", "PROPRIA"),
        ]
        for propria, descoberta, origem in casos:
            with self.subTest(propria=propria, descoberta=descoberta):
                itens = [candidata(1, 1, propria, 100), candidata(2, 2, descoberta, 1, descoberta=True, condicao="IDOSO")]
                self.assertEqual(selecionar(itens, [1])["origem"], origem)

    def test_desempate_entre_descobertas_por_ordem_efetiva_e_id(self):
        itens = [candidata(2, 8, "AMARELA", 100, descoberta=True), candidata(3, 3, "AMARELA", 100, descoberta=True), candidata(4, 4, "AMARELA", 90, descoberta=True)]
        self.assertEqual(selecionar(itens, [1])["candidata"]["ficha"]["id"], 4)
        itens[2]["ficha"]["fila_em"] = 110
        self.assertEqual(selecionar(itens, [1])["candidata"]["ficha"]["id"], 3)

    def test_vermelha_propria_mais_antiga_e_menor_id(self):
        itens = [candidata(1, 8, "VERMELHA", 100), candidata(2, 3, "VERMELHA", 100), candidata(4, 9, "AZUL", 1, descoberta=True)]
        resultado = selecionar(itens, [1, 2])
        self.assertEqual((resultado["origem"], resultado["candidata"]["ficha"]["id"]), ("PROPRIA", 3))

    def test_rodizio_proprio_e_salto_de_fila_vazia(self):
        itens = [candidata(1, 1, "AMARELA", 10), candidata(3, 3, "AZUL", 30)]
        self.assertEqual(selecionar(itens, [1, 2, 3], ultima=1)["candidata"]["especialidade_id"], 3)
        self.assertEqual(selecionar(itens, [1, 2, 3], ultima=3)["candidata"]["especialidade_id"], 1)

    def test_rodizio_preserva_ciclo_interno_de_cada_fila(self):
        car = proxima([ficha(1, "AMARELA", 1), ficha(2, "AZUL", 2)], posicao=1)["ficha"]
        neu = proxima([ficha(3, "AMARELA", 3), ficha(4, "AZUL", 4)], posicao=3)["ficha"]
        itens = [{"especialidade_id": 1, "descoberta": False, "ficha": car}, {"especialidade_id": 2, "descoberta": False, "ficha": neu}]
        resultado = selecionar(itens, [1, 2], ultima=1)
        self.assertEqual((resultado["candidata"]["especialidade_id"], resultado["candidata"]["ficha"]["prioridade_atual"]), (2, "AZUL"))

    def test_descoberta_mais_grave_supera_propria(self):
        itens = [candidata(1, 1, "AZUL", 10), candidata(2, 2, "VERMELHA", 20, descoberta=True)]
        self.assertEqual(selecionar(itens, [1])["origem"], "DESCOBERTA")

    def test_empate_de_cor_favorece_propria(self):
        itens = [candidata(1, 1, "AMARELA", 20), candidata(2, 2, "AMARELA", 1, descoberta=True, condicao="GESTANTE")]
        resultado = selecionar(itens, [1])
        self.assertEqual(resultado["origem"], "PROPRIA")

    def test_sem_propria_prioriza_descoberta_mesmo_com_coberta_mais_grave(self):
        itens = [candidata(2, 2, "AZUL", 20, descoberta=True), candidata(3, 3, "VERMELHA", 10)]
        self.assertEqual(selecionar(itens, [1])["candidata"]["especialidade_id"], 2)

    def test_fallback_coberta_e_desempates_descoberta(self):
        coberta = selecionar([candidata(2, 2, "AMARELA", 20)], [1])
        self.assertEqual(coberta["origem"], "COBERTA")
        itens = [
            candidata(2, 2, "AZUL", 1, descoberta=True),
            candidata(3, 3, "AMARELA", 3, descoberta=True),
            candidata(4, 4, "AMARELA", 2, descoberta=True, condicao="IDOSO"),
            candidata(5, 5, "AMARELA", 2, descoberta=True, condicao="CRIANCA"),
        ]
        self.assertEqual(selecionar(itens, [1])["candidata"]["ficha"]["id"], 4)

    def test_fila_vazia(self):
        self.assertIsNone(selecionar([], [1])["candidata"])

    def test_politica_completa_com_duas_proprias_e_terceira_fila(self):
        # Médico 1: Cardiologia e Neurologia próprias; Médico 2: Clínica Geral.
        # A Clínica Geral fica descoberta quando o médico 2 sai da cobertura.
        car_vermelha = candidata(1, 11, "VERMELHA", 20)
        neu_vermelha = candidata(2, 21, "VERMELHA", 10)
        cli_vermelha = candidata(3, 31, "VERMELHA", 5, descoberta=True)
        primeira = selecionar([car_vermelha, neu_vermelha, cli_vermelha], [1, 2])
        self.assertEqual((primeira["origem"], primeira["candidata"]["ficha"]["id"]), ("PROPRIA", 21))

        car_amarela = candidata(1, 12, "AMARELA", 30)
        neu_azul = candidata(2, 22, "AZUL", 35)
        descoberta = selecionar([car_amarela, neu_azul, cli_vermelha], [1, 2], ultima=2)
        self.assertEqual((descoberta["origem"], descoberta["candidata"]["ficha"]["id"]), ("DESCOBERTA", 31))

        empate = selecionar([car_amarela, candidata(3, 32, "AMARELA", 1, descoberta=True)], [1, 2], ultima=2)
        self.assertEqual((empate["origem"], empate["candidata"]["ficha"]["id"]), ("PROPRIA", 12))

        rodizio = selecionar([car_amarela, neu_azul], [1, 2], ultima=1)
        self.assertEqual(rodizio["candidata"]["especialidade_id"], 2)
        coberta = selecionar([candidata(3, 33, "AZUL", 50)], [1, 2], ultima=2)
        self.assertEqual((coberta["origem"], coberta["candidata"]["ficha"]["id"]), ("COBERTA", 33))


if __name__ == "__main__":
    unittest.main()
