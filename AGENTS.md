# Worldo — Backend Python (FastAPI)

Módulo de backend da rede social Worldo. O app Next.js (`worldo-social-network`, que tem o próprio
`AGENTS.md`) chama esta API para: carrinho de compras (Redis), criação de molduras cosméticas
(cobrança em moedas + upload ao Cloudflare R2) e edição de perfil (avatar/capa no R2).

Idioma do projeto: **português** (comentários, docstrings, mensagens de erro e commits).

## Ambiente

- Python **3.15** (`.python-version`). Ambiente virtual em `venv/`:
  `uv venv --python 3.15 venv && uv pip install --python venv/bin/python -r requirements.txt`.
- Executar: `venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
- Configuração lida do `.env` com prefixo `WORLDO_` (`app/core/config.py`). Redis via
  `docker compose up -d`; PostgreSQL é o mesmo banco do Next.js.
- Todas as dependências têm versão fixa no `requirements.txt`. Versões mantidas abaixo da mais nova
  têm um comentário explicando qual dependência impede a atualização (ex.: `bcrypt` pelo `passlib`,
  `python-dateutil` pelo `botocore`).

## Verificação antes de concluir

```bash
venv/bin/python -m compileall -q app            # sintaxe
venv/bin/python -W error -c "import app.main"   # importa tudo sem avisos de depreciação
```

- Teste as rotas alteradas com a API rodando (o JWT de teste pode ser gerado com `python-jose` e o
  `WORLDO_JWT_SECRET`). Prefira entradas que sejam recusadas antes de gravar no banco/R2.
- `test_cart_repository.py` e `test_redis.py` são scripts manuais (`python <arquivo>`).

## Estrutura

```
app/
  main.py                 Cria o FastAPI (lifespan com pool do PostgreSQL, CORS, routers, /health)
  api/router.py           Router raiz: rotas protegidas por JWT sob WORLDO_API_PREFIX
  api/routes/<domínio>/   Um router.py por domínio e uma pasta <ação>_use_case/use_case.py por ação
  auth/                   Validação do JWT emitido pelo Next.js (dependencies) e UserInfo (schemas)
  core/                   config, database (asyncpg), redis_client, r2 (boto3), constants
  entities/               Entidades Pydantic (carrinho e item) sobre interfaces/entity_interface.py
  repositories/           Persistência (carrinho no Redis)
  services/               Regras reutilizáveis (carrinho, consultas de anúncios)
  utils/                  response (respostas padronizadas), image_utils (conversão para WebP)
```

Pastas e arquivos em `snake_case`; classes em `PascalCase`. Arquivos vazios em `chat/`,
`user_status/` e `websocket/` são reservados para funcionalidades ainda não implementadas.

## Como implementar uma rota

1. **Router** (`api/routes/<domínio>/router.py`): declara a rota, recebe o usuário com
   `Depends(get_current_user)`, monta a requisição e chama o caso de uso. Converte o resultado com
   `success_response(...)` ou `error_response(mensagem, status)` (`app/utils/response.py`).
2. **Caso de uso** (`<ação>_use_case/use_case.py`): uma classe `<Ação>Request` com os parâmetros e
   uma classe `<Ação>UseCase` com `async def execute(...) -> tuple[dict, int]` que retorna
   `(resposta, status HTTP)`. Erros de validação → 400; erros inesperados são registrados no log e
   retornam 500 sem detalhes internos.
3. **Serviço/repositório**: regras compartilhadas em `services/`, acesso a Redis em
   `repositories/`, PostgreSQL via `db` (`app/core/database.py`: `fetch_one`, `fetch_all`,
   `execute`, `transaction()`).
4. Operações que gravam em mais de uma tabela usam `async with db.transaction()`. Uploads ao R2
   feitos antes de uma falha devem ser removidos (padrão `_rollback` nos casos de uso).
5. Registre o router do domínio em `app/api/router.py` (ou no router do domínio pai).

## Constantes

- Valores compartilhados entre módulos ficam em `app/core/constants.py` (`MB`, tipos de imagem
  aceitos, `WEBP_MIME_TYPE`). Valores de um único caso de uso são constantes da classe
  (ex.: `MAX_FRAME_SIZE`, `IMAGE_SIZE`, `WEBP_QUALITY`). Não repita números nem listas.
- Limites também validados no frontend (tamanho de upload, nome, username, bio…) existem no Next.js
  em `constants/uploads.ts` e `constants/validation.ts`; ao mudar aqui, mude lá.
- Limites do carrinho: `RedisCartService.MAX_ITEMS_PER_CART` e `MAX_QUANTITY_PER_ITEM`.

## Pydantic

- Pydantic 2: configure modelos com `model_config = ConfigDict(...)` (não use `class Config` nem
  `json_encoders`, que estão depreciados). Para aceitar nome do campo e alias use
  `validate_by_name=True, validate_by_alias=True`.

## Autenticação

- O Next.js assina o JWT com `WORLDO_JWT_SECRET`; `get_current_user` exige as claims `sub`/`id` e
  `email`. Nome e username caem no prefixo do email quando ausentes. O token não traz dados de
  perfil: busque no banco o que precisar.

## Comentários

- Primeira linha de todo arquivo: `# caminho/do/arquivo.py`, seguida de `# descrição` (rotas e casos
  de uso: incluir método e caminho, ex.: `DELETE /cosmetics/marketplace/cart/remove/{item_id}`).
- Toda função, método e classe tem docstring `"""..."""` em português descrevendo o que faz
  **hoje**. Docstrings de rota começam com método e caminho.
- Nada de comentários históricos ("antes fazia X", "CORRIGIDO", "← NOVO"), emojis, passos
  numerados (`# 1.`) ou separadores (`# ====`). Ao citar um limite, referencie a constante.
- Ao mudar código, atualize as docstrings e comentários afetados.
