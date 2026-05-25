# Visão do Produto (60+ Friendly)

## Objetivo principal
Permitir que a equipe gere orçamentos rapidamente, com linguagem simples e poucos cliques.

## Regras de negócio centrais
1. Orçamento segue a estrutura obrigatória: Orçamento > Fases > Serviços.
2. Cada orçamento pertence a 1 cliente e deve ter pelo menos 1 fase e 1 serviço por fase.
3. Orçamento contém: número (ID único), descrição, cliente, data de emissão, previsão de início (opcional), previsão de término (opcional), status e total mão-de-obra.
4. Serviços possuem descrição, quantidade (decimal; padrão 1), valor unitário e valor total (quantidade x valor unitário).
5. Fase possui descrição e subtotal (soma dos totais dos serviços da fase).
6. Total mão-de-obra do orçamento é a soma dos subtotais das fases.
7. Orçamento possui versionamento: rascunho inicia em v1; após emitido, cada edição gera nova versão.
8. Status: Rascunho, Emitido, Aprovado, Cancelado.
9. Emitido permite aprovar/cancelar e gerar/imprimir PDF.
10. Aprovado bloqueia edição, cancelamento e PDF; é a versão usada para vincular à obra.
11. Cancelado bloqueia PDF e representa reprovado, sem resposta ou fora do ROC esperado.
12. Orçamento considera somente mão de obra (sem material).
13. Permitir consulta de orçamentos por número, nome do orçamento, nome do cliente e status.

## Princípios de UX para 60+
- Fonte maior e alto contraste.
- Botões claros com ação explícita.
- Fluxo linear com progresso visível.
- Confirmações de ação com linguagem simples.
- Histórico de alterações fácil de consultar.
