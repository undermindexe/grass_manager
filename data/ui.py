from textual.app import App, ComposeResult
from textual.widgets import Button, Label, Input, Link, Static
from textual.containers import Vertical, Horizontal, Container
from textual.events import Enter, Leave
from .ui_text import DEFAULT_VALUES, DEFAULT_DESCRIPTION, CSS


class MenuButton(Button):
    def on_enter(self, event: Enter) -> None:
        if self.id in DEFAULT_DESCRIPTION:
            description = self.app.query_one("#description", Static)
            description.update(DEFAULT_DESCRIPTION[self.id])
        super()._on_enter(event) 

class InfoInput(Input):
    def on_enter(self, event: Enter) -> None:
        if self.id in DEFAULT_DESCRIPTION:
            description = self.app.query_one("#description", Static)
            description.update(DEFAULT_DESCRIPTION[self.id])
        super()._on_enter(event)

class MyInterface(App):
    CSS = CSS
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


    def compose(self) -> ComposeResult:
        self.theme = 'tokyo-night'
        with Horizontal(id='container'):
            self.container = self.start_menu()
            yield self.container

    def start_menu(self):
        start_menu = Horizontal(self.panel_links(), 
        Vertical(Static("GRASS FAKER\nAccount manager", classes="title"),
                           Static("Наведите курсор на кнопку для описания", classes="title2"),
                            MenuButton("Регистрация", id="registration", classes="button"),
                            MenuButton("Верификация", id="verification", classes="button"),
                            MenuButton("Обновить информацию", id="update", classes="button"),
                            MenuButton("Импорт", id="import", classes="button"),
                            MenuButton("Экспорт", id="export", classes="button"),
                            MenuButton("Добавить imap данные", id="add_imap", classes="button"),
                            classes="column_central"),
        Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container')
        return start_menu

    def panel_links(self):
        panel = Vertical(Vertical(Static("---> Где нас найти <---", classes="title"),
                                  Vertical(Link('Telegram Канал', url='https://t.me/expanse_crypto', classes='link'), classes="link_container"),
                                  Vertical(Link('Telegram Чат', url='https://t.me/expanse_chat', classes='link'), classes="link_container"),
                                  Vertical(Link('Поддержка', url='https://t.me/UnderMindExe', classes='link'), classes="link_container"),
                                  Vertical(Link('Купить Grass Faker', url='https://t.me/grass_faker_bot', classes='link'), classes="link_container"),
                                  classes="container_about1"),
                         Vertical(Static("---> Купить прокси <---", classes="title"), 
                                  Vertical(Link('Proxy Seller', url='https://proxy-seller.com/?partner=SU9ID7IKFWSKOZ', classes='link'), classes="link_container"),
                                  Vertical(Link('Proxy Seller, но намного дешевле', url='https://t.me/node_proxy_bot', classes='link'), classes="link_container"),
                                  Static("---> Купить почты <---", classes="title"),
                                  Vertical(Link('Firstmail', url='https://firstmail.ltd/?ref=28236', classes='link'), classes="link_container"),
                                  Static("---> Аренда сервера <---", classes="title"),
                                  Vertical(Link('Appletec', url='https://appletec.ru/?from=32434', classes='link'), classes="link_container"),
                                  classes='container_about2'),
                         Vertical(Static("О программе", classes="title"), 
                                  Static('''Автоматическая регистрация, верификация аккаунтов проекта Grass\nСоздано Expanse Crypto''', id='about', classes='about'), classes='container_about3'),
                         classes='container_vert_left')
        return panel

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.container.remove_children()
            self.container.mount(self.start_menu())

        if event.button.id == "registration":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Регистрация", classes="title"),
                                                InfoInput(placeholder='Accounts file path', type='text', id='accounts'),
                                                InfoInput(placeholder='Fixed imap for all acc', type='text', id='imap'),
                                                InfoInput(placeholder='Forward mode', type='text', id='forward_mode'),
                                                InfoInput(placeholder='Proxy file path', type='text', id='proxy'),
                                                InfoInput(placeholder='Proxy rotate time (in seconds)', type='integer', id='rotate'),
                                                InfoInput(placeholder='Captcha service', type='text', id='captcha_service'),
                                                InfoInput(placeholder='Captcha api key', type='text', id='captcha_key'),
                                                InfoInput(placeholder='Referrals file path', type='text', id='ref'),
                                                InfoInput(placeholder='Number of threads', type='integer', id = 'threads'),
                                                Button('ЗАПУСК', id='start_registration', classes="button"),
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_registration":
            self.action('registration')

        if event.button.id == "verification":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Верификация", classes="title"),
                                                InfoInput(placeholder='Proxy file path', type='text', id='proxy'),
                                                InfoInput(placeholder='Proxy rotate time (in seconds)', type='integer', id='rotate'),
                                                InfoInput(placeholder='Proxy file for imap (Optional)', type='text', id='imap_proxy'),
                                                InfoInput(placeholder='Forward mode', type='text', id='forward_mode'),
                                                InfoInput(placeholder='Captcha service', type='text', id='captcha_service'),
                                                InfoInput(placeholder='Captcha api key', type='text', id='captcha_key'),
                                                InfoInput(placeholder='Number of threads', type='integer', id = 'threads'),
                                                Button('ЗАПУСК', id='start_verification', classes="button"), 
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_verification":
            self.action('verification')

        if event.button.id == "update":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Обновить данные", classes="title"),
                                                InfoInput(placeholder='Proxy file path', type='text', id='proxy'),
                                                InfoInput(placeholder='Proxy rotate time (in seconds)', type='integer', id='rotate'),
                                                InfoInput(placeholder='Number of threads', type='integer', id = 'threads'),
                                                Button('ЗАПУСК', id='start_update', classes="button"), 
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_update":
            self.action('update')

        if event.button.id == "import":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Импорт аккаунтов", classes="title"),
                                                InfoInput(placeholder='Import file name', type='text', id='file_name'),
                                                InfoInput(placeholder='Separator', type='text', id='separator'),
                                                InfoInput(placeholder='Format data', type='text', id='format'),
                                                Button('ЗАПУСК', id='start_import', classes="button"), 
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_import":
            self.action('import')

        if event.button.id == "export":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Экспорт аккаунтов", classes="title"),
                                                InfoInput(placeholder='Export type', type='text', id='export_type'),
                                                InfoInput(placeholder='Export file name', type='text', id='file_name'),
                                                Static("Если выбран txt файл, укажите:", classes="title_menu"),
                                                InfoInput(placeholder='Separator', type='text', id='separator'),
                                                InfoInput(placeholder='Format data', type='text', id='format'),
                                                Button('ЗАПУСК', id='start_export', classes="button"), 
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_export":
            self.action('export')

        if event.button.id == "add_imap":
            self.container.remove_children()
            self.container.mount(Horizontal(self.panel_links(),
                                            Vertical(
                                                Static("Добавить imap данные", classes="title"),
                                                InfoInput(placeholder='Accounts file path', type='text', id='accounts'),
                                                InfoInput(placeholder='Fixed imap for all acc', type='text', id='imap'),
                                                Button('ЗАПУСК', id='start_imap', classes="button"), 
                                                Button('НАЗАД', id='back', classes="button"),
                                                classes="column_central"),
                                            Vertical(Static("Описание", classes="title"), Static("", id='description', classes='description'), classes='container_vert_right'), classes='container'))
        if event.button.id == "start_imap":
            self.action('imap')

    def action(self, action):
        inputs = self.query(InfoInput)
        int_value = ['rotate', 'threads']
        result = DEFAULT_VALUES
        for i in inputs:
            if i.value == '':
                result[i.id] = DEFAULT_VALUES[i.id]
            else:
                result[i.id] = int(i.value) if i.id in int_value else i.value
        result['action'] = action
        self.exit(result)
