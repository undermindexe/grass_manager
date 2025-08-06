from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QTextEdit,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QTabWidget,
    QToolBar,
    QStatusBar,
    QFileDialog,
)
from PySide6.QtCore import Qt, QSize, QSettings, QThread, Signal, Slot
from PySide6.QtGui import QFont, QPalette, QColor, QAction, QIcon
from .ui_text import DEFAULT_VALUES, DEFAULT_DESCRIPTION
from .db import DataBase
from .custom_logger import logger
import asyncio
import os


class DatabaseInitializer(QThread):
    finished = Signal()
    error = Signal(str)

    def __init__(self, window):
        super().__init__()
        self.window = window

    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.window.initialize_database())
            self.finished.emit()
        except Exception as e:
            logger.debug(f"DatabaseInitializer error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Grass Faker - Account Manager")
        self.setMinimumSize(600, 800)

        self.settings = QSettings("GrassFaker", "AccountManager")

        self.input_fields = {}

        self.total_accounts = 0
        self.verified_accounts = 0
        self.total_points = 0

        self.stats_labels = {}

        self.current_language = "ru"

        self.last_action = None
        self.last_args = None

        # Флаг для предотвращения повторной инициализации
        self.database_initialized = False

        self.setup_ui()

        self.db_initializer = DatabaseInitializer(self)
        self.db_initializer.finished.connect(self.on_database_initialized)
        self.db_initializer.error.connect(self.on_database_error)
        self.db_initializer.start()

    @Slot()
    def on_database_initialized(self):
        # Предотвращаем повторную инициализацию
        if self.database_initialized:
            return

        self.database_initialized = True
        self.update_stats_display()
        self.refresh_input_fields()

    @Slot(str)
    def on_database_error(self, error_message):
        print(f"Error initializing database: {error_message}")

    def update_stats_display(self):
        logger.debug("Updating stats display...")
        if hasattr(self, "stats_labels"):
            for label_type, label in self.stats_labels.items():
                if label_type == "total":
                    label.setText(str(self.total_accounts))
                elif label_type == "verified":
                    label.setText(str(self.verified_accounts))
                elif label_type == "points":
                    label.setText(str(self.total_points))
            logger.debug("Stats display updated")

    def refresh_input_fields(self):
        """Обновляет значения полей ввода после инициализации базы данных"""
        self.settings.sync()
        for field_id, fields in self.input_fields.items():
            saved_value = self.settings.value(f"settings/{field_id}", "")
            if field_id == "threads" and not saved_value:
                saved_value = "1"

            # Обрабатываем как список, так и одиночный словарь
            if isinstance(fields, list):
                for field in fields:
                    field["input"].setText(saved_value)
            else:
                fields["input"].setText(saved_value)

    async def initialize_database(self):
        try:
            await DataBase.migration()

            result = await DataBase.query_custom_row("SELECT COUNT(*) FROM Accounts")
            self.total_accounts = result[0][0] if result else 0

            result = await DataBase.query_custom_row(
                "SELECT COUNT(*) FROM Accounts WHERE wallet_verified = 1"
            )
            self.verified_accounts = result[0][0] if result else 0

            result = await DataBase.query_custom_row(
                "SELECT SUM(totalpoints) FROM Accounts"
            )
            self.total_points = result[0][0] if result else 0

        except Exception as e:
            if DataBase._connection:
                await DataBase.close_connection()
            raise

    def setup_ui(self):
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #F3F3F3;
            }
            QWidget {
                background-color: #F3F3F3;
                color: #111111;
                font-family: 'Karla';
            }
            QWidget#parameterBlock {
                background-color: #F2FED1;
                border: 1px solid #000000;
                border-radius: 20px;
                padding: 20px;
            }
            QWidget#parameterBlock QLabel {
                background-color: #F2FED1;
            }
            QWidget#parameterBlock QWidget {
                background-color: transparent;
            }
            QWidget#parameterBlock QLineEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #ABF600;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #ABF600;
                color: #111111;
                border: 1px solid #000000;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #9CE600;
            }
            QPushButton:pressed {
                background-color: #8CD600;
            }
            QPushButton#linkButton {
                background-color: transparent;
                color: #111111;
                border: none;
                text-decoration: underline;
                font-size: 14px;
                text-align: center;
            }
            QPushButton#linkButton:hover {
                color: #000000;
                background-color: transparent;
            }
            QPushButton#fileButton {
                padding: 4px 8px;
                font-size: 12px;
                margin-left: 5px;
                background-color: #ABF600;
                margin-top: 22px;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #ABF600;
                border-radius: 4px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #ABF600;
            }
            QLabel {
                color: #111111;
            }
            QTextEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #ABF600;
                border-radius: 4px;
                padding: 5px;
            }
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #F3F3F3;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #ABF600;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #9CE600;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QToolTip {
                background-color: #ABF600;
                color: #000000;
                border: 1px solid #000000;
                border-radius: 10px;
                padding: 5px;
                font-weight: bold;
                background-image: none;
                background-clip: padding-box;
                border-image: none;
                border-style: solid;
                border-width: 1px;
                border-color: #000000;
                border-radius: 10px;
                margin: 0px;
                min-width: 0px;
                max-width: 1000px;
                min-height: 0px;
                max-height: 1000px;
            }
        """
        )

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(10)

        buttons = [
            ("Main", lambda: self.show_screen("main")),
            ("Registration", lambda: self.show_screen("registration")),
            ("Verification", lambda: self.show_screen("verification")),
            ("Update", lambda: self.show_screen("update")),
            ("Import", lambda: self.show_screen("import")),
            ("Export", lambda: self.show_screen("export")),
            ("IMAP", lambda: self.show_screen("imap")),
        ]

        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setToolTip(
                DEFAULT_DESCRIPTION[self.current_language].get(text.lower(), "")
            )
            btn.clicked.connect(callback)
            self.nav_layout.addWidget(btn)

        main_layout.addLayout(self.nav_layout)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.main_menu = self.create_main_menu()
        self.registration_screen = self.create_registration_screen()
        self.verification_screen = self.create_verification_screen()
        self.update_screen = self.create_update_screen()
        self.import_screen = self.create_import_screen()
        self.export_screen = self.create_export_screen()
        self.imap_screen = self.create_imap_screen()

        self.stacked_widget.addWidget(self.main_menu)
        self.stacked_widget.addWidget(self.registration_screen)
        self.stacked_widget.addWidget(self.verification_screen)
        self.stacked_widget.addWidget(self.update_screen)
        self.stacked_widget.addWidget(self.import_screen)
        self.stacked_widget.addWidget(self.export_screen)
        self.stacked_widget.addWidget(self.imap_screen)

        lang_layout = QHBoxLayout()
        lang_layout.setAlignment(Qt.AlignRight)

        self.lang_btn = QPushButton("RUS" if self.current_language == "ru" else "ENG")
        self.lang_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ABF600;
                color: #111111;
                border: 1px solid #000000;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #9CE600;
            }
            QPushButton:pressed {
                background-color: #8CD600;
            }
        """
        )
        self.lang_btn.clicked.connect(self.toggle_language)
        lang_layout.addWidget(self.lang_btn)

        main_layout.addLayout(lang_layout)

        self.show_screen("main")

    def create_registration_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Registration")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Accounts file path", "accounts"),
            ("Fixed imap for all acc", "imap"),
            ("Forward mode", "forward_mode"),
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Referrals file path", "ref"),
            ("Number of threads", "threads"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("registration"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def create_verification_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Verification")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Proxy file for imap (Optional)", "imap_proxy"),
            ("Forward mode", "forward_mode"),
            ("Number of threads", "threads"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("verification"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def create_update_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Update Information")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Number of threads", "threads"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("update"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def create_import_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Import Accounts")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Import file name", "file_name"),
            ("Separator", "separator"),
            ("Format data", "format"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("import"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def create_export_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Export Accounts")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Export type", "export_type"),
            ("Export file name", "file_name"),
            ("Separator", "separator"),
            ("Format data", "format"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("export"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def create_imap_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        title = QLabel("Add IMAP Data")
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #0e639c;
            margin-bottom: 20px;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        fields = [
            ("Accounts file path", "accounts"),
            ("Fixed imap for all acc", "imap"),
        ]

        for placeholder, field_id in fields:
            layout.addWidget(self.create_input_field(placeholder, field_id))

        start_btn = QPushButton("START")
        start_btn.clicked.connect(lambda: self.start_action("imap"))
        layout.addWidget(start_btn)

        layout.addStretch()
        return widget

    def on_tab_changed(self, index):
        tab_names = [
            "main",
            "registration",
            "verification",
            "update",
            "import",
            "export",
            "imap",
        ]
        if index < len(tab_names):
            self.show_description(tab_names[index])

    def create_left_panel(self):
        panel = QWidget()
        panel.setFixedWidth(250)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        sections = [
            (
                "Where to find us",
                [
                    ("Telegram Channel", "https://t.me/expanse_crypto"),
                    ("Telegram Chat", "https://t.me/expanse_chat"),
                    ("Support", "https://t.me/UnderMindExe"),
                    ("Buy Grass Faker", "https://t.me/grass_faker_bot"),
                ],
            ),
            (
                "Buy Proxies",
                [
                    (
                        "Proxy Seller",
                        "https://proxy-seller.com/?partner=SU9ID7IKFWSKOZ",
                    ),
                    ("Cheaper Proxy Seller", "https://t.me/node_proxy_bot"),
                ],
            ),
            ("Buy Emails", [("Firstmail", "https://firstmail.ltd/?ref=28236")]),
            ("Server Rental", [("Appletec", "https://appletec.ru/?from=32434")]),
        ]

        for title, links in sections:
            title_label = QLabel(title)
            title_label.setStyleSheet(
                """
                font-weight: bold;
                color: #0e639c;
                padding: 10px;
                border-bottom: 1px solid #3c3c3c;
            """
            )
            layout.addWidget(title_label)

            for link_text, url in links:
                link = QPushButton(link_text)
                link.setStyleSheet(
                    """
                    text-align: left;
                    padding-left: 20px;
                    background-color: transparent;
                    border: none;
                """
                )
                link.clicked.connect(lambda checked, u=url: self.open_url(u))
                layout.addWidget(link)

            layout.addSpacing(5)

        layout.addStretch()
        return panel

    def create_main_menu(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setAlignment(Qt.AlignCenter)

        content_container = QWidget()
        content_container.setObjectName("parameterBlock")
        content_container.setFixedWidth(400)
        content_layout = QVBoxLayout(content_container)
        content_layout.setSpacing(20)

        title = QLabel("GRASS FAKER\nAccount Manager")
        title.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            color: #111111;
            margin-bottom: 20px;
            background-color: #F2FED1;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        links_container = QWidget()
        links_layout = QVBoxLayout(links_container)
        links_layout.setSpacing(15)

        sections = [
            (
                "Where to find us",
                [
                    ("Telegram Channel", "https://t.me/expanse_crypto"),
                    ("Telegram Chat", "https://t.me/expanse_chat"),
                    ("Support", "https://t.me/UnderMindExe"),
                    ("Buy Grass Faker", "https://t.me/grass_faker_bot"),
                ],
            ),
            (
                "Buy Proxies",
                [
                    (
                        "Proxy Seller",
                        "https://proxy-seller.com/?partner=SU9ID7IKFWSKOZ",
                    ),
                    ("Cheaper Proxy Seller", "https://t.me/node_proxy_bot"),
                ],
            ),
            ("Buy Emails", [("Firstmail", "https://firstmail.ltd/?ref=28236")]),
            ("Server Rental", [("Appletec", "https://appletec.ru/?from=32434")]),
        ]

        for title, links in sections:
            section_title = QLabel(title)
            section_title.setStyleSheet(
                """
                font-weight: bold;
                color: #111111;
                font-size: 16px;
                background-color: #F2FED1;
            """
            )
            section_title.setAlignment(Qt.AlignCenter)
            links_layout.addWidget(section_title)

            for link_text, url in links:
                link_btn = QPushButton(link_text)
                link_btn.setObjectName("linkButton")
                link_btn.setCursor(Qt.PointingHandCursor)
                link_btn.clicked.connect(lambda checked, u=url: self.open_url(u))
                links_layout.addWidget(link_btn)

            if sections.index((title, links)) < len(sections) - 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.HLine)
                separator.setStyleSheet("background-color: #ABF600;")
                links_layout.addWidget(separator)

        content_layout.addWidget(links_container)
        left_layout.addWidget(content_container)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setAlignment(Qt.AlignCenter)

        stats_container = QWidget()
        stats_container.setObjectName("parameterBlock")
        stats_container.setFixedWidth(400)
        self.stats_layout = QVBoxLayout(stats_container)
        self.stats_layout.setSpacing(20)

        stats_title = QLabel("Statistics")
        stats_title.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            color: #111111;
            margin-bottom: 20px;
            background-color: #F2FED1;
        """
        )
        stats_title.setAlignment(Qt.AlignCenter)
        self.stats_layout.addWidget(stats_title)

        stats_data = [
            ("total", "Total Accounts:", str(self.total_accounts)),
            ("verified", "Verified Accounts:", str(self.verified_accounts)),
            ("points", "Total Points:", str(self.total_points)),
        ]

        for stat_id, label_text, value in stats_data:
            stat_container = QWidget()
            stat_layout = QHBoxLayout(stat_container)
            stat_layout.setSpacing(10)

            label = QLabel(label_text)
            label.setStyleSheet(
                """
                font-size: 16px;
                font-weight: bold;
                color: #111111;
                background-color: #F2FED1;
            """
            )

            value_label = QLabel(value)
            value_label.setStyleSheet(
                """
                font-size: 16px;
                color: #111111;
                background-color: #F2FED1;
            """
            )

            self.stats_labels[stat_id] = value_label

            stat_layout.addWidget(label)
            stat_layout.addWidget(value_label)
            stat_layout.addStretch()

            self.stats_layout.addWidget(stat_container)

        right_layout.addWidget(stats_container)

        layout.addWidget(left_container)
        layout.addWidget(right_container)

        return widget

    def create_description_panel(self):
        panel = QWidget()
        panel.setFixedWidth(300)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        lang_layout = QHBoxLayout()
        lang_layout.setAlignment(Qt.AlignRight)

        self.lang_btn = QPushButton("ENG")
        self.lang_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #ABF600;
                color: #111111;
                border: 1px solid #000000;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #9CE600;
            }
            QPushButton:pressed {
                background-color: #8CD600;
            }
        """
        )
        self.lang_btn.clicked.connect(self.toggle_language)
        lang_layout.addWidget(self.lang_btn)

        layout.addLayout(lang_layout)

        title = QLabel("Description")
        title.setStyleSheet(
            """
            font-weight: bold;
            color: #0e639c;
            padding: 10px;
            border-bottom: 1px solid #3c3c3c;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setStyleSheet(
            """
            background-color: #2d2d2d;
            border: none;
            padding: 10px;
        """
        )
        layout.addWidget(self.description_text)

        return panel

    def create_input_field(self, placeholder, field_id):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        input_container = QWidget()
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(5)

        label = QLabel(placeholder)

        if field_id in DEFAULT_DESCRIPTION[self.current_language]:
            label.setToolTip(DEFAULT_DESCRIPTION[self.current_language][field_id])
        input_layout.addWidget(label)

        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)

        if field_id in DEFAULT_DESCRIPTION[self.current_language]:
            input_field.setToolTip(DEFAULT_DESCRIPTION[self.current_language][field_id])

        self.settings.sync()
        saved_value = self.settings.value(f"settings/{field_id}", "")
        if field_id == "threads" and not saved_value:
            saved_value = "1"
        input_field.setText(saved_value)

        input_field.textChanged.connect(
            lambda text, id=field_id: self.save_setting(id, text)
        )

        if field_id in self.input_fields:
            if isinstance(self.input_fields[field_id], list):
                self.input_fields[field_id].append(
                    {
                        "input": input_field,
                        "label": label,
                        "placeholder": placeholder,
                    }
                )
            else:
                self.input_fields[field_id] = [
                    self.input_fields[field_id],
                    {
                        "input": input_field,
                        "label": label,
                        "placeholder": placeholder,
                    },
                ]
        else:
            self.input_fields[field_id] = {
                "input": input_field,
                "label": label,
                "placeholder": placeholder,
            }

        input_layout.addWidget(input_field)

        layout.addWidget(input_container)

        if field_id in ["accounts", "proxy", "ref", "file_name", "imap_proxy"]:
            file_btn = QPushButton("...")
            file_btn.setObjectName("fileButton")
            file_btn.clicked.connect(lambda: self.select_file(input_field))
            layout.addWidget(file_btn)

        return container

    def select_file(self, input_field):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file_name:
            input_field.setText(file_name)

    def save_setting(self, field_id, value):
        self.settings.setValue(f"settings/{field_id}", value)
        self.settings.sync()

    def create_screen_base(self, title_text, fields):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignTop)

        params_container = QWidget()
        params_container.setObjectName("parameterBlock")
        params_layout = QVBoxLayout(params_container)
        params_layout.setSpacing(10)

        title = QLabel(title_text)
        title.setStyleSheet(
            """
            font-size: 20px;
            font-weight: bold;
            color: #111111;
            margin-bottom: 20px;
            background-color: #F2FED1;
        """
        )
        title.setAlignment(Qt.AlignCenter)
        params_layout.addWidget(title)

        for placeholder, field_id in fields:
            input_field = self.create_input_field(placeholder, field_id)
            params_layout.addWidget(input_field)

        start_btn = QPushButton("START")
        start_btn.setStyleSheet(
            """
            background-color: #ABF600;
            color: #111111;
            border: 1px solid #000000;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
            margin-top: 10px;
        """
        )
        start_btn.clicked.connect(lambda: self.start_action(title_text.lower()))
        params_layout.addWidget(start_btn)

        layout.addWidget(params_container)
        layout.addStretch()
        return widget

    def create_registration_screen(self):
        fields = [
            ("Accounts file path", "accounts"),
            ("Fixed imap for all acc", "imap"),
            ("Forward mode", "forward_mode"),
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Referrals file path", "ref"),
            ("Number of threads", "threads"),
        ]
        return self.create_screen_base("registration", fields)

    def create_verification_screen(self):
        fields = [
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Proxy file for imap (Optional)", "imap_proxy"),
            ("Forward mode", "forward_mode"),
            ("Number of threads", "threads"),
        ]
        return self.create_screen_base("verification", fields)

    def create_update_screen(self):
        fields = [
            ("Proxy file path", "proxy"),
            ("Proxy rotate time (in seconds)", "rotate"),
            ("Number of threads", "threads"),
        ]
        return self.create_screen_base("update", fields)

    def create_import_screen(self):
        fields = [
            ("File path", "file_name"),
            ("Separator", "separator"),
            ("Format", "format"),
        ]
        return self.create_screen_base("import", fields)

    def create_export_screen(self):
        fields = [
            ("File path", "file_name"),
            ("Export type", "export_type"),
            ("Separator", "separator"),
            ("Format", "format"),
        ]
        return self.create_screen_base("export", fields)

    def create_imap_screen(self):
        fields = [("IMAP domain", "imap"), ("Accounts file path", "accounts")]
        return self.create_screen_base("imap", fields)

    def show_description(self, action):
        if action in DEFAULT_DESCRIPTION[self.current_language]:
            self.description_text.setText(
                DEFAULT_DESCRIPTION[self.current_language][action]
            )

    def show_screen(self, screen_name):
        screen_map = {
            "main": self.main_menu,
            "registration": self.registration_screen,
            "verification": self.verification_screen,
            "update": self.update_screen,
            "import": self.import_screen,
            "export": self.export_screen,
            "imap": self.imap_screen,
        }

        if screen_name in screen_map:
            self.stacked_widget.setCurrentWidget(screen_map[screen_name])

    def start_action(self, action):
        values = {}
        for field_id, fields in self.input_fields.items():
            if isinstance(fields, list):
                value = fields[0]["input"].text()
            else:
                value = fields["input"].text()
            # Используем точное значение из поля, даже если оно пустое
            values[field_id] = value

        self.last_args = {
            "action": action,
            "accounts": values.get("accounts", ""),
            "imap": values.get("imap", ""),
            "forward_mode": values.get("forward_mode", "") == "True",
            "proxy": values.get("proxy", ""),
            "rotate": int(values.get("rotate", 0)) if values.get("rotate") else 0,
            "ref": values.get("ref", ""),
            "threads": int(values.get("threads", 1)) if values.get("threads") else 1,
            "file_name": values.get("file_name", ""),
            "separator": values.get("separator", ""),
            "format": values.get("format", ""),
            "export_type": values.get("export_type", ""),
            "imap_proxy": values.get("imap_proxy", ""),
        }

        self.last_action = action

        self.close()

    def get_args(self):
        return self.last_args

    def open_url(self, url):
        import webbrowser

        webbrowser.open(url)

    def toggle_language(self):
        self.current_language = "en" if self.current_language == "ru" else "ru"
        self.lang_btn.setText("RUS" if self.current_language == "ru" else "ENG")

        for field_id, fields in self.input_fields.items():
            if field_id in DEFAULT_DESCRIPTION[self.current_language]:
                tooltip = DEFAULT_DESCRIPTION[self.current_language][field_id]
                if isinstance(fields, list):
                    for field in fields:
                        field["input"].setToolTip(tooltip)
                        field["label"].setToolTip(tooltip)
                        field["label"].setText(field["placeholder"])
                else:
                    fields["input"].setToolTip(tooltip)
                    fields["label"].setToolTip(tooltip)
                    fields["label"].setText(fields["placeholder"])

        for i in range(self.nav_layout.count()):
            widget = self.nav_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                text = widget.text().lower()
                if text in DEFAULT_DESCRIPTION[self.current_language]:
                    widget.setToolTip(DEFAULT_DESCRIPTION[self.current_language][text])

        if hasattr(self, "main_menu"):
            for widget in self.main_menu.findChildren(QPushButton):
                if widget.objectName() == "linkButton":
                    continue
                text = widget.text().lower()
                if text in DEFAULT_DESCRIPTION[self.current_language]:
                    widget.setToolTip(DEFAULT_DESCRIPTION[self.current_language][text])

        for screen in [
            self.registration_screen,
            self.verification_screen,
            self.update_screen,
            self.import_screen,
            self.export_screen,
            self.imap_screen,
        ]:
            if screen:
                for widget in screen.findChildren(QPushButton):
                    if widget.objectName() == "fileButton":
                        continue
                    text = widget.text().lower()
                    if text in DEFAULT_DESCRIPTION[self.current_language]:
                        widget.setToolTip(
                            DEFAULT_DESCRIPTION[self.current_language][text]
                        )


def run_ui():
    app = QApplication([])
    window = MainWindow()

    window.show()
    app.exec()
    return window.get_args()
