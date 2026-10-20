# Geekz Backend

Backend da loja Geekz desenvolvido com Django e Django REST Framework.

## Desenvolvimento

Com o ambiente virtual ativado e o arquivo `.env` configurado, o servidor de desenvolvimento pode ser iniciado com:

`.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000`

## Execução WSGI

O backend expõe a aplicação WSGI em `config.wsgi:application`.

Após instalar as dependências com:

`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`

No Windows, o servidor pode ser iniciado com Waitress:

`.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 config.wsgi:application`

Em produção, o endereço e a porta devem ser definidos de acordo com a infraestrutura utilizada.

Domínio, proxy reverso, TLS e demais configurações específicas de hospedagem não são definidos neste repositório enquanto a plataforma de deploy não estiver escolhida.

## Health check

O endpoint `GET /api/health/` verifica se a aplicação e o banco de dados estão respondendo.

Quando saudável, responde HTTP 200 com `{"status":"ok"}`.

Se o banco estiver indisponível, responde HTTP 503 com `{"status":"unavailable"}` sem expor detalhes internos da falha.
