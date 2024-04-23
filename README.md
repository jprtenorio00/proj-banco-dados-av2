# Processador de Consultas SQL

## Descrição
Este projeto visa a implementação de um processador de consultas SQL com uma interface gráfica para demonstrar a análise, execução e otimização de consultas SQL. O processador inclui funcionalidades como parsing de consultas SQL, geração de grafo de operadores, e exibição dos resultados através de uma interface gráfica.

## Funcionalidades

### Interface Gráfica
- Mostra o funcionamento do processador de consultas em tempo real.

### Funcionalidades Principais
1. **Parser de Consultas SQL**
   - Análise e separação dos componentes principais de uma consulta SQL.
2. **Geração do Grafo de Operadores**
   - Criação de um grafo representando a consulta, com nós para operadores/tabelas/constantes.
3. **Ordem de Execução da Consulta**
   - Geração e exibição da ordem de execução baseada no grafo de operadores.
4. **Exibição dos Resultados**
   - Mostra o resultado da consulta e as operações realizadas na interface gráfica.

## Banco de Dados de Exemplo
Utilizamos um banco de dados MySQL para testar as consultas. Os scripts para criação do banco estão disponíveis no arquivo `db-joaotenorio-proj-banco-dados.sql`.

## Heurísticas de Otimização
- Priorização de operações que reduzem o tamanho dos resultados intermediários, como seleções e projeções.
- Reordenação dos nós para evitar operações custosas como o produto cartesiano.

## Autores
- João Pedro Rodrigues Tenório