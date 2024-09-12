import logging
import os
import re
import subprocess
import paramiko
import psycopg2
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext

# Constants
TOKEN = os.getenv('TOKEN')

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_database = os.getenv('DB_DATABASE')
postgres_version = os.getenv('postgres_version')

SSH_DETAILS = {
    'hostname': os.getenv('RM_HOST'),
    'port': os.getenv('RM_PORT'),
    'username': os.getenv('RM_USER'),
    'password': os.getenv('RM_PASSWORD')
}
# Regex Patterns
PHONE_REGEX = re.compile(r'\+?[87][(\s-]?\(?\d{3}[)\s-]?\s?\d{3}[\s-]?\d{2}[\s-]?\d{2}')
EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

# Logging
logging.basicConfig(filename='logfile.txt', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Utility Functions
def non_command_answer(update: Update, context: CallbackContext):
    update.message.reply_text('Please write command! More info: /help')
    logger.info(f'{update.effective_user.full_name} write \"{update.message.text}\"')

def ssh_connect(command):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(**SSH_DETAILS)
    stdin, stdout, stderr = client.exec_command(command)
    data = (stdout.read() + stderr.read()).decode().strip()
    client.close()
    return data


def pg_connect(query, update: Update, fetch=False):
    logger.debug(f'Query for PG: "{query}"')
    try:
        connection = psycopg2.connect(user=db_user, password=db_password, host=db_host, port=db_port, database=db_database)
        cursor = connection.cursor()
        cursor.execute(query)
        if fetch:
            data = cursor.fetchall()
            cursor.close()
            connection.close()
            return data
        connection.commit()
        cursor.close()
        connection.close()
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Error occurred: {error}")
        update.message.reply_text(f'Something gone wrong with DB!')
        if connection:
            connection.rollback()
        cursor.close()
        connection.close()
        raise

def send_long_message(update: Update, text: str):
    max_length = 4096
    for i in range(0, len(text), max_length):
        update.message.reply_text(text[i:i + max_length])

# Command Handlers
def start_command(update: Update, context: CallbackContext):
    user = update.effective_user
    update.message.reply_text(f'Hello {user.full_name}!')
    logger.info(f'{user.full_name} started bot')

def help_command(update: Update, context: CallbackContext):
    help_text = (
        "Here are the available commands:\n\n"
        "/start - Start the bot and get a welcome message.\n"
        "/help - Show this help message.\n"
        "/find_phone_number - Find phone numbers in the provided text.\n"
        "/find_email - Find email addresses in the provided text.\n"
        "/get_emails - Show all emails in DB.\n"
        "/get_phone_numbers - Show all phone numbers in DB.\n"
        "/get_repl_logs - Get replication logs.\n"
        "/get_release - Get the release information of the remote system.\n"
        "/get_uname - Get the uname information of the remote system.\n"
        "/get_uptime - Get the uptime of the remote system.\n"
        "/get_df - Get the disk usage information of the remote system.\n"
        "/get_mpstat - Get the CPU usage statistics of the remote system.\n"
        "/get_critical - Get the last 5 critical log entries of the remote system.\n"
        "/get_w - Get the list of active users on the remote system.\n"
        "/get_auths - Get the last 10 authentication attempts on the remote system.\n"
        "/get_ps - Get the process list of the remote system.\n"
        "/get_ss - Get the socket statistics of the remote system.\n"
        "/get_services - Get the list of active services on the remote system.\n"
        "/get_apt_list - Get the list of installed packages or information about a specific package.\n"
    )
    update.message.reply_text(help_text)
    logger.info(f'{update.effective_user.full_name} asked for help')

def get_release(update: Update, context: CallbackContext):
    data = ssh_connect('lsb_release -a')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for release information')


def get_uname(update: Update, context: CallbackContext):
    data = ssh_connect('uname')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for uname information')


def get_uptime(update: Update, context: CallbackContext):
    data = ssh_connect('uptime -p')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for uptime information')


def get_df(update: Update, context: CallbackContext):
    data = ssh_connect('df -h')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for disk usage information')


def get_free(update: Update, context: CallbackContext):
    data = ssh_connect('free -h')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for memory usage information')


def get_mpstat(update: Update, context: CallbackContext):
    data = ssh_connect('mpstat')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for CPU statistics')


def get_w(update: Update, context: CallbackContext):
    data = ssh_connect('w -h')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for active users')


def get_auths(update: Update, context: CallbackContext):
    data = ssh_connect('last -n 10')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for authentication attempts')


def get_critical(update: Update, context: CallbackContext):
    data = ssh_connect('journalctl -p 2 -n 5 -q')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for critical logs')


def get_ps(update: Update, context: CallbackContext):
    data = ssh_connect('ps')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for process list')


def get_ss(update: Update, context: CallbackContext):
    data = ssh_connect('ss -tulpan')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for socket statistics')


def get_apt_list_command(update: Update, context: CallbackContext):
    update.message.reply_text('What do you want to see?\n1. All packets list\n2. Info about some packet\nEnter 1 or 2:')
    return 'get_apt_list_choice'


def get_apt_list_choice(update: Update, context: CallbackContext):
    user_input = update.message.text
    if user_input == '1':
        data = ssh_connect("apt list --installed")
        send_long_message(update, data)
        logger.info(f'{update.effective_user.full_name} asked for all installed packets')
        return ConversationHandler.END
    elif user_input == '2':
        update.message.reply_text('Enter packet name: ')
        return 'get_apt_list_find_packet'
    else:
        update.message.reply_text("Enter 1 or 2:")
        return 'get_apt_list_choice'


def get_apt_list_find_packet(update: Update, context: CallbackContext):
    user_input = update.message.text
    data = ssh_connect(f"apt show {user_input}")
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for info about packet {user_input}')
    return ConversationHandler.END


def get_services(update: Update, context: CallbackContext):
    data = ssh_connect('systemctl list-units --type=service --state=active')
    update.message.reply_text(data)
    logger.info(f'{update.effective_user.full_name} asked for active services')

def get_repl_logs(update: Update, context: CallbackContext):
    shell_script = """
    if [ -f "/pg_logs/postgresql.log" ]; then
        grep -i repl /pg_logs/postgresql.log
    else
        /usr/bin/sudo grep -i repl /var/log/postgresql/postgresql-15-main.log
    fi
    """
    data = subprocess.run(shell_script, shell=True, text=True, capture_output=True)
    send_long_message(update, data.stdout)
    logger.info(f'{update.effective_user.full_name} asked for repl logs')

def get_emails(update: Update, context: CallbackContext):
    data = pg_connect('SELECT email FROM emails;', update, fetch=True)
    email_list = '\n'.join(row[0] for row in data)
    update.message.reply_text(email_list)
    logger.info(f'{update.effective_user.full_name} asked for email list')

def get_phone_numbers(update: Update, context: CallbackContext):
    data = pg_connect('SELECT phonenumber FROM phonenumbers;', update, fetch=True)
    phone_list = '\n'.join(row[0] for row in data)
    update.message.reply_text(phone_list)
    logger.info(f'{update.effective_user.full_name} asked for phone numbers')

def find_phone_numbers_command(update: Update, context: CallbackContext):
    update.message.reply_text('Enter text to search for phone numbers: ')
    return 'find_phone_number'

def find_phone_numbers(update: Update, context: CallbackContext):
    user_input = update.message.text
    phone_numbers = PHONE_REGEX.findall(user_input)
    if not phone_numbers:
        update.message.reply_text('No phone numbers in text')
    else:
        for number in phone_numbers:
            query = f'INSERT INTO phonenumbers (phonenumber) VALUES (\'{number}\');'
            pg_connect(query, update)
        update.message.reply_text('\n'.join(f'{i + 1}. {num}' for i, num in enumerate(phone_numbers)) + ' added to DB')
    logger.info(f'{update.effective_user.full_name} searched for phone numbers')
    return ConversationHandler.END

def find_emails_command(update: Update, context: CallbackContext):
    update.message.reply_text('Enter text to search for emails: ')
    return 'find_email'

def find_emails(update: Update, context: CallbackContext):
    user_input = update.message.text
    emails = EMAIL_REGEX.findall(user_input)
    if not emails:
        update.message.reply_text('No emails in text')
    else:
        for email in emails:
            query = f'INSERT INTO emails (email) VALUES (\'{email}\');'
            pg_connect(query, update)
        update.message.reply_text('\n'.join(f'{i + 1}. {email}' for i, email in enumerate(emails)) + ' added to DB')
    logger.info(f'{update.effective_user.full_name} searched for emails')
    return ConversationHandler.END

# Main Function
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # Conversation Handlers
    conv_handler_find_phone_numbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', find_phone_numbers_command)],
        states={'find_phone_number': [MessageHandler(Filters.text & ~Filters.command, find_phone_numbers)]},
        fallbacks=[]
    )

    conv_handler_find_emails = ConversationHandler(
        entry_points=[CommandHandler('find_email', find_emails_command)],
        states={'find_email': [MessageHandler(Filters.text & ~Filters.command, find_emails)]},
        fallbacks=[]
    )

    conv_handler_get_apt_list = ConversationHandler(
        entry_points=[CommandHandler('get_apt_list', get_apt_list_command)],
        states={
            'get_apt_list_choice': [MessageHandler(Filters.text & ~Filters.command, get_apt_list_choice)],
            'get_apt_list_find_packet': [MessageHandler(Filters.text & ~Filters.command, get_apt_list_find_packet)],
        },
        fallbacks=[]
    )

    # Adding Handlers
    dp.add_handler(CommandHandler("start", start_command))
    dp.add_handler(CommandHandler("help", help_command))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))

    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(conv_handler_get_apt_list)

    dp.add_handler(conv_handler_find_phone_numbers)
    dp.add_handler(conv_handler_find_emails)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, non_command_answer))

    # Start Bot
    updater.start_polling()
    logger.info('Bot started')
    updater.idle()

if __name__ == '__main__':
    main()
