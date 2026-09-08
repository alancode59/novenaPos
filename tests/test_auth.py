from datetime import datetime, timedelta

from app import PUBLIC_ENDPOINTS
from app.auth.decorators import roles_required
from app.extensions import db
from app.models.user import User
from app.security.hashing import hash_password, verify_password


# --- Hashing (Argon2id + pepper) ---


def test_hash_and_verify_password_roundtrip_with_different_salts():
    h1 = hash_password("Sup3rSecreta!")
    h2 = hash_password("Sup3rSecreta!")

    # Salt aleatorio -> hashes distintos para el mismo password.
    assert h1 != h2

    assert verify_password(h1, "Sup3rSecreta!") is True
    assert verify_password(h2, "Sup3rSecreta!") is True


def test_verify_password_rejects_wrong_password():
    stored = hash_password("Sup3rSecreta!")
    assert verify_password(stored, "otra-cosa") is False


def test_verify_password_never_raises_on_garbage_input():
    assert verify_password("no-es-un-hash-argon2", "cualquier-cosa") is False
    assert verify_password("", "cualquier-cosa") is False
    assert verify_password(hash_password("x"), "") is False


# --- Modelo User / Flask-Login ---


def test_is_active_column_not_shadowed_by_usermixin():
    """`is_active` debe ser la columna, no la property de UserMixin."""
    inactive = User(
        username="inactivo",
        password_hash=hash_password("x"),
        role="mesero",
        is_active=False,
    )
    active = User(
        username="activo",
        password_hash=hash_password("x"),
        role="mesero",
        is_active=True,
    )

    assert inactive.is_active is False
    assert active.is_active is True

    # UserMixin.is_authenticated delega en is_active.
    assert inactive.is_authenticated is False
    assert active.is_authenticated is True
    assert inactive.is_anonymous is False


# --- Login ---


def test_login_success_creates_session(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "Sup3rSecreta!"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    set_cookie_headers = resp.headers.get_all("Set-Cookie")
    assert any("posnovena_session" in c for c in set_cookie_headers)

    # Sesion autenticada: logout debe funcionar, no rebotar.
    logout_resp = client.post("/auth/logout", follow_redirects=False)
    assert logout_resp.status_code == 302
    # `reason=logout` distingue el logout manual de una sesion expirada.
    assert logout_resp.headers["Location"] == "/auth/login?reason=logout"


def test_login_wrong_password_increments_failed_attempts(client, make_user, app):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "incorrecta"},
        headers={"Accept": "application/json"},
    )

    assert resp.status_code == 401
    # El fixture `app` ya mantiene un app_context; abrir otro rompe refresh().
    db.session.refresh(user)
    assert user.failed_login_attempts == 1
    assert user.locked_until is None


def test_login_inactive_user_rejected_even_with_valid_password(client, make_user, app):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero", is_active=False)

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "Sup3rSecreta!"},
        headers={"Accept": "application/json"},
    )

    assert resp.status_code == 401

    # Sin autenticar: logout debe redirigir a login.
    logout_resp = client.post(
        "/auth/logout",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert logout_resp.status_code in (302, 401)


def test_lockout_after_five_failed_attempts(client, make_user, app):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    for _ in range(5):
        resp = client.post(
            "/auth/login",
            data={"username": "ana", "password": "incorrecta"},
            headers={"Accept": "application/json"},
        )
        assert resp.status_code == 401

    db.session.refresh(user)
    assert user.failed_login_attempts == 5
    assert user.locked_until is not None
    assert user.locked_until > datetime.utcnow()
    # Debe rondar los 15 minutos, con margen de ejecucion.
    assert user.locked_until < datetime.utcnow() + timedelta(minutes=16)


def test_locked_account_rejects_even_correct_password(client, make_user, app):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    db.session.refresh(user)
    user.failed_login_attempts = 5
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "Sup3rSecreta!"},
        headers={"Accept": "application/json"},
    )

    # locked_until se revisa ANTES del password: por eso no resetea intentos.
    assert resp.status_code == 401
    db.session.refresh(user)
    assert user.failed_login_attempts == 5


