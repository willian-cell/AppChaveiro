import os
from flask import Flask, render_template_string, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Length
import pandas as pd
import plotly.graph_objects as go
import threading
import webbrowser

# Configuração do aplicativo Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sistema.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicialização do banco de dados
db = SQLAlchemy(app)


# Modelo para vendas
class Venda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Float, nullable=False)


# Modelo para gastos
class Gasto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10), nullable=False)
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Float, nullable=False)


# Formulário para Vendas
class VendaForm(FlaskForm):
    data = DateField('Data', validators=[DataRequired()])
    descricao = StringField('Descrição',
                            validators=[DataRequired(), Length(min=2, max=100)])
    unidade = IntegerField('Unidade',
                           validators=[DataRequired(), NumberRange(min=1)])
    valor_unitario = FloatField('Valor Unitário',
                                validators=[DataRequired()])
    submit = SubmitField('Cadastrar Venda')


# Formulário para Gastos
class GastoForm(FlaskForm):
    data = DateField('Data', validators=[DataRequired()])
    descricao = StringField('Descrição', validators=[DataRequired(), Length(min=2, max=100)])
    valor = FloatField('Valor', validators=[DataRequired()])
    submit = SubmitField('Cadastrar Gasto')


def abrir_navegador():
    webbrowser.open_new('http://127.0.0.1:5000')


@app.route('/', methods=['GET', 'POST'])
def home():
    vendas_form = VendaForm()
    gastos_form = GastoForm()

    if vendas_form.validate_on_submit() and 'cadastrar_venda' in request.form:
        nova_venda = Venda(
            data=vendas_form.data.data.strftime('%Y-%m-%d'),
            descricao=vendas_form.descricao.data,
            unidade=vendas_form.unidade.data,
            valor_unitario=vendas_form.valor_unitario.data
        )
        db.session.add(nova_venda)
        db.session.commit()
        flash('Venda cadastrada com sucesso!', 'success')
        return redirect(url_for('home'))

    if gastos_form.validate_on_submit() and 'cadastrar_gasto' in request.form:
        novo_gasto = Gasto(
            data=gastos_form.data.data.strftime('%Y-%m-%d'),
            descricao=gastos_form.descricao.data,
            valor=gastos_form.valor.data
        )
        db.session.add(novo_gasto)
        db.session.commit()
        flash('Gasto cadastrado com sucesso!', 'success')
        return redirect(url_for('home'))

    vendas = Venda.query.all()
    gastos = Gasto.query.all()

    return render_template_string(HOME_HTML, vendas=vendas, gastos=gastos, vendas_form=vendas_form, gastos_form=gastos_form)


@app.route('/dashboard_vendas')
def dashboard_vendas():
    vendas_df = pd.read_sql_query("SELECT * FROM venda", db.engine)

    if vendas_df.empty:
        flash("Nenhum dado de vendas encontrado!", "info")
        return render_template_string(DASHBOARD_VENDAS_HTML, plot="")

    vendas_df['data'] = pd.to_datetime(vendas_df['data'], errors='coerce')
    vendas_df['mes'] = vendas_df['data'].dt.month

    fig = go.Figure(data=[
        go.Bar(
            name='Vendas Mensais',
            x=vendas_df['mes'].value_counts().sort_index().index,
            y=vendas_df.groupby('mes')['unidade'].sum(),
            marker_color='#00b4d8'
        )
    ])
    fig.update_layout(
        title='Vendas Mensais',
        xaxis_title='Mês',
        yaxis_title='Unidades Vendidas',
        template='plotly_dark'
    )

    graph_html = fig.to_html(full_html=False)
    return render_template_string(DASHBOARD_VENDAS_HTML, plot=graph_html)

@app.route('/dashboard_gastos')
def dashboard_gastos():
    gastos_df = pd.read_sql_query("SELECT * FROM gasto", db.engine)

    if gastos_df.empty:
        flash("Nenhum dado de gastos encontrado!", "info")
        return render_template_string(DASHBOARD_GASTOS_HTML, plot="")

    gastos_df['data'] = pd.to_datetime(gastos_df['data'], errors='coerce')
    gastos_df['mes'] = gastos_df['data'].dt.month

    fig = go.Figure(data=[
        go.Bar(
            name='Gastos Mensais',
            x=gastos_df['mes'].value_counts().sort_index().index,
            y=gastos_df.groupby('mes')['valor'].sum(),
            marker_color='#e63946'
        )
    ])
    fig.update_layout(
        title='Gastos Mensais',
        xaxis_title='Mês',
        yaxis_title='Valor (R$)',
        template='plotly_dark'
    )

    graph_html = fig.to_html(full_html=False)
    return render_template_string(DASHBOARD_GASTOS_HTML, plot=graph_html)

