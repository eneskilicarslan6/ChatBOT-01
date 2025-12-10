# -*- coding: utf-8 -*-
##--------------------------------------------------------------------------------------------------------------------##
import customtkinter as ctk
from tkinter import messagebox
import speech_recognition as sr
import threading
from gtts import gTTS
import pygame
from groq import Groq
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import datetime
import dotenv

dotenv.load_dotenv()

LLAMA_API_URL = os.getenv("LLAMA_API_URL")
LLAMA_API_KEY = os.getenv("LLAMA_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

pygame.mixer.init()


def llama_sor(message):
    try:
        client = Groq(api_key=GROQ_API_KEY)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": message}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Hata: {e}"


def metni_seslendir(metin):
    tts = gTTS(text=metin, lang='tr')
    tts.save("response.mp3")
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()


def konusmayi_dinle():
    tanıyıcı = sr.Recognizer()
    with sr.Microphone() as kaynak:
        try:
            tanıyıcı.adjust_for_ambient_noise(kaynak)
            ses = tanıyıcı.listen(kaynak)
            return tanıyıcı.recognize_google(ses, language="tr-TR")
        except sr.UnknownValueError:
            return "Üzgünüm, anlayamadım."
        except sr.RequestError as e:
            return f"Hata: {e}"


def sohbeti_yonet():
    kullanici_girdisi = girdi_kutusu.get("1.0", "end").strip()
    if not kullanici_girdisi:
        messagebox.showwarning("Uyarı", "Lütfen bir mesaj girin.")
        return

    sohbeti_goster(kullanici_girdisi, "kullanici")
    girdi_kutusu.delete("1.0", "end")

    if kullanici_girdisi in ["bye", "görüşürüz", "bay bay", "bye bye", "see you", "see u", "allaha emanet ol", "Kaçıyorum ben", "kapat"]:
        sohbeti_goster("AI: Görüşmek üzere! 👋", "ai")
        app.after(2000, app.quit)
        return


    def cevap_getir():
        ai_cevap = llama_sor(kullanici_girdisi)
        sohbeti_goster(ai_cevap, "ai")

        if cevap_modu.get() == "Sesli Çıkış":
            metni_seslendir(ai_cevap)

    threading.Thread(target=cevap_getir).start()


def enter_tusu_event(event):
    sohbeti_yonet()


def sohbeti_goster(sohbet_metin, role):
    if role == "kullanici":
        sohbet_ekrani.insert("end", f"Sen: {sohbet_metin}\n", "kullanici")
    elif role == "ai":
        sohbet_ekrani.insert("end", f"AI: {sohbet_metin}\n", "ai")
    sohbet_ekrani.see("end")


def sesli_girdi():
    def ses_isle():
        sohbeti_goster("Dinleniyor...", "bilgi")
        kullanici_girdisi = konusmayi_dinle().lower()
        sohbeti_goster(f"Sen (Ses): {kullanici_girdisi}", "kullanici")

        if kullanici_girdisi in ["bye", "görüşürüz", "bay bay", "bye bye", "see you", "see u", "allaha emanet ol", "kaçıyorum ben", "kapat"]:
            sohbeti_goster("AI: Görüşmek üzere! 👋", "ai")
            app.after(2000, app.quit)
            return

        ai_cevap = llama_sor(kullanici_girdisi)
        sohbeti_goster(ai_cevap, "ai")

        if cevap_modu.get() == "Sesli Çıkış":
            metni_seslendir(ai_cevap)

    threading.Thread(target=ses_isle).start()


def sohbeti_kaydet_pdf():
    sohbet_text = sohbet_ekrani.get("1.0", "end").strip()
    if not sohbet_text:
        messagebox.showwarning("Uyarı", "Sohbet geçmişi boş!")
        return

    sohbet_klasoru = "sohbet_gecmisi"

    if not os.path.exists(sohbet_klasoru):
        os.makedirs(sohbet_klasoru)


    zaman_damgasi = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pdf_dosya = os.path.join(sohbet_klasoru, f"sohbet_gecmisi_{zaman_damgasi}.pdf")


    pdfmetrics.registerFont(TTFont('DejaVu', '../ChatBOT-61/build/ChatBOT/fonts/dejavu-fonts-ttf-2.37/ttf/DejaVuSans.ttf'))

    c = canvas.Canvas(pdf_dosya, pagesize=letter)
    c.setFont("DejaVu", 10)
    y_position = 750

    for line in sohbet_text.split("\n"):
        c.drawString(30, y_position, line)
        y_position -= 12
        if y_position < 40:
            c.showPage()
            c.setFont("DejaVu", 10)
            y_position = 750

    c.save()
    messagebox.showinfo("Bilgi", f"Sohbet geçmişi {pdf_dosya} olarak kaydedildi.")


def temizle_sohbet():
    sohbet_ekrani.delete("1.0", "end")

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.attributes("-alpha", 1)
app.configure(bg="SystemTransparent")
app.title("ChatBOT-61")
app.geometry("1024x768")

sohbet_ekrani = ctk.CTkTextbox(app, height=400, wrap="word", corner_radius=15, border_width=2, border_color="gray")
sohbet_ekrani.pack(padx=20, pady=20, fill="both", expand=True)
sohbet_ekrani.tag_config("kullanici", foreground="Orange")
sohbet_ekrani.tag_config("ai", foreground="darkgray")
sohbet_ekrani.tag_config("bilgi", foreground="gray")

girdi_kutusu = ctk.CTkTextbox(app, height=50, corner_radius=15, border_width=2, border_color="gray")
girdi_kutusu.pack(padx=20, pady=(0, 10), fill="x")

dugme_cerceve = ctk.CTkFrame(app, corner_radius=15)
dugme_cerceve.pack(pady=20, fill="x", padx=20)

gonder_dugme = ctk.CTkButton(dugme_cerceve, text="Gönder", command=sohbeti_yonet, corner_radius=15, height=45, fg_color="darkblue", hover_color="darkblue")
gonder_dugme.pack(side="left", padx=10)

sesli_dugme = ctk.CTkButton(dugme_cerceve, text="🎙 Sesli Giriş", command=sesli_girdi, corner_radius=15, height=45, fg_color="darkblue", hover_color="darkblue")
sesli_dugme.pack(side="left", padx=10)

cevap_modu = ctk.StringVar(value="Yazılı Çıkış")
cevap_modu_menu = ctk.CTkOptionMenu(dugme_cerceve, variable=cevap_modu, values=["Yazılı Çıkış", "Sesli Çıkış"], corner_radius=15)
cevap_modu_menu.pack(side="right", padx=10)

girdi_kutusu.bind("<Return>", enter_tusu_event)
sohbet_ekrani.bind("<Key>", lambda e: "break")

tema_modu = ctk.StringVar(value="🌑")
tema_menu = ctk.CTkOptionMenu(dugme_cerceve, variable=tema_modu, values=["🌑", "☀️"], corner_radius=15, command=lambda val: ctk.set_appearance_mode("dark" if val == "🌑" else "light"))
tema_menu.pack(side="right", padx=10)


kaydet_dugme = ctk.CTkButton(dugme_cerceve, text="💾 Kaydet", command=sohbeti_kaydet_pdf, corner_radius=15, height=45, fg_color="darkblue", hover_color="darkblue")
kaydet_dugme.pack(side="left", padx=10)

temizle_dugme = ctk.CTkButton(dugme_cerceve, text="🗑 Temizle", command=temizle_sohbet, corner_radius=15, height=45, fg_color="darkblue", hover_color="darkblue")
temizle_dugme.pack(side="left", padx=10)

app.mainloop()
##-------------------------This command is maded by CAYCLE  ~~  Finished on 15.05.2025 ~ 12.47------------------------##