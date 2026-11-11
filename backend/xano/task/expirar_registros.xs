// Rotina de expiração (add-expiracao-24h, D1/D4): a cada hora, garante os parâmetros da fila (cria HORAS_EXPIRACAO=24
// se faltar, sem sobrescrever) e encerra como desistência fichas e tickets que passaram do prazo.
task "expirar_registros" {
  description = "A cada hora, encerra como desistência fichas e tickets não concluídos dentro de HORAS_EXPIRACAO horas."

  stack {
    function.run "inicializar_parametros_fila" {
      input = {}
    } as $parametros

    function.run "manutencao/expirar_registros" {
      input = {}
    } as $resultado

    debug.log {
      value = $resultado
    }
  }

  schedule = [{starts_on: 2026-11-11 00:00:00+0000, freq: 3600}]
}
