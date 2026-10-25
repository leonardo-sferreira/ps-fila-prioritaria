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

  response = $usuario
  guid = "nT4cvJFnCLpa3B6ijMw3TEyYfBw"
}
