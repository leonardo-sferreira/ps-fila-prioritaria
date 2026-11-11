// Cadastro da pessoa com perfil RECEPCAO_TRIAGEM, vinculado 1:1 ao usuário. O nome e o e-mail ficam no usuário.
// Desativado junto com o login, nunca excluído (add-cadastros-administrador, D3 e D5).
table recepcao_triagem {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int usuario_id {
      table = "usuario"
    }
    // Só dígitos, validado por pacientes/normalizar_cpf.
    text cpf filters=trim
    // Cadastral; não limita a triagem.
    int? especialidade_referencia_id? {
      table = "especialidade"
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "usuario_id", op: "asc"}]}
    {type: "btree|unique", field: [{name: "cpf", op: "asc"}]}
  ]
  guid = "2LihNU7KY429toOcqlOKjDXV8Vc"
}
