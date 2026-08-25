from backend.agent.moderation import contiene_termino_bloqueado


def test_detecta_termino_con_mayusculas_y_acento():
    assert contiene_termino_bloqueado("Eres un IMBÉCIL") is True


def test_respeta_limites_de_palabra():
    assert contiene_termino_bloqueado("La computación distribuida") is False

