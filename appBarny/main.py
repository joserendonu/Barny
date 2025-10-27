from kivy.app import App
from kivy.uix.label import Label
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.clock import mainthread

import os
import json
import shutil
import uuid
from datetime import datetime

try:
    from plyer import filechooser
except Exception:
    filechooser = None

DATA_FILE = "products.json"
IMAGES_DIR = "images"

class ProductForm(BoxLayout):
    def __init__(self, app, product=None, **kwargs):
        super().__init__(orientation="vertical", spacing=8, padding=12, **kwargs)
        self.app = app
        self.product = product  # None = nuevo, o dict = editar

        self.add_widget(Label(text="Nombre"))
        self.name_input = TextInput(multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.name_input)

        self.add_widget(Label(text="Descripción"))
        self.desc_input = TextInput(size_hint_y=None, height=100)
        self.add_widget(self.desc_input)

        self.add_widget(Label(text="Foto"))
        self.image_preview = Image(size_hint_y=None, height=200, allow_stretch=True, keep_ratio=True)
        self.add_widget(self.image_preview)

        btn_row = BoxLayout(size_hint_y=None, height=40, spacing=8)
        self.choose_btn = Button(text="Elegir foto")
        self.choose_btn.bind(on_release=self.choose_file)
        btn_row.add_widget(self.choose_btn)

        self.save_btn = Button(text="Guardar")
        self.save_btn.bind(on_release=self.on_save)
        btn_row.add_widget(self.save_btn)

        self.cancel_btn = Button(text="Cancelar")
        self.cancel_btn.bind(on_release=self.on_cancel)
        btn_row.add_widget(self.cancel_btn)

        self.add_widget(btn_row)

        self.status = Label(text="", size_hint_y=None, height=30)
        self.add_widget(self.status)

        self.chosen_path = None

        if product:
            # cargar datos para editar
            self.name_input.text = product.get("name", "")
            self.desc_input.text = product.get("description", "")
            img = product.get("image", "")
            if img and os.path.exists(img):
                self.chosen_path = img
                self.image_preview.source = img

    def choose_file(self, *args):
        if filechooser:
            filechooser.open_file(on_selection=self._on_file_selected)
        else:
            # fallback: intentar abrir diálogo nativo no disponible -> mostrar mensaje
            self.status.text = "Selector de archivos no disponible."

    @mainthread
    def _on_file_selected(self, selection):
        if not selection:
            self.status.text = "No se seleccionó archivo."
            return
        path = selection[0]
        if os.path.isfile(path):
            self.chosen_path = path
            self.image_preview.source = path
            self.image_preview.reload()
            self.status.text = os.path.basename(path)
        else:
            self.status.text = "Ruta inválida."

    def on_save(self, *args):
        name = self.name_input.text.strip()
        desc = self.desc_input.text.strip()
        if not name:
            self.status.text = "Ingrese un nombre."
            return

        data_dir = self.app.user_data_dir
        images_dir = os.path.join(data_dir, IMAGES_DIR)
        os.makedirs(images_dir, exist_ok=True)

        # Si se seleccionó una imagen (nuevo o reemplazo), copiarla a folder de la app
        image_dest = None
        if self.chosen_path and os.path.isfile(self.chosen_path):
            ext = os.path.splitext(self.chosen_path)[1]
            unique_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex}{ext}"
            image_dest = os.path.join(images_dir, unique_name)
            try:
                shutil.copy(self.chosen_path, image_dest)
            except Exception as e:
                self.status.text = f"Error copiando imagen: {e}"
                return
        elif self.product:
            # si estamos editando y no se eligió nueva imagen, mantener la anterior
            image_dest = self.product.get("image")

        product = {
            "id": self.product.get("id") if self.product else uuid.uuid4().hex,
            "name": name,
            "description": desc,
            "image": image_dest,
            "updated_at": datetime.utcnow().isoformat() + "Z"
        }

        # guardar via App
        self.app.save_or_update_product(product)
        self.status.text = "Guardado."
        # volver a lista
        self.app.show_list()

    def on_cancel(self, *args):
        self.app.show_list()

