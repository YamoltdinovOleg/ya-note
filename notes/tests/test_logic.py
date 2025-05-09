# news/tests/test_logic.py
from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


# Импортируем в код всё необходимое для работы,
# создадим класс для первой группы тестов и подготовим в нём объекты,
# необходимые для тестирования.
class TestNoteCreation(TestCase):
    # Текст комментария понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса.
    NOTE_TEXT = 'Текст комментария'
    NOTE_TITLE = 'Заголовок'
    NOTE_SLUG = 'slug'

    @classmethod
    def setUpTestData(cls):
        # Адрес добавочной страницы.
        cls.url_add = reverse('notes:add')

        # Создаём пользователя и логинимся в клиенте.
        cls.author = User.objects.create(username='Мимо Крокодил')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Создаём читающего и логинимся в клиенте.
        cls.reader = User.objects.create(username='Мимо Панда')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # Данные для POST-запроса при создании комментария.
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE,
            'slug': cls.NOTE_SLUG
        }

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, отправляя данные формы.
        response = self.client.post(self.url_add, data=self.form_data)

        # Получаем URL для страницы входа.
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.url_add}'

        # Проверяем, что анонимный пользователь перенаправляется
        # на страницу входа.
        self.assertRedirects(response, expected_url)

        # Считаем количество записей.
        notes_count = Note.objects.count()

        # Ожидаем, что записей в базе нет - сравниваем с нулём.
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        response = self.author_client.post(
            self.url_add,
            data=self.form_data
        )
        # Проверяем, что редирект привёл к разделу с успехом.
        self.assertRedirects(response, reverse('notes:success'))

        # Считаем количество заметок.
        notes_count = Note.objects.count()

        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)

        # Получаем объект заметки из базы.
        note = Note.objects.get()

        # Проверяем, что все атрибуты заметки совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.author)
        self.assertEqual(note.slug, self.NOTE_SLUG)

    def test_slug(self):
        # Удаляем slug из данных формы.
        self.form_data.pop('slug')

        # Отправляем POST-запрос с оставшимися данными формы.
        response = self.author_client.post(
            self.url_add,
            data=self.form_data
        )

        # Проверяем, что редирект приводит к успешной странице.
        self.assertRedirects(response, reverse('notes:success'))

        # Проверяем, что заметка была создана.
        self.assertEqual(Note.objects.count(), 1)

        # Получаем созданную заметку из базы данных.
        new_note = Note.objects.get()

        # Формируем ожидаемый slug на основе заголовка заметки.
        expected_slug = slugify(self.form_data['title'])

        # Проверяем, что slug заметки соответствует ожидаемому значению.
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteSlug(TestCase):
    # Текст комментария понадобится в нескольких местах кода,
    # поэтому запишем его в атрибуты класса.
    NOTE_TEXT = 'text'
    NOTE_TITLE = 'title'
    NOTE_SLUG = 'no_slug'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и логинимся в клиенте.
        cls.author = User.objects.create(username='Мимо Петух')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        # Создаём читающего и логинимся в клиенте.
        cls.reader = User.objects.create(username='Мимо Куница')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        # Данные для POST-запроса при создании комментария.
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE,
            'slug': cls.NOTE_SLUG
        }

        # Создаём новость в БД
        cls.note = Note.objects.create(
            title='title',
            text='text',
            author=cls.author,
            slug='no_slug')

        # Адрес добавочной страницы.
        cls.url_add = reverse('notes:add')
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_delete = reverse('notes:delete', args=(cls.note.slug,))
        cls.url_success = reverse('notes:success')

    def test_user_cannot_create_note_with_duplicate_slug(self):
        # Создаем первую заметку
        self.author_client.post(self.url_add, data=self.form_data)

        # Устанавливаем slug для новой заметки,
        # чтобы он совпадал с существующим
        self.form_data['slug'] = self.note.slug

        # Пытаемся создать новую заметку с дублирующимся slug
        response = self.author_client.post(self.url_add, data=self.form_data)

        # Проверяем, что мы получили ошибку для поля 'slug'
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.note.slug + WARNING
        )

        # Убеждаемся, что количество заметок в базе осталось равным 1
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        # Создаем заметку
        response = self.author_client.post(self.url_edit, self.form_data)

        # Проверяем, что редирект приводит к успешной странице
        self.assertRedirects(response, self.url_success)

        # Проверяем, что заметка была обновлена
        self.note.refresh_from_db()  # Обновляем объект из базы данных
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_user_cannot_edit_other_user_note(self):
        # Создаем заметку
        response = self.reader_client.post(self.url_edit, self.form_data)

        # Проверяем, что редирект приводит к успешной странице
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        # Проверяем, что заметка была обновлена
        self.note.refresh_from_db()  # Обновляем объект из базы данных
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_user_can_delete_own_note(self):
        # Создаем заметку
        self.author_client.post(self.url_add, data=self.form_data)
        note = Note.objects.get()

        # Удаляем заметку
        response = self.author_client.post(
            reverse('notes:delete', args=[note.slug]))

        # Проверяем, что редирект приводит к успешной странице
        self.assertRedirects(response, reverse('notes:success'))

        # Проверяем, что заметка была удалена
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_comment_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.url_delete)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), 1)
