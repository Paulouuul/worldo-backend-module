# WORLDO - SOCIAL NETWORK (Backend Python Module)

## Resumo

Repositório dedicado ao módulo de backend para integração com o projeto
da rede social [Worldo - Social Network](https://github.com/Paulouuul/worldo-social-network).

## Funcionalidades já implementadas no backend

- Criação de molduras (cosméticos), realização de transação de moedas virtuais para custo de criação e armazenamento de mídias do cosmético no Cloudflare R2
- Edição de perfil de usuário e informações, incluindo troca de foto de perfil/banner e armazernamento de mídia no Cloudflare R2
- Carrinho de compras de cosméticos do Marketplace armazenado em cache no Redis
- Autenticação e validação de credenciais utilizando tokens JWT


## Requisitos

- Python
- Banco de dados PostgreSql configurado de acordo com o projeto [Worldo - Social Network](https://github.com/Paulouuul/worldo-social-network)
- Cloudflare R2 com 2 buckets: privado / público
- Banco de dados Redis

## Como executar

### 1. Criação de containers Docker (Redis)

```bash
docker compose up
```

### 2. Configuração de ambiente virtual

```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Ou no CMD do Windows
venv\Scripts\activate.bat

# No Linux/Mac
source venv/bin/activate

# Instalar dependências necessárias
pip install -r requirements.txt
```

### 3. Configuração de variáveis de ambiente

- Crie o arquivo .env conforme o .env.example
- Configure os valores de acordo com o seu ambiente de desenvolvimento

### 4. Inicialização da api

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Tecnologias
- Python
- FastApi
- Jwt
- PostgreSql
- Redis
- Docker
- Cloudflare R2