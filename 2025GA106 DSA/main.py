import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
import os
import random
import copy
import time

from sorting_algorithms import ALGORITHMS, _val
from searching_algorithms import SEARCH_ALGORITHMS, STRING_FILTERS, NUMERIC_FILTERS, multi_column_search
from scraper import ProductScraper, save_products, load_products

COLUMNS = ["id", "name", "brand", "category", "price", "rating", "stock", "discount", "description", "sku"]
NUMERIC_COLS = {"id", "price", "rating", "stock", "discount"}
DATA_FILE = "products_data.json"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CS200 DSA Project - Product Manager")
        self.root.geometry("1350x820")
        self.all_products = []
        self.filtered_products = []
        self.is_filtered = False
        self.scraper = None
        self.multi_sort_rows = []
        self.multi_search_rows = []
        self.build_ui()
        self.try_load()

    def build_ui(self):
        top = ttk.LabelFrame(self.root, text="Scraper")
        top.pack(fill="x", padx=5, pady=3)
        self.build_scraper(top)

        mid = ttk.PanedWindow(self.root, orient="horizontal")
        mid.pack(fill="both", expand=True, padx=5, pady=3)

        nb = ttk.Notebook(mid)
        nb.add(self.build_sort_tab(nb), text="Sort")
        nb.add(self.build_search_tab(nb), text="Search")
        nb.add(self.build_multi_sort_tab(nb), text="Multi-Sort")
        nb.add(self.build_multi_search_tab(nb), text="Multi-Search")
        nb.add(self.build_benchmark_tab(nb), text="Benchmark")
        mid.add(nb, weight=0)

        tf = ttk.Frame(mid)
        mid.add(tf, weight=1)
        self.build_table(tf)

        self.metrics_var = tk.StringVar(value="Metrics will appear here after sorting or searching.")
        ttk.Label(self.root, textvariable=self.metrics_var, relief="sunken",
                  anchor="w", padding=5).pack(fill="x", padx=5, pady=2)

        self.status_var = tk.StringVar(value="Ready - no products loaded")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken",
                  anchor="w", padding=3).pack(fill="x", padx=5, pady=(0, 3))

    def build_scraper(self, parent):
        ttk.Label(parent, text="URL:").pack(side="left", padx=2)
        self.url_var = tk.StringVar()
        ttk.Entry(parent, textvariable=self.url_var, width=35).pack(side="left", padx=2)

        ttk.Label(parent, text="Count:").pack(side="left", padx=2)
        self.count_var = tk.IntVar(value=15000)
        ttk.Spinbox(parent, from_=1000, to=50000, increment=1000,
                     textvariable=self.count_var, width=7).pack(side="left", padx=2)

        self.btn_scrape = ttk.Button(parent, text="▶ Scrape", command=self.on_scrape)
        self.btn_scrape.pack(side="left", padx=2)
        self.btn_pause = ttk.Button(parent, text="⏸ Pause", command=self.on_pause, state="disabled")
        self.btn_pause.pack(side="left", padx=2)
        self.btn_resume = ttk.Button(parent, text="▶ Resume", command=self.on_resume, state="disabled")
        self.btn_resume.pack(side="left", padx=2)
        self.btn_stop = ttk.Button(parent, text="⏹ Stop", command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left", padx=2)
        ttk.Button(parent, text="💾 Save", command=self.on_save).pack(side="left", padx=2)
        ttk.Button(parent, text="📂 Load", command=self.on_load).pack(side="left", padx=2)

        self.progress = ttk.Progressbar(parent, length=200, mode="determinate")
        self.progress.pack(side="left", padx=5, fill="x", expand=True)
        self.prog_label = ttk.Label(parent, text="0/0")
        self.prog_label.pack(side="left", padx=2)

    def build_table(self, parent):
        cols = COLUMNS
        self.tree = ttk.Treeview(parent, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c.upper())
            w = 60 if c in NUMERIC_COLS else 120
            if c == "description":
                w = 200
            self.tree.column(c, width=w, minwidth=40)

        vsb = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(parent, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

    def build_sort_tab(self, parent):
        f = ttk.Frame(parent, padding=10)

        ttk.Label(f, text="Column:").pack(anchor="w")
        self.sort_col = ttk.Combobox(f, values=COLUMNS, state="readonly", width=20)
        self.sort_col.set(COLUMNS[0])
        self.sort_col.pack(fill="x", pady=2)

        ttk.Label(f, text="Algorithm:").pack(anchor="w")
        self.sort_algo = ttk.Combobox(f, values=list(ALGORITHMS.keys()), state="readonly", width=20)
        self.sort_algo.set(list(ALGORITHMS.keys())[0])
        self.sort_algo.pack(fill="x", pady=2)

        ttk.Label(f, text="Sort Scope:").pack(anchor="w", pady=(8, 0))
        self.scope_var = tk.StringVar(value="full")
        ttk.Radiobutton(f, text="Full dataset", variable=self.scope_var, value="full").pack(anchor="w")
        ttk.Radiobutton(f, text="Filtered results only", variable=self.scope_var, value="filtered").pack(anchor="w")

        bf = ttk.Frame(f)
        bf.pack(fill="x", pady=10)
        ttk.Button(bf, text="Sort ▲ Ascending", command=lambda: self.on_sort(False)).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(bf, text="Sort ▼ Descending", command=lambda: self.on_sort(True)).pack(side="left", expand=True, fill="x", padx=2)

        return f

    def build_search_tab(self, parent):
        f = ttk.Frame(parent, padding=10)

        ttk.Label(f, text="Column:").pack(anchor="w")
        self.search_col = ttk.Combobox(f, values=COLUMNS, state="readonly", width=20)
        self.search_col.set(COLUMNS[1])
        self.search_col.bind("<<ComboboxSelected>>", self.update_filters)
        self.search_col.pack(fill="x", pady=2)

        ttk.Label(f, text="Filter type:").pack(anchor="w")
        self.search_filter = ttk.Combobox(f, values=STRING_FILTERS, state="readonly", width=20)
        self.search_filter.set(STRING_FILTERS[0])
        self.search_filter.pack(fill="x", pady=2)

        ttk.Label(f, text="Algorithm:").pack(anchor="w")
        self.search_algo = ttk.Combobox(f, values=list(SEARCH_ALGORITHMS.keys()), state="readonly", width=20)
        self.search_algo.set(list(SEARCH_ALGORITHMS.keys())[0])
        self.search_algo.pack(fill="x", pady=2)

        ttk.Label(f, text="Search value:").pack(anchor="w")
        self.search_val = ttk.Entry(f, width=25)
        self.search_val.pack(fill="x", pady=2)

        bf = ttk.Frame(f)
        bf.pack(fill="x", pady=10)
        ttk.Button(bf, text="🔍 Search", command=self.on_search).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(bf, text="✖ Clear", command=self.on_clear).pack(side="left", expand=True, fill="x", padx=2)

        return f

    def build_multi_sort_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        ttk.Label(f, text="Sort levels (primary → secondary → ...):").pack(anchor="w")

        self.ms_frame = ttk.Frame(f)
        self.ms_frame.pack(fill="both", expand=True, pady=5)

        bf = ttk.Frame(f)
        bf.pack(fill="x")
        ttk.Button(bf, text="+ Add Level", command=self.ms_add).pack(side="left", padx=2)
        ttk.Button(bf, text="- Remove", command=self.ms_remove).pack(side="left", padx=2)
        ttk.Button(bf, text="▶ Apply", command=self.ms_apply).pack(side="left", padx=2)

        self.ms_add()
        return f

    def ms_add(self):
        row = ttk.Frame(self.ms_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"Level {len(self.multi_sort_rows)+1}:").pack(side="left")
        col = ttk.Combobox(row, values=COLUMNS, state="readonly", width=12)
        col.set(COLUMNS[0])
        col.pack(side="left", padx=3)
        order = ttk.Combobox(row, values=["Ascending", "Descending"], state="readonly", width=12)
        order.set("Ascending")
        order.pack(side="left", padx=3)
        self.multi_sort_rows.append((col, order, row))

    def ms_remove(self):
        if len(self.multi_sort_rows) > 1:
            col, order, row = self.multi_sort_rows.pop()
            row.destroy()

    def ms_apply(self):
        if not self.all_products:
            return
        data = copy.deepcopy(self.all_products)
        start = time.perf_counter()
        for col_cb, order_cb, _ in reversed(self.multi_sort_rows):
            c = col_cb.get()
            rev = order_cb.get() == "Descending"
            data.sort(key=lambda x: _val(x, c), reverse=rev)
        ms = (time.perf_counter() - start) * 1000
        self.all_products = data
        self.refresh_table()
        levels = " → ".join(f"{c.get()} ({o.get()})" for c, o, _ in self.multi_sort_rows)
        self.metrics_var.set(f"Multi-Level Sort  |  {levels}  |  Time: {ms:.2f} ms  |  Items: {len(data)}")

    def build_multi_search_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        ttk.Label(f, text="Filter conditions:").pack(anchor="w")

        self.mc_frame = ttk.Frame(f)
        self.mc_frame.pack(fill="both", expand=True, pady=5)

        cf = ttk.LabelFrame(f, text="Combine")
        cf.pack(fill="x", pady=3)
        self.combine_var = tk.StringVar(value="AND")
        ttk.Radiobutton(cf, text="AND", variable=self.combine_var, value="AND").pack(side="left", padx=10)
        ttk.Radiobutton(cf, text="OR", variable=self.combine_var, value="OR").pack(side="left", padx=10)

        bf = ttk.Frame(f)
        bf.pack(fill="x")
        ttk.Button(bf, text="+ Add", command=self.mc_add).pack(side="left", padx=2)
        ttk.Button(bf, text="- Remove", command=self.mc_remove).pack(side="left", padx=2)
        ttk.Button(bf, text="🔍 Apply", command=self.mc_apply).pack(side="left", padx=2)
        ttk.Button(bf, text="✖ Clear", command=self.on_clear).pack(side="left", padx=2)

        self.mc_add()
        return f

    def mc_add(self):
        row = ttk.Frame(self.mc_frame)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=f"F{len(self.multi_search_rows)+1}:").pack(side="left")
        col = ttk.Combobox(row, values=COLUMNS, state="readonly", width=10)
        col.set(COLUMNS[1])
        col.pack(side="left", padx=2)
        ft = ttk.Combobox(row, values=STRING_FILTERS + NUMERIC_FILTERS, state="readonly", width=11)
        ft.set("contains")
        ft.pack(side="left", padx=2)
        val = ttk.Entry(row, width=12)
        val.pack(side="left", padx=2)
        negate_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="NOT", variable=negate_var).pack(side="left", padx=2)
        self.multi_search_rows.append((col, ft, val, negate_var, row))

    def mc_remove(self):
        if len(self.multi_search_rows) > 1:
            col, ft, val, neg, row = self.multi_search_rows.pop()
            row.destroy()

    def mc_apply(self):
        if not self.all_products:
            return
        filters = []
        for col, ft, val, neg, _ in self.multi_search_rows:
            v = val.get().strip()
            if v:
                filters.append({
                    "column": col.get(),
                    "filter_type": ft.get(),
                    "value": v,
                    "negate": neg.get(),
                })
        if not filters:
            messagebox.showwarning("Warning", "Enter at least one filter value.")
            return
        combine = self.combine_var.get()
        result = multi_column_search(self.all_products, filters, combine)
        self.filtered_products = result.data
        self.is_filtered = True
        self.refresh_table()
        self.metrics_var.set(
            f"Multi-Column Search ({combine})  |  Matches: {result.matches_found}  |  Time: {result.time_ms:.2f} ms")
        self.status_var.set(f"Showing {result.matches_found} of {len(self.all_products)} products")

    def build_benchmark_tab(self, parent):
        f = ttk.Frame(parent, padding=10)
        ttk.Label(f, text="Benchmark all 8 algorithms:").pack(anchor="w")

        ttk.Label(f, text="Column:").pack(anchor="w")
        self.bench_col = ttk.Combobox(f, values=COLUMNS, state="readonly", width=20)
        self.bench_col.set("price")
        self.bench_col.pack(fill="x", pady=2)

        ttk.Label(f, text="Sample size:").pack(anchor="w")
        self.bench_size = tk.IntVar(value=5000)
        ttk.Spinbox(f, from_=100, to=50000, increment=1000,
                     textvariable=self.bench_size, width=10).pack(fill="x", pady=2)

        self.btn_bench = ttk.Button(f, text="▶ Run Benchmark", command=self.on_benchmark)
        self.btn_bench.pack(fill="x", pady=5)

        self.bench_text = tk.Text(f, height=15, width=40, font=("Courier", 9), state="disabled")
        self.bench_text.pack(fill="both", expand=True, pady=5)

        return f

    def on_scrape(self):
        url = self.url_var.get().strip() or None
        count = self.count_var.get()
        self.scraper = ProductScraper(target_count=count, url=url)
        self.scraper.start()
        self.btn_scrape.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.btn_stop.config(state="normal")
        self.btn_resume.config(state="disabled")
        self.progress["maximum"] = count
        self.poll_scraper()

    def poll_scraper(self):
        if self.scraper is None:
            return
        self.progress["value"] = self.scraper.current
        self.prog_label.config(text=f"{self.scraper.current}/{self.scraper.target_count}")
        self.status_var.set(self.scraper.status_msg)

        if self.scraper.done:
            if self.scraper.error_msg:
                messagebox.showerror("Error", self.scraper.error_msg)
            else:
                self.all_products = self.scraper.products
                self.is_filtered = False
                self.refresh_table()
                path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
                save_products(self.all_products, path)
                self.status_var.set(f"Loaded {len(self.all_products)} products")
            self.btn_scrape.config(state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="disabled")
            self.btn_stop.config(state="disabled")
            return

        self.root.after(100, self.poll_scraper)

    def on_pause(self):
        if self.scraper:
            self.scraper.pause()
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="normal")

    def on_resume(self):
        if self.scraper:
            self.scraper.resume()
            self.btn_pause.config(state="normal")
            self.btn_resume.config(state="disabled")

    def on_stop(self):
        if self.scraper:
            self.scraper.stop()
            self.btn_scrape.config(state="normal")
            self.btn_pause.config(state="disabled")
            self.btn_resume.config(state="disabled")
            self.btn_stop.config(state="disabled")

    def on_save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                             filetypes=[("JSON", "*.json")])
        if path:
            save_products(self.all_products, path)
            self.status_var.set(f"Saved to {path}")

    def on_load(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if path:
            self.all_products = load_products(path)
            self.is_filtered = False
            self.refresh_table()
            self.status_var.set(f"Loaded {len(self.all_products)} products from file")

    def on_sort(self, reverse):
        data = self.filtered_products if (self.scope_var.get() == "filtered" and self.is_filtered) else self.all_products
        if not data:
            messagebox.showinfo("Info", "No data to sort.")
            return
        algo_name = self.sort_algo.get()
        column = self.sort_col.get()
        func = ALGORITHMS[algo_name]
        self.status_var.set(f"Sorting by {column} using {algo_name}...")
        self.root.update()

        def do_sort():
            result = func(data, column, reverse)
            self.root.after(0, lambda: self.sort_done(result))

        threading.Thread(target=do_sort, daemon=True).start()

    def sort_done(self, result):
        if self.scope_var.get() == "filtered" and self.is_filtered:
            self.filtered_products = result.data
        else:
            self.all_products = result.data
        self.refresh_table()
        self.metrics_var.set(
            f"Algorithm: {result.algorithm}  |  Time: {result.time_ms:.2f} ms  |  "
            f"Comparisons: {result.comparisons:,}  |  Swaps: {result.swaps:,}  |  "
            f"Complexity: {result.time_complexity}  |  Stable: {'Yes' if result.stable else 'No'}  |  "
            f"Items: {len(result.data):,}")
        self.status_var.set(f"{result.algorithm} completed")

    def update_filters(self, event=None):
        col = self.search_col.get()
        if col in NUMERIC_COLS:
            self.search_filter.config(values=NUMERIC_FILTERS)
            self.search_filter.set(NUMERIC_FILTERS[0])
        else:
            self.search_filter.config(values=STRING_FILTERS)
            self.search_filter.set(STRING_FILTERS[0])

    def on_search(self):
        if not self.all_products:
            messagebox.showinfo("Info", "No data to search.")
            return
        val = self.search_val.get().strip()
        if not val:
            messagebox.showwarning("Warning", "Enter a search value.")
            return
        algo = self.search_algo.get()
        col = self.search_col.get()
        ft = self.search_filter.get()
        func = SEARCH_ALGORITHMS[algo]
        result = func(self.all_products, col, val, ft)
        self.filtered_products = result.data
        self.is_filtered = True
        self.refresh_table()
        self.metrics_var.set(
            f"Search: {result.algorithm}  |  Column: {col}  |  Filter: {ft}  |  "
            f"Matches: {result.matches_found:,}  |  Time: {result.time_ms:.2f} ms")
        self.status_var.set(f"Showing {result.matches_found} of {len(self.all_products)} products")

    def on_clear(self):
        self.is_filtered = False
        self.filtered_products = []
        self.search_val.delete(0, "end")
        self.refresh_table()
        self.metrics_var.set("Filter cleared.")
        self.status_var.set(f"Showing all {len(self.all_products)} products")

    def on_benchmark(self):
        if not self.all_products:
            messagebox.showinfo("Info", "No data to benchmark.")
            return
        sample = min(self.bench_size.get(), len(self.all_products))
        bench_data = random.sample(self.all_products, sample) if sample < len(self.all_products) else self.all_products
        column = self.bench_col.get()
        self.bench_text.config(state="normal")
        self.bench_text.delete("1.0", "end")
        self.bench_text.insert("end", f"Benchmarking {len(bench_data)} items on '{column}'...\n\n")
        header = f"{'Algorithm':<18} {'Time(ms)':>10} {'Comparisons':>14} {'Swaps':>10} {'Complexity':<12} {'Stable':<6}\n"
        self.bench_text.insert("end", header)
        self.bench_text.insert("end", "─" * 76 + "\n")
        self.bench_text.config(state="disabled")
        self.btn_bench.config(state="disabled")

        def run():
            for name, func in ALGORITHMS.items():
                result = func(bench_data, column, False)
                line = (f"{result.algorithm:<18} {result.time_ms:>10.2f} "
                        f"{result.comparisons:>14,} {result.swaps:>10,} "
                        f"{result.time_complexity:<12} {'Yes' if result.stable else 'No':<6}\n")
                self.root.after(0, lambda l=line: self.bench_add_line(l))
            self.root.after(0, self.bench_finish)

        threading.Thread(target=run, daemon=True).start()

    def bench_add_line(self, line):
        self.bench_text.config(state="normal")
        self.bench_text.insert("end", line)
        self.bench_text.config(state="disabled")
        self.bench_text.see("end")

    def bench_finish(self):
        self.bench_text.config(state="normal")
        self.bench_text.insert("end", "\n✅ Benchmark complete!")
        self.bench_text.config(state="disabled")
        self.btn_bench.config(state="normal")
        self.status_var.set("Benchmark finished")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        data = self.filtered_products if self.is_filtered else self.all_products
        for p in data:
            vals = [str(p.get(c, "")) for c in COLUMNS]
            self.tree.insert("", "end", values=vals)
        count = len(data)
        total = len(self.all_products)
        if self.is_filtered:
            self.status_var.set(f"Showing {count} of {total} products")
        else:
            self.status_var.set(f"Showing all {total} products")

    def try_load(self):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)
        if os.path.exists(path):
            self.all_products = load_products(path)
            self.refresh_table()
            self.status_var.set(f"Auto-loaded {len(self.all_products)} products")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
