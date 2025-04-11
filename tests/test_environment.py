import os
import pytest


def test_env_variables_loaded():
    """
    Проверка, что переменные окружения из .env файла доступны в тестах
    """
    # Проверяем, что переменные окружения из .env файла доступны
    assert False
    assert os.environ.get("POSTGRES_PASSWORD") != None
    assert os.environ.get("POSTGRES_DB") != None
    assert os.environ.get("PORT_POSTGRES") != None
