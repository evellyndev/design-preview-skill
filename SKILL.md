---
name: design-preview
description: Gera exatamente três propostas visuais alternativas para a mesma tela ou fluxo, respeitando o arquivo design_guideline do projeto. Cria previews independentes em preview/design-01, design-02 e design-03 usando HTML, CSS e JavaScript mínimo; permite escolher uma opção e remove somente as outras duas após seleção explícita. Use quando o usuário pedir para explorar, comparar ou escolher designs de uma interface antes de implementar.
---

# Design Preview — três alternativas, uma escolha

## Objetivo

Criar **três designs realmente diferentes da mesma tela ou do mesmo fluxo** para avaliação antes da implementação definitiva. O resultado deve poder ser aberto num navegador sem instalar bibliotecas. Nunca confundir três alternativas de design com três telas distintas de um mesmo produto: as três propostas devem responder ao mesmo pedido funcional, a menos que o usuário determine outra coisa.

## 1. Ler as diretrizes antes de desenhar

1. Encontrar o arquivo indicado pelo usuário como `design_guideline`. Se nenhum caminho for informado, procurar primeiro `design_guideline.md`, `design_guideline.mdx`, `design_guideline.txt`, `design-guideline.md` e equivalentes sob `docs/` ou `design/` na raiz do projeto. Aceitar PDF se houver ferramenta para ler seu conteúdo. Não inferir o conteúdo de um arquivo que não foi lido.
2. Ler o arquivo **inteiro**, além de tokens CSS, fontes, componentes, exemplos e assets a que ele explicitamente fizer referência. Se houver orientação de produto, preservar o objetivo, o conteúdo e as restrições do usuário.
3. Extrair uma pequena checklist interna de: cores e tokens, tipografia, espaçamento, componentes, acessibilidade, tom visual e restrições. Diretrizes explícitas têm prioridade sobre preferências genéricas de design.
4. Se não houver arquivo de diretrizes legível, não inventar uma identidade visual: pedir ao usuário o arquivo/caminho antes de gerar propostas.

## 2. Criar um lote de prévias isoladas

A partir da raiz do repositório:

```bash
python3 .agents/skills/design-preview/scripts/preview_manager.py init --project-root .
```

Se a skill tiver sido instalada globalmente, usar o caminho real do script da skill em vez de `.agents/skills/...`.

O comando cria:

```text
preview/
├── index.html                 # galeria de comparação e escolha
├── .design-preview.json       # metadados controlados pela skill
├── design-01/
│   └── index.html
├── design-02/
│   └── index.html
└── design-03/
    └── index.html
```

Os três subdiretórios também incluem uma pequena marca de gerenciamento criada pelo script. **Não apagar, sobrescrever ou mover um diretório `preview/` preexistente**. Se `init` recusar porque já existe um lote, primeiro inspecionar seu conteúdo e explicar ao usuário; só refazer ou arquivar com autorização explícita.

## 3. Gerar exatamente três designs

Implementar **cada proposta integralmente no respectivo `preview/design-0N/index.html`** (ou com um `styles.css` local caso fique mais legível). Cada uma deve:

- Realizar a **mesma tarefa do usuário**, com os mesmos textos, informações e ações principais. Se informações não existirem, usar dados fictícios reconhecíveis como demonstração, nunca apresentar como reais.
- Obedecer ao `design_guideline` de forma rastreável. Diferenciar soluções por **estrutura, hierarquia, navegação, composição, densidade e uso de espaço**, não só trocar cores.
- Ser um HTML completo e independente, responsivo para desktop e celular, legível, acessível ao teclado e com contraste adequado.
- Usar **HTML semântico e CSS vanilla**. Adicionar JavaScript vanilla apenas quando for indispensável para demonstrar uma interação; sem React, Vue, Tailwind, bibliotecas de componentes, build, CDN ou dependências externas, a menos que o usuário autorize.
- Manter todos os arquivos e recursos de cada opção dentro da própria pasta, sem dependências das outras duas.
- Não modificar o código de produção antes da escolha do usuário.

As três propostas devem ser visual e estruturalmente distinguíveis à primeira vista. Evitar três variantes triviais do mesmo template. Se for adequado às diretrizes, explorar por exemplo: composição editorial; organização com painel e navegação; composição modular e concentrada. Essas são direções possíveis, não estilos obrigatórios.

Depois de gerar os três HTMLs, atualizar **somente** os campos `name` e `description` de cada objeto em `preview/.design-preview.json`, com descrições verdadeiras e curtas do que distingue a proposta. Preservar `status`, `id` e outros campos. Atualizar a galeria com:

```bash
python3 .agents/skills/design-preview/scripts/preview_manager.py index --project-root .
```

Validar a existência de todas as três propostas e abrir/testar a galeria quando houver meios disponíveis. A galeria mostra as três opções lado a lado em telas largas e empilhadas em telas pequenas.

## 4. Apresentar e aguardar a escolha

Informar ao usuário os três nomes/diferenças e como abrir `preview/index.html`. Para que os botões **“Escolher esta opção”** da galeria possam apagar diretórios, iniciar o servidor local padrão da biblioteca Python:

```bash
python3 .agents/skills/design-preview/scripts/preview_manager.py serve --project-root . --port 8765
```

Abrir `http://127.0.0.1:8765/`. O servidor escuta apenas no computador local. **Não escolher pelo usuário**, mesmo que uma opção pareça superior. Se o usuário abrir `index.html` via `file://` ou usar um servidor estático genérico, ele ainda poderá visualizar as três propostas, mas o botão de exclusão não funcionará; nesse caso, a escolha pode ser feita na conversa e executada via CLI.

## 5. Excluir as duas alternativas apenas depois da seleção explícita

Quando o usuário escolher `1`, `2` ou `3` na conversa, executar:

```bash
python3 .agents/skills/design-preview/scripts/preview_manager.py select --project-root . --design 2
```

Substituir `2` pela opção realmente escolhida. O script valida a marca de gerenciamento, preserva a escolhida, apaga **somente** os dois subdiretórios de propostas descartadas, atualiza o estado e faz `preview/index.html` apontar para o design vencedor. O botão da galeria realiza a mesma operação pelo servidor local, após um clique explícito.

Não apagar nada fora dos diretórios `preview/design-01`, `preview/design-02` e `preview/design-03`; não alterar o projeto de produção automaticamente. Não executar seleção por suposição ou para “limpar” arquivos. Após a escolha, informar o design preservado e a localização.

## Critérios de aceite

- Antes da escolha: exatamente três opções independentes, navegáveis em `preview/`, seguindo o guideline.
- Cada opção é uma solução diferente para a **mesma necessidade**.
- Sem frameworks e sem JavaScript supérfluo.
- Nenhuma opção descartada antes da escolha explícita.
- Depois da escolha: resta apenas o diretório escolhido, e nenhum arquivo fora das duas opções descartadas foi apagado.
