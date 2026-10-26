// Código de 6 dígitos enviado por e-mail no login e na redefinição de senha (design D12/D13).
table codigo_verificacao {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int usuario_id {
      table = "usuario"
    }
    enum finalidade {
      values = ["LOGIN", "REDEFINICAO_SENHA"]
    }
    // HMAC do código; o código em texto só segue por e-mail.
    text codigo_hash {
      sensitive = true
    }
    // Início do pedido (no login, quando a senha foi conferida); reenvios mantêm o mesmo valor.
    timestamp iniciado_em
    timestamp criado_em
    timestamp expira_em
    int tentativas?=0
    timestamp? usado_em?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "usuario_id", op: "asc"}]}
    {type: "btree", field: [{name: "criado_em", op: "desc"}]}
  ]
  guid = "Y0J4ut52XT0Y3sYbtMPOhxSObno"
}
