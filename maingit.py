import os
import json
import fnmatch
import requests 


from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout






DATA_FILE = "Download/inventarioooo.json"

GITHUB_URL = "https://raw.githubusercontent.com/joserendonu/AppFilterOfOil/main/inventarioooo.json"



# -----------------------------------
# ITEM PERSONALIZADO (CORRECTO 🔥)
# -----------------------------------
class ItemRow(BoxLayout):
    texto = StringProperty("")
    index = NumericProperty(0)


KV = """
<ItemRow>:
    orientation: 'horizontal'
    size_hint_y: None
    height: dp(90)
    padding: dp(5)
    spacing: dp(5)

    Label:
        text: root.texto
        text_size: self.width, None
        halign: "left"
        valign: "middle"

    Button:
        text: "✏️"
        size_hint_x: None
        width: dp(50)
        on_press: app.editar_item(root.index)

    Button:
        text: "🗑️"
        size_hint_x: None
        width: dp(50)
        on_press: app.eliminar_item(root.index)

BoxLayout:
    orientation: 'vertical'

    TextInput:
        id: input_desc
        hint_text: "Escribe producto..."
        size_hint_y: None
        height: dp(50)

    Button:
        text: "➕ , COMA EN VEZ DE *"
        size_hint_y: None
        height: dp(50)
        on_press: app.agregar()

    TextInput:
        hint_text: "🔍 Buscar (usa *)"
        size_hint_y: None
        height: dp(50)
        on_text: app.aplicar_filtro(self.text)

    RecycleView:
        id: rv
        viewclass: 'ItemRow'

        RecycleBoxLayout:
            default_size: None, dp(90)
            default_size_hint: 1, None
            size_hint_y: None
            height: self.minimum_height
            orientation: 'vertical'
"""


# -----------------------------------
# APP
# -----------------------------------
class InventarioApp(App):
    
    def build(self):
        self.items = self.cargar_inventario()
        self.filtro_texto = ""

        root = Builder.load_string(KV)
        self.rv = root.ids.rv
        self.input_desc = root.ids.input_desc

        self.actualizar_lista()
        return root

    # -----------------------------------
    # DATA
    # -----------------------------------
    def cargar_inventario(self):

        items = []
        vistos = set()

        # Leer GitHub
        try:
            response = requests.get(GITHUB_URL, timeout=10)

            if response.status_code == 200:

                datos = response.json()

                if isinstance(datos, list):

                    for item in datos:

                        desc = item.get("desc", "").strip()

                        if desc and desc not in vistos:
                            vistos.add(desc)
                            items.append(item)

        except Exception as e:
            print("GitHub:", e)

        # Leer archivo local
        try:

            if os.path.exists(DATA_FILE):

                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    datos = json.load(f)

                if isinstance(datos, list):

                    for item in datos:

                        desc = item.get("desc", "").strip()

                        if desc and desc not in vistos:
                            vistos.add(desc)
                            items.append(item)

        except Exception as e:
            print("Local:", e)

        return items

    def guardar(self):

        try:

            carpeta = os.path.dirname(DATA_FILE)

            if carpeta:
                os.makedirs(carpeta, exist_ok=True)

            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    self.items,
                    f,
                    indent=2,
                    ensure_ascii=False
                )

        except Exception as e:
            print("Guardar:", e)



    # -----------------------------------
    # AGREGAR
    # -----------------------------------
    def agregar(self):
        desc = self.input_desc.text.strip()

        if not desc:
            return

        self.items.append({"desc": desc})
        self.guardar()
        self.actualizar_lista()

        self.input_desc.text = ""

    # -----------------------------------
    # EDITAR
    # -----------------------------------
    def editar_item(self, index):
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.textinput import TextInput
        from kivy.uix.button import Button
        from kivy.uix.popup import Popup

        item = self.items[index]

        layout = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        inp = TextInput(text=item["desc"])

        btn = Button(text="Guardar", size_hint_y=None, height=dp(50))

        def guardar(_):
            item["desc"] = inp.text.strip()
            self.guardar()
            self.actualizar_lista()
            popup.dismiss()

        btn.bind(on_press=guardar)

        layout.add_widget(inp)
        layout.add_widget(btn)

        popup = Popup(title="Editar", content=layout, size_hint=(0.9, 0.5))
        popup.open()

    # -----------------------------------
    # ELIMINAR
    # -----------------------------------
    def eliminar_item(self, index):
        del self.items[index]
        self.guardar()
        self.actualizar_lista()

    # -----------------------------------
    # FILTRO
    # -----------------------------------
    def aplicar_filtro(self, texto):
        self.filtro_texto = texto.lower().strip()
        self.actualizar_lista()

    # -----------------------------------
    # LISTA
    # -----------------------------------
    def actualizar_lista(self):
        data = []
        filtro = self.filtro_texto

        for i, item in enumerate(self.items):
            desc = item["desc"]

            if filtro:
                patron = filtro.replace(",", "*")
                patron = f"{patron}"

                if not fnmatch.fnmatch(desc.lower(), patron):
                    continue

            data.append({
                "texto": desc,
                "index": i
            })

        self.rv.data = data


if _name_ == "_main_":
    InventarioApp().run()