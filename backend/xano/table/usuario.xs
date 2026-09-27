// Pessoa da equipe que acessa o sistema (tabela de autenticação).
table usuario {
  auth = true

  schema {
    int id
    timestamp created_at?=now
    text nome filters=trim
    email email filters=trim|lower
    password password filters=min:8
    enum perfil {
      values = ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
    }
    bool ativo?=true
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "email", op: "asc"}]}
  ]
  guid = "qZWNw40tw5OursPW86Yx33QfQBY"
}
