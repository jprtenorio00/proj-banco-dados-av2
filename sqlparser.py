import tkinter as tk
from tkinter import scrolledtext
import sqlparse
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector

class SQLProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SQL Processor App")
        self.sql_input = scrolledtext.ScrolledText(root, width=70, height=10)
        self.sql_input.pack(pady=20)
        self.run_button = tk.Button(root, text="Processar Consulta", command=self.process_query)
        self.run_button.pack(pady=10)
        self.result_text = scrolledtext.ScrolledText(root, width=70, height=10)
        self.result_text.pack(pady=20)
        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.canvas_frame)

    def process_query(self):
        sql = self.sql_input.get("1.0", tk.END)
        formatted_sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
        
        self.parse_sql(formatted_sql)
        self.execute_query(sql)
        self.display_graph(sql)

    def parse_sql(self, sql):
        parsed = sqlparse.parse(sql)[0]
        for token in parsed.tokens:
            print(token.ttype, token.value)

    def execute_query(self, sql):
        try:
            conn = mysql.connector.connect(user='your_username', password='your_password', host='your_host', database='BD_Vendas')
            cursor = conn.cursor()
            cursor.execute(sql)
            records = cursor.fetchall()
            self.result_text.delete('1.0', tk.END)
            for record in records:
                self.result_text.insert(tk.END, str(record) + '\n')
            cursor.close()
            conn.close()
        except Exception as e:
            self.result_text.insert(tk.END, "Erro: " + str(e))
    
    def display_graph(self, sql):
        G = nx.DiGraph()
        self.figure.clf()
        nx.draw(G, with_labels=True, ax=self.figure.add_subplot(111))
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = SQLProcessorApp(root)
    root.mainloop()
