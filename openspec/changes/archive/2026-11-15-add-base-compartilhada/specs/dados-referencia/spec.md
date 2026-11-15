## ADDED Requirements

### Requirement: Carga automática das especialidades
O sistema DEVE criar, quando faltarem, as especialidades Cardiologia (CAR), Clínica Geral (CLI), Neurologia (NEU), Ortopedia (ORT) e Pediatria (PED), as ligações dos sintomas do catálogo à sua especialidade e o parâmetro `ESPECIALIDADE_PADRAO`. A carga DEVE ser idempotente: NÃO DEVE duplicar registros nem sobrescrever dados alterados pelo Administrador. Os sintomas são mantidos pelo Administrador nos cadastros.

#### Scenario: Ambiente recém-preparado
- **QUANDO** o direcionamento roda pela primeira vez sem especialidades cadastradas
- **ENTÃO** as cinco especialidades e o `ESPECIALIDADE_PADRAO` são criados

#### Scenario: Dado alterado depois da carga
- **QUANDO** o Administrador alterou uma ligação de sintoma e a carga roda de novo
- **ENTÃO** a ligação alterada é mantida
