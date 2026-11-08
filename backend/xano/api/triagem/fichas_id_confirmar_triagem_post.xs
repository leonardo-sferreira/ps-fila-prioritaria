// Confirmação da triagem (add-direcionamento-senha, D5; RF47/RF48): exige ficha EM_TRIAGEM com cor definida,
// define o destino pelos sintomas, gera a senha e leva a ficha a AGUARDANDO numa única transação auditada.
query "fichas/{ficha_id}/confirmar-triagem" verb=POST {
  api_group = "Triagem"
  description = "Confirma a triagem: destino pelos sintomas, senha COR-ESP-NNN e ficha AGUARDANDO."

  auth = "usuario"

  input {
    int ficha_id
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

        function.run "direcionamento/inicializar_direcionamento" {
          input = {}
        } as $direcionamento_inicializado

        db.get ficha_atendimento {
          field_name = "id"
          field_value = $input.ficha_id
        } as $ficha

        precondition ($ficha != null) {
          error_type = "notfound"
          error = "FICHA_NAO_ENCONTRADA"
        }

        precondition ($ficha.status == "EM_TRIAGEM") {
          error_type = "inputerror"
          error = "FICHA_FORA_DA_TRIAGEM"
        }

        precondition ($ficha.prioridade_atual != null) {
          error_type = "inputerror"
          error = "FICHA_SEM_PRIORIDADE"
        }

        function.run "direcionamento/destino_da_ficha" {
          input = {ficha_id: $ficha.id}
        } as $destino

        precondition (!($destino.avaliacao.classificacao.pendencias|in:"SEM_SINTOMA_OU_OBSERVACAO")) {
          error_type = "inputerror"
          error = "FICHA_SEM_SINTOMA_OU_OBSERVACAO"
        }

        precondition ($destino.especialidade != null) {
          error_type = "inputerror"
          error = "DESTINO_NAO_CONFIGURADO"
        }

        function.run "direcionamento/gerar_senha" {
          input = {especialidade_id: $destino.especialidade.id, sigla: $destino.especialidade.sigla, prioridade: $ficha.prioridade_atual}
        } as $senha

        db.patch ficha_atendimento {
          field_name = "id"
          field_value = $ficha.id
          data = {
            especialidade_sugerida_id : $destino.especialidade.id
            especialidade_atribuida_id: $destino.especialidade.id
            senha                     : $senha.senha
            senha_numero              : $senha.numero
            status                    : "AGUARDANDO"
          }
        } as $ficha_confirmada

        function.run "registrar_alteracao" {
          input = {
            usuario_id    : $usuario.id
            tipo_evento   : "TRIAGEM_CONFIRMADA"
            entidade      : "FICHA_ATENDIMENTO"
            registro_id   : $ficha.id
            valor_anterior: {status: $ficha.status}
            valor_novo    : {status: "AGUARDANDO", especialidade_id: $destino.especialidade.id, motivo_destino: $destino.motivo, senha: $senha.senha, prioridade_atual: $ficha.prioridade_atual}
          }
        } as $auditoria
      }
    }
  }

  response = {
    id           : $input.ficha_id
    status       : "AGUARDANDO"
    senha        : $senha.senha
    prioridade   : $ficha.prioridade_atual
    especialidade: $destino.especialidade
  }
  guid = "YRvQbCSQu5Qx6p8h6ikYcWaGEvo"
}
