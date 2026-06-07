import cv2
import tkinter as tk
from tkinter import Label, Button, Frame, StringVar
from PIL import Image, ImageTk, ImageDraw
import time
import os
import qrcode
import imageio
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor

# Google Drive API Modules
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

class LifeFourCutsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Summer Party Four Cuts (Master Kiosk Framework)")
        
        # Maximize the window for full kiosk immersion
        self.root.attributes('-fullscreen', True)
        self.root.bind("<Escape>", lambda e: self.on_close())
        self.root.configure(bg='white')

        # System States & Empirical Data Buffers
        self.is_running = True
        self.state = "IDLE"
        self.captured_images = []
        self.captured_gifs = []
        self.frame_buffer = deque(maxlen=60)
        
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.gif_paths = [None] * 4

        # Session & Network State Variables
        self.session_dir = ""
        self.cloud_folder_id = None
        self.is_cloud_ready = False

        self.selected_theme = StringVar(value="")
        self.thumb_frames = {}

        # Container-based UI Isolation
        self.ui_container = Frame(self.root, bg='white')
        self.ui_container.pack(expand=True, fill="both")
        
        self.video_label = Label(self.ui_container, bg='black')
        self.info_label = Label(self.ui_container, text="Initializing OS and I/O...", font=("Helvetica", 24, "bold"), bg='white')

        print("[*] Initializing Google Drive API OAuth Sequence...")
        self.gdrive_service = self.authenticate_gdrive()
        print("[*] Google Drive API Authorized.")

        self.cap = cv2.VideoCapture(0)
        self.update_frame()
        self.show_start_screen()

    def authenticate_gdrive(self):
        SCOPES = ['https://www.googleapis.com/auth/drive.file']
        creds = None
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        return build('drive', 'v3', credentials=creds)

    def clear_container(self):
        """Purges active UI widgets to prevent memory leaks during state transitions."""
        for widget in self.ui_container.winfo_children():
            widget.pack_forget()

    # ==========================================
    # State Machine UI Rendering
    # ==========================================

    def show_start_screen(self):
        self.state = "IDLE"
        self.clear_container()

        title = Label(self.ui_container, text="Summer Party MPI CBS\nFour Cuts", font=("Helvetica", 42, "bold"), fg="#FF5722", bg='white')
        title.pack(pady=(250, 50))
        
        subtitle = Label(self.ui_container, text="Capture your colorful memories", font=("Helvetica", 20), bg='white')
        subtitle.pack(pady=20)

        start_btn = Button(self.ui_container, text="START", font=("Helvetica", 28, "bold"), bg="#4CAF50", fg="white", 
                           command=self.show_config_screen, width=15, height=2, cursor="hand2")
        start_btn.pack(pady=80)

    def show_config_screen(self):
        self.state = "CONFIG"
        self.clear_container()
        self.selected_theme.set("")
        self.thumb_frames.clear()

        Label(self.ui_container, text="Select Frame Matrix", font=("Helvetica", 32, "bold"), bg='white').pack(pady=(60, 20))

        def on_select():
            selected = self.selected_theme.get()
            if selected:
                next_btn.config(state="normal", bg="#2196F3", fg="white")
                # Highlight active selection
                for mode, border_frame in self.thumb_frames.items():
                    if mode == selected:
                        border_frame.config(bg="#2196F3")
                    else:
                        border_frame.config(bg="white")

        # Horizontal Scroll Architecture
        scroll_wrapper = Frame(self.ui_container, bg='white')
        scroll_wrapper.pack(pady=20, fill="x", padx=100)

        
        canvas = tk.Canvas(scroll_wrapper, bg='white', highlightthickness=0, height=450)
        scrollbar = tk.Scrollbar(scroll_wrapper, orient="horizontal", command=canvas.xview)
        scrollable_frame = Frame(canvas, bg='white')

        scrollable_frame.bind(
            "<Configure>",
           # lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure() # xscrollcommand=scrollbar.set)

        canvas.pack(side="top", fill="x", expand=True)
        # scrollbar.pack(side="bottom", fill="x")

        # Mouse wheel binding for horizontal scroll
        # def _on_mousewheel(event):
        #     canvas.xview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>",) # _on_mousewheel)

        themes = [
            ("Modern", "connectivity"),
            ("S-A Axis", "sa_axis"),
            ("Dual Origin", "brainspace"),
            ("Blue Sky", "dual_origin"),
            ("Uni-to-Trans", "func_seg"),
            ("Myelination", "greyscale_net"),
        ]

        self.thumbnail_refs = []

        for text, mode in themes:
            border_frame = Frame(scrollable_frame, bg='white', padx=8, pady=8)
            border_frame.pack(side="left", padx=36)
            self.thumb_frames[mode] = border_frame

            opt_frame = Frame(border_frame, bg='white')
            opt_frame.pack()

            thumb_img = self.generate_background_canvas(120, 360, mode)
            draw = ImageDraw.Draw(thumb_img)
            box_outline = "#E0E0E0" if mode == "white" else "#424242"
            
            for i in range(4):
                y0 = 18 + i * 84
                draw.rectangle([12, y0, 108, y0+72], outline=box_outline, fill="#F5F5F5", width=2)

            thumb_tk = ImageTk.PhotoImage(thumb_img)
            self.thumbnail_refs.append(thumb_tk)

            img_lbl = Label(opt_frame, image=thumb_tk, bg='white', cursor="hand2")
            img_lbl.pack(side="top", pady=10)

            # Native selection binding mapped directly to the thumbnail tensor
            img_lbl.bind("<Button-1>", lambda e, m=mode: [self.selected_theme.set(m), on_select()])

            rb = tk.Radiobutton(opt_frame, text=text, variable=self.selected_theme, value=mode, 
                                font=("Helvetica", 14, "bold"), bg='white', command=on_select, justify="center")
            rb.pack(side="top", pady=5)

        def go_next():
            canvas.unbind_all("<MouseWheel>")
            self.show_camera_screen()

        next_btn = Button(self.ui_container, text="Initialize Camera", font=("Helvetica", 24, "bold"), state="disabled",
                          command=go_next, width=20, height=2, cursor="hand2")
        next_btn.pack(pady=40)

    def show_camera_screen(self):
        self.state = "READY"
        self.clear_container()

        header_label = Label(self.ui_container, text="Get Ready for the Shoot!", font=("Helvetica", 32, "bold"), fg="#FF5722", bg='white')
        header_label.pack(pady=(40, 20))

        self.video_label.pack(pady=10)

        self.info_label = Label(self.ui_container, text="Press Start When Ready", font=("Helvetica", 28, "bold"), fg="#1976D2", bg='white')
        self.info_label.pack(pady=20)

        self.start_capture_btn = Button(self.ui_container, text="START", font=("Helvetica", 24, "bold"), bg="#E91E63", fg="white",
                                        command=self.trigger_capture_sequence, width=20, height=2, cursor="hand2")
        self.start_capture_btn.pack(pady=30)

    # ==========================================
    # Empirical Data Acquisition & Processing
    # ==========================================

    def update_ui_text(self, text):
        self.root.after(0, lambda: self.info_label.config(text=text))

    def trigger_flash(self):
        """Synthesizes a 100ms optical saturation effect over the primary tensor."""
        flash = Frame(self.video_label, bg="white")
        flash.place(relwidth=1, relheight=1)
        self.root.after(100, flash.destroy)

    def update_frame(self):
        if not self.is_running:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            cv2_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            if self.state == "COUNTDOWN":
                self.frame_buffer.append(cv2_rgb)

            if self.state in ["READY", "COUNTDOWN"]:
                img = Image.fromarray(cv2_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)

        self.root.after(30, self.update_frame)

    def trigger_capture_sequence(self):
        self.start_capture_btn.pack_forget()
        self.state = "COUNTDOWN"
        self.captured_images.clear()
        self.gif_paths = [None] * 4
        self.cloud_folder_id = None
        self.is_cloud_ready = False

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.session_dir = os.path.join("output", timestamp)
        os.makedirs(self.session_dir, exist_ok=True)
        
        threading.Thread(target=self.prepare_cloud_folder_worker, daemon=True).start()
        threading.Thread(target=self.capture_sequence, daemon=True).start()

    def save_gif_worker(self, frames, index):
        downsampled_frames = []
        for frame in frames:
            resized = cv2.resize(frame, (320, 240), interpolation=cv2.INTER_LINEAR)
            downsampled_frames.append(resized)
            
        gif_path = os.path.join(self.session_dir, f"temp_gif_{index}.gif")
        imageio.mimsave(gif_path, downsampled_frames, fps=15, loop=0)
        self.gif_paths[index] = gif_path

    def capture_sequence(self):
        for i in range(4):
            for count in range(5, 0, -1):
                self.update_ui_text(f"⏳ Time Remaining: {count}s  (Shot {i+1}/4)")
                time.sleep(1)
            
            self.root.after(0, self.trigger_flash)
            self.update_ui_text("📸 FLASH!")
            
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                img_tensor = Image.fromarray(rgb_frame)
                self.captured_images.append(img_tensor)
                
                photo_path = os.path.join(self.session_dir, f"photo_{i}.jpg")
                img_tensor.save(photo_path)
                
                buffer_snapshot = list(self.frame_buffer)
                self.executor.submit(self.save_gif_worker, buffer_snapshot, i)
                self.frame_buffer.clear()
            
            time.sleep(1)

        self.state = "PROCESSING"
        self.update_ui_text("PROCESSING & GENERATING QR CODE")
        
        self.executor.shutdown(wait=True)
        self.captured_gifs = [p for p in self.gif_paths if p is not None]
        self.executor = ThreadPoolExecutor(max_workers=4) 
        
        self.process_results()

    def generate_background_canvas(self, width, height, theme):
        """
        Maps aesthetic themes to linear color gradients.
        """
        base = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(base)

        # Define endpoints for linear interpolation: (R, G, B)
        if theme == "sa_axis":
            c0, c1 = (75, 0, 130), (255, 255, 0) # Indigo to Yellow
        elif theme == "brainspace":
            c0, c1 = (0, 128, 128), (255, 140, 0) # Teal to Orange
        elif theme == "dual_origin":
            c0, c1 = (26, 35, 126), (129, 212, 250) # Deep Blue to Light Blue
        elif theme == "greyscale_net":
            c0, c1 = (50, 50, 50), (220, 220, 220)
        elif theme == "func_seg":
            c0, c1 = (255, 0, 85), (0, 255, 170) # Neon Pink to Cyan
        else:
            c0, c1 = (0, 0, 0), (0, 0, 0) # Dark

        # Linear interpolation calculation
        for y in range(height):
            # Calculate interpolation factor alpha in range [0, 1]
            alpha = y / height
        
            # Linearly interpolate each channel
            r = int(c0[0] + alpha * (c1[0] - c0[0]))
            g = int(c0[1] + alpha * (c1[1] - c0[1]))
            b = int(c0[2] + alpha * (c1[2] - c0[2]))
        
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        return base

    def process_results(self):
        bg_width, bg_height = 600, 1800
        theme = self.selected_theme.get()
        result_img = self.generate_background_canvas(bg_width, bg_height, theme)
        
        y_offset = 50
        for img in self.captured_images:
            img_resized = img.resize((500, 350))
            result_img.paste(img_resized, (50, y_offset))
            y_offset += 400
            
        final_image_path = os.path.join(self.session_dir, "final_cut.jpg")
        result_img.save(final_image_path)

        qr_path = os.path.join(self.session_dir, "qr_code.png")
        
        timeout_counter = 0
        while not self.is_cloud_ready and timeout_counter < 40:
            self.update_ui_text(f"Syncing Network I/O... ({20 - timeout_counter//2}s)")
            time.sleep(0.5)
            timeout_counter += 1

        is_success = self.is_cloud_ready and os.path.exists(qr_path)

        if is_success:
            threading.Thread(target=self.upload_files_worker, args=(final_image_path, self.captured_gifs), daemon=True).start()

        self.root.after(0, lambda: self.show_final_screen(final_image_path, qr_path, is_success))

    # ==========================================
    # Decoupled Network I/O (Google Drive API)
    # ==========================================

    def prepare_cloud_folder_worker(self):
        try:
            parent_folder_name = 'summer_party'
            query = f"name='{parent_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            
            results = self.gdrive_service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])

            if not items:
                parent_metadata = {
                    'name': parent_folder_name,
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                parent_folder = self.gdrive_service.files().create(body=parent_metadata, fields='id').execute()
                parent_id = parent_folder.get('id')
            else:
                parent_id = items[0].get('id')

            folder_name = os.path.basename(self.session_dir)
            folder_metadata = {
                'name': f'SummerParty_{folder_name}',
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_id]
            }
            
            folder = self.gdrive_service.files().create(body=folder_metadata, fields='id, webViewLink').execute()
            
            self.cloud_folder_id = folder.get('id')
            folder_link = folder.get('webViewLink')

            permission = {'type': 'anyone', 'role': 'reader'}
            self.gdrive_service.permissions().create(fileId=self.cloud_folder_id, body=permission).execute()

            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(folder_link)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img.save(os.path.join(self.session_dir, "qr_code.png"))

            self.is_cloud_ready = True

        except Exception as e:
            print(f"[!] Critical Network Initialization Error: {e}")
            self.is_cloud_ready = False

    def upload_files_worker(self, final_image_path, gif_paths):
        if not self.cloud_folder_id:
            return

        try:
            def upload_file(filepath, mimetype):
                metadata = {'name': os.path.basename(filepath), 'parents': [self.cloud_folder_id]}
                media = MediaFileUpload(filepath, mimetype=mimetype)
                self.gdrive_service.files().create(body=metadata, media_body=media, fields='id').execute()

            upload_file(final_image_path, 'image/jpeg')
            
            for gif in gif_paths:
                if os.path.exists(gif):
                    upload_file(gif, 'image/gif')

        except Exception as e:
            print(f"[!] Asynchronous Population Fault: {e}")

    # ==========================================
    # Final Representation
    # ==========================================

    def show_final_screen(self, img_path, qr_path, is_success=True):
        self.state = "RESULT"
        self.clear_container()
        
        # 1. Use a scrollable area or a larger fixed container if necessary
        content_frame = Frame(self.ui_container, bg='white')
        content_frame.pack(pady=20, expand=True)

        # 2. Open and resize properly
        img = Image.open(img_path)
        # Force a consistent scale that fits the screen height
        # Assuming your screen height is 1080p, let's use 800px height for the strip
        target_h = 800
        aspect_ratio = img.width / img.height
        target_w = int(target_h * aspect_ratio)
        
        final_img = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        final_imgtk = ImageTk.PhotoImage(image=final_img)
        
        # 3. Explicitly set dimensions on the label to prevent clipping
        img_lbl = Label(content_frame, image=final_imgtk, bg='white', 
                        width=target_w, height=target_h)
        img_lbl.image = final_imgtk
        img_lbl.pack(side="left", padx=50)

        # 4. Right side panel
        right_frame = Frame(content_frame, bg='white')
        right_frame.pack(side="left", padx=50, fill="y")

        if is_success and os.path.exists(qr_path):
            qr_img = Image.open(qr_path).resize((250, 250))
            qr_imgtk = ImageTk.PhotoImage(image=qr_img)
            qr_lbl = Label(right_frame, image=qr_imgtk, bg='white')
            qr_lbl.image = qr_imgtk
            qr_lbl.pack(side="top", pady=20)

            msg_text = f"Scan the QR code to\naccess your photos and GIFs!\n\n(The link will expire in 3 days)"
            msg_color = "#E53935"
        else:
            error_icon = Label(right_frame, text="⚠️", font=("Helvetica", 72), bg='white', fg="#FF9800")
            error_icon.pack(side="top", pady=(20, 0))
            
            msg_text = f"Cloud Allocation Failed.\nNo QR code generated.\n\nPlease contact the organizer, CNG group."
            msg_color = "#757575"

        msg_lbl = Label(right_frame, text=msg_text, font=("Helvetica", 18, "bold"), fg=msg_color, bg='white', justify="center")
        msg_lbl.pack(side="top", pady=40)

        reset_btn = Button(right_frame, text="Return to Start", font=("Helvetica", 20, "bold"), command=self.show_start_screen, width=20, height=2, cursor="hand2")
        reset_btn.pack(side="bottom", pady=50)

    def on_close(self):
        self.is_running = False
        if self.cap.isOpened():
            self.cap.release()
        self.executor.shutdown(wait=False)
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LifeFourCutsApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()