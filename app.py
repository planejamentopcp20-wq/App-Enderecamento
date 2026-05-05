from flask import Flask, request, render_template, session, redirect
import requests
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave_secreta_123')

# ===== URL DO APPS SCRIPT =====
# Após publicar o Apps Script como Web App, cole a URL aqui
# Ou defina como variável de ambiente no Render: APPS_SCRIPT_URL
APPS_SCRIPT_URL = os.environ.get('APPS_SCRIPT_URL', 'COLE_AQUI_A_URL_DO_APPS_SCRIPT')


# =========================================================
# 🔒 PROTEÇÃO DE ROTAS
# =========================================================
@app.before_request
def proteger_rotas():
    if request.endpoint not in ['login', 'static']:
        if 'usuario' not in session:
            return redirect('/login')


# =========================================================
# 🔐 LOGIN
# =========================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None

    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')

        try:
            resp = requests.get(APPS_SCRIPT_URL, params={
                'acao': 'login',
                'usuario': usuario,
                'senha': senha
            }, timeout=15)

            data = resp.json()

            if data.get('ok'):
                session['usuario'] = usuario
                return redirect('/')
            else:
                erro = data.get('erro', 'Usuário ou senha inválidos')

        except Exception as e:
            erro = f"Erro ao conectar com a base: {str(e)}"

    return render_template('login.html', erro=erro)


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# =========================================================
# MENU
# =========================================================
@app.route('/')
def menu():
    return render_template('menu.html', usuario=session.get('usuario'))


@app.route('/enderecamento')
def tela_enderecamento():
    return render_template('Endereçamento.html')


@app.route('/retirada')
def tela_retirada():
    return render_template('retirada.html')


# =========================================================
# CONSULTA
# =========================================================
@app.route('/consultar', methods=['GET', 'POST'])
def consultar():
    dados = None
    erro = None

    if request.method == 'POST':
        pedido = str(request.form.get('pedido')).strip()

        try:
            resp = requests.get(APPS_SCRIPT_URL, params={
                'acao': 'consultar',
                'pedido': pedido
            }, timeout=15)

            data = resp.json()

            if 'erro' in data:
                erro = data['erro']
            else:
                dados = data.get('dados', [])

        except Exception as e:
            erro = f"Erro ao consultar: {str(e)}"

    return render_template('consulta.html', dados=dados, erro=erro)


# =========================================================
# SALVAR PEDIDO
# =========================================================
@app.route('/salvar', methods=['POST'])
def salvar():
    pedido = str(request.form.get('pedido')).strip()

    artigos = request.form.getlist('artigo[]')
    qtds = request.form.getlist('qtd_artigo[]')

    lista_artigos = [
        {'artigo': str(a).strip(), 'qtd': int(q)}
        for a, q in zip(artigos, qtds)
    ]

    payload = {
        'acao': 'salvar',
        'pedido': pedido,
        'artigos': lista_artigos,
        'departamento': request.form.get('departamento'),
        'endereco': request.form.get('endereco'),
        'data_do_enderecamento': request.form.get('data_do_enderecamento'),
        'hora_inicio': request.form.get('hora_inicio'),
        'responsavel': request.form.get('responsavel'),
        'qtd_pallet': request.form.get('qtd_pallet')
    }

    try:
        resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        data = resp.json()

        if data.get('ok'):
            return render_template('sucesso.html',
                titulo='✅ Pedido Salvo!',
                mensagem=f'Pedido <b>{pedido}</b> endereçado com sucesso.',
                voltar='/'
            )
        else:
            return render_template('sucesso.html',
                titulo='❌ Erro',
                mensagem=data.get('erro', 'Erro desconhecido'),
                voltar='/enderecamento'
            )

    except Exception as e:
        return render_template('sucesso.html',
            titulo='❌ Erro de conexão',
            mensagem=str(e),
            voltar='/enderecamento'
        )


# =========================================================
# RETIRADA
# =========================================================
@app.route('/retirar', methods=['POST'])
def retirar():
    pedido = str(request.form.get('pedido')).strip()

    artigos = request.form.getlist('artigo[]')
    qtds = request.form.getlist('qtd_retirada[]')

    lista_artigos = [
        {'artigo': str(a).strip(), 'qtd': int(q)}
        for a, q in zip(artigos, qtds)
    ]

    payload = {
        'acao': 'retirar',
        'pedido': pedido,
        'artigos': lista_artigos,
        'endereco_atual': request.form.get('endereco_atual'),
        'data_retirada': request.form.get('data_retirada'),
        'hora_retirada': request.form.get('hora_retirada'),
        'destino': request.form.get('destino'),
        'responsavel_retirada': request.form.get('responsavel_retirada'),
        'observacao': request.form.get('observacao', '')
    }

    try:
        resp = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        data = resp.json()

        if data.get('ok'):
            return render_template('sucesso.html',
                titulo='✅ Retirada Realizada!',
                mensagem=f'Pedido <b>{pedido}</b> atualizado com sucesso.',
                voltar='/'
            )
        else:
            return render_template('sucesso.html',
                titulo='❌ Erro na Retirada',
                mensagem=data.get('erro', 'Erro desconhecido'),
                voltar='/retirada'
            )

    except Exception as e:
        return render_template('sucesso.html',
            titulo='❌ Erro de conexão',
            mensagem=str(e),
            voltar='/retirada'
        )


# =========================================================
# RUN
# =========================================================
if __name__ == '__main__':
    app.run(debug=False)
