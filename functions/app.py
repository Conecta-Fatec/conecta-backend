import os
import sys
from serverless_wsgi import handle_request

# 1. Mostra para o Netlify onde está a raiz do seu projeto
# Isso faz o Python enxergar a pasta 'conecta_fatec' e o 'manage.py'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# 2. Importa o aplicativo principal do seu Django
from conecta_fatec.wsgi import application

# 3. A função principal que o Netlify vai chamar a cada acesso
def handler(event, context):
    return handle_request(application, event, context)