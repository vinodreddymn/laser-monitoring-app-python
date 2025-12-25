# gui/windows/qr_settings_modal.py
import customtkinter as ctk
from backend.settings_dao import save_qr_settings, get_qr_settings

import customtkinter as ctk
from backend.settings_dao import save_qr_settings, get_qr_settings


class QRSettingsModal(ctk.CTkToplevel):
    def __init__(self, parent, model, callback):
        super().__init__(parent)

        self.model = model
        self.callback = callback

        self.title(f"Activate Model: {model['name']}")
        self.geometry("500x420")
        self.resizable(False, False)
        self.grab_set()

        settings = get_qr_settings()

        self.prefix = ctk.StringVar(
            value=settings.get("qr_text_prefix", model["name"])
        )
        self.counter = ctk.IntVar(
            value=settings.get("qr_start_counter", 1)
        )

        # NEW: model_type comes from model
        self.model_type = model.get("model_type", "RHD")

        self.setup_ui()

    # ---------------------------------------------------
    def setup_ui(self):
        ctk.CTkLabel(
            self,
            text=f"Activate Model: {self.model['name']} ({self.model_type})",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        frame = ctk.CTkFrame(self)
        frame.pack(padx=40, pady=20, fill="both", expand=True)

        ctk.CTkLabel(frame, text="QR Text Prefix").pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkEntry(frame, textvariable=self.prefix).pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame, text="Starting Counter").pack(anchor="w", padx=20, pady=(10, 5))
        ctk.CTkEntry(frame, textvariable=self.counter).pack(fill="x", padx=20, pady=5)

        preview = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=18, family="Courier", weight="bold")
        )
        preview.pack(pady=20)

        def update_preview(*args):
            p = self.prefix.get().strip() or "Text"
            c = str(self.counter.get()).zfill(5)
            preview.configure(
                text=f"Next QR → {p}.{c}"
            )

        self.prefix.trace_add("write", update_preview)
        self.counter.trace_add("write", update_preview)
        update_preview()

        btns = ctk.CTkFrame(self)
        btns.pack(pady=20)

        ctk.CTkButton(
            btns,
            text="Cancel",
            fg_color="gray",
            command=self.destroy
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btns,
            text="Activate & Save",
            fg_color="#10b981",
            command=self.activate
        ).pack(side="left", padx=10)

    # ---------------------------------------------------
    def activate(self):
        save_qr_settings(
            prefix=self.prefix.get().strip(),
            counter=self.counter.get(),
            model_type=self.model_type
        )

        self.callback()
        self.destroy()
