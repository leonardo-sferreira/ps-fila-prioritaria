// Regra do último administrador (add-autenticacao-perfis, D9/D14). Função pura: recebe os IDs dos administradores
// ativos e o usuário afetado; true quando tirar esse usuário deixaria o sistema sem nenhum administrador ativo.
function "usuarios/deixa_sem_admin" {
  description = "true se, sem o usuário informado, não sobrar nenhum administrador ativo."

  input {
    json? admins_ativos?
    int usuario_id
  }

  stack {
    var $restantes {
      value = ($input.admins_ativos ?? [])|filter:($$ != $input.usuario_id)
    }
  }

  response = ($restantes|count) == 0

  test "único administrador ativo" {
    input = {admins_ativos: [7], usuario_id: 7}
    expect.to_be_true ($response)
  }

  test "há outro administrador ativo" {
    input = {admins_ativos: [7, 9], usuario_id: 7}
    expect.to_be_false ($response)
  }

  test "usuário afetado não é administrador" {
    input = {admins_ativos: [7], usuario_id: 3}
    expect.to_be_false ($response)
  }
}
