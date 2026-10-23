"""Catálogo Musicalia: regras testáveis em CPython e interface via PyScript."""

import json
import re
import sys
import unicodedata
from collections import Counter, deque
from datetime import datetime, timezone
from html import escape

import numpy as np

FAMILIAS = ("Cordas", "Teclas", "Percussão", "Sopros")
STATUS = ("Disponível", "Em aula", "Em manutenção")
NIVEIS = ("Iniciante", "Intermediário", "Todos os níveis")
ORDENS = ("nome", "norma")
DIMENSOES = ("Acústico", "Rítmico", "Melódico", "Polifônico")


def texto_seguro(valor, campo, limite=240):
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite:
        raise ValueError(f"Campo {campo} inválido.")
    if any(unicodedata.category(c).startswith("C") for c in valor):
        raise ValueError(f"Campo {campo} contém caracteres de controle.")
    return valor.strip()


def norma_embedding(vetor):
    """Norma L2 de quatro descritores didáticos, finitos e entre zero e um."""
    if not isinstance(vetor, list) or len(vetor) != 4:
        raise ValueError("Embedding deve ter quatro dimensões.")
    if any(type(v) not in (int, float) for v in vetor):
        raise ValueError("Embedding deve conter apenas números.")
    valores = np.array(vetor, dtype=float)
    if not np.isfinite(valores).all() or ((valores < 0) | (valores > 1)).any():
        raise ValueError("Embedding deve conter valores finitos entre 0 e 1.")
    return float(np.linalg.norm(valores))


def validar_catalogo(dados):
    if not isinstance(dados, dict) or type(dados.get("versao")) is not int or dados["versao"] != 1:
        raise ValueError("Versão do catálogo não suportada.")
    if dados.get("dimensoes") != list(DIMENSOES):
        raise ValueError("Dimensões do embedding incompatíveis.")
    registros = dados.get("instrumentos")
    if not isinstance(registros, list) or not 1 <= len(registros) <= 100:
        raise ValueError("Catálogo deve conter de 1 a 100 instrumentos.")
    catalogo, ids = [], set()
    for registro in registros:
        if not isinstance(registro, dict):
            raise ValueError("Instrumento deve ser um objeto.")
        item = {campo: texto_seguro(registro.get(campo), campo) for campo in (
            "id", "nome", "familia", "nivel", "status", "imagem", "sala", "descricao"
        )}
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", item["id"]) or item["id"] in ids:
            raise ValueError("ID inválido ou duplicado.")
        if item["familia"] not in FAMILIAS or item["status"] not in STATUS or item["nivel"] not in NIVEIS:
            raise ValueError("Família, status ou nível desconhecido.")
        if not re.fullmatch(r"src/assets/[a-z0-9_-]+\.(?:svg|jpg|jpeg|png|webp)", item["imagem"]):
            raise ValueError("Imagem deve ser um arquivo local em src/assets/.")
        tags = registro.get("tags")
        if not isinstance(tags, list) or not 1 <= len(tags) <= 5:
            raise ValueError("Forneça de 1 a 5 tags.")
        item["tags"] = [texto_seguro(tag, "tag", 30) for tag in tags]
        item["norma"] = norma_embedding(registro.get("embedding"))
        item["embedding"] = list(registro["embedding"])
        ids.add(item["id"])
        catalogo.append(item)
    return catalogo


def normalizar(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.casefold()) if not unicodedata.combining(c))


def filtrar_instrumentos(catalogo, busca="", familia="Todas", disponibilidade="Todos", ordem="nome"):
    if not isinstance(busca, str) or len(busca) > 80:
        raise ValueError("Use até 80 caracteres na busca.")
    if any(unicodedata.category(c).startswith("C") for c in busca):
        raise ValueError("Digite uma busca sem caracteres de controle.")
    if familia not in ("Todas", *FAMILIAS) or disponibilidade not in ("Todos", *STATUS) or ordem not in ORDENS:
        raise ValueError("Selecione um filtro válido.")
    termos = normalizar(busca).split()
    resultado = []
    for item in catalogo:
        texto = normalizar(" ".join([item["nome"], item["familia"], item["descricao"], item["nivel"], *item["tags"]]))
        if (familia == "Todas" or item["familia"] == familia) and (
            disponibilidade == "Todos" or item["status"] == disponibilidade
        ) and all(termo in texto for termo in termos):
            resultado.append(item)
    return sorted(resultado, key=lambda i: (-i["norma"], normalizar(i["nome"])) if ordem == "norma" else (normalizar(i["nome"]),))


class Telemetria:
    """Métricas efêmeras. Não coleta o texto digitado nem faz requisições."""

    def __init__(self):
        self.contadores = Counter()
        self.eventos = deque(maxlen=50)

    def registrar(self, tipo, instrumento=None):
        if tipo not in ("busca", "filtro", "detalhe", "bloqueio"):
            raise ValueError("Evento desconhecido.")
        if instrumento is not None and not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", instrumento):
            raise ValueError("ID de telemetria inválido.")
        self.contadores[tipo] += 1
        self.eventos.append({"tipo": tipo, "instrumento": instrumento, "horario": datetime.now(timezone.utc).isoformat()})


