// Gera e envia por e-mail um código de verificação, invalidando o anterior da mesma finalidade (design D12/D13).
function "auth/emitir_codigo" {
  description = "Invalida o código aberto do usuário na finalidade, grava o hash de um novo código de 6 dígitos e o envia pelo modelo da Brevo."

  input {
    int usuario_id
    text nome
    text email
    enum finalidade {
      values = ["LOGIN", "REDEFINICAO_SENHA"]
    }
    timestamp iniciado_em
  }

  stack {
    var $ttl {
      value = $env.CODIGO_TTL_SEGUNDOS|to_int
    }

    precondition ($ttl > 0) {
      error_type = "standard"
      error = "Variável de ambiente CODIGO_TTL_SEGUNDOS não configurada."
    }

    db.query codigo_verificacao {
      where = $db.codigo_verificacao.usuario_id == $input.usuario_id && $db.codigo_verificacao.finalidade == $input.finalidade && $db.codigo_verificacao.usado_em == null
    } as $abertos

    // Só um código válido por usuário e finalidade.
    foreach ($abertos) {
      each as $aberto {
        db.edit codigo_verificacao {
          field_name = "id"
          field_value = $aberto.id
          data = {usado_em: now}
        }
      }
    }

    security.random_number {
      min = 100000
      max = 999999
    } as $numero

    var $codigo {
      value = $numero|to_text
    }

    db.add codigo_verificacao {
      data = {
        usuario_id : $input.usuario_id
        finalidade : $input.finalidade
        codigo_hash: $codigo|hmac_sha256:("ps-codigo:" ~ ($input.usuario_id|to_text))
        iniciado_em: $input.iniciado_em
        criado_em  : now
        expira_em  : now|add_secs_to_timestamp:$ttl
        tentativas : 0
      }
    } as $novo

    // Modelos da Brevo: 6 = ps_codigo_acesso_login, 7 = ps_redefinicao_senha (backend/brevo/).
    api.request {
      url = "https://api.brevo.com/v3/smtp/email"
      method = "POST"
      params = {
        sender    : {name: "Sistema de Fila Prioritária", email: $env.BREVO_REMETENTE}
        to        : [{email: $input.email, name: $input.nome}]
        templateId: ($input.finalidade == "LOGIN" ? 6 : 7)
        params    : {nome: $input.nome, codigo: $codigo, minutos: ($ttl / 60)|floor}
      }
      headers = [
        "Content-Type: application/json"
        "api-key: " ~ $env.BREVO_API_KEY
      ]
    } as $resposta_brevo

    precondition ($resposta_brevo.response.status >= 200 && $resposta_brevo.response.status < 300) {
      error_type = "standard"
      error = "Não foi possível enviar o código. Tente novamente em instantes."
    }
  }

  response = {criado_em: $novo.criado_em}
  guid = "fBb7DQFrBoBFEnt0cDwBjf1XG-E"
}
