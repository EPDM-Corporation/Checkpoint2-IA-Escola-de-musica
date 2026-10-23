# Publicação manual e retorno

Esta entrega é local e por pull request. O CI somente verifica código.

## Homologação

1. Integrar os dois PRs aprovados em dev. Executar testes e a conferência do README.
2. Registrar o SHA exato aprovado (`git rev-parse HEAD`) e gerar um pacote imutável
   com `git archive --format=zip --output=musicalia-<SHA>.zip <SHA>`.
3. Extrair esse pacote em pasta nova e servir via HTTP local. Conferir busca,
   filtros, modal, telemetria, imagens e dependências externas no navegador alvo.
4. Registrar SHA, checksum SHA-256 do pacote, data e resultado da validação.

## Produção, quando solicitada

Escolher primeiro o destino e o ambiente. Usar hospedagem estática; não há benefício
em adicionar backend, banco ou containers para este catálogo. Conferir créditos e
permissões de uso das imagens, nomes dos integrantes e dados de demonstração.

Promover exatamente o pacote homologado, preservando o pacote anterior. Confirmar
a identidade do destino, usar acesso pessoal com escopo restrito e permitir só uma
publicação por vez. Atualizar apenas a pasta deste site, sem alterar outros sites.
Após a ativação, conferir as funcionalidades e registrar o resultado com SHA do artefato.

## Retorno

Restaurar o pacote anterior, sem recompilar. Conferir catálogo e dependências externas.
Não há dados persistentes ou migrations: a telemetria é apagada ao recarregar a aba.
O pacote fixa o código e as imagens; ainda depende da disponibilidade dos CDNs de
PyScript/Pyodide e das fontes opcionais. Uso sem internet exige empacotar também o runtime.
