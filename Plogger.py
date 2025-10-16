import os
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import fnmatch
import json
import datetime
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import fnmatch
import json
import datetime

class ProjectLogger:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Logger")
        # Matrix dark theme colors
        self.D_BG = "#1a1a1a"         # main background (deep black)
        self.F_BG = "#1e1e1e"         # frame/canvas background (almost black)
        self.W_BG = "#111111"         # widget background (labels, buttons, entries, listboxes)
        self.W_FG = "#00FF00"         # Matrix green text (labels, buttons, entries, listboxes)
        self.ENTRY_BG = "#111111"     # entry/listbox background (same as W_BG)
        self.ENTRY_FG = "#00FF00"     # entry/listbox foreground (Matrix green)
        self.HL_BG = "#004400"        # highlight for listbox selection and active (dark muted green)
        self.HL_FG = "#00FF00"        # highlight foreground (Matrix green)
        self.DISABLED_FG = "#007700"  # dark muted green for disabled/muted text
        self.SMALL_FONT = ("Arial", 9)
        self.SMALL_FONT_BOLD = ("Arial", 9, "bold")
        self.root.configure(bg=self.D_BG)

        # --- ttk Style for Matrix Button, Scrollbar, and Checkbutton ---
        self.style = ttk.Style()
        # Set theme to 'clam' for better customization (esp. on MacOS)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self.style.configure(
            'Matrix.TButton',
            background=self.W_BG,
            foreground=self.W_FG,
            font=self.SMALL_FONT,
            borderwidth=0,
            focusthickness=0,
            focuscolor=self.W_BG,
            highlightthickness=0,
            relief="flat"
        )
        self.style.map(
            'Matrix.TButton',
            background=[('active', self.HL_BG), ('!active', self.W_BG)],
            foreground=[('disabled', self.DISABLED_FG), ('active', self.W_FG), ('!active', self.W_FG)],
            highlightcolor=[('focus', self.W_BG), ('!focus', self.W_BG)],
        )
        # Remove focus ring and Aqua effects on Mac
        self.style.layout('Matrix.TButton', [
            ('Button.background', None),
            ('Button.padding', {'children': [
                ('Button.label', {'side': 'left', 'expand': 1})
            ]}),
        ])
        # --- Custom ttk style for Matrix vertical scrollbar ---
        self.style.element_create("Matrix.Vertical.Scrollbar.trough", "from", "clam")
        self.style.element_create("Matrix.Vertical.Scrollbar.thumb", "from", "clam")
        self.style.layout(
            "Matrix.Vertical.TScrollbar",
            [
                ("Vertical.Scrollbar.trough", {
                    "children": [
                        ("Vertical.Scrollbar.thumb", {"unit": "1", "sticky": "nswe"})
                    ],
                    "sticky": "ns"
                })
            ]
        )
        self.style.configure(
            "Matrix.Vertical.TScrollbar",
            troughcolor="#1a1a1a",
            background="#004400",
            bordercolor="#1a1a1a",
            lightcolor="#004400",
            darkcolor="#004400",
            arrowcolor="#00FF00",
            relief="flat"
        )
        self.style.map(
            "Matrix.Vertical.TScrollbar",
            background=[("active", "#004400"), ("!active", "#004400")],
            troughcolor=[("active", "#1a1a1a"), ("!active", "#1a1a1a")],
            bordercolor=[("active", "#1a1a1a"), ("!active", "#1a1a1a")],
            arrowcolor=[("active", "#00FF00"), ("!active", "#00FF00")],
            lightcolor=[("active", "#004400"), ("!active", "#004400")],
            darkcolor=[("active", "#004400"), ("!active", "#004400")],
        )
        # --- Matrix ttk style for Checkbutton (no custom images, dark Matrix look) ---
        self.style.configure(
            "Matrix.TCheckbutton",
            background=self.D_BG,
            foreground=self.W_FG,
            font=self.SMALL_FONT,
            indicatorbackground="#004400",   # dark green for box background
            indicatorforeground="#00FF00",   # Matrix green for indicator (check)
            selectcolor="#00FF00",           # checked mark color (Matrix green)
            borderwidth=0,
            highlightthickness=0,
            relief="flat",
            padding=(2, 1, 2, 1),
            focuscolor=self.D_BG
        )
        self.style.map(
            "Matrix.TCheckbutton",
            background=[("active", self.D_BG), ("!active", self.D_BG)],
            foreground=[("!disabled", self.W_FG), ("disabled", self.DISABLED_FG)],
            indicatorbackground=[("selected", "#00FF00"), ("!selected", "#004400")],
            selectcolor=[("selected", "#00FF00"), ("!selected", "#004400")],
        )
        # Remove Aqua/macos artifacts and compact padding
        self.style.layout("Matrix.TCheckbutton", [
            ("Checkbutton.padding", {
                "sticky": "nswe",
                "children": [
                    ("Checkbutton.indicator", {"side": "left", "sticky": "w"}),
                    ("Checkbutton.label", {"side": "left", "sticky": "w"})
                ]
            })
        ])
        # --- Matrix style for Treeview ---
        self.style.configure("Treeview", background=self.F_BG, fieldbackground=self.F_BG, foreground=self.W_FG, borderwidth=0)
        self.style.map("Treeview", background=[('selected', self.HL_BG)], foreground=[('selected', self.W_FG)])

        self.folder_path = tk.StringVar()
        self.size_limit_mb = tk.IntVar(value=10)  # default 10MB limit
        self.show_venv = tk.BooleanVar(value=False)  # new var for showing venv files
        self.search_var = tk.StringVar()  # for search box
        self.skip_patterns_var = tk.StringVar()  # for skip patterns input

        self.tag_filter_var = tk.StringVar()  # for tag filtering
        self.batch_tag_var = tk.StringVar()   # for batch tag entry

        self.files = []
        self.file_vars = {}
        self.file_checkbuttons = {}
        self.file_colors = {}  # store color state per file
        self.toggle_all_state = True  # True means next toggle will select all
        self.plogger_path = None
        self.last_output_path = None

        self.file_tags = {}  # full_path -> set of tags
        self.file_tag_vars = {}  # full_path -> tk.StringVar for Entry widget
        self.file_tag_entries = {}  # full_path -> Entry widget

        # Session tracking
        self.psession_path = None
        self.psession_data = {
            "important_files": [],
            "tags": {},
            "todos": [],
            "done_todos": [],
            "ideas": "",
            "last_session": None
        }

        self.sidebar_visible = True
        self.sidebar_widgets = {}
        # Summarize options state
        self.summarize_options = {
            "include_files": tk.BooleanVar(value=True),
            "folder_filter": tk.StringVar(value="")
        }
        # Show only selected files in summary schematic
        self.show_only_selected = tk.BooleanVar(value=False)
        self.build_gui()

    def build_gui(self):
        # Usage instruction label at the top, now with a dragon mascot emoji 🐲 in Matrix green
        instruction_text = "Tip: Use Ctrl or Shift to multi-select files. You can use skip patterns like '*.log' or '/build/' to ignore files. 🐲"
        # Place the emoji at the end and ensure it inherits the Matrix green foreground color
        tk.Label(self.root, text=instruction_text, bg=self.D_BG, fg=self.W_FG).pack(side="top", fill="x", padx=8, pady=(6, 1))

        # Main frame with sidebar and main content
        main_container = tk.Frame(self.root, bg=self.D_BG)
        main_container.pack(fill="both", expand=True)

        # Sidebar - always visible at start
        self.sidebar_frame = tk.Frame(main_container, width=200, bg=self.F_BG, relief="sunken", bd=0)
        self.sidebar_frame.pack(side="left", fill="y")
        self.build_sidebar()

        # Button to toggle sidebar
        toggle_btn = ttk.Button(
            main_container, text="Toggle Sidebar", command=self.toggle_sidebar,
            style='Matrix.TButton'
        )
        toggle_btn.pack(side="top", anchor="ne", padx=2, pady=1)

        # Main content frame
        self.main_frame = tk.Frame(main_container, bg=self.D_BG)
        self.main_frame.pack(side="left", padx=4, pady=4, fill="both", expand=True)

        # Batch tag, tag filter, and remove tag frame (all at top for clean layout)
        tag_top_frame = tk.Frame(self.main_frame, bg=self.D_BG)
        tag_top_frame.pack(fill="x", pady=1)
        # Batch Tag controls
        tk.Label(tag_top_frame, text="Batch Tag:", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left", padx=(0,1))
        batch_tag_entry = tk.Entry(tag_top_frame, textvariable=self.batch_tag_var, width=12,
                                   bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT)
        batch_tag_entry.pack(side="left", padx=(0,1))
        ttk.Button(
            tag_top_frame, text="Apply Tag", command=self.apply_batch_tag,
            style='Matrix.TButton'
        ).pack(side="left", padx=(0,4))
        # Tag Filter controls
        tk.Label(tag_top_frame, text="Tag Filter:", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left", padx=(0,1))
        tag_filter_entry = tk.Entry(tag_top_frame, textvariable=self.tag_filter_var, width=12,
                                    bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT)
        tag_filter_entry.pack(side="left", padx=(0,4))
        tag_filter_entry.bind("<Return>", self.apply_tag_filter)
        tag_filter_entry.bind("<KeyRelease>", lambda e: self.on_tag_filter_change())
        # Remove Tag controls
        self.remove_tag_var = tk.StringVar()
        tk.Label(tag_top_frame, text="Remove Tag:", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left", padx=(0,1))
        remove_tag_entry = tk.Entry(tag_top_frame, textvariable=self.remove_tag_var, width=12,
                                   bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT)
        remove_tag_entry.pack(side="left", padx=(0,1))
        ttk.Button(
            tag_top_frame, text="Remove Tag", command=self.remove_tag_from_files,
            style='Matrix.TButton'
        ).pack(side="left", padx=(0,0))

        # Folder chooser
        folder_frame = tk.Frame(self.main_frame, bg=self.D_BG)
        folder_frame.pack(fill="x", pady=1)

        ttk.Button(
            folder_frame, text="Choose Project Folder", command=self.choose_folder,
            style='Matrix.TButton'
        ).pack(side="left")
        tk.Entry(folder_frame, textvariable=self.folder_path, width=48,
                 bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT,
                 disabledbackground=self.ENTRY_BG, disabledforeground=self.DISABLED_FG).pack(side="left", padx=2)

        # Size limit
        tk.Label(folder_frame, text="Size Limit (MB):", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left", padx=(4,1))
        tk.Entry(folder_frame, textvariable=self.size_limit_mb, width=5,
                 bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT,
                 disabledbackground=self.ENTRY_BG, disabledforeground=self.DISABLED_FG).pack(side="left")

        # Show venv checkbox (ttk, styled for Matrix dark theme)
        ttk.Checkbutton(
            folder_frame,
            text="Show 'venv' files",
            variable=self.show_venv,
            command=self.scan_folder,
            style="Matrix.TCheckbutton"
        ).pack(side="left", padx=(4,0))

        # Skip patterns input
        skip_frame = tk.Frame(self.main_frame, bg=self.D_BG)
        skip_frame.pack(fill="x", pady=1)
        tk.Label(skip_frame, text="Skip Patterns (comma separated):", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left")
        skip_entry = tk.Entry(skip_frame, textvariable=self.skip_patterns_var,
                              bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT)
        skip_entry.pack(side="left", fill="x", expand=True, padx=(2,0))
        skip_entry.bind("<KeyRelease>", lambda e: self.scan_folder())

        # Search box
        search_frame = tk.Frame(self.main_frame, bg=self.D_BG)
        search_frame.pack(fill="x", pady=1)
        tk.Label(search_frame, text="Search:", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT).pack(side="left")
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, highlightthickness=0, font=self.SMALL_FONT)
        search_entry.pack(side="left", fill="x", expand=True, padx=(2,0))
        search_entry.bind("<KeyRelease>", lambda e: self.scan_folder())

        # Buttons frame for new buttons
        buttons_frame = tk.Frame(self.main_frame, bg=self.D_BG)
        buttons_frame.pack(fill="x", pady=1)
        # Sidebar action buttons: use ttk with Matrix style
        ttk.Button(buttons_frame, text="Toggle Selected", command=self.toggle_selected, style='Matrix.TButton').pack(side="left", padx=(0,2))
        ttk.Button(buttons_frame, text="Toggle All / None", command=self.toggle_all_none, style='Matrix.TButton').pack(side="left", padx=(0,2))
        ttk.Button(buttons_frame, text="Save Selection as Config", command=self.save_selection_as_config, style='Matrix.TButton').pack(side="left", padx=(0,2))
        ttk.Button(buttons_frame, text="Quick Resummarize", command=self.quick_resummarize, style='Matrix.TButton').pack(side="left")
        ttk.Button(
            buttons_frame, text="📖 Edit Project Summary", command=self.edit_project_summary,
            style='Matrix.TButton'
        ).pack(side="left", padx=(2,0))

        # Files list with scrollbar
        self.files_frame_container = tk.Frame(self.main_frame, bg=self.D_BG)
        self.files_frame_container.pack(fill="both", expand=True, pady=1)

        self.tree = ttk.Treeview(self.files_frame_container, selectmode="extended", show="tree")
        self.tree.pack(side="left", fill="both", expand=True)

        self.scrollbar = ttk.Scrollbar(self.files_frame_container, orient="vertical", command=self.tree.yview, style="Matrix.Vertical.TScrollbar")
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        self.tree.bind("<Double-1>", self.on_tree_item_toggle)
        self.tree.bind("<space>", self.on_tree_item_toggle)

        self.tree_items = {}

        # Summarize button
        ttk.Button(
            self.main_frame, text="Summarize Project", command=self.summarize,
            style='Matrix.TButton'
        ).pack(pady=4)

        # Show only selected files in summary checkbox
        ttk.Checkbutton(
            self.main_frame,
            text="Show only selected files in summary",
            variable=self.show_only_selected,
            style="Matrix.TCheckbutton"
        ).pack()

        # Status label and progress percentage
        status_frame = tk.Frame(self.root, bg=self.D_BG)
        status_frame.pack(fill="x", padx=6, pady=(0,4))
        self.status_label = tk.Label(status_frame, text="", anchor="w", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT)
        self.status_label.pack(side="left", fill="x", expand=True)
        self.progress_label = tk.Label(status_frame, text="", anchor="e", bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT)
        self.progress_label.pack(side="right")
    def edit_project_summary(self):
        window = tk.Toplevel(self.root)
        window.title("Edit Project Summary")
        window.configure(bg=self.D_BG)
        window.resizable(True, True)

        def save_and_close():
            self.psession_data["project_log"]["summary"] = summary_entry.get("1.0", "end-1c").strip()
            self.psession_data["project_log"]["tech_stack"] = [item.strip() for item in tech_entry.get("1.0", "end-1c").split(",") if item.strip()]
            self.psession_data["project_log"]["key_components"] = [item.strip() for item in components_entry.get("1.0", "end-1c").split(",") if item.strip()]
            self.psession_data["project_log"]["features"] = [item.strip() for item in features_entry.get("1.0", "end-1c").split(",") if item.strip()]
            self.psession_data["project_log"]["open_tasks"] = [item.strip() for item in tasks_entry.get("1.0", "end-1c").splitlines() if item.strip()]
            self.psession_data["project_log"]["notes"] = notes_entry.get("1.0", "end-1c").strip()
            self.save_psession_sidebar_only()
            window.destroy()

        fields = [
            ("Summary", "summary"),
            ("Tech Stack (comma separated)", "tech_stack"),
            ("Key Components (comma separated)", "key_components"),
            ("Features (comma separated)", "features"),
            ("Open Tasks (one per line)", "open_tasks"),
            ("Notes", "notes")
        ]

        entries = {}

        for label_text, key in fields:
            tk.Label(window, text=label_text, bg=self.D_BG, fg=self.W_FG, font=self.SMALL_FONT_BOLD).pack(anchor="w", padx=10, pady=(6,0))
            entry = tk.Text(window, height=3, bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, font=self.SMALL_FONT)
            entry.pack(fill="both", expand=True, padx=10)
            current_value = self.psession_data.get("project_log", {}).get(key, "")
            if isinstance(current_value, list):
                if key == "open_tasks":
                    entry.insert("1.0", "\n".join(current_value))
                else:
                    entry.insert("1.0", ", ".join(current_value))
            else:
                entry.insert("1.0", current_value)
            entries[key] = entry

        summary_entry = entries["summary"]
        tech_entry = entries["tech_stack"]
        components_entry = entries["key_components"]
        features_entry = entries["features"]
        tasks_entry = entries["open_tasks"]
        notes_entry = entries["notes"]

        ttk.Button(window, text="Save Summary", command=save_and_close, style="Matrix.TButton").pack(pady=10)
    def build_sidebar(self):
        # Clear sidebar
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()
        self.sidebar_widgets = {}

        # Sidebar title
        tk.Label(self.sidebar_frame, text="Project Session", bg=self.F_BG, fg=self.W_FG, font=("Arial", 11, "bold")).pack(fill="x", pady=(4,1))

        # --- TODOs Section ---
        tk.Label(self.sidebar_frame, text="TODOs:", anchor="w", bg=self.F_BG, fg=self.W_FG, font=self.SMALL_FONT_BOLD).pack(fill="x", padx=4, pady=(2,0))
        self.sidebar_widgets['todos_listbox'] = tk.Listbox(self.sidebar_frame, height=6,
                                                          bg=self.ENTRY_BG, fg=self.ENTRY_FG, selectbackground=self.HL_BG, selectforeground=self.HL_FG,
                                                          highlightthickness=0, font=self.SMALL_FONT, relief="flat", bd=0,
                                                          activestyle="none")
        self.sidebar_widgets['todos_listbox'].pack(fill="both", expand=True, padx=4, pady=(0,2))
        # Add "Mark Done" button
        mark_done_btn = ttk.Button(
            self.sidebar_frame, text="Mark Done", command=self.mark_sidebar_todo_done,
            style='Matrix.TButton'
        )
        mark_done_btn.pack(fill="x", padx=4, pady=(1, 0))
        # Add TODO Entry and Button
        todo_entry_frame = tk.Frame(self.sidebar_frame, bg=self.F_BG)
        todo_entry_frame.pack(fill="x", padx=4, pady=(0,2))
        self.sidebar_widgets['todo_entry_var'] = tk.StringVar()
        todo_entry = tk.Entry(todo_entry_frame, textvariable=self.sidebar_widgets['todo_entry_var'],
                              bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG, font=self.SMALL_FONT, highlightthickness=0)
        todo_entry.pack(side="left", fill="x", expand=True)
        add_todo_btn = ttk.Button(
            todo_entry_frame, text="Add TODO", command=self.add_sidebar_todo,
            style='Matrix.TButton'
        )
        add_todo_btn.pack(side="left", padx=(2,0))

        # --- Ideas/Notes Section ---
        tk.Label(self.sidebar_frame, text="Ideas / Notes:", anchor="w", bg=self.F_BG, fg=self.W_FG, font=self.SMALL_FONT_BOLD).pack(fill="x", padx=4, pady=(0,0))
        self.sidebar_widgets['ideas_text'] = tk.Text(self.sidebar_frame, height=6, wrap="word",
                                                     bg=self.ENTRY_BG, fg=self.ENTRY_FG, insertbackground=self.ENTRY_FG,
                                                     highlightthickness=0, font=self.SMALL_FONT, bd=0)
        self.sidebar_widgets['ideas_text'].pack(fill="both", expand=True, padx=4, pady=(0,2))
        # Save ideas on focus out
        self.sidebar_widgets['ideas_text'].bind("<FocusOut>", lambda e: self.save_sidebar_ideas())

        # --- Important Files Section ---
        tk.Label(self.sidebar_frame, text="Important Files:", anchor="w", bg=self.F_BG, fg=self.W_FG, font=self.SMALL_FONT_BOLD).pack(fill="x", padx=4, pady=(0,0))
        self.sidebar_widgets['files_listbox'] = tk.Listbox(self.sidebar_frame, height=6,
                                                          bg=self.ENTRY_BG, fg=self.ENTRY_FG, selectbackground=self.HL_BG, selectforeground=self.HL_FG,
                                                          highlightthickness=0, font=self.SMALL_FONT, relief="flat", bd=0,
                                                          activestyle="none")
        self.sidebar_widgets['files_listbox'].pack(fill="both", expand=True, padx=4, pady=(0,2))
        # Add Important File Button
        add_impfile_btn = ttk.Button(
            self.sidebar_frame, text="Add Important File", command=self.add_sidebar_important_file,
            style='Matrix.TButton'
        )
        add_impfile_btn.pack(fill="x", padx=4, pady=(1,2))

        # Fill sidebar with current psession data
        self.update_sidebar()
    def add_sidebar_todo(self):
        # Add a TODO from the sidebar Entry
        todo_text = self.sidebar_widgets.get('todo_entry_var').get().strip()
        if not todo_text:
            messagebox.showinfo("Add TODO", "Cannot add empty TODO.")
            return
        # Add to psession_data
        todos = self.psession_data.get("todos", [])
        todos.append(todo_text)
        self.psession_data["todos"] = todos
        # Clear entry
        self.sidebar_widgets['todo_entry_var'].set("")
        # Save immediately
        self.save_psession_sidebar_only()
        # Refresh sidebar
        self.update_sidebar()

    def mark_sidebar_todo_done(self):
        # Mark the selected TODO as done, remove from todos, add to done_todos, save immediately
        lb = self.sidebar_widgets.get('todos_listbox')
        if lb is None:
            return
        sel = lb.curselection()
        if not sel:
            messagebox.showinfo("Mark Done", "No TODO selected.")
            return
        idx = sel[0]
        todos = self.psession_data.get("todos", [])
        if idx < 0 or idx >= len(todos):
            return
        todo_item = todos.pop(idx)
        # Add to done_todos
        done_todos = self.psession_data.get("done_todos", [])
        done_todos.append(todo_item)
        self.psession_data["todos"] = todos
        self.psession_data["done_todos"] = done_todos
        self.save_psession_sidebar_only()
        self.update_sidebar()

    def add_sidebar_important_file(self):
        # Add an Important File via file picker (restricted to project folder)
        if not self.folder_path.get():
            messagebox.showerror("Error", "No project folder selected.")
            return
        # Only allow files within the project folder
        project_folder = os.path.abspath(self.folder_path.get())
        file_path = filedialog.askopenfilename(initialdir=project_folder)
        if not file_path:
            return
        file_path = os.path.abspath(file_path)
        # Check if selected file is inside the project folder
        try:
            common = os.path.commonpath([project_folder, file_path])
        except Exception:
            common = ""
        if not common or common != project_folder:
            messagebox.showwarning("Invalid File", "You can only add files inside the current project folder.")
            return
        # Get relative path
        rel_path = os.path.relpath(file_path, project_folder)
        # Add to important_files if not already present
        important_files = self.psession_data.get("important_files", [])
        if rel_path not in important_files:
            important_files.append(rel_path)
            self.psession_data["important_files"] = important_files
            # Save immediately
            self.save_psession_sidebar_only()
            self.update_sidebar()
        else:
            messagebox.showinfo("Already Added", "This file is already marked as important.")

    def save_psession_sidebar_only(self):
        # Save only psession_data (no file selection/tag changes)
        if not self.psession_path:
            return
        # Last session timestamp
        now_str = datetime.datetime.now().isoformat()
        self.psession_data["last_session"] = now_str
        # Always ensure done_todos key exists
        if "done_todos" not in self.psession_data:
            self.psession_data["done_todos"] = []
        try:
            with open(self.psession_path, "w", encoding="utf-8") as f:
                json.dump(self.psession_data, f, indent=2)
        except Exception:
            pass

    def toggle_sidebar(self):
        # Only show/hide the sidebar; do not recreate other controls.
        if self.sidebar_visible:
            self.sidebar_frame.pack_forget()
            self.sidebar_visible = False
        else:
            self.sidebar_frame.pack(side="left", fill="y")
            self.sidebar_visible = True

    def choose_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            # Determine .plogger file path based on folder name
            folder_name = os.path.basename(os.path.normpath(folder))
            self.plogger_path = os.path.join(folder, f"{folder_name}.plogger")
            self.psession_path = os.path.join(folder, f"{folder_name}.psession")
            self.load_psession()
            self.scan_folder()
            self.update_sidebar()

    def matches_skip_patterns(self, path, rel_path):
        patterns = [p.strip() for p in self.skip_patterns_var.get().split(",") if p.strip()]
        if not patterns:
            return False
        # Check folder skip patterns with slashes in pattern
        for pattern in patterns:
            if '/' in pattern:
                # Treat as folder pattern, check if pattern in rel_path
                if pattern in rel_path.replace(os.sep, '/'):
                    return True
            else:
                # Treat as filename pattern
                if fnmatch.fnmatch(os.path.basename(path), pattern):
                    return True
        return False

    def scan_folder(self):
        self.tree.delete(*self.tree.get_children())
        self.tree_items = {}
        self.file_vars = {}
        self.files = []

        # Load preselected files and tags from .plogger if exists
        preselected_rel_paths = set()
        preselected_tags = {}
        if self.plogger_path and os.path.isfile(self.plogger_path):
            try:
                with open(self.plogger_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # Format: rel_path[,tag1,tag2,...]
                        if ',' in line:
                            rel_path, *tags = line.split(',')
                            rel_path = rel_path.strip()
                            tagset = set([t.strip() for t in tags if t.strip()])
                            preselected_rel_paths.add(rel_path)
                            preselected_tags[rel_path] = tagset
                        else:
                            preselected_rel_paths.add(line)
            except Exception:
                preselected_rel_paths = set()
                preselected_tags = {}
        # Load tags from psession if available (for new files)
        if self.psession_data.get("tags"):
            for rel_path, tags in self.psession_data["tags"].items():
                if rel_path not in preselected_tags:
                    preselected_tags[rel_path] = set(tags)

        search_text = self.search_var.get().lower()
        tag_filter = self.tag_filter_var.get().strip().lower()

        def insert_node(parent, path, rel_path):
            if os.path.isdir(path):
                folder_id = self.tree.insert(parent, "end", text=os.path.basename(path), open=False)
                self.tree_items[path] = folder_id
                try:
                    for item in sorted(os.listdir(path)):
                        item_path = os.path.join(path, item)
                        item_rel_path = os.path.relpath(item_path, self.folder_path.get())
                        # Filter out 'venv' dirs if show_venv is False
                        if not self.show_venv.get() and os.path.isdir(item_path) and item == "venv":
                            continue
                        # Skip folders matching skip patterns
                        if os.path.isdir(item_path) and self.matches_skip_patterns(item_path, item_rel_path):
                            continue
                        insert_node(folder_id, item_path, item_rel_path)
                except Exception:
                    pass
            else:
                # Apply skip patterns and search/tag filters
                if self.matches_skip_patterns(path, rel_path):
                    return
                if search_text and search_text not in rel_path.lower():
                    return
                tags_for_file = preselected_tags.get(rel_path, set()) if preselected_tags else set()
                if tag_filter:
                    if not any(tag_filter == t.lower() for t in tags_for_file):
                        return
                checked = True
                if self.plogger_path:
                    checked = rel_path in preselected_rel_paths
                display_text = "[X] " + os.path.basename(path) if checked else "[ ] " + os.path.basename(path)
                file_id = self.tree.insert(parent, "end", text=display_text)
                self.tree_items[path] = file_id
                self.file_vars[path] = tk.BooleanVar(value=checked)
                try:
                    size = os.path.getsize(path) / (1024 * 1024)
                except Exception:
                    size = 0
                self.files.append((path, rel_path, size))

        insert_node("", self.folder_path.get(), ".")

        # Clear any selection state
        self.selected_checkbuttons = set()
        # Update sidebar if visible
        if self.sidebar_visible:
            self.update_sidebar()

    def on_tree_item_toggle(self, event):
        item_id = self.tree.focus()
        if not item_id:
            return
        for path, iid in self.tree_items.items():
            if iid == item_id:
                break
        else:
            return
        if os.path.isdir(path):
            return
        var = self.file_vars.get(path)
        if var is None:
            return
        var.set(not var.get())
        basename = os.path.basename(path)
        new_text = "[X] " + basename if var.get() else "[ ] " + basename
        self.tree.item(item_id, text=new_text)
    def on_tag_entry_change(self, full_path, tag_var):
        tags = [t.strip() for t in tag_var.get().split(",") if t.strip()]
        self.file_tags[full_path] = set(tags)
        # update entry in case user e.g. entered duplicates
        tag_var.set(", ".join(sorted(self.file_tags[full_path])))
        # Update sidebar if visible
        if self.sidebar_visible:
            self.update_sidebar()

    def apply_batch_tag(self):
        tag_text = self.batch_tag_var.get().strip()
        if not tag_text:
            messagebox.showinfo("Batch Tag", "No tag entered.")
            return
        tags = [t.strip() for t in tag_text.split(",") if t.strip()]
        if not tags:
            messagebox.showinfo("Batch Tag", "No valid tags entered.")
            return
        # Use multi-selection if present, else all checked files
        if self.selected_checkbuttons:
            targets = list(self.selected_checkbuttons)
        else:
            targets = [fp for fp, var in self.file_vars.items() if var.get()]
        for fp in targets:
            current_tags = self.file_tags.get(fp, set())
            for t in tags:
                if t not in current_tags:
                    current_tags.add(t)
            self.file_tags[fp] = current_tags
            # Update entry widget
            tag_var = self.file_tag_vars.get(fp)
            if tag_var is not None:
                tag_var.set(", ".join(sorted(current_tags)))
        messagebox.showinfo("Batch Tag", f"Applied tag(s): {', '.join(tags)}")
        if self.sidebar_visible:
            self.update_sidebar()

    def apply_tag_filter(self, event=None):
        # On Enter in tag filter entry
        self.scan_folder()

    def on_tag_filter_change(self):
        # If filter is cleared, show all files again
        if not self.tag_filter_var.get().strip():
            self.scan_folder()

    def on_checkbutton_click(self, event):
        # Detect which checkbutton was clicked and handle multi-select toggle
        widget = event.widget
        # Find full_path by matching widget
        clicked_path = None
        for path, cb in self.file_checkbuttons.items():
            if cb == widget:
                clicked_path = path
                break
        if clicked_path is None:
            return

        # If Ctrl or Shift is pressed, toggle selection of multiple
        ctrl_pressed = (event.state & 0x4) != 0
        shift_pressed = (event.state & 0x1) != 0

        if ctrl_pressed or shift_pressed:
            # Select or deselect this cb in selected_checkbuttons set
            if clicked_path in self.selected_checkbuttons:
                self.selected_checkbuttons.remove(clicked_path)
                widget.config(relief="flat")
            else:
                self.selected_checkbuttons.add(clicked_path)
                widget.config(relief="sunken")
            # Prevent default toggle to allow manual toggle_selected usage
            return "break"
        else:
            # Clear previous selection highlights
            for path in self.selected_checkbuttons:
                cb = self.file_checkbuttons.get(path)
                if cb:
                    cb.config(relief="flat")
            self.selected_checkbuttons.clear()

    def toggle_selected(self):
        if not self.selected_checkbuttons:
            messagebox.showinfo("Info", "No files selected for toggling. Use Ctrl+Click or Shift+Click on file names to select multiple.")
            return
        # Determine if we should check or uncheck based on current states
        # If all selected are checked, uncheck all; else check all
        all_checked = all(self.file_vars[path].get() for path in self.selected_checkbuttons)
        new_state = not all_checked
        for path in self.selected_checkbuttons:
            self.file_vars[path].set(new_state)

    def toggle_all_none(self):
        # Determine next state based on toggle_all_state
        new_state = self.toggle_all_state
        for var in self.file_vars.values():
            var.set(new_state)
        # Flip state for next toggle
        self.toggle_all_state = not self.toggle_all_state

    def save_selection_as_config(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "No folder selected.")
            return
        if not self.plogger_path:
            # Determine .plogger file path based on folder name
            folder_name = os.path.basename(os.path.normpath(self.folder_path.get()))
            self.plogger_path = os.path.join(self.folder_path.get(), f"{folder_name}.plogger")

        try:
            with open(self.plogger_path, 'w', encoding='utf-8') as f:
                for full_path, rel_path, _ in self.files:
                    if self.file_vars[full_path].get():
                        tags = self.file_tags.get(full_path, set())
                        if tags:
                            f.write(rel_path + "," + ",".join(sorted(tags)) + "\n")
                        else:
                            f.write(rel_path + "\n")
            messagebox.showinfo("Saved", f"Selection saved to config file:\n{self.plogger_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config file:\n{str(e)}")

    def quick_resummarize(self):
        if not self.folder_path.get():
            messagebox.showerror("Error", "No folder selected.")
            return
        if not self.last_output_path:
            messagebox.showinfo("Info", "No previous summary output found. Please summarize first.")
            return
        self.summarize(output_path=self.last_output_path)

    def is_text_file(self, filename):
        try:
            with open(filename, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:
                    return False
                # Try decoding to UTF-8
                chunk.decode('utf-8')
                return True
        except Exception:
            return False

    def summarize(self, output_path=None):
        self.summarize_actual(output_path)


    def print_tree_layout(self, out_file, node="", indent_level=0):
        children = self.tree.get_children(node)
        for child in children:
            path = None
            for p, iid in self.tree_items.items():
                if iid == child:
                    path = p
                    break
            if not path:
                continue
            is_checked = self.file_vars.get(path, tk.BooleanVar(value=False)).get()
            # If toggle is on, skip unselected files, but keep folders if they contain selected files
            if self.show_only_selected.get():
                if not os.path.isdir(path) and not is_checked:
                    continue
                # For folders, check if any descendant file is checked; if not, skip folder
                if os.path.isdir(path):
                    def has_checked_descendant(n):
                        for ch in self.tree.get_children(n):
                            ch_path = None
                            for pp, iid2 in self.tree_items.items():
                                if iid2 == ch:
                                    ch_path = pp
                                    break
                            if not ch_path:
                                continue
                            if os.path.isdir(ch_path):
                                if has_checked_descendant(ch):
                                    return True
                            else:
                                if self.file_vars.get(ch_path, tk.BooleanVar(value=False)).get():
                                    return True
                        return False
                    if not has_checked_descendant(child):
                        continue
            check_mark = "[X]" if is_checked else "[ ]"
            indent = "    " * indent_level
            name = self.tree.item(child, "text")
            if name.startswith("[X]") or name.startswith("[ ]"):
                name = name[3:].strip()
            out_file.write(f"{indent}{check_mark} {name}\n")
            # Only expand children if:
            # - Folder is expanded
            # - And folder is not hidden by toggle
            if os.path.isdir(path) and self.tree.item(child, "open"):
                self.print_tree_layout(out_file, node=child, indent_level=indent_level+1)

    def summarize_actual(self, output_path=None):
        if not self.folder_path.get():
            messagebox.showerror("Error", "No folder selected.")
            return

        if not output_path:
            output_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
            if not output_path:
                return
            self.last_output_path = output_path  # Save for quick resummarize

        # Load selected files from .plogger
        plogger_files = []
        if self.plogger_path and os.path.isfile(self.plogger_path):
            try:
                with open(self.plogger_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            rel_path = line.split(',')[0].strip()
                            plogger_files.append(rel_path)
            except Exception:
                pass

        unreadable_files = []
        skipped_files = []

        selected_files = [(full_path, rel_path, file_size) for full_path, rel_path, file_size in self.files if self.file_vars[full_path].get()]
        total_selected = len(selected_files)
        if total_selected == 0:
            messagebox.showinfo("Info", "No files selected for summarization.")
            return

        try:
            self.status_label.config(text="Writing folder structure...")
            self.progress_label.config(text="")
            self.root.update_idletasks()

            with open(output_path, "w", encoding="utf-8") as out_file:
                # Write Project Log first
                project_log = self.psession_data.get("project_log", {})
                out_file.write("# 📚 Project Summary\n\n")
                out_file.write(f"**Summary**:\n{project_log.get('summary', '').strip()}\n\n")
                out_file.write(f"**Tech Stack**:\n{', '.join(project_log.get('tech_stack', []))}\n\n")
                out_file.write(f"**Key Components**:\n{', '.join(project_log.get('key_components', []))}\n\n")
                out_file.write(f"**Features**:\n{', '.join(project_log.get('features', []))}\n\n")
                out_file.write(f"**Open Tasks**:\n")
                for task in project_log.get('open_tasks', []):
                    out_file.write(f"- {task}\n")
                out_file.write("\n**Notes**:\n")
                out_file.write(project_log.get('notes', '').strip())
                out_file.write("\n\n--- Folder Structure ---\n")
                self.print_tree_layout(out_file)

                out_file.write("\n--- Included Files (from config) ---\n")
                for included_file in sorted(plogger_files):
                    out_file.write(included_file + "\n")

                out_file.write("\n--- Selected Files ---\n")

                for idx, (full_path, rel_path, file_size) in enumerate(selected_files):
                    self.status_label.config(text=f"Processing file {idx+1} of {total_selected}: {rel_path}")
                    percent = int((idx+1) / total_selected * 100)
                    self.progress_label.config(text=f"{percent}%")
                    self.root.update_idletasks()

                    if file_size > self.size_limit_mb.get():
                        out_file.write(f"\n--- Skipped large file: {rel_path} ({file_size:.2f}MB) ---\n")
                        skipped_files.append(rel_path)
                        continue

                    if not self.is_text_file(full_path):
                        unreadable_files.append(rel_path)
                        continue

                    # Write tags if present
                    tags = self.file_tags.get(full_path, set())
                    if tags:
                        out_file.write(f"\n--- File: {rel_path} [tags: {', '.join(sorted(tags))}] ---\n")
                    else:
                        out_file.write(f"\n--- File: {rel_path} ---\n")
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            out_file.write(f.read())
                    except Exception:
                        unreadable_files.append(rel_path)

                out_file.write("\n--- Skipped Files ---\n")
                for skipped in skipped_files + unreadable_files:
                    out_file.write(f"{skipped}\n")

            self.status_label.config(text="Summarization complete.")
            self.progress_label.config(text="")
            self.root.update_idletasks()

            if unreadable_files:
                messagebox.showwarning("Unreadable Files Skipped", "The following files were skipped because they are not readable as text:\n" + "\n".join(unreadable_files))

            if skipped_files:
                messagebox.showinfo("Skipped Files", "The following files were skipped due to size limits:\n" + "\n".join(skipped_files))

            messagebox.showinfo("Success", f"Project summarized successfully!\nSaved to: {output_path}")

            # --- Save .psession file with session data ---
            self.save_psession(selected_files)
            if self.sidebar_visible:
                self.update_sidebar()

        except Exception as e:
            self.status_label.config(text="")
            self.progress_label.config(text="")
            messagebox.showerror("Error", str(e))

    def extract_todos_from_files(self, selected_files):
        # Extract TODOs from files tagged as 'todo'
        todos = []
        for full_path, rel_path, file_size in selected_files:
            tags = self.file_tags.get(full_path, set())
            if "todo" in [t.lower() for t in tags]:
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line_strip = line.strip()
                            # Accept lines like: - something, * something, [ ] something, [x] something, [ ]: etc.
                            if (line_strip.startswith("- ") or
                                line_strip.startswith("* ") or
                                line_strip.startswith("[ ]") or
                                line_strip.startswith("[x]") or
                                line_strip.startswith("[X]") or
                                line_strip.startswith("[ ]:") or
                                line_strip.startswith("[x]:") or
                                line_strip.startswith("[X]:")):
                                todos.append(f"{rel_path}: {line_strip}")
                except Exception:
                    continue
        return todos

    def save_psession(self, selected_files):
        if not self.psession_path:
            # If folder not chosen, skip
            return
        # Save important files (relative paths)
        important_rel_paths = []
        tags_dict = {}
        for full_path, rel_path, _ in selected_files:
            important_rel_paths.append(rel_path)
            tags_dict[rel_path] = sorted(self.file_tags.get(full_path, set()))
        # Extract TODOs
        todos = self.extract_todos_from_files(selected_files)
        # Ideas/notes from sidebar
        ideas = ""
        if self.sidebar_widgets.get('ideas_text'):
            ideas = self.sidebar_widgets['ideas_text'].get("1.0", "end-1c")
        # Last session timestamp
        now_str = datetime.datetime.now().isoformat()
        # Preserve done_todos from previous psession_data if present
        done_todos = self.psession_data.get("done_todos", [])
        # Save expanded folders (relative to project root)
        expanded_folders = []
        for path, iid in self.tree_items.items():
            if os.path.isdir(path) and self.tree.item(iid, "open"):
                rel_path = os.path.relpath(path, self.folder_path.get())
                expanded_folders.append(rel_path)
        # Preserve project_log if present, else set default
        project_log = self.psession_data.get("project_log", {
            "summary": "",
            "tech_stack": [],
            "key_components": [],
            "features": [],
            "open_tasks": [],
            "notes": ""
        })
        session_data = {
            "important_files": important_rel_paths,
            "tags": tags_dict,
            "todos": todos,
            "done_todos": done_todos,
            "ideas": ideas,
            "last_session": now_str,
            "expanded_folders": expanded_folders,
            "project_log": project_log
        }
        try:
            with open(self.psession_path, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2)
            self.psession_data = session_data
        except Exception:
            pass

    def load_psession(self):
        # Load .psession file if exists, else blank
        if self.psession_path and os.path.isfile(self.psession_path):
            try:
                with open(self.psession_path, "r", encoding="utf-8") as f:
                    self.psession_data = json.load(f)
                # ensure done_todos key exists
                if "done_todos" not in self.psession_data:
                    self.psession_data["done_todos"] = []
            except Exception:
                self.psession_data = {
                    "important_files": [],
                    "tags": {},
                    "todos": [],
                    "done_todos": [],
                    "ideas": "",
                    "last_session": None
                }
        else:
            self.psession_data = {
                "important_files": [],
                "tags": {},
                "todos": [],
                "done_todos": [],
                "ideas": "",
                "last_session": None
            }
        # Ensure project_log key exists
        if "project_log" not in self.psession_data:
            self.psession_data["project_log"] = {
                "summary": "",
                "tech_stack": [],
                "key_components": [],
                "features": [],
                "open_tasks": [],
                "notes": ""
            }
        # After loading psession, schedule restoring expanded folders after scan
        self.root.after(500, self.restore_expanded_folders)

    def restore_expanded_folders(self):
        expanded_folders = self.psession_data.get("expanded_folders", [])
        for path, iid in self.tree_items.items():
            rel_path = os.path.relpath(path, self.folder_path.get())
            if rel_path in expanded_folders:
                self.tree.item(iid, open=True)

    def update_sidebar(self):
        # Fill sidebar widgets from psession_data
        # TODOs
        todos = self.psession_data.get("todos", [])
        lb = self.sidebar_widgets.get('todos_listbox')
        if lb:
            lb.delete(0, "end")
            for todo in todos:
                lb.insert("end", todo)
        # Ideas/notes
        ideas = self.psession_data.get("ideas", "")
        txt = self.sidebar_widgets.get('ideas_text')
        if txt:
            txt.delete("1.0", "end")
            txt.insert("1.0", ideas)
        # Important files
        files = self.psession_data.get("important_files", [])
        files_lb = self.sidebar_widgets.get('files_listbox')
        if files_lb:
            files_lb.delete(0, "end")
            for f in files:
                files_lb.insert("end", f)

    def save_sidebar_ideas(self):
        # Save ideas from sidebar text to psession and file
        if not self.psession_path:
            return
        ideas = self.sidebar_widgets.get('ideas_text').get("1.0", "end-1c") if self.sidebar_widgets.get('ideas_text') else ""
        self.psession_data["ideas"] = ideas
        # Always ensure done_todos key exists
        if "done_todos" not in self.psession_data:
            self.psession_data["done_todos"] = []
        # Save immediately
        try:
            with open(self.psession_path, "w", encoding="utf-8") as f:
                json.dump(self.psession_data, f, indent=2)
        except Exception:
            pass


    def remove_tag_from_files(self):
        tag_text = self.remove_tag_var.get().strip()
        if not tag_text:
            messagebox.showinfo("Remove Tag", "No tag entered.")
            return
        tag_to_remove = tag_text
        # Use multi-selection if present, else all checked files
        if getattr(self, "selected_checkbuttons", None) and self.selected_checkbuttons:
            targets = list(self.selected_checkbuttons)
        else:
            targets = [fp for fp, var in self.file_vars.items() if var.get()]
        updated_count = 0
        for fp in targets:
            current_tags = self.file_tags.get(fp, set())
            if tag_to_remove in current_tags:
                current_tags = set(current_tags)
                current_tags.discard(tag_to_remove)
                self.file_tags[fp] = current_tags
                updated_count += 1
            # Update entry widget regardless (to reflect any changes)
            tag_var = self.file_tag_vars.get(fp)
            if tag_var is not None:
                tag_var.set(", ".join(sorted(self.file_tags[fp])))
        messagebox.showinfo("Remove Tag", f"Removed tag '{tag_to_remove}' from {updated_count} file(s).")
        if self.sidebar_visible:
            self.update_sidebar()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProjectLogger(root)
    root.mainloop()