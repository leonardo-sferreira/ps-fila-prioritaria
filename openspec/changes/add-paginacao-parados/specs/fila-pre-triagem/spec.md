## ADDED Requirements

### Requirement: Prévia paginada dos parados
A prévia de fichas e tickets parados no dashboard do Administrador DEVE ser apresentada numa lista única, com o tipo de cada item, paginada com 10 itens por página por padrão. O Administrador DEVE poder escolher 10, 25 ou 50 itens por página e ordenar por maior tempo parado (padrão) ou menor tempo parado. A paginação NÃO DEVE alterar o alcance da dispensa, que continua encerrando todos os itens parados.

#### Scenario: Mais de uma página
- **QUANDO** há 11 itens parados e o tamanho é 10
- **ENTÃO** a página 1 mostra os 10 mais antigos e a página 2 mostra o mais recente

#### Scenario: Troca de quantidade
- **QUANDO** há 11 itens parados e o Administrador escolhe 25 por página
- **ENTÃO** todos aparecem numa só página, que volta a ser a página 1

#### Scenario: Menor tempo primeiro
- **QUANDO** o Administrador escolhe "Menor tempo parado"
- **ENTÃO** o item emitido mais recentemente aparece primeiro

#### Scenario: Dispensa ignora a página
- **QUANDO** há 30 itens parados, o Administrador está na página 2 e dispensa todos
- **ENTÃO** os 30 itens são encerrados
