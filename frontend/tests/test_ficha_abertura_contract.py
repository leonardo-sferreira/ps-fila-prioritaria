"""Regressões do contrato local de abertura de ficha (RN03)."""

from pathlib import Path
import unittest


ARQUIVO_POST_FICHAS = (
    Path(__file__).resolve().parents[2]
    / "backend/xano/api/triagem/fichas_post.xs"
)


class TestContratoAberturaFicha(unittest.TestCase):
    def test_apenas_ficha_ativa_do_mesmo_paciente_bloqueia_nova_abertura(self) -> None:
        """Finais não entram no filtro; os três estados ativos continuam bloqueando."""
        codigo = ARQUIVO_POST_FICHAS.read_text(encoding="utf-8")

        self.assertIn(
            '$db.ficha_atendimento.paciente_id == $input.paciente_id',
            codigo,
        )
        self.assertIn(
            '$db.ficha_atendimento.status in ["EM_TRIAGEM", "AGUARDANDO", "CHAMADO"]',
            codigo,
        )
        self.assertIn('error = "FICHA_NAO_FINALIZADA_EXISTENTE"', codigo)
        self.assertNotIn('status != "ATENDIDO"', codigo)
        self.assertNotIn('status != "CANCELADO"', codigo)
        self.assertNotIn('"ATENDIDO", "DESISTENCIA", "CANCELADO"', codigo)


if __name__ == "__main__":
    unittest.main()
