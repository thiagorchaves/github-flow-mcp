# GitHub Flow MCP

Servidor open source de Model Context Protocol com políticas para GitHub e GitHub Actions. O foco é permitir automação assistida por IA em fluxos de infraestrutura sem transformar o agente em uma chave mestra: leitura e preview são amplos, enquanto escritas remotas ficam atrás de guardrails e revisão humana.

![Arquitetura do GitHub Flow MCP](docs/github-flow-mcp-architecture.svg)

## Principais recursos

- inspeção de repositórios, branches, PRs, reviews e GitHub Actions
- inspeção de Git local sem branch, commit, push ou merge silenciosos
- preview de branch, PR e comentário
- tokens temporários, de uso único, vinculados ao conteúdo exato do preview
- integração opcional com Basecamp
- políticas opcionais de label/reviewer por repositório
- nenhuma tool de merge, remoção de branch ou alteração de branch protection

## Modelo de segurança

As tools de escrita remota não são registradas enquanto:

```dotenv
GITHUB_WRITE_ENABLED=false
```

Quando a escrita é habilitada, criação de branch, PR e comentário ainda exigem um `confirmation_id` retornado pelo preview correspondente. Se o SHA de origem, body do PR, labels, reviewers ou comentário mudar, o token deixa de servir e um novo preview é necessário.

> [!NOTE]
> O servidor garante preview-before-write e vínculo exato do payload. O cliente MCP deve repassar o token somente após aprovação real do usuário.

## Instalação

```bash
uv tool install git+https://github.com/thiagorchaves/github-flow-mcp.git
```

Para desenvolvimento:

```bash
git clone https://github.com/thiagorchaves/github-flow-mcp.git
cd github-flow-mcp
uv sync --extra dev
```

## Configuração

```bash
cp .env.example .env
chmod 600 .env
```

Use um fine-grained GitHub token com o menor escopo possível. Configurações específicas da empresa, como organização padrão, marcador de produção, repositórios que exigem determinada label ou reviewer e obrigatoriedade de link do Basecamp, devem ficar somente no `.env` local.

## Tools

Leitura: `healthcheck`, `get_authenticated_user`, `get_repository`, `list_branches`, `get_collaborator_permission`, `inspect_local_repository`, `list_pull_requests`, `get_pull_request`, `list_pull_request_files`, `list_pull_request_reviews`, `list_workflows`, `list_workflow_runs`.

Preview: `preview_branch_name`, `preview_local_commit`, `preview_remote_branch`, `preview_pull_request`, `preview_pull_request_comment`.

Escrita protegida: `create_remote_branch`, `create_pull_request`, `add_pull_request_comment`.

Integração: `build_basecamp_pr_update` apenas gera Markdown para ser entregue a outro MCP.

## Fluxo recomendado

1. Obter o contexto da demanda.
2. Inspecionar o repositório sem alterar nada.
3. Gerar preview da branch e pedir aprovação.
4. Usar o token do preview para criar a branch remota, se necessário.
5. Alterar arquivos e fazer commit local pelo fluxo normal de Git assinado.
6. Fazer push.
7. Gerar preview do PR.
8. Usar o token após aprovação para abrir o PR.
9. Manter review e aplicação da mudança sob responsabilidade humana.

## Segurança

Nunca faça commit de `.env`, tokens, dados de repositórios privados, caminhos internos da empresa ou links privados de demandas. Consulte [SECURITY.md](SECURITY.md).

## Licença

MIT.
