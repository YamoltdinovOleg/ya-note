# news/tests/test_content.py
from django.test import TestCase
# Импортируем функцию reverse(), она понадобится для получения адреса страницы.
from django.urls import reverse

# Импортируем функцию для получения модели пользователя.
from django.contrib.auth import get_user_model
# Дополнительно к News импортируем модель комментария.
from notes.models import Note

from notes.forms import NoteForm

User = get_user_model()


class TestDetailPage(TestCase):
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
        # Сохраняем в переменную адрес, который будет содержать
        # URL-адрес для страницы добавления новой заметки
        cls.add_url = reverse('notes:add')

    # 1 - отдельная заметка передаётся на страницу со
    # списком заметок в списке object_list в словаре context;
    def test_note_in_context(self):
        # Авторизуем клиент при помощи ранее созданного пользователя.
        self.client.force_login(self.author)

        # Загружаем страницу со списком заметок.
        response = self.client.get(reverse('notes:list'))

        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']

        # Определяем количество записей в списке.
        self.assertIn(self.note, object_list)

    # 2 - в список заметок одного пользователя не попадают
    # заметки другого пользователя;
    def test_user_notes_exclusion(self):
        # Авторизуем клиент при помощи ранее созданного читателя.
        self.client.force_login(self.reader)

        # Загружаем страницу со списком заметок.
        response = self.client.get(reverse('notes:list'))

        # Получаем список объектов из словаря контекста.
        object_list = response.context['object_list']

        # Определяем количество записей в списке.
        self.assertNotIn(self.note, object_list)

    # 3 - на страницы создания и редактирования заметки передаются  формы.
    def test_anonymous_add_has_no_form(self):
        # Авторизуем автора при помощи ранее созданного читателя.
        self.client.force_login(self.author)

        # Загружаем добавочную страницу.
        response = self.client.get(self.add_url)

        # в контексте ответа присутствует объект формы с ключом.
        self.assertIn('form', response.context)

    def test_authorized_edit_has_form(self):
        # Авторизуем клиента
        self.client.force_login(self.author)

        # Получаем URL для редактирования заметки
        url = reverse('notes:edit', args=(self.note.slug,))
        response = self.client.get(url)

        # Проверяем, что форма присутствует в контексте
        self.assertIn('form', response.context)

        # Проверяем, что объект формы соответствует нужному классу формы
        self.assertIsInstance(response.context['form'], NoteForm)