def iniciar_painel():
    """Adaptador DOM: as mesmas regras acima atendem busca, filtros e detalhes."""
    from pyscript import document
    from pyodide.ffi import create_proxy

    def elemento(id_):
        return document.getElementById(id_)

    status_runtime = elemento("runtime-status")
    carregamento = elemento("carregamento")
    try:
        with open("dados.json", encoding="utf-8") as arquivo:
            catalogo = validar_catalogo(json.load(arquivo))
    except (OSError, ValueError, TypeError) as erro:
        status_runtime.textContent = "Catálogo indisponível"
        carregamento.textContent = f"Não foi possível carregar os instrumentos. {erro} Recarregue a página após corrigir os dados."
        carregamento.setAttribute("role", "alert")
        return

    metricas = Telemetria()
    estado = {"familia": "Todas", "origem": None}
    proxies = []  # Preservar callbacks enquanto a página estiver aberta.

    def ouvir(alvo, evento, funcao):
        proxy = create_proxy(funcao)
        proxies.append(proxy)
        alvo.addEventListener(evento, proxy)

    def atualizar(evento=None, tipo=None):
        if tipo:
            metricas.registrar(tipo)
        try:
            itens = filtrar_instrumentos(catalogo, elemento("busca").value, estado["familia"])
        except ValueError as erro:
            metricas.registrar("bloqueio")
            elemento("erro-busca").textContent = str(erro)
            elemento("busca").setAttribute("aria-invalid", "true")
            return
        elemento("erro-busca").textContent = ""
        elemento("busca").removeAttribute("aria-invalid")
        cards = []
        for item in itens:
            e = {chave: escape(valor, quote=True) for chave, valor in item.items() if isinstance(valor, str)}
            classe = {"Disponível": "disponivel", "Em aula": "em-aula", "Em manutenção": "manutencao"}[item["status"]]
            cards.append(f'''<article class="instrumento">
                <div class="instrumento-foto"><img src="{e['imagem']}" alt="{e['nome']}" width="640" height="420" loading="lazy">
                <span class="disponibilidade {classe}"><span aria-hidden="true">●</span> {e['status']}</span></div>
                <div class="instrumento-conteudo"><p class="familia-label">{e['familia']} <span>·</span> {e['nivel']}</p>
                <h3>{e['nome']}</h3><p class="descricao">{e['descricao']}</p>
                <button class="conhecer" type="button" data-instrumento="{e['id']}" aria-label="Conhecer {e['nome']}">Conhecer instrumento <span aria-hidden="true">↗</span></button></div></article>''')
        elemento("catalogo-grid").innerHTML = "".join(cards)
        elemento("sem-resultados").hidden = bool(itens)
        quantidade = len(itens)
        elemento("contagem").textContent = f"{quantidade} instrumento{'s' if quantidade != 1 else ''} encontrado{'s' if quantidade != 1 else ''}"
        for botao in document.querySelectorAll("[data-familia]"):
            botao.setAttribute("aria-pressed", "true" if botao.getAttribute("data-familia") == estado["familia"] else "false")

    def selecionar_familia(evento):
        botao = evento.target.closest("button[data-familia]")
        if botao:
            estado["familia"] = botao.getAttribute("data-familia")
            atualizar(tipo="filtro")

    def limpar(evento):
        elemento("busca").value = ""
        estado["familia"] = "Todas"
        atualizar(tipo="filtro")
        elemento("busca").focus()

    def abrir_detalhe(evento):
        botao = evento.target.closest("button[data-instrumento]")
        if not botao:
            return
        id_ = botao.getAttribute("data-instrumento")
        item = next((i for i in catalogo if i["id"] == id_), None)
        if item is None:
            metricas.registrar("bloqueio")
            return
        estado["origem"] = botao
        elemento("detalhe-nome").textContent = item["nome"]
        elemento("detalhe-familia").textContent = item["familia"]
        elemento("detalhe-descricao").textContent = item["descricao"]
        elemento("detalhe-status").textContent = item["status"]
        elemento("detalhe-sala").textContent = item["sala"]
        elemento("detalhe-nivel").textContent = item["nivel"]
        elemento("detalhe-tags").textContent = " · ".join(item["tags"])
        elemento("detalhe-foto").src = item["imagem"]
        elemento("detalhe-foto").alt = item["nome"]
        elemento("detalhe-norma").textContent = f"{item['norma']:.3f}".replace(".", ",")
        elemento("detalhe-formula").textContent = "√(" + " + ".join(f"{v:g}²" for v in item["embedding"]) + ")"
        elemento("detalhe-vetores").innerHTML = "".join(
            f'<div class="vetor"><span>{escape(nome)}</span><meter min="0" max="1" value="{valor}" aria-label="{escape(nome)}">{valor}</meter><span>{valor:g}</span></div>'
            for nome, valor in zip(DIMENSOES, item["embedding"])
        )
        metricas.registrar("detalhe", id_)
        elemento("detalhe").showModal()

    def fechar_detalhe(evento):
        elemento("detalhe").close()

    def devolver_foco(evento):
        if estado["origem"]:
            estado["origem"].focus()

    ouvir(elemento("busca"), "input", lambda e: atualizar(e, "busca"))
    ouvir(elemento("familias"), "click", selecionar_familia)
    ouvir(elemento("limpar-vazio"), "click", limpar)
    ouvir(elemento("catalogo-grid"), "click", abrir_detalhe)
    ouvir(elemento("fechar-detalhe"), "click", fechar_detalhe)
    ouvir(elemento("detalhe"), "close", devolver_foco)
    # Referência Python explícita para manter vivos todos os proxies e closures.
    globals()["_callbacks_painel"] = proxies
    elemento("total-instrumentos").textContent = str(len(catalogo)).zfill(2)
    elemento("total-familias").textContent = str(len({i["familia"] for i in catalogo})).zfill(2)
    elemento("total-disponiveis").textContent = str(sum(i["status"] == "Disponível" for i in catalogo)).zfill(2)
    atualizar()
    elemento("controles").disabled = False
    carregamento.hidden = True
    status_runtime.textContent = ""


if sys.platform == "emscripten":
    iniciar_painel()
