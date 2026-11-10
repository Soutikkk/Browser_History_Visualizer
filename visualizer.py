
    def update_table(self) -> None:
        """Display a limited number of filtered history records."""
        tree = self.tree
        tree.delete(*tree.get_children())

        df = self.filtered_df
        if df is None or df.empty:
            return

        limit = self.DISPLAY_LIMIT
        total = len(df)

        rows = df.iloc[:limit][
            ["title", "url", "visit_time"]
        ].itertuples(index=False, name=None)

        for index, row in enumerate(rows, start=1):
            tree.insert("", "end", values=(index, *row))

        if total > limit:
            tree.insert(
                "",
                "end",
                values=(
                    "...",
                    f"Showing {limit:,} of {total:,} matches",
                    "Refine your search",
                    "",
                ),
            )

    def update_chart(self, data: pd.DataFrame | None) -> None:
        """Update the chart with the 10 most visited domains."""
        ax = self.ax
        ax.clear()

        if data is None or data.empty:
            self._draw_empty_chart()
            return

        domains = data["domain"]
        valid = domains[~domains.isin(self.INVALID_DOMAINS)]

        counts = valid.value_counts().nlargest(10)

        if counts.empty:
            self._draw_empty_chart()
            return

        counts = counts.sort_values()

        ax.barh(
            counts.index,
            counts.to_numpy(),
            height=0.6,
            edgecolor="grey",
        )

        ax.set(
            xlabel="Visits",
            title="Top 10 Most Visited Domains",
        )
        ax.title.set(fontsize=10, fontweight="bold")
        ax.tick_params(axis="both", labelsize=8)

        self._refresh_chart()

    def _draw_empty_chart(self) -> None:
        """Display a placeholder when chart data is unavailable."""
        ax = self.ax
        ax.clear()

        ax.text(
            0.5,
            0.5,
            "No domain data to display\n"
            "Load history to populate chart",
            ha="center",
            va="center",
            color="gray",
            transform=ax.transAxes,
        )

        ax.set_xticks([])
        ax.set_yticks([])

        self._refresh_chart()

    def _refresh_chart(self) -> None:
        """Apply chart styling and schedule a redraw."""
        ax = self.ax

        for side in ("top", "right"):
            ax.spines[side].set_visible(False)

        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _on_close(self) -> None:
        """Cancel pending callbacks and close the application."""
        if self._search_job is not None:
            self.root.after_cancel(self._search_job)
            self._search_job = None

        self.root.destroy()


def main() -> None:
    root = tk.Tk()

    style = ttk.Style(root)

    if "clam" in style.theme_names():
        style.theme_use("clam")

    style.configure(
        "Treeview.Heading",
        font=("Arial", 9, "bold"),
    )
    style.configure(
        "Treeview",
        font=("Arial", 9),
        rowheight=22,
    )

    BrowserHistoryVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
