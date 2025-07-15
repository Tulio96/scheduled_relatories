Estruturação do envio de e-mails automáticos:

Nas pastas com formato /XX.Carteira estão as pastas com o tipo de relatório enviado, ex: 02.Ogochi/Base_ativa

Dentro da pasta Base_ativa estão os arquivos que carregam as informações nas quais consistem a elaboração do relatório e o envio por e-mail e também os arquivos que 
configuram a conexão ao banco de dados.

No arquivo .env são associadas as credenciais do acesso ao banco de dados;

No arquivo config.py as credenciais são associadas a variáveis, vindas do .env;

No arquivo database.py a função engine é configurada, para se conectar ao banco. As credenciais vêm do arquivo config.py;

No arquivo query.py está a consulta e o caminho para o salvamento dos dados da consulta com extensão .xlsx. Os dados de conexão do banco são importados via função 
engine, do arquivo database.py;

No arquivo salvar.py é configurado o salvamento do relatório e o envio de uma mensagem via google chat para confirmação do sucesso do salvamento do relatório.
A estrutura da mensagem é configurada via 'notificacao_chat.py' e os parâmetros como nome de arquivo, horário, etc. são provenientes do query.py, onde a função 
salvar.py é chamada ao fim do código;

No arquivo envio_email.py são definidas as credenciais de login no e-mail, o remetente, destinatário, CC, assunto, corpo do e-mail e caminho do arquivo anexo. 
O caminho do arquivo anexo deve ser exatamente o mesmo caminho que é definido no query.py, para que o python possa encontrar o relatório gerado a partir da 
query e enviar por e-mail. O código envio_email.py configura os parâmetros e a função que estrutura o envio é a função 'funcao_enviar_email.py', que se encontra 
em /Relatorios_Agendados/Envio_emails/funcao_enviar_email.py.

O arquivo script.py é responsável por executar as funções para gerar o relatório e, também, executar o envio do e-mail;

Os registros de envio ficam salvos no arquivo 'cron_log.log';

O agendamento da execução dos scripts é feito usando o comando 'crontab -e' no terminal do linux. Ajuda sobre os comandos para agendar as execuções podem 
ser encontradas na internet.
