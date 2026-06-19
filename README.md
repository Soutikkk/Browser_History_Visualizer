# Browser History Visualizer 🌐📊

A clean, minimal, and lightweight Python desktop application built with **Tkinter** and **Matplotlib** to parse, filter, and visualize browser history data directly from a CSV file.

No complex setup, databases, or local servers are required—just load a CSV file and immediately see statistics, sort history tables, filter logs dynamically, and visualize domain frequencies!

---

## Features 🚀

- **Simple File Loader**: Easily load any browser history export CSV with standard columns (`url`, `title`, `visit_time`).
- **Interactive Data Table**: View your browser history in a clean, scrollable tabular format.
- **Dynamic Sortable Columns**: Click on any column header (`#`, `Title`, `URL`, `Visit Time`) to instantly sort the rows in ascending or descending order.
- **Real-time Search & Filtering**: Type queries into the search bar to filter history logs by page title or URL. The table and domain statistics/chart update instantly.
- **At-a-Glance Metrics**: View the **Total Visits** and **Unique Domains** for the current search/filter state.
- **Matplotlib Visualization**: View a clean, embedded horizontal bar chart displaying the **Top 10 Most Visited Domains** in real-time.
- **Robust Error Handling**: Gracefully handles missing column values, invalid rows, or formatting inconsistencies.

---

## Installation & Setup 🛠️

### Prerequisites
Make sure you have **Python 3.8+** installed on your system. You can verify your version by running:
```bash
python --version
```

### 1. Clone the Repository
Clone this repository to your local machine:
```bash
git clone https://github.com/Soutikkk/Browser_History_Visualizer.git
cd Browser_History_Visualizer
```

### 2. Install Dependencies
Install the required packages using `pip`:
```bash
pip install pandas matplotlib
```

---

## How to Run 💻

Start the desktop visualizer application by running:
```bash
python visualizer.py
```

---

## CSV Data Requirements 📁

Your CSV history file should contain the following three headers (case-insensitive):
- **`url`**: The fully qualified web address (e.g., `https://github.com/Soutikkk`).
- **`title`**: The title of the visited webpage (e.g., `Soutikkk - GitHub`).
- **`visit_time`**: The time the website was visited. This can be in standard timestamp format (`YYYY-MM-DD HH:MM:SS`) or generic string format.

### Sample CSV Template
```csv
url,title,visit_time
https://www.google.com/search?q=python,Google Search - python,2026-06-19 09:00:00
https://github.com/Soutikkk/Browser_History_Visualizer,Soutikkk/Browser_History_Visualizer GitHub,2026-06-19 09:10:00
https://stackoverflow.com/questions,Newest Questions - Stack Overflow,2026-06-19 09:15:00
https://wikipedia.org/wiki/Tkinter,Tkinter - Wikipedia,2026-06-19 09:46:00
```
*Note: A sample file named `sample_history.csv` is included in this repository for you to try immediately.*

---

## Application Walkthrough & Architecture 🏛️

The application uses standard components to deliver high responsiveness:
1. **Pandas Engine**: Automatically handles standard CSV loading, drops completely blank URL rows, processes fallback page titles (e.g., `"No Title"`), and parses domains using Python's robust `urllib.parse` library.
2. **Tkinter & TTK**: Built using the modern, clean `clam` theme styling, featuring robust column-width adjustments and custom grid frames that resize perfectly as you expand or shrink the window.
3. **Embedded Matplotlib**: Updates a horizontal bar chart on-the-fly. The chart sorts domains by frequency and displays them from highest (top) to lowest, avoiding vertical clutter.

---

## License 📄

This project is licensed under the MIT License. Feel free to copy, modify, and distribute it.
