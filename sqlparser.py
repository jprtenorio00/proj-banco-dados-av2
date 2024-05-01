import tkinter as tk
from tkinter import scrolledtext, messagebox
import networkx as nx
import matplotlib.pyplot as plt
import mysql.connector
import re

def build_database_schema():
    return {
        'Categoria': ['idCategoria', 'Descricao'],
        'Produto': ['idProduto', 'Nome', 'Descricao', 'Preco', 'QuantEstoque', 'Categoria_idCategoria'],
        'TipoCliente': ['idTipoCliente', 'Descricao'],
        'Cliente': ['idCliente', 'Nome', 'Email', 'Nascimento', 'Senha', 'TipoCliente_idTipoCliente', 'DataRegistro'],
        'TipoEndereco': ['idTipoEndereco', 'Descricao'],
        'Endereco': ['idEndereco', 'EnderecoPadrao', 'Logradouro', 'Numero', 'Complemento', 'Bairro', 'Cidade', 'UF', 'CEP', 'TipoEndereco_idTipoCliente', 'Cliente_idCliente'],
        'Telefone': ['Numero', 'Cliente_idCliente'],
        'Status': ['idStatus', 'Descricao'],
        'Pedido': ['idPedido', 'Status_idStatus', 'DataPedido', 'ValorTotalPedido', 'Cliente_idCliente'],
        'Pedido_has_Produto': ['idPedidoProduto', 'Pedido_idPedido', 'Produto_idProduto', 'Quantidade', 'PrecoUnitario']
    }

class SQLQueryParser:
    def __init__(self, query):
        self.query = query.strip(';')
        self.schema = build_database_schema()
        self.components = {
            'SELECT': [],
            'FROM': [],
            'WHERE': [],
            'JOIN': []
        }
        self.valid_keywords = ['SELECT', 'FROM', 'WHERE', 'JOIN', 'ON']
        self.valid_operators = ['=', '>', '<', '<=', '>=', '<>', 'AND', '(', ')', '*']
        self.invalid_keywords = [
            'ADD', 'ALL', 'ALTER', 'ANALYZE', 'AS', 'ASC', 'AUTO_INCREMENT',
            'BETWEEN', 'CASE', 'CHECK', 'COLUMN', 'COMMIT', 'CONSTRAINT', 'CREATE',
            'DATABASE', 'DEFAULT', 'DELETE', 'DESC', 'DISTINCT', 'DROP', 'ELSE',
            'EXCEPT', 'EXISTS', 'FALSE', 'FOREIGN', 'FULL', 'GROUP BY', 'HAVING',
            'IF', 'IN', 'INDEX', 'INNER', 'INSERT', 'INTERSECT', 'INTO', 'IS',
            'IS NULL', 'KEY', 'LEFT', 'LIKE', 'LIMIT', 'NOT', 'NOT NULL', 'NULL',
            'OR', 'ORDER BY', 'OUTER', 'PRIMARY', 'PROCEDURE', 'RIGHT', 'ROLLBACK',
            'ROW', 'SET', 'TABLE', 'THEN', 'TO', 'TRANSACTION', 'TRUE', 'UNION',
            'UNIQUE', 'UPDATE', 'VALUES', 'VIEW', 'WHEN', 'WITH'
        ]
        self.invalid_operators = [
            '||', '+', '-', '/', '^', '!=', '!>', '!<', '~', '!~', '@>', '<@', '&', '|', '#', '%', '<<', '>>'
        ]
        self.errors = []
        self.parse_query()

    def parse_query(self):
        regex_keywords = r'\b(?:' + '|'.join(self.valid_keywords + self.invalid_keywords) + r')\b'
        regex_operators = r'(?:' + '|'.join(map(re.escape, self.valid_operators + self.invalid_operators)) + r')'
        regex_pattern = regex_keywords + '|' + regex_operators
        parts = re.split(regex_pattern, self.query, flags=re.I)
        keys = re.findall(regex_pattern, self.query, flags=re.I)
        tokens = list(zip(keys, parts[1:]))
        for key, part in tokens:
            key = key.upper().strip()
            if key in self.invalid_keywords or key in self.invalid_operators:
                self.errors.append(f"Invalid SQL keyword or operator used: '{key}'")
            else:
                self.process_key(key, part.strip())
    
    def process_key(self, key, part):
        if key == 'SELECT':
            self.components['SELECT'] = [item.strip() for item in part.split(',')]
        elif key == 'FROM':
            self.components['FROM'] = [item.strip() for item in part.split(',')]
        elif key == 'WHERE':
            self.components['WHERE'] = self.extract_conditions(part.strip())
        elif key == 'JOIN':
            join_components = {'table': None, 'on': []}
            on_index = part.upper().find(' ON ')
            if on_index != -1:
                join_components['table'] = part[:on_index].strip()
                join_components['on'] = self.extract_conditions(part[on_index + 4:].strip())
            else:
                join_components['table'] = part.strip()
            self.components['JOIN'].append(join_components)
        self.validate_query()

    def extract_conditions(self, condition_string):
        parts = re.split(r'(\b(?:=|>|<|<=|>=|<>|AND|OR)\b|\(|\)|\s)', condition_string)
        tokens = [part.strip() for part in parts if part.strip()]
        return tokens

    def validate_query(self):
        if not self.errors:
            for component_list in self.components.values():
                for component in component_list:
                    if isinstance(component, dict):
                        if any(token not in self.valid_keywords + self.valid_operators and not re.match(r'^[\w\.]+$', token) for token in self.extract_conditions(component['table'])):
                            self.errors.append(f"Invalid JOIN table: '{component['table']}'")
                        for cond in component['on']:
                            if any(token not in self.valid_keywords + self.valid_operators and not re.match(r'^[\w\.]+$', token) and not re.match(r'^[\w\.]+\s+[\w\.]+$', token) and not re.match(r'^\'[\w\s]+\'$', token) and not re.match(r'^\d+$', token) for token in self.extract_conditions(cond)):
                                self.errors.append(f"Invalid operator or condition in JOIN ON: '{cond}'")
                        pass
                    else:
                        if any(token not in self.valid_keywords + self.valid_operators and not re.match(r'^[\w\.]+$', token) and not re.match(r'^[\w\.]+\s+[\w\.]+$', token) and not re.match(r'^\'[\w\s]+\'$', token) and not re.match(r'^\d+$', token) for token in self.extract_conditions(component)):
                            self.errors.append(f"Invalid token or operator in SQL: '{component}'")
                        pass
        if self.errors:
            self.errors.insert(0, "Errors detected in SQL query:")

    def get_components(self):
        return self.components

    def get_errors(self):
        return self.errors

