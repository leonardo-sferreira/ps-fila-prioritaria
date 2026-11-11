// Dispensa por prazo (add-expiracao-24h, D1): recalcula no servidor o que está parado agora e encerra tudo como
// DESISTENCIA, auditando EXPIRACAO em nome do Administrador. Não recebe IDs da tela, para não encerrar algo que
// mudou entre a prévia e o clique.
query "expiracao" verb=POST {
  api_group = "Triagem"
  description = "Encerra como desistência as fichas e os tickets parados há mais de HORAS_EXPIRACAO horas, com auditoria."

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
      input = {aplicar: true, usuario_id: $usuario.id}
    } as $resultado
  }

  response = $resultado
  guid = "focXJpdRqU9_RvvGveecMbbWZbM"
}