# Criação do banco de dados
with app.app_context():
    db.create_all()

# HTML para as páginas de dashboard (DASHBOARD_VENDAS_HTML e DASHBOARD_GASTOS_HTML)
DASHBOARD_VENDAS_HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Vendas</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            min-height: 100vh; 
            display: flex;
            flex-direction: column;
            margin: 0;
        }
        .navbar {
            background-color: #0f3460;
            box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.6);
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 999;
        }
        .navbar-space {
            height: 80px;
        }
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
            color: #fff;
        }
        .nav-link {
            color: #e0e1dd;
            font-weight: bold;
            margin-right: 15px;
            transition: color 0.3s;
        }
        .nav-link:hover {
            color: #00b4d8;
        }
        .section-title {
            margin-top: 20px;
            text-align: center;
            font-weight: bold;
            font-size: 1.8rem;
        }
        .card {
            border-radius: 16px;
            margin-top: 20px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
            color: #e9ecef;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s;
        }
        .card:hover {
            transform: scale(1.05);
            box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.7);
        }
        .info-card {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .info-icon {
            font-size: 2rem;
        }
        .chart-container {
            height: 300px;
        }
        footer {
            background-color: #0f3460;
            padding: 15px;
            text-align: center;
            color: #d9d9d9;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('home') }}">Chaveiro Willian Mix</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('dashboard_vendas') }}">Dashboard Vendas</a>
                <a class="nav-link" href="{{ url_for('dashboard_gastos') }}">Dashboard Gastos</a>
            </div>
        </div>
    </nav>

    <div class="navbar-space"></div>

    <div class="container mt-5">
        <h1 class="section-title">Resumo de Vendas</h1>
        <div class="row">
            <div class="col-md-4">
                <div class="card p-4 bg-primary">
                    <div class="info-card">
                        <i class="fas fa-calendar-day info-icon"></i>
                        <div>
                            <h5>Total do Dia</h5>
                            <p id="totalDia">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-4 bg-info">
                    <div class="info-card">
                        <i class="fas fa-calendar-alt info-icon"></i>
                        <div>
                            <h5>Total do Mês</h5>
                            <p id="totalMes">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-4 bg-success">
                    <div class="info-card">
                        <i class="fas fa-calendar info-icon"></i>
                        <div>
                            <h5>Total do Ano</h5>
                            <p id="totalAno">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card mt-5">
            <div class="card-body chart-container">
                {{ plot|safe }}
            </div>
        </div>
    </div>

    <footer>
        <p>&copy; 2024 - Sistema Willian Batista Oliveira</p>
    </footer>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<script>
    // Função para obter dados do backend e atualizar a página
    async function fetchSalesData() {
        try {
            const response = await fetch('/api/resumo_vendas'); // Faz a requisição para o backend
            const data = await response.json(); // Converte a resposta para JSON

            // Atualiza os elementos HTML com os dados recebidos
            document.getElementById('totalDia').innerText = `R$ ${data.total_dia.toFixed(2)}`;
            document.getElementById('totalMes').innerText = `R$ ${data.total_mes.toFixed(2)}`;
            document.getElementById('totalAno').innerText = `R$ ${data.total_ano.toFixed(2)}`;
        } catch (error) {
            console.error('Erro ao buscar dados de vendas:', error);
        }
    }

    // Chama a função ao carregar a página
    document.addEventListener('DOMContentLoaded', fetchSalesData);
</script>

    <script>
        // Função para obter dados do backend e atualizar a página
        async function fetchSalesData() {
            try {
                const response = await fetch('/api/resumo_vendas'); // Faz a requisição para o backend
                const data = await response.json(); // Converte a resposta para JSON

                // Atualiza os elementos HTML com os dados recebidos
                document.getElementById('totalDia').innerText = `R$ ${data.total_dia.toFixed(2)}`;
                document.getElementById('totalMes').innerText = `R$ ${data.total_mes.toFixed(2)}`;
                document.getElementById('totalAno').innerText = `R$ ${data.total_ano.toFixed(2)}`;
            } catch (error) {
                console.error('Erro ao buscar dados de vendas:', error);
            }
        }

        // Chama a função ao carregar a página
        document.addEventListener('DOMContentLoaded', fetchSalesData);
    </script>
    </body>
</html>

'''

DASHBOARD_GASTOS_HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Gastos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            min-height: 100vh; 
            display: flex;
            flex-direction: column;
            margin: 0;
        }
        .navbar {
            background-color: #0f3460;
            box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.6);
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 999;
        }
        .navbar-space {
            height: 80px;
        }
        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
            color: #fff;
        }
        .nav-link {
            color: #e0e1dd;
            font-weight: bold;
            margin-right: 15px;
            transition: color 0.3s;
        }
        .nav-link:hover {
            color: #00b4d8;
        }
        .card {
            border-radius: 16px;
            margin-top: 20px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
            color: #e9ecef;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s;
        }
        .card:hover {
            transform: scale(1.05);
            box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.7);
        }
        .info-card {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .info-icon {
            font-size: 2rem;
        }
        .chart-container {
            height: 300px;
        }
        footer {
            background-color: #0f3460;
            padding: 15px;
            text-align: center;
            color: #d9d9d9;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('home') }}">Chaveiro Willian Mix</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('dashboard_vendas') }}">Dashboard Vendas</a>
                <a class="nav-link" href="{{ url_for('dashboard_gastos') }}">Dashboard Gastos</a>
            </div>
        </div>
    </nav>

    <div class="navbar-space"></div>

    <div class="container mt-5">
        <h1 class="text-center mb-5">Resumo de Gastos</h1>

        <div class="row">
            <div class="col-md-4">
                <div class="card p-4 bg-danger">
                    <div class="info-card">
                        <i class="fas fa-calendar-day info-icon"></i>
                        <div>
                            <h5>Gasto do Dia</h5>
                            <p id="gastoDia">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-4 bg-warning">
                    <div class="info-card">
                        <i class="fas fa-calendar-alt info-icon"></i>
                        <div>
                            <h5>Gasto do Mês</h5>
                            <p id="gastoMes">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card p-4 bg-dark">
                    <div class="info-card">
                        <i class="fas fa-calendar info-icon"></i>
                        <div>
                            <h5>Gasto do Ano</h5>
                            <p id="gastoAno">R$ 0,00</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card mt-4">
            <div class="card-body chart-container">
                {{ plot|safe }}
            </div>
        </div>
    </div>

    <footer>
        <p>&copy; 2024 - Sistema Willian Batista Oliveira</p>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</body>
</html>

'''

HOME_HTML = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Vendas e Gastos</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: #ffffff;
            font-family: 'Arial', sans-serif;
            min-height: 100vh; 
            display: flex;
            flex-direction: column;
            margin: 0;
        }
    
        .navbar {
            background-color: #0f3460;
            box-shadow: 0px 2px 12px rgba(0, 0, 0, 0.6);
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            z-index: 999;
        }

        .navbar-space {
            height: 80px;
        }

        .navbar-brand {
            font-weight: bold;
            font-size: 1.5rem;
            color: #fff;
        }
    
        .nav-link {
            color: #e0e1dd;
            font-weight: bold;
            margin-right: 15px;
            transition: color 0.3s;
        }
    
        .nav-link:hover {
            color: #00b4d8;
        }
    
        .card {
            background: linear-gradient(135deg, #3a0ca3, #4361ee);
            border-radius: 16px;
            margin-top: 20px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.5);
            color: #e9ecef;
            transition: transform 0.2s ease-in-out, box-shadow 0.2s;
        }
    
        .card:hover {
            transform: scale(1.05);
            box-shadow: 0px 8px 30px rgba(0, 0, 0, 0.7);
        }
    
        .btn-primary {
            background-color: #00b4d8;
            border: none;
            font-weight: bold;
            transition: background-color 0.3s, transform 0.4s ease-in-out;
        }
    
        .btn-primary:hover {
            background-color: #0077b6;
            transform: scale(1.15);
        }
    
        .list-group-item {
            background-color: #14213d;
            color: #e9ecef;
            transition: background-color 0.3s ease-in-out;
        }
    
        .list-group-item:hover {
            background-color: #1f4068;
        }
    
        footer {
            background-color: #0f3460;
            padding: 15px;
            text-align: center;
            color: #d9d9d9;
            margin-top: auto;
        }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('home') }}">Chaveiro Willian Mix</a>
            <div class="navbar-nav">
                <a class="nav-link" href="{{ url_for('dashboard_vendas') }}">Dashboard Vendas</a>
                <a class="nav-link" href="{{ url_for('dashboard_gastos') }}">Dashboard Gastos</a>
            </div>
        </div>
    </nav>
    <div class="navbar-space"></div>

    <div class="container mt-5">
        <h1 class="text-center mb-5">Gestão de Vendas e Gastos</h1>

        <!-- Formulário de Vendas -->
        <div class="row" id="vendas">
            <div class="col-md-6">
                <div class="card p-4">
                    <h3 class="text-center">Registrar Venda</h3>
                    <form id="vendaForm" action="/cadastrar_venda" method="POST">
                        <div class="mb-3">
                            <label for="dataVenda" class="form-label">Data</label>
                            <input type="date" class="form-control" id="dataVenda" name="dataVenda" required>
                        </div>
                        <div class="mb-3">
                            <label for="descricaoVenda" class="form-label">Descrição</label>
                            <input type="text" class="form-control" id="descricaoVenda" name="descricaoVenda" required>
                        </div>
                        <div class="mb-3">
                            <label for="unidadeVenda" class="form-label">Unidade</label>
                            <input type="number" class="form-control" id="unidadeVenda" name="unidadeVenda" min="1" required>
                        </div>
                        <div class="mb-3">
                            <label for="valorUnitarioVenda" class="form-label">Valor Unitário</label>
                            <input type="number" step="0.01" class="form-control" id="valorUnitarioVenda" name="valorUnitarioVenda" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Cadastrar Venda</button>
                    </form>
                </div>
            </div>

            <!-- Formulário de Gastos -->
            <div class="col-md-6" id="gastos">
                <div class="card p-4">
                    <h3 class="text-center">Registrar Gasto</h3>
                    <form id="gastoForm" action="/cadastrar_gasto" method="POST">
                        <div class="mb-3">
                            <label for="dataGasto" class="form-label">Data</label>
                            <input type="date" class="form-control" id="dataGasto" name="dataGasto" required>
                        </div>
                        <div class="mb-3">
                            <label for="descricaoGasto" class="form-label">Descrição</label>
                            <input type="text" class="form-control" id="descricaoGasto" name="descricaoGasto" required>
                        </div>
                        <div class="mb-3">
                            <label for="valorGasto" class="form-label">Valor</label>
                            <input type="number" step="0.01" class="form-control" id="valorGasto" name="valorGasto" required>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Cadastrar Gasto</button>
                    </form>
                </div>
            </div>
        </div>

        <div class="navbar-space"></div>

        <div class="card p-3 mt-5">
            <h3>Vendas Registradas</h3>
            <ul class="list-group mt-3" id="listaVendas"></ul>
        </div>

        <div class="navbar-space"></div>

        <div class="card p-3 mt-4">
            <h3>Gastos Registrados</h3>
            <ul class="list-group mt-3" id="listaGastos"></ul>
        </div>
    </div>

    <div class="navbar-space"></div>

    <footer>
        <p>&copy; 2024 - Sistema Willian Batista Oliveira | Desenvolvido com HTML, CSS e JS</p>
    </footer>

    <script>
        function carregarVendas() {
            const listaVendas = document.getElementById('listaVendas');
            listaVendas.innerHTML = '';
            const vendas = JSON.parse(localStorage.getItem('vendas')) || [];
            vendas.forEach(venda => {
                const item = document.createElement('li');
                item.className = 'list-group-item d-flex justify-content-between align-items-center';
                item.innerHTML = `${venda.data} - ${venda.descricao} <span class="badge bg-primary">R$ ${venda.valorTotal.toFixed(2)}</span>`;
                listaVendas.appendChild(item);
            });
        }

        function carregarGastos() {
            const listaGastos = document.getElementById('listaGastos');
            listaGastos.innerHTML = '';
            const gastos = JSON.parse(localStorage.getItem('gastos')) || [];
            gastos.forEach(gasto => {
                const item = document.createElement('li');
                item.className = 'list-group-item d-flex justify-content-between align-items-center';
                item.innerHTML = `${gasto.data} - ${gasto.descricao} <span class="badge bg-danger">R$ ${gasto.valor.toFixed(2)}</span>`;
                listaGastos.appendChild(item);
            });
        }

        document.getElementById('vendaForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const data = document.getElementById('dataVenda').value;
            const descricao = document.getElementById('descricaoVenda').value;
            const unidade = parseInt(document.getElementById('unidadeVenda').value);
            const valorUnitario = parseFloat(document.getElementById('valorUnitarioVenda').value);
            const valorTotal = unidade * valorUnitario;
            const vendas = JSON.parse(localStorage.getItem('vendas')) || [];
            vendas.push({ data, descricao, unidade, valorTotal });
            localStorage.setItem('vendas', JSON.stringify(vendas));
            carregarVendas();
            e.target.reset();
        });

        document.getElementById('gastoForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const data = document.getElementById('dataGasto').value;
            const descricao = document.getElementById('descricaoGasto').value;
            const valor = parseFloat(document.getElementById('valorGasto').value);
            const gastos = JSON.parse(localStorage.getItem('gastos')) || [];
            gastos.push({ data, descricao, valor });
            localStorage.setItem('gastos', JSON.stringify(gastos));
            carregarGastos();
            e.target.reset();
        });

        window.onload = function() {
            carregarVendas();
            carregarGastos();
        };
    </script>
</body>
</html>

'''

if __name__ == '__main__':
    threading.Timer(1.5, abrir_navegador).start()
    app.run(debug=True)
