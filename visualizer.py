        ]

        self.lbl_total_visits.configure(text=f"Total Visits: {len(data):,}")
        self.lbl_unique_domains.configure(
            text=f"Unique Domains: {valid_domains.nunique():,}"
        )

    def update_table(self) -> None:
        """Render only the first DISPLAY_LIMIT matching records."""
        children = self.tree.get_children()
        if children:
            self.tree.delete(*children)

        if self.filtered_df is None:
            return

        visible = self.filtered_df.iloc[: self.DISPLAY_LIMIT]

        # itertuples is generally faster and lighter than iterrows.
        rows = visible[["title", "url", "visit_time"]].itertuples(
            index=False, name=None
        )
        for display_index, (title, url, visit_time) in enumerate(rows, 1):
            self.tree.insert(
                "",
                tk.END,
                values=(display_index, title, url, visit_time),
            )

        total = len(self.filtered_df)
        if total > self.DISPLAY_LIMIT:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    "...",
                    f"[Showing first {self.DISPLAY_LIMIT:,} of {total:,} matches]",
                    "Search to refine results",
                    "",
                ),
            )

    # ------------------------------------------------------------------
    # Chart
    # ------------------------------------------------------------------

    def update_chart(self, data: pd.DataFrame | None) -> None:
        self.ax.clear()

        if data is None or data.empty:
            self._draw_empty_chart()
            return

        domains = data.loc[
            ~data["domain"].isin(self.INVALID_DOMAINS), "domain"
        ]
        top_domains = domains.value_counts().head(10).sort_values()

        if top_domains.empty:
            self._draw_empty_chart()
            return

        self.ax.barh(
            top_domains.index,
            top_domains.values,
            edgecolor="grey",
            height=0.6,
        )
        self.ax.set_xlabel("Visits")
        self.ax.set_title(
            "Top 10 Most Visited Domains", fontsize=10, fontweight="bold"
        )
        self.ax.tick_params(axis="both", labelsize=8)
        self._style_chart()
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _draw_empty_chart(self) -> None:
        self.ax.clear()
        self.ax.text(
            0.5,
            0.5,
            "No domain data to display\nLoad history to populate chart",
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            color="gray",
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self._style_chart()
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _style_chart(self) -> None:
        self.ax.spines["top"].set_visible(False)
        self.ax.spines["right"].set_visible(False)

    def _on_close(self) -> None:
        if self._search_job is not None:
            self.root.after_cancel(self._search_job)
        self.root.destroy()


def main() -> None:
    root = tk.Tk()

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("Treeview.Heading", font=("Arial", 9, "bold"))
    style.configure("Treeview", font=("Arial", 9), rowheight=22)

    BrowserHistoryVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
