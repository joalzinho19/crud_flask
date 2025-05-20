from flask import Flask, render_template, request, redirect, url_for
import redis
from datetime import datetime
# Inicializa o Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Inicializa o Flask
app = Flask(__name__)

def criar_tarefa(titulo, desc):
    # Gerar ID único para o usuário
    tarefa_id = r.incr('tarefa:id')
    data_criacao = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    status = 'PENDENTE'
    # Usar hset para adicionar campos individualmente
    r.hset(f'tarefa:{tarefa_id}', 'titulo', titulo)
    r.hset(f'tarefa:{tarefa_id}', 'desc', desc)
    r.hset(f'tarefa:{tarefa_id}', 'data', data_criacao)
    r.hset(f'tarefa:{tarefa_id}', 'status', status)

    return tarefa_id

def obter_tarefa(tarefa_id):
    # Usar hgetall para pegar o hash completo
    tarefa = r.hgetall(f'tarefa:{tarefa_id}')
    if not tarefa:
        return None
    # Converter bytes para string
    return {k.decode('utf-8'): v.decode('utf-8') for k, v in tarefa.items()}

def listar_tarefas():
    # Encontrar todas as chaves que seguem o padrão 'tarefa:*'
    tarefa_keys = r.keys('tarefa:*')
    
    # Inicializar uma lista para armazenar todos os usuários
    tarefas = []
    
    # Para cada chave, obter os dados do usuário
    for key in tarefa_keys:
        key_str = key.decode('utf-8')
        # Ignorar a chave 'tarefa:id' (que é o contador)
        if key_str == 'tarefa:id':
            continue
        
        tarefa_id = key_str.split(':')[1]  # Extrair o ID do usuário da chave
        tarefa = obter_tarefa(tarefa_id)  # Obter os dados do usuário
        tarefas.append({f'{tarefa_id}': tarefa})  # Adicionar à lista de usuários
    
    return tarefas

def getID():
    keys = r.keys('*')
    return [key.decode('utf-8') for key in keys]

@app.route('/atualizar_tarefa', methods=['POST'])
def atualizar_tarefa():
    # Recupera os dados enviados pelo formulário
    key = request.form['key']
    titulo = request.form['titulo']
    desc = request.form['desc']
    data = request.form['data']
    status = request.form['status']
    
    # Atualiza os dados no Redis
    if r.exists(key):
        r.hset(key, 'titulo', titulo)
        r.hset(key, 'desc', desc)
        r.hset(key, 'data', data)
        r.hset(key, 'status', status)
    
    # Redireciona de volta para a página de atualização/exclusão
    return redirect(url_for('atualizar_exc'))

@app.route('/atualizar_excluir', methods=['GET', 'POST'])
def atualizar_exc():    
    idTarefas = getID()

    tarefa = None
    if request.method == 'POST':
        selected_key = request.form['key']
        
        # Verifique se o id existe e busque a tarefa
        if r.exists(selected_key):
            # Usar hgetall para pegar todos os campos se for um hash
            tarefa_data = r.hgetall(selected_key)

            # Decodificar os dados (porque hgetall retorna bytes)
            tarefa = {
                'id': selected_key,
                'titulo': tarefa_data.get(b'titulo').decode('utf-8'),
                'desc': tarefa_data.get(b'desc').decode('utf-8'),
                'data': tarefa_data.get(b'data').decode('utf-8'),
                'status': tarefa_data.get(b'status').decode('utf-8')
            }
    return render_template('atualizar_excluir.html', idTarefas=idTarefas, tarefa=tarefa)

@app.route('/apagar_tarefas', methods=['POST'])
def apag_tarefa():
    selected_key = request.form['key']
    
    if r.exists(selected_key):
        r.delete(selected_key)
    
    return redirect(url_for('atualizar_exc'))
    # Rota para a página inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota para criar um usuário
@app.route('/criar_tarefas', methods=['POST'])
def criar_tarefas_view():
    # Obter dados do formulário
    titulo = request.form['titulo']
    desc = request.form['desc']
    
    
    # Criar usuário
    tarefa_id = criar_tarefa(titulo, desc)
    
    # Redireciona para a página de listagem de usuários
    return redirect(url_for('listar_tarefas_view'))

# Rota para listar todos os usuários
@app.route('/tarefas')
def listar_tarefas_view():
    tarefas = listar_tarefas()
    return render_template('tarefas.html', tarefas=tarefas)

if __name__ == '__main__':
    app.run(debug=True)
