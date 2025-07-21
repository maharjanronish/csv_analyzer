import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class ScrollableFrame(tk.Frame):
    """A scrollable frame class with mouse wheel support."""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)

        self.canvas = tk.Canvas(self, height=400, highlightthickness=0, bg="#f0f0f0")
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f0f0f0")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel) 
        self.canvas.bind_all("<Button-5>", self._on_mousewheel) 

    def _on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")

class CSVAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Analyzer")
        self.root.geometry("850x750")
        self.root.configure(bg="white")
        self.df = None

        self.style = ttk.Style(self.root)
        self.style.theme_use('clam')

        # Define base button style
        self.style.configure("Glass.TButton",
                             foreground="#ffffff",
                             background="#3a86ff",
                             borderwidth=1,
                             focusthickness=3,
                             focuscolor='none',
                             font=("Segoe UI", 11, "bold"),
                             padding=8,
                             relief="flat")

        self.style.map("Glass.TButton",
                       background=[("active", "#2c6cd1"), ("!active", "#3a86ff")],
                       relief=[("active", "raised"), ("!active", "flat")],
                       bordercolor=[("active", "#1f4f8b"), ("!active", "#3a86ff")])

        # --- WATERMARK TOP ---
        self.top_watermark = tk.Label(root, text="Made by Ronish Maharjan",
                                  font=("Segoe UI", 10, "italic"), fg="gray", bg="white")
        self.top_watermark.pack(side="top", pady=5)

        # Initial centered upload button frame
        self.upload_frame = tk.Frame(root, bg="white")
        self.upload_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title above upload button (centered)
        self.upload_title = tk.Label(self.upload_frame, text="CSV Analyzer",
                                     font=("Segoe UI", 20, "bold"), fg="#3a86ff", bg="white")
        self.upload_title.pack(pady=(0,15))

        self.upload_btn = ttk.Button(self.upload_frame, text="Upload CSV", style="Glass.TButton",
                                     command=self.load_csv)
        self.upload_btn.pack(ipadx=30, ipady=12)

        # Features Frame hidden initially
        self.features_frame = tk.Frame(root, bg="white")

        # Title label above feature buttons
        self.features_title = tk.Label(self.features_frame, text="Available Features",
                                       font=("Segoe UI", 20, "bold"), fg="#3a86ff", bg="white")
        self.features_title.pack(pady=(10, 0))

        # Buttons frame in features frame - 3 column grid
        self.features_btn_frame = tk.Frame(self.features_frame, bg="white")
        self.features_btn_frame.pack(pady=15, padx=10, anchor="center")

        self.buttons_data = [
            ("Upload CSV", self.load_csv),
            ("Show Columns", self.toggle_show_columns_section),
            ("Show Column Data", self.toggle_show_column_data_section),
            ("Add Column", self.toggle_add_column_section),
            ("Add Row", self.toggle_add_row_section),
            ("Export CSV", self.export_csv),
            ("Visualize Data", self.toggle_visualize_section),
        ]
        self.feature_buttons = []
        for i, (text, cmd) in enumerate(self.buttons_data):
            btn = ttk.Button(self.features_btn_frame, text=text, style="Glass.TButton", command=cmd)
            btn.grid(row=i//3, column=i%3, padx=10, pady=8, sticky="ew")
            self.feature_buttons.append(btn)

        self.sections_scrollable = ScrollableFrame(self.features_frame)
        self.sections_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        container = self.sections_scrollable.scrollable_frame

        self.show_columns_section = tk.Frame(container, relief=tk.RIDGE, borderwidth=2, bg="white")
        self._add_section_title(self.show_columns_section, "Available Columns", self.toggle_show_columns_section)
        self.columns_listbox = tk.Listbox(self.show_columns_section, height=15, font=("Segoe UI", 10))
        self.columns_listbox.pack(fill="both", expand=True, padx=15, pady=8)
        self.show_columns_section.pack_forget()

        self.show_column_data_section = tk.Frame(container, relief=tk.RIDGE, borderwidth=2, bg="white")
        self._add_section_title(self.show_column_data_section, "Select Columns to Show Data", self.toggle_show_column_data_section)
        self.checkbox_frame = tk.Frame(self.show_column_data_section, bg="white")
        self.checkbox_frame.pack(fill="x", padx=15)
        self.show_data_btn = ttk.Button(self.show_column_data_section, text="Show Selected Column Data",
                                        command=self.show_selected_column_data, style="Glass.TButton")
        self.show_data_btn.pack(pady=8)
        self.column_data_text = tk.Text(self.show_column_data_section, height=20, font=("Segoe UI", 10))
        self.column_data_text.pack(fill="both", expand=True, padx=15, pady=10)
        self.show_column_data_section.pack_forget()
        self.checkbox_vars = []

        self.add_column_section = tk.Frame(container, relief=tk.RIDGE, borderwidth=2, bg="white")
        self._add_section_title(self.add_column_section, "Add New Column", self.toggle_add_column_section)
        add_col_frame = tk.Frame(self.add_column_section, bg="white")
        add_col_frame.pack(pady=20, padx=20, fill="x")

        tk.Label(add_col_frame, text="Column Name:", font=("Segoe UI", 12), bg="white").grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.new_col_name_entry = tk.Entry(add_col_frame, width=30, font=("Segoe UI", 12))
        self.new_col_name_entry.grid(row=0, column=1, pady=8, padx=5, sticky="w")

        tk.Label(add_col_frame, text="Default Value:", font=("Segoe UI", 12), bg="white").grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.new_col_default_entry = tk.Entry(add_col_frame, width=30, font=("Segoe UI", 12))
        self.new_col_default_entry.grid(row=1, column=1, pady=8, padx=5, sticky="w")

        ttk.Button(self.add_column_section, text="Add Column", command=self.add_column, style="Glass.TButton").pack(pady=15)
        self.add_column_section.pack_forget()

        self.add_row_section = tk.Frame(container, relief=tk.RIDGE, borderwidth=2, bg="white")
        self._add_section_title(self.add_row_section, "Add New Row", self.toggle_add_row_section)
        self.row_checkbox_frame = tk.Frame(self.add_row_section, bg="white")
        self.row_checkbox_frame.pack(fill="x", padx=20, pady=15)

        ttk.Button(self.add_row_section, text="Add Row", command=self.add_row, style="Glass.TButton").pack(pady=15)
        self.add_row_section.pack_forget()

        self.row_entry_widgets = {}

        self.visualize_section = tk.Frame(container, relief=tk.RIDGE, borderwidth=2, bg="white")
        self._add_section_title(self.visualize_section, "Visualize Data", self.toggle_visualize_section)

        self.visualize_column_var = tk.StringVar()
        self.visualize_dropdown = None
        self.visualize_label = None  

        self.visualize_buttons_title = tk.Label(self.visualize_section, text="Select Chart Type",
                                                font=("Segoe UI", 14, "bold"), fg="#3a86ff", bg="white")

        self.visualize_btn_frame = tk.Frame(self.visualize_section, bg="white")
        self.visualize_canvas_frame = tk.Frame(self.visualize_section, bg="white")

        self.visualize_section.pack_forget()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.canvas_obj = None

    def _add_section_title(self, frame, title_text, close_command):
        title_frame = tk.Frame(frame, bg="white")
        title_frame.pack(fill="x", pady=6)
        tk.Label(title_frame, text=title_text, font=("Segoe UI", 14, "bold"), bg="white").pack(side="left", padx=10)
        close_btn = tk.Button(title_frame, text="X", fg="red", font=("Segoe UI", 14, "bold"), command=close_command, bg="white", bd=0)
        close_btn.pack(side="right", padx=10)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        try:
            self.df = pd.read_csv(file_path)
            self.upload_frame.place_forget()
            self.features_frame.pack(fill="both", expand=True, padx=15, pady=10)

            self.columns_listbox.delete(0, tk.END)
            for col in self.df.columns:
                self.columns_listbox.insert(tk.END, col)

            self.setup_checkboxes()
            self.setup_row_entries()
            self.setup_visualize_dropdown()

            self.column_data_text.delete(1.0, tk.END)
            for _, var in self.checkbox_vars:
                var.set(False)
            for var, entry in self.row_entry_widgets.values():
                var.set(False)
                entry.delete(0, tk.END)

            for sec in [self.show_columns_section, self.show_column_data_section,
                        self.add_column_section, self.add_row_section, self.visualize_section]:
                sec.pack_forget()

            messagebox.showinfo("Success", f"Loaded CSV with {len(self.df)} rows and {len(self.df.columns)} columns.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def toggle_show_columns_section(self):
        self._toggle_section(self.show_columns_section)

    def toggle_show_column_data_section(self):
        self._toggle_section(self.show_column_data_section)

    def toggle_add_column_section(self):
        self._toggle_section(self.add_column_section)

    def toggle_add_row_section(self):
        self._toggle_section(self.add_row_section)

    def toggle_visualize_section(self):
        self._toggle_section(self.visualize_section)

    def _toggle_section(self, section):
        if section.winfo_ismapped():
            section.pack_forget()
        else:
            for sec in [self.show_columns_section, self.show_column_data_section, self.add_column_section,
                        self.add_row_section, self.visualize_section]:
                if sec != section:
                    sec.pack_forget()
            section.pack(fill="both", expand=True, padx=10, pady=5)

    def setup_checkboxes(self):
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        if self.df is None:
            return

        cols = list(self.df.columns)
        for i, col in enumerate(cols):
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(self.checkbox_frame, text=col, variable=var, bg="white")
            cb.grid(row=i//3, column=i%3, sticky="w", padx=10, pady=5)
            self.checkbox_vars.append((col, var))

    def show_selected_column_data(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV loaded.")
            return

        selected_cols = [col for col, var in self.checkbox_vars if var.get()]
        if not selected_cols:
            messagebox.showwarning("Warning", "Select at least one column.")
            return

        display_df = self.df[selected_cols]
        self.column_data_text.delete(1.0, tk.END)
        self.column_data_text.insert(tk.END, display_df.to_string(index=True))

    def add_column(self):
        col_name = self.new_col_name_entry.get().strip()
        default_val = self.new_col_default_entry.get()
        if not col_name:
            messagebox.showwarning("Input Error", "Please enter a column name.")
            return
        if self.df is not None:
            if col_name in self.df.columns:
                messagebox.showwarning("Input Error", "Column already exists.")
                return
            self.df[col_name] = default_val
            messagebox.showinfo("Info", f"Added column '{col_name}'.")
            self.columns_listbox.insert(tk.END, col_name)
            self.setup_checkboxes()
            self.setup_row_entries()
            self.setup_visualize_dropdown()
            self.new_col_name_entry.delete(0, tk.END)
            self.new_col_default_entry.delete(0, tk.END)

    def setup_row_entries(self):
        for widget in self.row_checkbox_frame.winfo_children():
            widget.destroy()
        self.row_entry_widgets.clear()
        if self.df is None:
            return
        cols = list(self.df.columns)
        for i, col in enumerate(cols):
            frame = tk.Frame(self.row_checkbox_frame, bg="white")
            frame.grid(row=i//2, column=i%2, sticky="w", padx=10, pady=5)
            var = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(frame, text=col, variable=var, bg="white")
            cb.pack(side="left")
            entry = tk.Entry(frame, width=25)
            entry.pack(side="left", padx=5)
            self.row_entry_widgets[col] = (var, entry)

    def add_row(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV loaded.")
            return

        checked_cols = [col for col, (var, _) in self.row_entry_widgets.items() if var.get()]
        if not checked_cols:
            messagebox.showwarning("Input Error", "Please select at least one column for new row data.")
            return

        for col in checked_cols:
            _, entry = self.row_entry_widgets[col]
            if entry.get().strip() == "":
                messagebox.showwarning("Input Error", f"Please enter data for column '{col}'.")
                return

        new_row = {}
        for col, (var, entry) in self.row_entry_widgets.items():
            if var.get():
                new_row[col] = entry.get()
            else:
                new_row[col] = ""

        new_row = {k: (v if v is not None else "") for k, v in new_row.items()}
        self.df = pd.concat([self.df, pd.DataFrame([new_row])], ignore_index=True)

        messagebox.showinfo("Info", "New row added.")
        self.setup_checkboxes()
        for var, entry in self.row_entry_widgets.values():
            var.set(False)
            entry.delete(0, tk.END)

    def export_csv(self):
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV loaded.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        try:
            self.df.to_csv(file_path, index=False)
            messagebox.showinfo("Success", f"Exported CSV to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save CSV:\n{e}")

    def setup_visualize_dropdown(self):
        if self.visualize_label:
            self.visualize_label.destroy()
            self.visualize_label = None

        if self.visualize_dropdown:
            self.visualize_dropdown.destroy()
            self.visualize_dropdown = None

        for widget in self.visualize_btn_frame.winfo_children():
            widget.destroy()
        for widget in self.visualize_canvas_frame.winfo_children():
            widget.destroy()

        if self.df is None:
            return

        self.visualize_buttons_title.pack_forget()
        self.visualize_btn_frame.pack_forget()
        self.visualize_canvas_frame.pack_forget()

        cols = list(self.df.columns)
        cols.insert(0, "All Columns")
        self.visualize_column_var.set(cols[0])

        self.visualize_label = ttk.Label(self.visualize_section, text="Select Column:", font=("Segoe UI", 12), background="white")
        self.visualize_label.pack(pady=(5,0))
        self.visualize_dropdown = ttk.OptionMenu(self.visualize_section, self.visualize_column_var, *cols)
        self.visualize_dropdown.pack(pady=5)

        self.visualize_buttons_title.pack(pady=(10, 5))
        self.visualize_btn_frame.pack(pady=5)
        bar_btn = ttk.Button(self.visualize_btn_frame, text="Bar Chart", command=self.show_bar_chart, style="Glass.TButton")
        pie_btn = ttk.Button(self.visualize_btn_frame, text="Pie Chart", command=self.show_pie_chart, style="Glass.TButton")
        bar_btn.grid(row=0, column=0, padx=10)
        pie_btn.grid(row=0, column=1, padx=10)

        self.visualize_canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def show_bar_chart(self):
        self._clear_canvas()
        col = self.visualize_column_var.get()
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV loaded.")
            return

        if col == "All Columns":
            counts = self.df.astype(str).apply(pd.Series.value_counts).sum(axis=1).sort_values(ascending=False).head(10)

            fig, ax = plt.subplots(figsize=(8, 5))
            counts.plot(kind="bar", ax=ax)
            ax.set_title("Top 10 Values Across All Columns")
            ax.set_ylabel("Count")
            ax.set_xlabel("Value")
        else:
            if col not in self.df.columns:
                messagebox.showwarning("Warning", f"Column '{col}' not found.")
                return
            counts = self.df[col].value_counts().head(10)
            fig, ax = plt.subplots(figsize=(8, 5))
            counts.plot(kind="bar", ax=ax)
            ax.set_title(f"Top 10 Values in '{col}'")
            ax.set_ylabel("Count")
            ax.set_xlabel(col)

        self._display_figure(fig)

    def show_pie_chart(self):
        self._clear_canvas()
        col = self.visualize_column_var.get()
        if self.df is None:
            messagebox.showwarning("Warning", "No CSV loaded.")
            return

        if col == "All Columns":
            messagebox.showinfo("Info", "Pie chart for all columns is not supported. Please select a specific column.")
            return
        if col not in self.df.columns:
            messagebox.showwarning("Warning", f"Column '{col}' not found.")
            return

        counts = self.df[col].value_counts().head(10)
        fig, ax = plt.subplots(figsize=(8, 5))
        counts.plot(kind="pie", ax=ax, autopct='%1.1f%%', startangle=140)
        ax.set_ylabel("")
        ax.set_title(f"Distribution of '{col}'")
        self._display_figure(fig)

    def _display_figure(self, fig):
        if self.canvas_obj:
            self.canvas_obj.get_tk_widget().destroy()

        self.canvas_obj = FigureCanvasTkAgg(fig, master=self.visualize_canvas_frame)
        self.canvas_obj.draw()
        self.canvas_obj.get_tk_widget().pack(fill="both", expand=True)
        plt.close(fig)

    def _clear_canvas(self):
        for widget in self.visualize_canvas_frame.winfo_children():
            widget.destroy()

    def on_close(self):
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVAnalyzerApp(root)
    root.mainloop()
