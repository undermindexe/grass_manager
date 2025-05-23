<div align="center">

![Icon](https://raw.githubusercontent.com/undermindexe/grass_manager/refs/heads/main/assets/icon.ico)

# The GRASS Account Manager

[![Download last realese](https://img.shields.io/badge/download-YellowGreen?style=plastic&logo=github&label=Stable&link=https%3A%2F%2Fgithub.com%2Fundermindexe%2Fgrass_manager%2Freleases)](https://github.com/undermindexe/grass_manager/releases)
[![Instruction](https://img.shields.io/badge/how_to_use-YellowGreen?style=plastic&logo=gitbook&label=Help&link=https%3A%2F%2Fexpanse-2.gitbook.io%2Fgrass-faker%2F)](https://expanse-2.gitbook.io/grass-faker/)

[![Crypto channel](https://img.shields.io/badge/crypto_channel-pink?style=plastic&label=Telegram&color=pink&link=https%3A%2F%2Ft.me%2Fexpanse_crypto)](https://t.me/expanse_crypto)
[![Crypto chat](https://img.shields.io/badge/crypto_chat-pink?style=plastic&label=Telegram&color=pink&link=https%3A%2F%2Ft.me%2Fexpanse_crypto)](https://t.me/expanse_chat)
[![It's me](https://img.shields.io/badge/I%60ts_me-pink?style=plastic&label=Telegram&color=pink&link=https%3A%2F%2Ft.me%2FUnderMindExe)](https://t.me/UnderMindExe)

[🇬🇧 English](#english) | [🇷🇺 Русский](#русский)

</div>

## English

This is a Python program designed for the automatic **registration**, **verification**, and **management** of accounts for the DePIN project's **GRASS** farms. The program is built in such a way that it can be easily integrated into your automation tools. To achieve this, it supports launch parameters that allow you to configure the required task in detail. All accounts and their data are stored in a single database, making it convenient to work with through DB Browser or any other software. For security, the program utilizes proxying, browser operation emulation, and session storage, including the user-agent. All of this, combined with asynchronous processing, enables you to work quickly with any number of accounts.

For those who only need basic functionality, a terminal interface has been provided for easy launching without the need for manual console or batch file usage.

<div align="center">
<img src="assets/GAM.png" alt="Icon" width="650"/>
</div>

---

### Core features

For accounts:

- Registration
- Email verification
- Wallet linking (with automatic wallet generation)
- Wallet verification via email
- Parsing all account information into the database

For the database:

- Importing accounts into the database from a text file according to a format specified by you
- Exporting accounts to an Excel file
- Exporting accounts to a TXT file according to the specified format (exporting only the required information)
- A separate function for adding IMAP information from email

### Compatibility

The program **works on Windows 8+**

### Install

**You can use the ready-made exe build or install it manually**

- `pip install -r requirements.txt`

## Start

- `python main.py`

### Contact

[Telegram](https://t.me/UnderMindExe)

---

## Русский

Это Python программа, создана для автоматической **регистрации**, **верификации** и **управления аккаунтами** ферм DePIN проекта **GRASS**. Программа сделана таким образом, что бы её было легко добавлять в свои средства автоматизации. Для этого реализован запуск с помощью параметров запуска, с которыми можно подробно настроить требуемую задачу. Все аккаунты, их данные хранятся в единой базе данных, для удобной работы с ней через DB Browser или любой чужой софт. Для безопасности используется проксификация, эмуляция браузерной работы и хранение сессий, включая user-agent. Всё это в асинхронной работе позволит вам работать быстро с любым количеством аккаунтов

Для тех кому достаточно базового функционала - сделан терминальный интерфейс, для удобства запуска, без ручного использования консоли или bat файлов

<div align="center">
<img src="assets/GAM.png" alt="Icon" width="650"/>
</div>

---

### Основные функции

Для аккаунтов:

- Регистрация
- Верификация почты
- Привязка кошелька (Генерация кошелька автоматическая)
- Верификация кошелька через почту
- Парсинг всей информации от аккаунтов в базу данных

Для базы данных:

- Импорт аккаунтов в базу с текстового файла и указанному вами формату
- Экспорт аккаунтов в excel файл
- Экспорт аккаунтов в txt файл по указанному фами формату (Какую надо информацию - ту и экспортируете)
- Отдельная функция для добавления imap информации от почты

### Совместимость

Программа работает на0 **Windows 8+**

### Установка

**Вы можете использовать готовый exe билд, либо установить в ручную**

- `pip install -r requirements.txt`

### Запуск

- `python main.py`

### Контакты

[Telegram](https://t.me/UnderMindExe)
