import tkinter as tk
from tkinter import scrolledtext, messagebox
import sqlparse
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mysql.connector
import re

class SQLQueryParser:
    def __init__(self, query):
        self.query = query
        self.tokens = []
        self.parse_query()

    def parse_query(self):
        parsed = sqlparse.parse(self.query)[0]
        self.tokens = [(token.ttype, token.value) for token in parsed.tokens if token.ttype]

    def extract_conditions(self, condition_string):
        operators_pattern = re.compile(r'(\b(?:=|>|<|<=|>=|<>|AND|OR)\b|\(|\))', re.I)
        tokens = operators_pattern.split(condition_string)
        tokens = [token.strip() for token in tokens if token.strip()]
        return tokens

    def extract_components(self):
        components = {
            'SELECT': [],
            'FROM': [],
            'WHERE': [],
            'JOIN': []
        }

        select_match = re.search(r'SELECT(.*?)FROM', self.query, re.S | re.I)
        if select_match:
            components['SELECT'] = select_match.group(1).strip().split(',')

        from_match = re.search(r'FROM(.*?)(WHERE|JOIN|$)', self.query, re.S | re.I)
        if from_match:
            components['FROM'] = from_match.group(1).strip().split(',')

        where_match = re.search(r'WHERE(.*?)(JOIN|$)', self.query, re.S | re.I)
        if where_match:
            components['WHERE'] = self.extract_conditions(where_match.group(1).strip())

        joins = re.findall(r'JOIN(.*?)(?=JOIN|$)', self.query, re.S | re.I)
        for join in joins:
            join_components = {}
            join_components['table'], *on_clause = re.split(r'ON', join, 1, flags=re.I)
            join_components['table'] = join_components['table'].strip()
            if on_clause:
                join_components['on'] = self.extract_conditions(on_clause[0].strip())
            else:
                join_components['on'] = []
            components['JOIN'].append(join_components)

        return components

class SQLGraph:
    def __init__(self, components):
        self.graph = nx.DiGraph()
        self.build_graph(components)

    def build_graph(self, components):
        for sel in components['SELECT']:
            self.graph.add_node(sel.strip(), label='SELECT')
        for frm in components['FROM']:
            self.graph.add_node(frm.strip(), label='FROM')
        for whr in components['WHERE']:
            self.graph.add_node(whr, label='WHERE')
        for join in components['JOIN']:
            self.graph.add_node(join['table'], label='JOIN')
            for cond in join['on']:
                self.graph.add_node(cond, label='ON')
                self.graph.add_edge(join['table'], cond)

        if components['WHERE']:
            for node in self.graph.nodes(data=True):
                if node[1]['label'] == 'FROM':
                    for whr in components['WHERE']:
                        self.graph.add_edge(node[0], whr)
        if components['JOIN']:
            for join in components['JOIN']:
                self.graph.add_edge(join['table'], join['on'][0])

    def draw_graph(self):
        pos = nx.spring_layout(self.graph)
        labels = {node: node for node in self.graph.nodes()}
        nx.draw(self.graph, pos, labels=labels, with_labels=True)
        plt.show()

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

    def process_query(self):
        sql = self.sql_input.get("1.0", tk.END).strip()
        if sql:
            formatted_sql = sqlparse.format(sql, reindent=True, keyword_case='upper')
            print("Formatted SQL:", formatted_sql)
            parser = SQLQueryParser(formatted_sql)
            components = parser.extract_components()
            graph = SQLGraph(components)
            graph.draw_graph()
            self.execute_query(formatted_sql)
        else:
            messagebox.showinfo("Informação", "Por favor, insira uma consulta SQL válida.")

    def execute_query(self, sql):
        try:
            with mysql.connector.connect(user='root', password='root', host='localhost', database='bd_vendas') as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    if cursor.description:
                        records = cursor.fetchall()
                        self.result_text.delete('1.0', tk.END)
                        for record in records:
                            self.result_text.insert(tk.END, str(record) + '\n')
                    else:
                        self.result_text.delete('1.0', tk.END)
                        self.result_text.insert(tk.END, "Nenhum dado para exibir.\n")
        except mysql.connector.Error as e:
            messagebox.showerror("Erro de Banco de Dados", str(e))
        except Exception as ex:
            messagebox.showerror("Erro Geral", str(ex))

if __name__ == "__main__":
    root = tk.Tk()
    app = SQLProcessorApp(root)
    root.mainloop()
