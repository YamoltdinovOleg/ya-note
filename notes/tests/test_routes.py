# news/tests/test_routes.py
from http import HTTPStatus

# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    # Метод setUpTestData — это специальный метод в классе тестов Django,
    # который вызывается один раз перед выполнением всех тестов в этом классе
    def setUpTestData(cls):

        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Лев Толстой')
        cls.reader = User.objects.create(username='Читатель простой')

        # Строка создания заметки
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author
        )

    # 3 - Страницы отдельной заметки, удаления и
    # редактирования заметки доступны только автору заметки.
    def test_availability_for_edit_delete_detail(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in (
                'notes:edit',
                'notes:delete',
                'notes:detail'
            ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    # 4 - При попытке перейти на страницы, анонимный пользователь
    # перенаправляется на страницу логина.
    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in (
            'notes:edit',
            'notes:delete',
            'notes:detail',
            'notes:add',
            'notes:list',
            'notes:success'
        ):
            with self.subTest(name=name):
                # Проверка на наличие аргументов
                if name in (
                    'notes:edit',
                    'notes:delete',
                    'notes:detail'
                ):
                    url = reverse(name, args=(self.note.slug,))
                else:
                    url = reverse(name)
                # Получаем ожидаемый адрес страницы логина,
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next, в
                # котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url)

    # 1 - Главная страница доступна анонимному пользователю.
    # 5 - Страницы регистрации пользователей, входа в учетную запись и выхода
    # из неё доступны всем пользователям.
    def test_pages_availability(self):
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            # Путь для главной страницы не принимает
            # никаких позиционных аргументов, 
            # поэтому вторым параметром ставим None.
            ('notes:home', None),
            ('users:signup', None),
            ('users:login', None),
            ('users:logout', None)
        )
        # Итерируемся по внешнему кортежу 
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # 2 - Аутентифицированному пользователю доступна страница со
    # списком заметок, страница успешного добавления заметки,
    # страница добавления новой заметки.
    def test_notes_done_add_available(self):
        # Получаем объект пользователя, который будет
        # использоваться для аутентификации.
        user = self.author
        # Аутентифицируем пользователя в тестовом клиенте.
        self.client.force_login(user)
        # Определяем кортеж с именами URL-адресов,
        # которые мы собираемся протестировать.
        names = (
            'notes:add',
            'notes:list',
            'notes:success'
        )
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
