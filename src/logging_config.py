"""Configuração de logging: nível por variável de ambiente NBA_DEBUG (1 = DEBUG) ou WARNING."""
import logging
import os

LOG_LEVEL = logging.DEBUG if os.environ.get("NBA_DEBUG") else logging.WARNING


def setup_logging():
    """Configura o logger raiz do app. Chamar no início do run()."""
    logging.basicConfig(
        level=LOG_LEVEL,
        format="%(levelname)s [%(name)s] %(message)s",
    )


def get_logger(name):
    """Retorna um logger com o nome do módulo."""
    return logging.getLogger(name)
