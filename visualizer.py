# ==============================================================================
# Browser History Visualizer
# ==============================================================================
# A Python desktop application using Tkinter and Matplotlib to visualize
# browser history loaded from a CSV file.
#
# Prerequisites & Installation:
# -----------------------------
# 1. Install Python 3 (3.8 or newer recommended) from python.org.
# 2. Open your terminal or command prompt and install the required external libraries:
#    pip install pandas matplotlib
#
# How to Run:
# -----------
# Run the script using Python:
#    python visualizer.py
#
# CSV Format Requirements:
# -----------------------
# The selected CSV file must contain the following columns (case-insensitive):
# - url (e.g., https://github.com/Soutikkk)
# - title (e.g., Soutikkk - GitHub)
# - visit_time (e.g., 2026-06-19 09:10:00)
# ==============================================================================

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from urllib.parse import urlparse
import pandas as pd

# Import Matplotlib and configure the Tkinter backend
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class BrowserHistoryVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Browser History Visualizer")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        # Application state variables
        self.df = None          # Complete loaded DataFrame
        self.filtered_df = None # Filtered DataFrame based on search query
        self.filepath = ""      # Path of the loaded CSV file
        
        # Keep track of sorting options
        self.sort_col = None
        self.sort_ascending = True

        # Initialize the User Interface
        self.setup_ui()

    def setup_ui(self):
        """Creates and layouts all GUI components."""
        # Main layout frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ----------------- TOP PANEL (Stats & File Selection) -----------------
        top_frame = ttk.LabelFrame(main_frame, text="Controls & Overview", padding="10")
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # File Selection row
        file_row = ttk.Frame(top_frame)
        file_row.pack(fill=tk.X, pady=5)

        self.btn_load = ttk.Button(file_row, text="Load CSV File", command=self.select_file)
        self.btn_load.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_filepath = ttk.Label(file_row, text="No CSV file loaded. Please click 'Load CSV File'.", font=("Arial", 9, "italic"))
        self.lbl_filepath.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Stats displays
        stats_row = ttk.Frame(top_frame)
        stats_row.pack(fill=tk.X, pady=(10, 5))

        self.lbl_total_visits = ttk.Label(stats_row, text="Total Visits: 0", font=("Arial", 11, "bold"))
        self.lbl_total_visits.pack(side=tk.LEFT, padx=(0, 30))

        self.lbl_unique_domains = ttk.Label(stats_row, text="Unique Domains: 0", font=("Arial", 11, "bold"))
        self.lbl_unique_domains.pack(side=tk.LEFT, padx=(0, 30))

        # Search Bar
        search_label = ttk.Label(stats_row, text="Search (URL/Title):", font=("Arial", 10))
        search_label.pack(side=tk.LEFT, padx=(30, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)
        self.entry_search = ttk.Entry(stats_row, textvariable=self.search_var, width=30)
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # ----------------- BOTTOM PANEL (Table & Chart split) -----------------
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Left Frame: History Table
        table_frame = ttk.LabelFrame(bottom_frame, text="History Logs", padding="5")
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Setup Table (Treeview)
        cols = ("Index", "Title", "URL", "Visit Time")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")
        
        # Define Headings and click events for sorting
        self.tree.heading("Index", text="#", command=lambda: self.sort_by_column("index"))
        self.tree.heading("Title", text="Title", command=lambda: self.sort_by_column("title"))
        self.tree.heading("URL", text="URL", command=lambda: self.sort_by_column("url"))
        self.tree.heading("Visit Time", text="Visit Time", command=lambda: self.sort_by_column("visit_time"))

        # Setup Column widths and anchors
        self.tree.column("Index", width=50, minwidth=40, anchor=tk.CENTER)
        self.tree.column("Title", width=250, minwidth=150, anchor=tk.W)
        self.tree.column("URL", width=250, minwidth=150, anchor=tk.W)
        self.tree.column("Visit Time", width=150, minwidth=120, anchor=tk.CENTER)

        # Scrollbars for the Treeview
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Pack Treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Right Frame: Domain Bar Chart
        self.chart_frame = ttk.LabelFrame(bottom_frame, text="Top 10 Most Visited Domains", padding="5")
        self.chart_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))

        # Setup blank Matplotlib figure
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.tight_layout()

        # Canvas to integrate Figure with Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Render initially empty chart state
        self.update_chart(pd.DataFrame(columns=["domain"]))

    def select_file(self):
        """Prompt user to choose a CSV file and load it."""
        file_selected = filedialog.askopenfilename(
            title="Select Browser History CSV",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")]
        )
        if file_selected:
            self.load_data(file_selected)

    def load_data(self, filepath):
        """Read data from the CSV, validate columns, and process URLs."""
        try:
            # Read CSV file
            df_raw = pd.read_csv(filepath)

            # Standardize columns to lowercase for flexible matching
            df_raw.columns = [col.strip().lower() for col in df_raw.columns]

            # Verify that required columns exist
            required_cols = ["url", "title", "visit_time"]
            missing_cols = [col for col in required_cols if col not in df_raw.columns]

            if missing_cols:
                raise ValueError(f"Missing required columns: {', '.join(missing_cols)}")

            # Select only required columns and create a copy
            df = df_raw[required_cols].copy()

            # Handle missing or invalid values
            # Drop rows where URL is completely missing or not a string
            df = df.dropna(subset=["url"])
            df["url"] = df["url"].astype(str)

            # Fallback for empty titles
            df["title"] = df["title"].fillna("No Title").astype(str)

            # Convert visit_time to string and fill blank values
            df["visit_time"] = df["visit_time"].fillna("Unknown Time").astype(str)

            # Extract Domain (netloc) from URLs and clean 'www.' prefix
            df["domain"] = df["url"].apply(self.extract_domain)

            # Reset sorting settings when loading a new file
            self.sort_col = None
            self.sort_ascending = True

            # Save state
            self.df = df
            self.filepath = filepath
            
            # Clear search
            self.search_var.set("")

            # Update status labels
            self.lbl_filepath.configure(text=f"Loaded: {os.path.basename(filepath)}")

            # Process data display
            self.apply_filter_and_update()

        except Exception as e:
            messagebox.showerror(
                "Data Load Error",
                f"Failed to load or parse CSV file:\n{str(e)}\n\n"
                "Please check that the file is a valid CSV containing url, title, and visit_time columns."
            )

    def extract_domain(self, url):
        """Helper to safely parse and return the domain name from a URL."""
        try:
            parsed = urlparse(url.strip())
            domain = parsed.netloc or parsed.path
            
            # Extract domain if port is included
            if ":" in domain:
                domain = domain.split(":")[0]

            # Remove common prefixes like 'www.'
            if domain.lower().startswith("www."):
                domain = domain[4:]

            return domain if domain else "Unknown Domain"
        except Exception:
            return "Invalid URL"

    def apply_filter_and_update(self):
        """Filters the dataframe using the search string and updates UI components."""
        if self.df is None:
            return

        query = self.search_var.get().strip().lower()

        if query:
            # Filter rows where URL or Title contains the query
            mask = self.df["url"].str.lower().str.contains(query, na=False) | \
                   self.df["title"].str.lower().str.contains(query, na=False)
            self.filtered_df = self.df[mask].copy()
        else:
            self.filtered_df = self.df.copy()

        # Perform sorting if a column is selected
        if self.sort_col:
            self.filtered_df = self.filtered_df.sort_values(
                by=self.sort_col, 
                ascending=self.sort_ascending, 
                key=lambda col: col.str.lower() if col.name in ["title", "url"] else col
            )

        # Update visual displays
        self.update_stats()
        self.update_table()
        self.update_chart(self.filtered_df)

    def on_search_change(self, *args):
        """Callback triggered when the user types in the search bar."""
        self.apply_filter_and_update()

    def update_stats(self):
        """Computes and updates aggregate history stats."""
        total_visits = len(self.filtered_df)
        
        # Calculate unique domains excluding empty/fallback indicators
        valid_domains = self.filtered_df[~self.filtered_df["domain"].isin(["Unknown Domain", "Invalid URL"])]
        unique_domains = valid_domains["domain"].nunique()

        self.lbl_total_visits.configure(text=f"Total Visits: {total_visits}")
        self.lbl_unique_domains.configure(text=f"Unique Domains: {unique_domains}")

    def update_table(self):
        """Populates the Treeview table with current filtered records."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new rows (limit to first 1000 for responsive UI scrolling performance)
        display_limit = 1000
        records = self.filtered_df.head(display_limit)

        for index, row in records.iterrows():
            self.tree.insert(
                "",
                tk.END,
                values=(
                    index + 1,  # 1-based record index
                    row["title"],
                    row["url"],
                    row["visit_time"]
                )
            )

        # Append visual indicator if list is truncated
        if len(self.filtered_df) > display_limit:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    "...",
                    f"[Showing first {display_limit} of {len(self.filtered_df)} matches]",
                    "Search or filter to refine results",
                    ""
                )
            )

    def sort_by_column(self, col_name):
        """Sets the active sort column, toggles direction, and redraws UI."""
        if self.df is None:
            return

        if self.sort_col == col_name:
            # Toggle direction
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_col = col_name
            self.sort_ascending = True

        self.apply_filter_and_update()

        # Update headings visually to show sort direction
        column_ids = {
            "index": "Index",
            "title": "Title",
            "url": "URL",
            "visit_time": "Visit Time"
        }
        headers = {
            "index": "#",
            "title": "Title",
            "url": "URL",
            "visit_time": "Visit Time"
        }
        for key, text in headers.items():
            arrow = ""
            if key == self.sort_col:
                arrow = " ▲" if self.sort_ascending else " ▼"
            self.tree.heading(column_ids[key], text=f"{text}{arrow}")

    def update_chart(self, data):
        """Generates and draws a horizontal bar chart of the top 10 domains."""
        self.ax.clear()

        # Filter out invalid domain values
        clean_data = data[~data["domain"].isin(["Unknown Domain", "Invalid URL"])]

        # Get top 10 domains by frequency
        top_domains = clean_data["domain"].value_counts().head(10)

        if not top_domains.empty:
            # Sort domain counts ascending to list highest at the top of the horizontal bar chart
            top_domains = top_domains.sort_values(ascending=True)

            # Create horizontal bar plot
            colors = ["#2B6CB0" if i == len(top_domains) - 1 else "#4299E1" for i in range(len(top_domains))]
            self.ax.barh(top_domains.index, top_domains.values, color=colors, edgecolor="grey", height=0.6)

            self.ax.set_xlabel("Visits")
            self.ax.set_title("Top 10 Most Visited Domains", fontsize=10, fontweight="bold")
            
            # Format tick labels to fit cleanly
            self.ax.tick_params(axis="y", labelsize=8)
            self.ax.tick_params(axis="x", labelsize=8)
            
            # Remove top and right spines for a clean minimal aesthetic
            self.ax.spines["top"].set_visible(False)
            self.ax.spines["right"].set_visible(False)
        else:
            self.ax.text(0.5, 0.5, "No domain data to display\nLoad history to populate chart", 
                         ha="center", va="center", transform=self.ax.transAxes, color="gray")
            self.ax.set_xticks([])
            self.ax.set_yticks([])

        self.fig.tight_layout()
        self.canvas.draw()


if __name__ == "__main__":
    # Create the root Tkinter application
    root = tk.Tk()
    
    # Configure grid weights for main window resizing support
    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)
    
    # Apply a modern clean style to the ttk elements
    style = ttk.Style()
    style.theme_use("clam")  # Clam theme offers a clean, cross-platform flat aesthetic

    # Configure custom padding/font styles
    style.configure("Treeview.Heading", font=("Arial", 9, "bold"))
    style.configure("Treeview", font=("Arial", 9), rowheight=22)

    app = BrowserHistoryVisualizer(root)
    root.mainloop()