class SQLGraph:
    def __init__(self, components):
        self.graph = nx.DiGraph()
        self.build_graph(components)

    def build_graph(self, components):
        for sel in components['SELECT']:
            sel_clean = sel.strip()
            self.graph.add_node(sel_clean, label='SELECT')

        for frm in components['FROM']:
            frm_clean = frm.strip()
            self.graph.add_node(frm_clean, label='FROM')
            for sel in components['SELECT']:
                sel_clean = sel.strip()
                self.graph.add_edge(frm_clean, sel_clean)

        if components['WHERE']:
            for whr in components['WHERE']:
                whr_clean = whr.strip()
                self.graph.add_node(whr_clean, label='WHERE')
                for frm in components['FROM']:
                    frm_clean = frm.strip()
                    self.graph.add_edge(frm_clean, whr_clean)

        for join in components['JOIN']:
            join_table = join['table'].strip()
            self.graph.add_node(join_table, label='JOIN')
            for frm in components['FROM']:
                frm_clean = frm.strip()
                self.graph.add_edge(frm_clean, join_table)
            for cond in join['on']:
                cond_clean = cond.strip()
                self.graph.add_node(cond_clean, label='ON')
                self.graph.add_edge(join_table, cond_clean)

    def draw_graph(self):
        pos = nx.spring_layout(self.graph)
        labels = {node: node for node in self.graph.nodes()}
        nx.draw(self.graph, pos, labels=labels, with_labels=True, node_color='lightblue', edge_color='gray')
        plt.show()

class QueryExecutionProcessor:
    def __init__(self, graph):
        self.graph = graph

    def execute_order(self):
        order = list(nx.topological_sort(self.graph))
        return order

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
            parser = SQLQueryParser(sql)
            errors = parser.get_errors()
            if errors:
                messagebox.showerror("Erro de Consulta SQL", "\n".join(errors))
            else:
                components = parser.get_components()
                graph = SQLGraph(components)
                graph.draw_graph()
                processor = QueryExecutionProcessor(graph.graph)
                order = processor.execute_order()
                print("Order of Execution:", order)
                self.execute_query(sql)
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
