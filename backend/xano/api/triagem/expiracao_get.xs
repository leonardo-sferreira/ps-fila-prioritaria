// Prévia da dispensa por prazo (add-expiracao-24h, D1): fichas e tickets parados há mais de HORAS_EXPIRACAO horas.
// Só para o Administrador; não altera dados (além de criar o parâmetro padrão, se faltar).
query "expiracao" verb=GET {
  api_group = "Triagem"
  description = "Lista as fichas e os tickets parados há mais de HORAS_EXPIRACAO horas, sem alterar nada."

  auth = "usuario"

  input {}

  stack {
    function.run "auth/verificar_acesso" {
      input = {usuario_id: $auth.id, perfis_permitidos: ["ADMINISTRADOR"]}
    } as $usuario

    function.run "inicializar_parametros_fila" {
      input = {}
    } as $parametros

    function.run "manutencao/expirar_registros" {
      input = {aplicar: false}
    } as $previa
  }

  response = $previa
  guid = "_yXo5ydULsPBi55HFpmjSUslsck"
}
