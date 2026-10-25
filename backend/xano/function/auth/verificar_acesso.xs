// Ponto único de autorização por perfil (design D3), chamado no início de todo endpoint protegido.
function "auth/verificar_acesso" {
  description = "Recarrega o usuário do token: 401 se não existir ou estiver inativo; 403 se o perfil não for permitido."

  input {
    int usuario_id
    text[] perfis_permitidos
  }

  stack {
    db.get usuario {
      field_name = "id"
      field_value = $input.usuario_id
    } as $usuario

    // Recarregar a cada requisição faz a desativação valer na hora, mesmo com token ainda válido.
    precondition ($usuario != null && $usuario.ativo) {
      error_type = "unauthorized"
      error = "Sessão inválida. Faça login novamente."
    }

    precondition ($input.perfis_permitidos|in:$usuario.perfil) {
      error_type = "accessdenied"
      error = "Acesso negado para o seu perfil."
    }
  }

  response = {
    id    : $usuario.id
    nome  : $usuario.nome
    email : $usuario.email
    perfil: $usuario.perfil
  }
  guid = "RT2RGSBZbsDvK6n8lIJczGdrwvA"
}
