# Protótipo de UX 60+ (Etapa 1)

Este documento define o protótipo inicial para a experiência do novo app SEPOL 2.0 com foco em público 60+.

## 1) Diretrizes visuais

- **Tipografia base:** 18px no conteúdo, 20–24px em títulos de tela.
- **Altura de linha:** mínimo 1.5 para facilitar leitura.
- **Peso mínimo:** 500 para rótulos e botões principais.
- **Contraste:** razão mínima WCAG AA (4.5:1), preferencialmente 7:1 em textos críticos.
- **Áreas clicáveis:** mínimo 44x44px.
- **Espaçamento:** blocos com 16–24px para reduzir poluição visual.

### Paleta sugerida (alto contraste)
- Fundo: `#F8FAFC`
- Texto primário: `#0F172A`
- Texto secundário: `#334155`
- Ação principal: `#0EA5E9`
- Sucesso: `#16A34A`
- Alerta: `#F59E0B`
- Erro: `#DC2626`

## 2) Modelo funcional do orçamento

### 2.1 Campos do Orçamento
- **Número:** ID único do orçamento.
- **Descrição:** detalhamento do orçamento (texto livre).
- **Cliente:** nome, endereço e indicação.
- **Data de Emissão:** data de início do processo do orçamento.
- **Previsão de Início:** opcional (só exibe no PDF se preenchido).
- **Previsão de Término:** opcional (só exibe no PDF se preenchido).
- **Status:** Rascunho, Emitido, Aprovado, Cancelado.
- **Total Mão-de-Obra:** soma dos totais das fases.

### 2.2 Estrutura obrigatória
1. A estrutura obrigatória é: **Orçamento > Fases > Serviços**.
2. Todo orçamento pertence a **1 cliente**.
3. Todo orçamento deve ter **pelo menos 1 fase**.
4. Toda fase deve ter **pelo menos 1 serviço**.
5. Somente mão de obra entra no orçamento (não inclui material).

### 2.3 Fases
- **Descrição:** detalhamento de cada fase a ser realizada.
- **Subtotal:** soma dos valores totais de cada serviço vinculado à fase.

### 2.4 Serviços
- **Descrição:** detalhamento do serviço da fase.
- **Quantidade:** decimal, valor padrão `1`.
- **Valor Unitário:** preço da mão de obra por unidade do serviço.
- **Valor Total:** cálculo de `Quantidade x Valor Unitário`.

## 3) Status e versionamento

- **Rascunho:** ainda não emitido; salvo na versão `v1`.
- **Emitido:** versão `v1` emitida. Após emitido, cada edição gera nova versão (`v2`, `v3`...). Permite aprovar ou cancelar. Permite gerar e imprimir PDF.
- **Aprovado:** versão aprovada pelo cliente; usada para vincular à obra. Não permite editar nem cancelar. **PDF bloqueado**.
- **Cancelado:** reprovado, não respondido pelo cliente ou não atende ROC esperado. **PDF bloqueado**.

## 4) Fluxo guiado (visão macro)

1. Iniciar orçamento.
2. Buscar ou cadastrar cliente.
3. Cadastrar fases e serviços.
4. Revisar totais por fase e total mão-de-obra.
5. Emitir orçamento.
6. (Opcional enquanto emitido) editar para gerar nova versão.
7. Aprovar ou cancelar orçamento emitido.
8. Se aprovado, vincular à obra.

### Progresso visível
- Barra no topo com etapas nomeadas.
- Etapa atual destacada.
- Etapas bloqueadas cinzas até pré-condição ser cumprida.

## 5) Wireframe textual das telas-chave

### Tela A — Dashboard inicial
- Card grande: **"Novo orçamento"**.
- Lista curta por status: Rascunhos, Emitidos, Aprovados, Cancelados.
- Busca rápida com filtros por número, nome do orçamento, cliente e status.

### Tela B — Iniciar Orçamento
- Ação 1: **Buscar cliente existente**.
- Ação 2: **Cadastrar novo cliente**.
- Campos de orçamento: número, descrição, data de emissão, previsões (opcionais).
- Bloco de fases: adicionar/editar/remover fase.
- Bloco de serviços por fase: adicionar/editar/remover serviço.
- Regra visual: bloquear avanço sem ao menos 1 fase e 1 serviço por fase.

### Tela C — Edição de Fases e Serviços
- Serviço: descrição, quantidade, valor unitário, valor total.
- Fase: subtotal calculado pela soma dos serviços da fase.
- Orçamento: total mão-de-obra calculado pela soma dos subtotais das fases.

### Tela D — Emissão do orçamento
- Botão: **"Emitir orçamento"**.
- Confirmação: "Deseja emitir este orçamento agora?"
- Após emissão:
  - Status: "Emitido"
  - Ações permitidas: editar (gera nova versão), aprovar, cancelar, gerar PDF, imprimir PDF.

### Tela E — Aprovação do orçamento
- Botão principal: **"Aprovar orçamento"** (somente quando status = Emitido).
- Mensagem: "Após aprovar, este orçamento será bloqueado para edição e cancelamento."
- Após aprovação:
  - Status: "Aprovado"
  - Ação disponível: **"Vincular à obra"**
  - PDF bloqueado.

### Tela F — Consulta de Orçamentos
- Filtros:
  - Número
  - Nome do orçamento
  - Nome do cliente
  - Status
- Resultado com ações por status (abrir, editar versão quando emitido, aprovar, cancelar, gerar/imprimir PDF quando emitido).

## 6) Regras de negócio complementares

1. Cliente contém nome, endereço e indicação.
2. Se o orçamento for aprovado, cadastrar/confirmar cadastro do cliente.
3. Previsão de início e término são opcionais e só entram no PDF se preenchidas.
4. PDF só pode ser gerado/imprimido para orçamento com status **Emitido**.

## 7) Padrões de linguagem (microcopy)

- Preferir frases curtas e diretas.
- Evitar jargão técnico.

### Textos de confirmação
- "Orçamento salvo com sucesso."
- "Orçamento emitido com sucesso."
- "Nova versão do orçamento criada."
- "Orçamento aprovado com sucesso."
- "Orçamento cancelado com sucesso."
- "Não foi possível salvar. Tente novamente."

## 8) Acessibilidade mínima obrigatória

- Navegação por teclado visível (focus ring forte).
- Labels associados a todos os campos.
- Mensagens de erro próximas ao campo.
- Não depender apenas de cor para comunicar estado.

## 9) Critérios de aceite da Etapa 1 (UX)

1. Campos obrigatórios e opcionais do orçamento estão definidos.
2. Estrutura **Orçamento > Fases > Serviços** está explícita e obrigatória.
3. Cálculos de subtotal por fase e total mão-de-obra estão documentados.
4. Status e regras de transição (rascunho, emitido, aprovado, cancelado) estão documentados.
5. Regras de PDF por status estão documentadas.
6. Consulta por número, nome do orçamento, cliente e status está definida.
7. Requisitos mínimos de acessibilidade estão definidos.

---

Com este protótipo fechado, o próximo passo do roadmap é implementar o módulo de orçamento em 3 passos aderente às regras acima.
