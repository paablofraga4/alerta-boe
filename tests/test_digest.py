"""Digest semanal: composición del email y envío por suscripción (dry-run)."""

from datetime import date, timedelta

from boe.alerts.digest import render_digest, run_weekly
from boe.core.enums import NotificationChannel, Scope
from boe.core.models import Document, Subscription, Summary, Topic, User

_HASTA = date(2024, 7, 12)


async def _seed(session_factory):
    async with session_factory() as s:
        subv = Topic(name="Subvención", slug="subvencion")
        d1 = Document(
            boe_id="BOE-A-2024-0001",
            published_at=_HASTA - timedelta(days=2),
            title="Ayudas a autónomos",
            full_text="El Gobierno aprueba ayudas para autónomos.",
            scope=Scope.NACIONAL,
            topics=[subv],
        )
        # Fuera de la ventana semanal → no debe aparecer.
        d2 = Document(
            boe_id="BOE-A-2024-0000",
            published_at=_HASTA - timedelta(days=30),
            title="Ayudas antiguas",
            scope=Scope.NACIONAL,
            topics=[subv],
        )
        s.add_all([d1, d2])
        u = User(email="ana@example.com")
        s.add(u)
        await s.flush()
        s.add(
            Summary(
                document_id=d1.id,
                short="Nuevas ayudas para autónomos.",
                structured={
                    "plazos": [
                        {"fecha": "31 de diciembre de 2099", "accion": "Solicitar la ayuda"}
                    ]
                },
            )
        )
        s.add(
            Subscription(
                user_id=u.id,
                channel=NotificationChannel.EMAIL,
                destination="ana@example.com",
                topic_slug="subvencion",
            )
        )
        # Suscripción sin novedades esta semana → se salta.
        s.add(
            Subscription(
                user_id=u.id,
                channel=NotificationChannel.EMAIL,
                destination="ana@example.com",
                keyword="pesca",
            )
        )
        await s.commit()


async def test_run_weekly_sends_and_skips(session_factory):
    await _seed(session_factory)
    result = await run_weekly(_HASTA, session_factory=session_factory)
    # Sin SMTP configurado el notificador va en dry-run y cuenta como enviado.
    assert result["enviados"] == 1
    assert result["sin_novedades"] == 1
    assert result["fallidos"] == 0


def test_render_digest_body():
    doc = Document(
        boe_id="BOE-A-2024-0001",
        published_at=_HASTA,
        title="Ayudas a autónomos",
        scope=Scope.NACIONAL,
    )
    doc.summaries = [
        Summary(
            short="Nuevas ayudas.",
            structured={
                "plazos": [{"fecha": "31 de diciembre de 2099", "accion": "Solicitar"}]
            },
        )
    ]
    rendered = render_digest([doc], desde=_HASTA - timedelta(days=6), hasta=_HASTA)
    assert rendered is not None
    subject, body = rendered
    assert "El BOE en 3 minutos" in subject
    assert "Nuevas ayudas." in body
    assert "Solicitar" in body            # el plazo vivo aparece
    assert "/documento/BOE-A-2024-0001" in body
    assert "/radar" in body


def test_render_digest_empty():
    assert render_digest([], desde=_HASTA - timedelta(days=6), hasta=_HASTA) is None
