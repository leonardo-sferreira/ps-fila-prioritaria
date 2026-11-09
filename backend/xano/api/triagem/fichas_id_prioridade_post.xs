// Ajuste manual da prioridade pela Recepção/Triagem (add-classificacao-prioridade, D6).
// Também é a classificação manual excepcional quando o cálculo automático está bloqueado
// (menor de 16 anos, gestante ou dado pendente). Justificativa obrigatória e auditada.
// Em AGUARDANDO, a troca de cor troca também a letra da senha (add-reavaliacao-ficha-aguardando, D4).
query "fichas/{ficha_id}/prioridade" verb=POST {
  api_group = "Triagem"
  description = "Define a prioridade atual da ficha EM_TRIAGEM ou AGUARDANDO com justificativa obrigatória e auditoria PRIORIDADE_ALTERADA; em AGUARDANDO, atualiza a senha."

  auth = "usuario"

  input {
    int ficha_id
    text prioridade? filters=trim|upper
    text justificativa? filters=trim
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["RECEPCAO_TRIAGEM"]}
    } as $usuario

    db.transaction {
      stack {
        function.run "classificacao/inicializar_classificacao" {
          input = {}
        } as $classificacao_inicializada

        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $ficha

        precondition ($ficha != null) {
          error_type = "notfound"
          error = "FICHA_NAO_ENCONTRADA"
        }

        precondition (["EM_TRIAGEM", "AGUARDANDO"]|in:$ficha.status) {
          error_type = "inputerror"
          error = "FICHA_FORA_DA_TRIAGEM"
        }

        function.run "classificacao/aplicar_ajuste" {
          input = {ficha_id: $ficha.id, usuario_id: $usuario.id, prioridade: $input.prioridade, justificativa: $input.justificativa, reavaliar_senha: $ficha.status == "AGUARDANDO"}
        } as $ajuste

        var $reavaliacao { value = $ajuste.reavaliacao }
      }
    }
  }

  response = {
    id                  : $input.ficha_id
    prioridade_calculada: $ajuste.prioridade_calculada
    prioridade_atual    : $ajuste.prioridade_atual
    justificativa_ajuste: $ajuste.justificativa_ajuste
    senha_anterior      : ($reavaliacao == null) ? null : $reavaliacao.senha_anterior
    senha               : ($reavaliacao == null) ? null : $reavaliacao.senha
    senha_alterada      : ($reavaliacao == null) ? false : $reavaliacao.senha_alterada
  }
  guid = "x3yrP4otR-fp0fb9tsb5QL-Tj-8"
}
