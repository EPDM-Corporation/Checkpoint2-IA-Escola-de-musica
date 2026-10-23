# Musicalia · Catálogo interativo

Painel acadêmico de escola de música com busca, filtros de família
e detalhes dos instrumentos com norma vetorial. HTML, CSS, JSON e
Python via PyScript. Não há servidor de aplicação, banco, login ou reservas.

## Executar no Windows

O ZIP de validação já combina backend e frontend. Extraia-o em uma pasta.
Na pasta do projeto, com Python instalado:

```powershell
py -m http.server 8000 --bind 127.0.0.1
```

Abra http://localhost:8000. Alternativa: extensão Live Server no VS Code.
Não abra o index.html diretamente por file://: o navegador precisa buscar os arquivos por HTTP.
No Mac/Linux, use `python3 -m http.server 8000 --bind 127.0.0.1`.
Encerre com Ctrl+C no terminal.

O primeiro carregamento precisa de internet para baixar PyScript/Pyodide/NumPy.
O site informa o carregamento e só libera os controles depois que os dados foram validados.
Fontes Google são opcionais e têm fallback local. Imagens do catálogo ficam em src/assets/.
Nenhuma variável de ambiente ou segredo é necessário.

## Entregas e integração

- `feature/catalogo-backend` → PR para `dev`: dados, contrato, regras Python e testes.
- `feature/catalogo-frontend` → PR para `dev`: interface, imagens e integração PyScript.
- Cada tarefa tem pelo menos três commits semânticos. Revisar e integrar ambos os PRs
  em `dev` para executar o catálogo completo; os PRs foram criados independentemente.
- Homologar o resultado em `dev`, depois abrir PR de `dev` para `main`.
- Nenhum commit, push ou merge faz deploy automático.

## Estrutura

```text
index.html                 layout, filtros, modal e importação PyScript
src/css/estilo.css         variáveis, grid e responsividade
src/python/main.py        validação, busca, telemetria e NumPy
src/python/dados.json     base demonstrativa com contrato v1
src/assets/               fotos locais e favicon
tests/test_catalogo.py    testes das regras em CPython
docs/                     contrato, fontes de imagens e publicação manual
```

O vetor [acústico, rítmico, melódico, polifônico] usa valores didáticos manuais entre
0 e 1. `numpy.linalg.norm` calcula sua norma L2. Isso demonstra a representação
vetorial; não há modelo treinado ou inferência de áudio. O JSON e os status são fictícios.

Os guardrails validam o esquema, IDs, caminhos de imagens, categorias e vetores;
limitam a busca a 80 caracteres e escapam os textos renderizados. A telemetria
mantém contadores e os últimos 50 eventos somente em memória. Não guarda o termo
digitado e não envia eventos para serviços externos. As métricas são internas, sem painel visual.

## Dependências e testes

Runtime fixado: [PyScript 2026.7.3](https://docs.pyscript.net/),
Pyodide 314.0.3 (Python 3.14.0) e NumPy 2.4.3, conforme seu
[lockfile de distribuição](https://cdn.jsdelivr.net/pyodide/v314.0.3/full/pyodide-lock.json).
A configuração é inline no index.html; `requirements.txt` fixa o mesmo NumPy para testes.

Com Python 3.14, no Windows:

```powershell
py -3.14 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests -v
```

No Mac/Linux substitua o primeiro comando por `python3.14 -m venv .venv` e use
`.venv/bin/python` nos demais. Para servir o site, não é necessário instalar NumPy localmente:
o PyScript carrega a dependência no navegador.

## Conferência no navegador

1. Aguardar seis cards, quatro famílias e quatro instrumentos disponíveis.
2. Buscar “violao”: deve retornar Violão sem exigir acento.
3. Limpar a busca; selecionar Cordas: deve retornar Violão e Violino.
4. Buscar um texto sem correspondência: ver estado vazio e usar “Ver todos”.
5. Abrir Piano: conferir norma 1,803 e quatro descritores; fechar por botão e Escape.
6. Selecionar Teclas: deve aparecer somente Piano.
7. Conferir navegação por Tab, foco no modal e layout em celular.
8. Conferir os dados e a autoria das imagens antes de uma publicação externa.

## Fontes e publicação

Ver [créditos das imagens](docs/creditos-imagens.md),
[contrato dos dados](docs/contrato-dados.md) e
[procedimento manual de publicação e retorno](docs/publicacao.md).
