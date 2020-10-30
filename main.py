import datetime
import json
import os
import plyer
import qrcode
import zlib
from collections import OrderedDict
from kivy import platform
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.checkbox import CheckBox
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from mimetypes import guess_type
from PyPDF2 import PdfFileReader, PdfFileWriter

if platform == 'android':
    from jnius import autoclass, cast
    ANDROID = True
else:
    def autoclass(*_):
        raise os.error("Can work only on Android")
    ANDROID = False

CONFIG = {
    "PRENOM": "",
    "NOM": "",
    "NAISSANCE": "",
    "VILLEN": "",
    "ADRESSE": "",
    "CPPPP": "",
    "VILLE": "",
    "DELTA": 0,
    "AUTO_OPEN": ""
}


class MainApp(App):
    def open_file(self, x):
        PA = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')

        x = x if isinstance(x, str) else x.text

        uri = 'content:///storage/emulated/0/Download/attestation_{}.pdf'.format(x)

        intent = Intent()
        intent.setAction(Intent.ACTION_VIEW)
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

        intent.setDataAndType(Uri.parse(uri), guess_type(uri)[0])

        currentActivity = cast('android.app.Activity', PA.mActivity)
        currentActivity.startActivity(intent)

    def make_pdf(self, n):
        n = n if isinstance(n, str) else n.text
        filename = '/storage/emulated/0/Download/attestation_{}.pdf'.format(n) if ANDROID else './attestation_{}.pdf'.format(n)
        try:
            with open("config.json", "r") as f:
                config = json.loads(f.read(), object_pairs_hook=OrderedDict)
        except:
            config = CONFIG

        chaine = "Cree le: AUJOURDUI a HHhMM; Nom: NOM; Prenom: PRENOM; Naissance: NAISSANCE a VILLEN; Adresse:ADRESSE CPPPP VILLE; Sortie: AUJOURDUI a HHhMM; Motifs: sport"

        hour = str(datetime.datetime.now().hour)
        mins = datetime.datetime.now().minute - config["DELTA"]
        if mins <= 10:
            mins = "00"
        else:
            mins = str(mins)

        config["AUJOURDUI"] = datetime.date.today().strftime("%d/%m/%Y")
        config["(HH)"] = "(" + hour + ")"
        config["HHhMM"] = hour + 'h' + mins
        config["HHh"] = hour + 'h'
        config["(MM)"] = "(" + mins + ")"
        config["hMM"] = "h" + mins
        config["HH\\072MM"] = "{}\\072{}".format(hour, mins)

        pdf_reader = PdfFileReader('final_{}.pdf'.format(n))
        page1 = pdf_reader.getPage(0)
        page1.compressContentStreams()

        content = page1.get('/Contents').getObject()
        c = content.getData()

        for k, v in config.items():
            if k in ["DELTA", "AUTO_OPEN"]:
                continue
            c = c.replace(bytes(k, "utf-8"), bytes(v, "utf-8").replace(b"/", b"\\057"))
            chaine = chaine.replace(k, v)

        content._data = zlib.compress(c)

        img = qrcode.make(chaine)
        img._img = img.resize((250, 250))
        img.save('tmp.pdf', format="pdf")

        img_reader = PdfFileReader('tmp.pdf')
        img_page = img_reader.getPage(0)

        resources = page1.get('/Resources').getObject()
        name = list(x for x in resources.get('/XObject').keys() if 'mage' in x or '/x7' == x)[0]
        resources.get('/XObject')[name] = img_page.get('/Resources').get('/XObject').get('/image')

        page2 = pdf_reader.getPage(1)
        resources = page2.get('/Resources').getObject()
        name = list(x for x in resources.get('/XObject').keys() if 'mage' in x or '/x7' == x)[0]
        resources.get('/XObject')[name] = img_page.get('/Resources').get('/XObject').get('/image')
        pdf_writer = PdfFileWriter()
        pdf_writer.addPage(page1)
        pdf_writer.addPage(page2)
        with open(filename, 'wb+') as f:
            pdf_writer.write(f)
        plyer.notification.notify(title='Attestation {}'.format(n), message=filename)
        if config["AUTO_OPEN"]:
            self.open_file(n)

    def generate_config(self):
        def update(conf):
            def real_update(_, value):
                if conf == "DELTA":
                    try:
                        value = int(value)
                    except ValueError:
                        value = -1
                CONFIG[conf] = value
            return real_update

        def toggle_auto(_, active):
            CONFIG["AUTO_OPEN"] = True if active else ""

        def save(*_):
            content = json.dumps(CONFIG)
            with open("config.json", "w+") as f:
                f.write(content)
            self.stop()

        layout = BoxLayout(orientation='vertical')
        for x in CONFIG:
            if x == "AUTO_OPEN":
                continue
            textinput = TextInput(
                text=(
                    x
                    .replace("VILLEN", "VILLE DE NAISSANCE")
                    .replace("CPPPP", "Code Postal")
                ),
                multiline=False,
            )
            textinput.bind(text=update(x))
            layout.add_widget(textinput)

        auto_open = BoxLayout(orientation="horizontal")
        auto_open.add_widget(
            Label(text="Open pdf automatically")
        )
        open_checkbox = CheckBox()
        open_checkbox.bind(active=toggle_auto)
        auto_open.add_widget(
            open_checkbox
        )

        layout.add_widget(auto_open)
        layout.add_widget(Button(text="sport", on_press=self.make_pdf))
        layout.add_widget(Button(text="courses", on_press=self.make_pdf))
        layout.add_widget(Button(text="feu", on_press=self.make_pdf))
        layout.add_widget(Button(text="""
        Never get back to this screen and generate both automatically when I open the app
        (Will use current settings... Advice: Double-check)
        """, on_press=save))

        return layout

    def on_pause(self):
        return True

    def build(self):
        if ANDROID:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.requestPermissions([
                "android.permission.READ_EXTERNAL_STORAGE",
                "android.permission.WRITE_EXTERNAL_STORAGE"
            ], 0)
        try:
            os.stat("config.json")
            self.make_pdf('sport')
            self.make_pdf('courses')
            self.make_pdf('feu')
            layout = BoxLayout(orientation='vertical')
            layout.add_widget(Button(text='sport', on_press=self.open_file))
            layout.add_widget(Button(text='courses', on_press=self.open_file))
            layout.add_widget(Button(text='feu', on_press=self.open_file))
            return layout
        except FileNotFoundError:
            return self.generate_config()


if __name__ == '__main__':
    MainApp().run()