def test_logout_clears_session(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    client.post("/auth/login", data={"username": "ana", "password": "Sup3rSecreta!"})

    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 302

    # Tras logout, un segundo logout (que exige sesion) debe rebotar.
    second_logout = client.post(
        "/auth/logout", headers={"Accept": "application/json"}
    )
    assert second_logout.status_code == 401


def test_login_error_messages_are_generic_and_indistinguishable(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp_no_user = client.post(
        "/auth/login",
        data={"username": "no-existe", "password": "lo-que-sea"},
        headers={"Accept": "application/json"},
    )
    resp_wrong_password = client.post(
        "/auth/login",
        data={"username": "ana", "password": "incorrecta"},
        headers={"Accept": "application/json"},
    )

    assert resp_no_user.status_code == resp_wrong_password.status_code == 401
    assert resp_no_user.get_json() == resp_wrong_password.get_json()


def test_login_error_messages_indistinguishable_when_locked(client, make_user, app):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    db.session.refresh(user)
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    resp_locked = client.post(
        "/auth/login",
        data={"username": "ana", "password": "Sup3rSecreta!"},
        headers={"Accept": "application/json"},
    )
    resp_no_user = client.post(
        "/auth/login",
        data={"username": "no-existe", "password": "lo-que-sea"},
        headers={"Accept": "application/json"},
    )

    assert resp_locked.status_code == resp_no_user.status_code == 401
    assert resp_locked.get_json() == resp_no_user.get_json()


# --- Redireccion `next` (anti open-redirect) ---


def test_login_redirects_to_safe_relative_next(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={
            "username": "ana",
            "password": "Sup3rSecreta!",
            "next": "/orders/health",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/orders/health"


def test_login_rejects_absolute_url_as_next(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={
            "username": "ana",
            "password": "Sup3rSecreta!",
            "next": "https://evil.example.com/phishing",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert "evil.example.com" not in location


def test_login_rejects_protocol_relative_url_as_next(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={
            "username": "ana",
            "password": "Sup3rSecreta!",
            "next": "//evil.example.com/phishing",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert "evil.example.com" not in location


# --- roles_required ---


def _register_admin_only_route(app):
    @app.route("/test-only/admin-area", methods=["GET"])
    @roles_required("admin")
    def _admin_only_view():
        return "ok-admin", 200

    return "_admin_only_view"


def test_roles_required_rejects_anonymous_with_redirect(app, client):
    _register_admin_only_route(app)

    resp = client.get(
        "/test-only/admin-area",
        headers={"Accept": "text/html"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 401)


def test_roles_required_rejects_anonymous_with_json_401(app, client):
    _register_admin_only_route(app)

    resp = client.get(
        "/test-only/admin-area",
        headers={"Accept": "application/json"},
    )
    assert resp.status_code == 401


def test_roles_required_forbids_wrong_role(app, client, make_user):
    _register_admin_only_route(app)
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    client.post(
        "/auth/login", data={"username": "mesero1", "password": "Sup3rSecreta!"}
    )

    resp = client.get("/test-only/admin-area")
    assert resp.status_code == 403


def test_roles_required_allows_matching_role(app, client, make_user):
    _register_admin_only_route(app)
    make_user(username="admin1", password="Sup3rSecreta!", role="admin")

    client.post(
        "/auth/login", data={"username": "admin1", "password": "Sup3rSecreta!"}
    )

    resp = client.get("/test-only/admin-area")
    assert resp.status_code == 200
    assert resp.get_data(as_text=True) == "ok-admin"


# --- Enumeracion de app.url_map: todo endpoint esta protegido o es publico ---


def test_every_endpoint_is_public_or_explicitly_role_protected(app):
    unprotected = []
    for rule in app.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint in PUBLIC_ENDPOINTS:
            continue
        view_func = app.view_functions[endpoint]
        if not getattr(view_func, "_role_protected", False):
            unprotected.append(endpoint)

    assert unprotected == [], (
        "Endpoints sin @roles_required/login_required_marked ni en "
        f"PUBLIC_ENDPOINTS: {unprotected}"
    )


# --- Renderizado de plantillas ---


def test_all_templates_compile(app):
    """Toda plantilla debe compilar, aunque ninguna vista la use todavia."""
    from jinja2 import TemplateSyntaxError

    errores = []
    for nombre in app.jinja_env.list_templates():
        try:
            app.jinja_env.get_template(nombre)
        except TemplateSyntaxError as exc:
            errores.append(f"{nombre}:{exc.lineno}: {exc.message}")

    assert errores == [], "Plantillas con error de sintaxis: " + "; ".join(errores)


def test_login_page_renders_form(client):
    """Ejerce el render real, no solo la compilacion de la plantilla."""
    resp = client.get("/auth/login", headers={"Accept": "text/html"})

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'name="username"' in html
    assert 'name="password"' in html
    assert "<form" in html


def test_login_page_includes_csrf_token(app, client):
    """Las demas pruebas corren sin CSRF: sin esto nadie verifica el token."""
    app.config["WTF_CSRF_ENABLED"] = True

    resp = client.get("/auth/login", headers={"Accept": "text/html"})

    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'name="csrf_token"' in html
    assert 'value=""' not in html.split('name="csrf_token"')[1][:40]


# --- Repropagacion de `username` (nunca `password`) tras un login fallido ---


def test_failed_login_repropagates_username_but_never_password(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "lo-que-sea-incorrecto"},
        headers={"Accept": "text/html"},
    )

    assert resp.status_code == 401
    html = resp.get_data(as_text=True)
    assert 'value="ana"' in html
    assert "lo-que-sea-incorrecto" not in html


def test_failed_login_with_unknown_user_repropagates_username_too(client, make_user):
    """Repropagar `username` tambien para usuarios inexistentes."""
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={"username": "no-existe", "password": "cualquier-cosa"},
        headers={"Accept": "text/html"},
    )

    assert resp.status_code == 401
    html = resp.get_data(as_text=True)
    assert 'value="no-existe"' in html
    assert "cualquier-cosa" not in html


# --- must_change_password ---


def _force_must_change_password(app, user):
    db.session.refresh(user)
    user.must_change_password = True
    db.session.commit()


def test_login_with_must_change_password_redirects_to_change_password(
    client, make_user, app
):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    _force_must_change_password(app, user)

    resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "Sup3rSecreta!"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/auth/change-password"


def test_must_change_password_blocks_navigation_to_other_routes(
    client, make_user, app
):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    _force_must_change_password(app, user)

    client.post(
        "/auth/login", data={"username": "ana", "password": "Sup3rSecreta!"}
    )

    # Ir directo al landing debe rebotar a change_password.
    resp = client.get("/orders/tables", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/auth/change-password"

    # Un endpoint publico si debe seguir siendo alcanzable.
    public_resp = client.get("/orders/health")
    assert public_resp.status_code == 200

    # auth.logout tambien debe seguir alcanzable (via de escape del flujo).
    logout_resp = client.post("/auth/logout", follow_redirects=False)
    assert logout_resp.status_code == 302


def test_change_password_success_clears_flag_and_allows_navigation(
    client, make_user, app
):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    _force_must_change_password(app, user)

    client.post(
        "/auth/login", data={"username": "ana", "password": "Sup3rSecreta!"}
    )

    resp = client.post(
        "/auth/change-password",
        data={
            "current_password": "Sup3rSecreta!",
            "new_password": "OtraSup3rSecreta!",
            "confirm_password": "OtraSup3rSecreta!",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/orders/tables"

    db.session.refresh(user)
    assert user.must_change_password is False
    assert user.password_changed_at is not None
    assert verify_password(user.password_hash, "OtraSup3rSecreta!")

    # Ya no deberia estar bloqueado: puede navegar a su landing.
    landing_resp = client.get("/orders/tables")
    assert landing_resp.status_code == 200


def test_change_password_rejects_wrong_current_password(client, make_user, app):
    user = make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    _force_must_change_password(app, user)

    client.post(
        "/auth/login", data={"username": "ana", "password": "Sup3rSecreta!"}
    )

    resp = client.post(
        "/auth/change-password",
        data={
            "current_password": "incorrecta",
            "new_password": "OtraSup3rSecreta!",
            "confirm_password": "OtraSup3rSecreta!",
        },
    )

    assert resp.status_code == 400
    db.session.refresh(user)
    assert user.must_change_password is True


# --- Landing por rol ---


def test_landing_url_by_role(client, make_user):
    cases = [
        ("mesero", "/orders/tables"),
        ("cocina", "/kitchen/queue"),
        ("caja", "/cashier/pending"),
        ("admin", "/products/dashboard"),
    ]

    for role, expected_landing in cases:
        username = f"user-{role}"
        make_user(username=username, password="Sup3rSecreta!", role=role)

        resp = client.post(
            "/auth/login",
            data={"username": username, "password": "Sup3rSecreta!"},
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == expected_landing

        landing_resp = client.get(expected_landing)
        assert landing_resp.status_code == 200

        client.post("/auth/logout")


# --- `next` validado contra el rol del usuario autenticado ---


def test_next_of_own_role_is_honored(client, make_user):
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={
            "username": "mesero1",
            "password": "Sup3rSecreta!",
            "next": "/orders/tables",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/orders/tables"


def test_next_of_another_role_is_ignored_silently(client, make_user):
    """`next` de otra area: ni aterriza ahi ni ve error, va a su landing."""
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={
            "username": "mesero1",
            "password": "Sup3rSecreta!",
            "next": "/products/dashboard",
        },
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert resp.headers["Location"] == "/orders/tables"

    # Sin mensaje de error: la respuesta es un redirect limpio.
    assert resp.get_data(as_text=True) == "" or "error" not in resp.headers


# --- Senal de motivo al redirigir a /auth/login (reason=expired|logout) ---


def test_session_expiration_redirects_with_reason_expired(client, make_user, app):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")
    client.post(
        "/auth/login", data={"username": "ana", "password": "Sup3rSecreta!"}
    )

    with client.session_transaction() as flask_session:
        # Fuerza la sesion a un instante ya vencido.
        flask_session["expires_at"] = 0

    resp = client.get(
        "/orders/tables", headers={"Accept": "text/html"}, follow_redirects=False
    )

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/auth/login")
    assert "reason=expired" in location


def test_first_visit_to_protected_route_has_no_reason(client):
    """Sin sesion previa el redirect no lleva `reason`, solo `next`."""
    resp = client.get(
        "/orders/tables", headers={"Accept": "text/html"}, follow_redirects=False
    )

    assert resp.status_code == 302
    location = resp.headers["Location"]
    assert location.startswith("/auth/login")
    assert "reason=" not in location


# --- Rate limit de /auth/login (429 distinguible de credenciales invalidas) ---


def test_rate_limit_exceeded_returns_distinguishable_429(client, make_user):
    make_user(username="ana", password="Sup3rSecreta!", role="mesero")

    # Limite 5/min: la sexta rebota por rate limit, no por credenciales.
    for _ in range(5):
        client.post(
            "/auth/login",
            data={"username": "ana", "password": "incorrecta"},
            headers={"Accept": "application/json"},
        )

    limited_resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "incorrecta"},
        headers={"Accept": "application/json"},
    )

    assert limited_resp.status_code == 429
    assert limited_resp.get_json() == {"error": "rate_limit_exceeded"}

    limited_html_resp = client.post(
        "/auth/login",
        data={"username": "ana", "password": "incorrecta"},
        headers={"Accept": "text/html"},
    )
    assert limited_html_resp.status_code == 429
    assert "<form" in limited_html_resp.get_data(as_text=True)


# --- Handler 403 generico ---


def test_forbidden_renders_403_template_for_html(app, client, make_user):
    _register_admin_only_route(app)
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    client.post(
        "/auth/login", data={"username": "mesero1", "password": "Sup3rSecreta!"}
    )

    resp = client.get(
        "/test-only/admin-area", headers={"Accept": "text/html"}
    )

    assert resp.status_code == 403
    assert "Acceso denegado" in resp.get_data(as_text=True)


def test_forbidden_returns_json_when_requested(app, client, make_user):
    _register_admin_only_route(app)
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    client.post(
        "/auth/login", data={"username": "mesero1", "password": "Sup3rSecreta!"}
    )

    resp = client.get(
        "/test-only/admin-area", headers={"Accept": "application/json"}
    )

    assert resp.status_code == 403
    assert resp.get_json() == {"error": "forbidden"}


# --- Normalizacion de username (Postgres distingue mayusculas) -------------


def test_normalize_username_canonicaliza():
    from app.security.usernames import normalize_username

    assert normalize_username("  Admin ") == "admin"
    assert normalize_username("MESERO") == "mesero"
    assert normalize_username(None) == ""


def test_login_acepta_username_con_mayusculas(client, make_user):
    """Postgres distingue mayusculas; sin normalizar, `Admin` no entraria."""
    make_user(username="mesero1", password="Sup3rSecreta!", role="mesero")

    resp = client.post(
        "/auth/login",
        data={"username": "MeSeRo1", "password": "Sup3rSecreta!"},
        follow_redirects=False,
    )

    assert resp.status_code == 302
    assert "/auth/login" not in resp.headers["Location"]
