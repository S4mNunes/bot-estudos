<<<<<<< HEAD
# 📚 Bot de Estudos Telegram

Assistente pessoal de estudos desenvolvido em Python para organizar exercícios, armazenar materiais acadêmicos e enviar lembretes automáticos pelo Telegram, com integração de inteligência artificial para classificação e resumo dos conteúdos.

O projeto foi criado para facilitar a organização da rotina acadêmica, centralizando exercícios e materiais em um único lugar.

## ✨ Funcionalidades

- **Recebimento de materiais:** envio de textos, fotos, PDFs e links pelo Telegram.
- **Inteligência artificial:** classificação automática por matéria e geração de resumos dos exercícios.
- **Banco de dados SQLite:** armazenamento local de exercícios, materiais e status de conclusão.
- **Gerenciamento de tarefas:** consulta de exercícios pendentes e marcação de atividades concluídas.
- **Lembretes automáticos:** notificações de segunda a sexta-feira, às 20h, no horário de Brasília.
- **Logs de execução:** acompanhamento de eventos, processamento, envios e erros.
- **Execução automatizada:** possibilidade de iniciar o bot com o Windows ou hospedá-lo em um servidor.

## 🛠️ Tecnologias utilizadas

- Python
- Telegram Bot API
- python-telegram-bot
- SQLite
- OpenAI API
- python-dotenv
- Logging

## 📂 Estrutura do projeto

```text
bot-estudos-telegram/
├── bot.py
├── .env
├── .gitignore
├── requirements.txt
├── estudos.db
├── arquivos/
└── logs/
    └── bot.log
```

Os arquivos `estudos.db`, `arquivos/` e `logs/` são gerados ou utilizados durante a execução, conforme a configuração do projeto.

## ⚙️ Pré-requisitos

- Python 3.10 ou superior.
- Uma conta no Telegram.
- Um bot criado pelo [@BotFather](https://t.me/BotFather).
- Uma chave de API da OpenAI para utilizar os recursos de inteligência artificial.

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone URL_DO_REPOSITORIO
cd bot-estudos-telegram
```

Substitua `URL_DO_REPOSITORIO` pelo endereço real do repositório.

### 2. Crie um ambiente virtual

No Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```dotenv
TELEGRAM_BOT_TOKEN=seu_token_do_telegram
OPENAI_API_KEY=sua_chave_da_openai
OPENAI_MODEL=gpt-4.1-mini
```

Substitua os valores de exemplo pelas suas credenciais. Verifique se o modelo escolhido está disponível na sua conta da API.

**Importante:** nunca publique seu token do Telegram ou sua chave da OpenAI no GitHub.

### 5. Execute o bot

```bash
python bot.py
```

Após a inicialização, abra a conversa com seu bot no Telegram e envie `/start`.

## 💬 Comandos disponíveis

| Comando | Descrição |
|---|---|
| `/start` | Inicia o bot e apresenta as instruções. |
| `/ajuda` | Exibe orientações de uso. |
| `/pendentes` | Lista os exercícios ainda não concluídos. |
| `/feito ID` | Marca um exercício como concluído. |

Exemplo:

```text
/feito 3
```

Esse comando marca o exercício de ID 3 como concluído, desde que pertença à conversa e esteja pendente.

## 🤖 Como funciona a inteligência artificial

Quando um material é recebido, o bot pode utilizar a API da OpenAI para identificar a disciplina, criar um título e produzir um resumo do conteúdo.

O objetivo é facilitar a organização dos estudos, sem substituir a consulta ao material original.

A análise depende da disponibilidade da API, das permissões e dos formatos aceitos pelo modelo configurado. Na versão inicial, links são registrados, mas o conteúdo das páginas não é extraído automaticamente.

## 🔒 Segurança

- Credenciais armazenadas em variáveis de ambiente.
- Arquivo `.env` excluído do controle de versão.
- Banco de dados e materiais pessoais fora do repositório público.
- Recomenda-se restringir o acesso ao bot e proteger os backups.
- O uso da API de IA pode gerar custos adicionais.

## 🗺️ Próximas melhorias

- [ ] Extração automática de conteúdo de páginas web.
- [ ] Suporte a novos formatos de documentos.
- [ ] Organização avançada por disciplina e aula.
- [ ] Definição de prazos individuais.
- [ ] Comandos para adiar tarefas e consultar o progresso.
- [ ] Planejamento semanal de estudos.
- [ ] Testes automatizados.
- [ ] Melhorias no monitoramento e tratamento de falhas.
- [ ] Logs de erros
- [ ] VPS Linux pra funcionamento na nuvem

## 🎯 Objetivo do projeto

Além de auxiliar na organização dos estudos, este projeto é uma oportunidade prática de desenvolver conhecimentos em Python, integração com APIs, persistência de dados, automação, tratamento de erros e implantação de aplicações.

---

**Status:** em desenvolvimento.

**Linguagem:** Python.

**Finalidade:** organização acadêmica e automação de tarefas de estudo.
=======
# bot-estudos
>>>>>>> 563a6bedfbbc564a70855362c9fa7b3ec801863f
