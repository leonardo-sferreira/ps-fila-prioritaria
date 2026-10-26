query "auth/me" verb=GET {
  api_group = "Autenticacao"
  description = "Devolve o usuário do token, recarregado do banco (usado pelo Reflex para proteger as rotas)."
  auth = "usuario"

  input {
  }

  stack {
    function.run "auth/verificar_acesso" {
      input = {
        usuario_id       : $auth.id,
        perfis_permitidos: ["RECEPCAO_TRIAGEM", "MEDICO", "ADMINISTRADOR"]
      }
    } as $usuario
  }

  // inatividade_segundos: tempo sem uso até a tela encerrar a sessão (add-privacidade, D4).
  response = {
    id                  : $usuario.id
    nome                : $usuario.nome
    email               : $usuario.email
    perfil              : $usuario.perfil
    inatividade_segundos: $env.INATIVIDADE_SEGUNDOS|to_int
  }
  guid = "nT4cvJFnCLpa3B6ijMw3TEyYfBw"
}
