

DEFAULT_VALUES = {
    'action': '',
    'proxy': 'proxy.txt',
    'rotate': 82000,
    'accounts': 'accounts.txt',
    'captcha_service': 'capmonster',
    'captcha_key': '',
    'accounts': 'accounts.txt',
    'ref': 'referral.txt',
    'threads': 1,
    'file_name': 'example',
    'separator': ':',
    'format': 'email:password',
    'export_type': 'excel',
    'imap_proxy': None,
    'imap': 'imap.firstmail.ltd',
    'debug': False
}

DEFAULT_DESCRIPTION = {
    'registration': '''Регистрация аккаунтов
После успешной регистрации все аккаунты будут добавлены в database.db
database.db - это база данных. Программой не предполагается ваш 
прямой доступ к базе, но если хотите - используйте DB Browser

Если вы хотите добавить уже существующие аккаунты Grass - используйте Импорт
Если вам надо получить в удобном виде ваши аккаунты - используйте Экспорт''',

    'verification': '''Верификация аккаунтов
Верификация всех аккаунтов в базе данных
Для успешной верификации обязательно, 
что бы у аккаунтов в базе был указан imap_domain и пароль от почты
указать его можно при импорте, регистрации или отдельной функцией Add imap domain

Верификация полная. Подтверждается почта, создается, привязывается и подтверждается кошелёк
Если аккаунт уже верифицирован, он будет пропущен. Если верифицирован частично - доведёт верификацию до конца

Получить данные от аккаунтов и кошельки с доступами к ним можно через экспорт, или напрямую в базе данных
''',

    'update': '''Обновление информации
Обновляет в базе данных всю имеющуюся информацию по аккаунтам
После регистрации или верификациюю эта функция не нужна

Основное назначение - получить количество поинтов на аккаунтах, или обновить информацию по импортированным аккаунтам
Для просмотра информации её надо экспортировать или открыть базу данных через DB Browser''',

    'import': '''Импорт аккаунтов
Импортирует существующие аккаунты в базу данных
Для импорта вы сами прописываете формат, по которому в вашем файле с аккаунтами все установлено

При импорте обязательно наличие почты и пароля от аккаунта. Другие данные опциональны''',

    'export': '''Экспорт аккаунтов
Экспортирует аккаунты из базы данных, в нужном виде. Доступны excel и txt файлы''',

    'add_imap': '''Добавление imap информации
Если аккаунты в вашей базе не имеют паролей от почт, и указанного imap домена, вы можете всё добавить здесь''',

    'accounts': '''Путь к txt файлу с аккаунтами
Внутри файла могут быть такие форматы:
email
email:email_password
email:email_password:imap_domain
Последний вариант приоритетен
    
Если оставить пустым - будет искать файл accounts.txt в папке с программой''',

    'proxy': '''Путь к файлу с прокси
Внутри файла необходимо соблюдать формат
username:password@ip:port
Каждый прокси с новой строки
Лишние символы и префиксы недопустимы

Если оставить пустым - будет искать файл proxy.txt в папке с программой''',

    'rotate': '''Время ротации прокси
Единица измерения - секунды
Если у вас ротация прокси раз в 5 минут, то ставим значение 300 (5*60)''',
    
    'imap_proxy': '''Прокси для доступа к почте
Ставить в случае, если сервис блокирует доступ через ваши рабочие прокси

Если оставить пустым - будут использоваться прокси, что и для регистрации''',

    'threads': '''Количество потоков
По умолчанию: 1
    
Поток - количество одновременно работающих задач, например регистраций
Чем больше потоков, тем быстрее выполнит все задачи''',

    'captcha_service': '''Используемый сервис капчи
Допустимые варианты:
capmonster\nanticaptcha\n2captcha\ncapsolver\ncaptchaai
Прописываем название целиком

Если оставить пустым - будут указан сервис capmonster''',

    'captcha_key': '''Ваш API Key от сервиса капчи
Указывать обязательно''',

    'ref': '''Путь к txt файлу с реферальными кодами
Указывать надо сами коды, с новой строки.
Указывать ссылкой нельзя

Если оставить пустым - будет искать файл referral.txt в папке с программой''',

    'file_name': '''Путь к файлу, или имя файла в папке
С файлом будет произведен экспорт/импорт данных
За формат экспорта/импорта отвечает поле Format
Разделитель можно настроить в поле Separator

Если оставить пустым - будет искать файл example.txt в папке с программой''',

    'separator': '''Разделитель
По умолчанию :
Разделитель нужен для разделения полей в формате''',

    'format': '''Формат экпорта и импорта
Разделитель должен соответствовать разделителю в Separator
Обязательные поля для экспорта и импорта: email, password
Допустимые поля для импорта и экспорта: email, password, email_password, imap_domain, username, user_agent, referal_code, wallet, private_key, seed

Например мы хотим экспортировать или импортировать почту, пароль и кошельки:
Пишем email:password:wallet:private_key''',

    'export_type': '''Вариант экспорта
Всего два варианта: excel, txt
excel - экспортирует базу аккаунтов целиком в excel формат xlxs
txt - экспортирует данные в текстовый файл, согласно вашему указанному формату''',

    'imap': '''Фиксированное значение imap
Если в вашем файле с аккаунтами не указан домен imap у каждой почты, но вы знаете,
что домен для всех почт один - вы можете прописать домен в это поле. Тогда в файле с аккаунтами будет
достаточно формата email:email_password'''
}

CSS = """
Screen {
    background: $background;
    color: white;
    align: center middle
}
#container {
    layout: horizontal;
    width: 140;
    height: 44;
    align: center middle;
}
.container_vert_left {
    layout: vertical;
    width: 33%;
    height: 90%;
    align: center middle;
}
.container_vert_right {
    border: round $foreground;
    layout: vertical;
    width: 33%;
    height: 90%;
    align: center middle;
}
.container_about1 {
    border: round $foreground;
    layout: vertical;
    width: 100%;
    height: 35%;
    align: center middle;
    margin: 0;
    padding: 0;
}
.container_about2 {
    border: round $foreground;
    layout: vertical;
    width: 100%;
    height: 40%;
    align: center middle;
}
.container_about3 {
    border: round $foreground;
    layout: vertical;
    width: 100%;
    height: 25%;
    align: center middle;
}
.column_central {
    border: round $foreground;
    padding: 2;
    width: 33%;
    height: 90%;
    align: center middle;
}
.title {
    text-style: bold;
    margin-bottom: 1;
    color: $foreground;
    text-align: center;
}
.title2 {
    color: rgb(255, 255, 255);
    margin-bottom: 1;
    text-align: center;
}
.title_menu {
    color: rgb(255, 255, 255);
    text-align: center;
}
.link_container {
    height: auto;
    align: center middle;
}
.link {
    text-style: underline bold;
    color: $text-secondary;
    margin-bottom: 1;
}    
.description {
    color: rgb(0, 0, 0);
    text-align: center;
    margin-bottom: 1;
    background: lightblue;
}
.about {
    color: rgb(0, 0, 0);
    text-align: center;
    margin-bottom: 1;
    background: lightblue;
}
.button {
    width: 100%;
    height: 3;
    text-align: center;
    margin-top: 1;
}
"""