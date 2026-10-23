import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("catalogo", ROOT / "src/python/main.py")
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class CatalogoTest(unittest.TestCase):
    def setUp(self):
        self.dados = json.loads((ROOT / "src/python/dados.json").read_text(encoding="utf-8"))
        self.catalogo = app.validar_catalogo(self.dados)

    def test_norma_conhecida(self):
        self.assertAlmostEqual(app.norma_embedding([0.3, 0.4, 0, 0]), 0.5)
        self.assertEqual(app.norma_embedding([0, 0, 0, 0]), 0)

    def test_vetores_invalidos(self):
        for vetor in ([1, 2], [1, 0, 0, float("nan")], [1, 0, 0, float("inf")],
                      [1, 0, 0, -1], [1, 0, 0, 2], [1, 0, 0, True], ["1", 0, 0, 0], None):
            with self.subTest(vetor=vetor), self.assertRaises(ValueError):
                app.norma_embedding(vetor)

    def test_busca_sem_acentos_por_tags_e_nivel(self):
        self.assertEqual([i["id"] for i in app.filtrar_instrumentos(self.catalogo, "VIOLAO")], ["violao"])
        self.assertEqual([i["id"] for i in app.filtrar_instrumentos(self.catalogo, "jazz", "Teclas")], ["piano"])
        self.assertEqual(len(app.filtrar_instrumentos(self.catalogo, "iniciante")), 2)

    def test_filtros_combinados(self):
        itens = app.filtrar_instrumentos(self.catalogo, familia="Cordas", disponibilidade="Disponível")
        self.assertEqual([i["id"] for i in itens], ["violao"])

    def test_sem_resultados_e_ordem(self):
        self.assertEqual(app.filtrar_instrumentos(self.catalogo, "astronauta"), [])
        self.assertEqual(app.filtrar_instrumentos(self.catalogo, ordem="norma")[0]["id"], "piano")
        self.assertEqual(app.filtrar_instrumentos(self.catalogo)[0]["id"], "bateria")

    def test_rejeita_busca_e_filtros_invalidos(self):
        for parametros in ({"busca": "a" * 81}, {"busca": "a\x00b"}, {"busca": None},
                           {"familia": "Metais"}, {"disponibilidade": "Livre"}, {"ordem": "script"}):
            with self.subTest(parametros=parametros), self.assertRaises(ValueError):
                app.filtrar_instrumentos(self.catalogo, **parametros)

    def test_busca_html_e_apenas_texto(self):
        self.assertEqual(app.filtrar_instrumentos(self.catalogo, '<img src=x onerror="alert(1)">'), [])

    def test_ids_duplicados(self):
        self.dados["instrumentos"].append(copy.deepcopy(self.dados["instrumentos"][0]))
        with self.assertRaises(ValueError):
            app.validar_catalogo(self.dados)

    def test_esquemas_invalidos(self):
        for campo, valor in (("versao", 2), ("versao", True), ("dimensoes", []), ("instrumentos", [])):
            dados = copy.deepcopy(self.dados)
            dados[campo] = valor
            with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                app.validar_catalogo(dados)

    def test_rejeita_caminhos_e_campos_invalidos(self):
        for campo, valor in (("imagem", "https://example.com/a.jpg"), ("imagem", "src/assets/../../a.jpg"),
                             ("nome", ""), ("tags", []), ("status", "Apagado"), ("id", "../x")):
            dados = copy.deepcopy(self.dados)
            dados["instrumentos"][0][campo] = valor
            with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                app.validar_catalogo(dados)

    def test_telemetria_limitada_e_sem_texto_de_busca(self):
        telemetria = app.Telemetria()
        for _ in range(70):
            telemetria.registrar("busca")
        self.assertEqual(telemetria.contadores["busca"], 70)
        self.assertEqual(len(telemetria.eventos), 50)
        self.assertEqual(set(telemetria.eventos[-1]), {"tipo", "horario", "instrumento"})
        with self.assertRaises(ValueError):
            telemetria.registrar("segredo")
        with self.assertRaises(ValueError):
            telemetria.registrar("busca", "texto livre digitado pelo usuario")

    def test_filtro_nao_modifica_base(self):
        original = copy.deepcopy(self.catalogo)
        app.filtrar_instrumentos(self.catalogo, "jazz", ordem="norma")
        self.assertEqual(self.catalogo, original)


if __name__ == "__main__":
    unittest.main()
