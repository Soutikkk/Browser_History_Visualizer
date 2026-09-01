```python
# ==============================================================================
# Browser History Visualizer - Optimized
# ==============================================================================
# A Python desktop application using Tkinter and Matplotlib to visualize
# browser history loaded from a CSV file.
#
# CSV requirements (case-insensitive):
#   url, title, visit_time
#
# Install:
#   pip install pandas matplotlib
#
# Run:
#   python visualizer.py
# ==============================================================================

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from urllib.parse import urlparse

import pandas as pd

# Configure Matplotlib before importing the TkAgg backend.
import matplotlib
matplotlib.use("TkAgg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class BrowserHistoryVisualizer:
    DISPLAY_LIMIT = 1000
    REQUIRED_COLUMNS = ("url", "title", "visit_time")
    INVALID_DOMAINS = frozenset({"Unknown Domain", "Invalid URL"})

    TREE_COLUMNS = ("Index", "Title", "URL", "Visit Time")

    SORT_COLUMN_MAP = {
        "index": "Index",
        "title": "Title",
        "url": "URL",
        "visit_time": "Visit Time",
    }

    def __init__(self, root):
        self.root = root
        self.root.title("Browser History Visualizer")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        # Application state
        self.df = None
        self.filtered_df = None
        self.filepath = ""

        # Sorting state
        self.sort_col = None
        self.sort_ascending = True

        self.setup_ui()

    # --------------------------------------------------------------------------
    # UI
    # --------------------------------------------------------------------------

    def setup_ui(self):
        """Create and configure all GUI components."""
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # ------------------------- Controls & Overview ------------------------

        top_frame = ttk.LabelFrame(
            main_frame,
            text="Controls & Overview",
            padding=10
        )
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        # File selection
        file_row = ttk.Frame(top_frame)
        file_row.pack(fill=tk.X, pady=5)

        self.btn_load = ttk.Button(
            file_row,
            text="Load CSV File",
            command=self.select_file
        )
        self.btn_load.pack(side=tk.LEFT, padx=(0, 10))

        self.lbl_filepath = ttk.Label(
            file_row,
            text="No CSV file loaded. Please click 'Load CSV File'.",
            font=("Arial", 9, "italic")
        )
        self.lbl_filepath.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Stats and search
        stats_row = ttk.Frame(top_frame)
        stats_row.pack(fill=tk.X, pady=(10, 5))

        self.lbl_total_visits = ttk.Label(
            stats_row,
            text="Total Visits: 0",
            font=("Arial", 11, "bold")
        )
        self.lbl_total_visits.pack(side=tk.LEFT, padx=(0, 30))

        self.lbl_unique_domains = ttk.Label(
            stats_row,
            text="Unique Domains: 0",
            font=("Arial", 11, "bold")
        )
        self.lbl_unique_domains.pack(side=tk.LEFT, padx=(0, 30))

        ttk.Label(
            stats_row,
            text="Search (URL/Title):",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(30, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.on_search_change)

        self.entry_search = ttk.Entry(
            stats_row,
            textvariable=self.search_var,
            width=30
        )
        self.entry_search.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True
        )

        # ------------------------- Table & Chart -------------------------------

        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(
            fill=tk.BOTH,
            expand=True,
            pady=10
        )

        # History table
        table_frame = ttk.LabelFrame(
            bottom_frame,
            text="History Logs",
            padding=5
        )
        table_frame.pack(
            side=tk.LEFT,
            fill=tk.BOTH,
            expand=True,
            padx=(0, 5)
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.TREE_COLUMNS,
            show="headings",
            selectmode="browse"
        )

        # Headings
        for column, sort_key, title in (
            ("Index", "index", "#"),
            ("Title", "title", "Title"),
            ("URL", "url", "URL"),
            ("Visit Time", "visit_time", "Visit Time"),
        ):
            self.tree.heading(
                column,
                text=title,
                command=lambda key=sort_key: self.sort_by_column(key)
            )

        # Column configuration
        column_config = {
            "Index": (50, 40, tk.CENTER),
            "Title": (250, 150, tk.W),
            "URL": (250, 150, tk.W),
            "Visit Time": (150, 120, tk.CENTER),
        }

        for column, (width, minwidth, anchor) in column_config.items():
            self.tree.column(
                column,
                width=width,
                minwidth=minwidth,
                anchor=anchor
            )

        # Scrollbars
        vsb = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )
        hsb = ttk.Scrollbar(
            table_frame,
            orient="horizontal",
            command=self.tree.xview
        )

        self.tree.configure(
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Chart
        self.chart_frame = ttk.LabelFrame(
            bottom_frame,
            text="Top 10 Most Visited Domains",
            padding=5
        )
        self.chart_frame.pack(
            side=tk.RIGHT,
            fill=tk.BOTH,
            expand=True,
            padx=(5, 0)
        )

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(
            self.fig,
            master=self.chart_frame
        )
        self.canvas.get_tk_widget().pack(
            fill=tk.BOTH,
            expand=True
        )

        self.update_chart(None)

    # --------------------------------------------------------------------------
    # File handling
    # --------------------------------------------------------------------------

    def select_file(self):
        """Prompt the user to select a CSV file."""
        filepath = filedialog.askopenfilename(
            title="Select Browser History CSV",
            filetypes=[
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        )

        if filepath:
            self.load_data(filepath)

    def load_data(self, filepath):
        """Load, validate, clean, and prepare CSV data."""
        try:
            df = pd.read_csv(filepath)

            # Normalize column names once.
            df.columns = (
                df.columns
                .str.strip()
                .str.lower()
            )

            missing = set(self.REQUIRED_COLUMNS) - set(df.columns)

            if missing:
                missing_text = ", ".join(sorted(missing))
                raise ValueError(
                    f"Missing required columns: {missing_text}"
                )

            # Keep only columns required by the application.
            df = df.loc[:, self.REQUIRED_COLUMNS].copy()

            # Remove rows without URLs.
            df = df.dropna(subset=["url"])

            # Normalize values.
            df["url"] = df["url"].astype(str).str.strip()

            df["title"] = (
                df["title"]
                .fillna("No Title")
                .astype(str)
            )

            df["visit_time"] = (
                df["visit_time"]
                .fillna("Unknown Time")
                .astype(str)
            )

            # Remove empty URL rows after string conversion.
            df = df[df["url"].ne("")]

            # Extract domains once.
            df["domain"] = df["url"].map(self.extract_domain)

            # Precompute searchable lowercase values.
            # This is significantly faster than lowercasing the entire
            # URL/title columns on every keystroke.
            df["_url_search"] = df["url"].str.lower()
            df["_title_search"] = df["title"].str.lower()

            # Reset application state.
            self.df = df
            self.filtered_df = df
            self.filepath = filepath

            self.sort_col = None
            self.sort_ascending = True

            self.search_var.set("")

            self.lbl_filepath.configure(
                text=f"Loaded: {os.path.basename(filepath)}"
            )

            self.apply_filter_and_update()

        except Exception as exc:
            messagebox.showerror(
                "Data Load Error",
                f"Failed to load or parse CSV file:\n"
                f"{exc}\n\n"
                "Please check that the file is a valid CSV containing "
                "url, title, and visit_time columns."
            )

    # --------------------------------------------------------------------------
    # Data processing
    # --------------------------------------------------------------------------

    @staticmethod
    def extract_domain(url):
        """Safely extract and normalize a domain from a URL."""
        try:
            url = url.strip()

            if not url:
                return "Unknown Domain"

            # urlparse treats URLs without a scheme as paths.
            # Add // so domains such as example.com are recognized.
            parsed = urlparse(
                url if "://" in url else f"//{url}",
                scheme=""
            )

            domain = parsed.netloc

            if not domain:
                return "Unknown Domain"

            # Remove optional port.
            domain = domain.split(":", 1)[0].lower()

            # Remove www.
            if domain.startswith("www."):
                domain = domain[4:]

            return domain or "Unknown Domain"

        except (ValueError, AttributeError):
            return "Invalid URL"

    def apply_filter_and_update(self):
        """Apply search/sorting and refresh all UI components."""
        if self.df is None:
            return

        query = self.search_var.get().strip().lower()

        if query:
            mask = (
                self.df["_url_search"].str.contains(
                    query,
                    regex=False,
                    na=False
                )
                |
                self.df["_title_search"].str.contains(
                    query,
                    regex=False,
                    na=False
                )
            )

            filtered = self.df.loc[mask]
        else:
            filtered = self.df

        # Sort only when requested.
        if self.sort_col:
            sort_column = self.sort_col

            # Use precomputed lowercase values for case-insensitive
            # text sorting without modifying the displayed data.
            if sort_column == "title":
                filtered = filtered.sort_values(
                    by="_title_search",
                    ascending=self.sort_ascending,
                    kind="stable"
                )

            elif sort_column == "url":
                filtered = filtered.sort_values(
                    by="_url_search",
                    ascending=self.sort_ascending,
                    kind="stable"
                )

            elif sort_column == "index":
                # Original CSV order.
                filtered = filtered.sort_index(
                    ascending=self.sort_ascending
                )

            else:
                filtered = filtered.sort_values(
                    by=sort_column,
                    ascending=self.sort_ascending,
                    kind="stable"
                )

        self.filtered_df = filtered

        self.update_stats()
        self.update_table()
        self.update_chart(filtered)

    # --------------------------------------------------------------------------
    # Search
    # --------------------------------------------------------------------------

    def on_search_change(self, *_):
        """Refresh results when the search text changes."""
        self.apply_filter_and_update()

    # --------------------------------------------------------------------------
    # Statistics
    # --------------------------------------------------------------------------

    def update_stats(self):
        """Update aggregate statistics."""
        if self.filtered_df is None:
            return

        total_visits = len(self.filtered_df)

        valid_domains = self.filtered_df.loc[
            ~self.filtered_df["domain"].isin(self.INVALID_DOMAINS),
            "domain"
        ]

        unique_domains = valid_domains.nunique()

        self.lbl_total_visits.configure(
            text=f"Total Visits: {total_visits}"
        )

        self.lbl_unique_domains.configure(
            text=f"Unique Domains: {unique_domains}"
        )

    # --------------------------------------------------------------------------
    # Table
    # --------------------------------------------------------------------------

    def update_table(self):
        """Refresh the Treeview with the current filtered records."""
        # Remove existing rows efficiently.
        children = self.tree.get_children()

        if children:
            self.tree.delete(*children)

        if self.filtered_df is None:
            return

        records = self.filtered_df.iloc[:self.DISPLAY_LIMIT]

        # Enumerate displayed rows so numbering remains correct after
        # filtering and sorting.
        for display_index, row in enumerate(records.itertuples(), start=1):
            self.tree.insert(
                "",
                tk.END,
                values=(
                    display_index,
                    row.title,
                    row.url,
                    row.visit_time
                )
            )

        # Display truncation indicator.
        total = len(self.filtered_df)

        if total > self.DISPLAY_LIMIT:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    "...",
                    f"[Showing first {self.DISPLAY_LIMIT} of {total} matches]",
                    "Search or filter to refine results",
                    ""
                )
            )

    # --------------------------------------------------------------------------
    # Sorting
    # --------------------------------------------------------------------------

    def sort_by_column(self, col_name):
        """Toggle sorting direction and refresh the interface."""
        if self.df is None:
            return

        if self.sort_col == col_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_col = col_name
            self.sort_ascending = True

        self.update_sort_headings()
        self.apply_filter_and_update()

    def update_sort_headings(self):
        """Update Treeview headings with sort direction indicators."""
        for key, column in self.SORT_COLUMN_MAP.items():
            titles = {
                "index": "#",
                "title": "Title",
                "url": "URL",
                "visit_time": "Visit Time",
            }

            arrow = ""

            if key == self.sort_col:
                arrow = " ▲" if self.sort_ascending else " ▼"

            self.tree.heading(
                column,
                text=f"{titles[key]}{arrow}"
            )

    # --------------------------------------------------------------------------
    # Chart
    # --------------------------------------------------------------------------

    def update_chart(self, data):
        """Draw a horizontal chart of the top 10 domains."""
        self.ax.clear()

        if data is None or data.empty:
            self.show_empty_chart()
            self.canvas.draw_idle()
            return

        clean_domains = data.loc[
            ~data["domain"].isin(self.INVALID_DOMAINS),
            "domain"
        ]

        top_domains = (
            clean_domains
            .value_counts()
            .head(10)
            .sort_values()
        )

        if top_domains.empty:
            self.show_empty_chart()
            self.canvas.draw_idle()
            return

        # Keep chart styling simple and let Matplotlib manage colors.
        self.ax.barh(
            top_domains.index,
            top_domains.values,
            edgecolor="grey",
            height=0.6
        )

        self.ax.set_xlabel("Visits")
        self.ax.set_title(
            "Top 10 Most Visited Domains",
            fontsize=10,
            fontweight="bold"
        )

        self.ax.tick_params(axis="y", labelsize=8)
        self.ax.tick_params(axis="x", labelsize=8)

        # Clean up unnecessary borders.
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

        self.fig.tight_layout()
        self.canvas.draw_idle()

    def show_empty_chart(self):
        """Display the empty chart state."""
        self.ax.text(
            0.5,
            0.5,
            "No domain data to display\nLoad history to populate chart",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            color="gray"
        )

        self.ax.set_xticks([])
        self.ax.set_yticks([])

        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)


# ==============================================================================
# Application entry point
# ==============================================================================

def main():
    root = tk.Tk()

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    style = ttk.Style()

    try:
        style.theme_use("clam")
    except tk.TclError:
        # Fall back to the platform default if Clam is unavailable.
        pass

    style.configure(
        "Treeview.Heading",
        font=("Arial", 9, "bold")
    )

    style.configure(
        "Treeview",
        font=("Arial", 9),
        rowheight=22
    )

    BrowserHistoryVisualizer(root)

    root.mainloop()


if __name__ == "__main__":
    main()
```
