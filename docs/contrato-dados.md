# Contrato do catálogo v1

`src/python/dados.json` contém `versao: 1`, quatro `dimensoes` e uma lista `instrumentos`.
Os dados são fictícios para demonstração e podem ser substituídos pela equipe mantendo o contrato.

Cada instrumento tem `id` único (letras minúsculas, números e hífen), `nome`,
`familia` (Cordas, Teclas, Percussão ou Sopros), `nivel` (Iniciante, Intermediário
ou Todos os níveis), `status` (Disponível, Em aula ou Em manutenção), `imagem`
(caminho local em src/assets/), `sala`, `descricao`, `tags` e `embedding`.

O embedding tem quatro valores finitos de 0 a 1, na ordem Acústico, Rítmico,
Melódico e Polifônico. São descritores didáticos escolhidos manualmente;
não foram obtidos de áudio nem de um modelo treinado. Não medem qualidade,
dificuldade ou adequação a uma pessoa.

A norma euclidiana é `numpy.linalg.norm(vetor)`, isto é,
`sqrt(x1² + x2² + x3² + x4²)`. Para [1, 0, 0, 0], o resultado é 1.

Guardrails: validar esquema, limites, caminhos locais, IDs, categorias e vetores;
limitar a busca a 80 caracteres; escapar texto ao renderizar HTML.
Telemetria: contadores e até 50 eventos em memória na aba, apenas tipo, horário
e ID do instrumento; não guardar termos de busca ou enviar dados para servidores.