class ProductList(Screen):
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.layout = BoxLayout(orientation="vertical", spacing=8, padding=8)
        header = BoxLayout(size_hint_y=None, height=40)
        header.add_widget(Label(text="Productos", bold=True))
        add_btn = Button(text="Nuevo", size_hint_x=None, width=100)
        add_btn.bind(on_release=lambda *a: self.app.show_form())
        header.add_widget(add_btn)
        self.layout.add_widget(header)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

    def refresh(self):
        self.grid.clear_widgets()
        products = self.app.load_products()
        if not products:
            self.grid.add_widget(Label(text="No hay productos guardados.", size_hint_y=None, height=40))
            return
        for p in products:
            item = BoxLayout(size_hint_y=None, height=80, spacing=8)
            thumb = Image(size_hint_x=None, width=80, allow_stretch=True, keep_ratio=True)
            img = p.get("image")
            if img and os.path.exists(img):
                thumb.source = img
            else:
                thumb.source = ""
            item.add_widget(thumb)

            info = BoxLayout(orientation="vertical")
            info.add_widget(Label(text=p.get("name", ""), size_hint_y=None, height=30))
            info.add_widget(Label(text=(p.get("description", "")[:80] + ("..." if len(p.get("description",""))>80 else ""))))
            item.add_widget(info)

            btns = BoxLayout(orientation="vertical", size_hint_x=None, width=120)
            view_btn = Button(text="Ver", size_hint_y=None, height=36)
            view_btn.bind(on_release=lambda inst, prod=p: self.app.show_detail(prod))
            edit_btn = Button(text="Editar", size_hint_y=None, height=36)
            edit_btn.bind(on_release=lambda inst, prod=p: self.app.show_form(prod))
            del_btn = Button(text="Eliminar", size_hint_y=None, height=36)
            del_btn.bind(on_release=lambda inst, prod=p: self.confirm_delete(prod))
            btns.add_widget(view_btn)
            btns.add_widget(edit_btn)
            btns.add_widget(del_btn)
            item.add_widget(btns)

            self.grid.add_widget(item)

    def confirm_delete(self, product):
        content = BoxLayout(orientation="vertical", spacing=8, padding=8)
        content.add_widget(Label(text=f"Eliminar '{product.get('name')}'?"))
        btns = BoxLayout(size_hint_y=None, height=40, spacing=8)
        yes = Button(text="Eliminar")
        no = Button(text="Cancelar")
        btns.add_widget(yes); btns.add_widget(no)
        content.add_widget(btns)
        popup = Popup(title="Confirmar", content=content, size_hint=(.8, .4))
        yes.bind(on_release=lambda *a: (self.app.delete_product(product), popup.dismiss()))
        no.bind(on_release=popup.dismiss)
        popup.open()

class ProductDetail(Popup):
    def __init__(self, product, app, **kwargs):
        super().__init__(title=product.get("name", "Detalle"), size_hint=(.9, .9), **kwargs)
        self.app = app
        box = BoxLayout(orientation="vertical", spacing=8, padding=8)
        img = Image(size_hint_y=None, height=300, allow_stretch=True, keep_ratio=True)
        if product.get("image") and os.path.exists(product.get("image")):
            img.source = product.get("image")
        box.add_widget(img)
        box.add_widget(Label(text=product.get("description", "")))
        close = Button(text="Cerrar", size_hint_y=None, height=40)
        close.bind(on_release=self.dismiss)
        box.add_widget(close)
        self.content = box

class MainApp(App):
    def build(self):
        try:
            Window.size = (420, 700)
        except Exception:
            pass
        self.sm = ScreenManager()
        self.list_screen = ProductList(self, name="list")
        self.sm.add_widget(self.list_screen)
        # form screen will be created on demand
        return self.sm

    def on_start(self):
        # cargar/crear carpeta de datos
        os.makedirs(self.user_data_dir, exist_ok=True)
        imgdir = os.path.join(self.user_data_dir, IMAGES_DIR)
        os.makedirs(imgdir, exist_ok=True)
        # mostrar lista
        self.show_list()

    def data_path(self):
        return os.path.join(self.user_data_dir, DATA_FILE)

    def load_products(self):
        path = self.data_path()
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def save_products(self, products):
        path = self.data_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(products, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error guardando productos:", e)

    def save_or_update_product(self, product):
        products = self.load_products()
        # buscar por id
        for i, p in enumerate(products):
            if p.get("id") == product.get("id"):
                products[i] = product
                break
        else:
            products.append(product)
        self.save_products(products)
        self.show_list()

    def delete_product(self, product):
        products = self.load_products()
        products = [p for p in products if p.get("id") != product.get("id")]
        self.save_products(products)
        # opcional: borrar imagen asociada (solo si existe y está dentro de folder images)
        img = product.get("image")
        if img and os.path.exists(img) and os.path.commonpath([img, os.path.join(self.user_data_dir, IMAGES_DIR)]) == os.path.join(self.user_data_dir, IMAGES_DIR):
            try:
                os.remove(img)
            except Exception:
                pass
        self.show_list()

    def show_list(self):
        # asegurar que la pantalla exista y refrescar
        if not self.sm.has_screen("list"):
            self.sm.add_widget(self.list_screen)
        self.sm.current = "list"
        self.list_screen.refresh()

    def show_form(self, product=None):
        # crear una pantalla temporal con el formulario
        form_screen_name = "form"
        if self.sm.has_screen(form_screen_name):
            self.sm.remove_widget(self.sm.get_screen(form_screen_name))
        form = ProductForm(self, product=product)
        screen = Screen(name=form_screen_name)
        screen.add_widget(form)
        self.sm.add_widget(screen)
        self.sm.current = form_screen_name

    def show_detail(self, product):
        ProductDetail(product, self).open()

if __name__ == "__main__":
    MainApp().run()
