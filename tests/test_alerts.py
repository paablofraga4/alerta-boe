"""F6: matcher de alertas, servicio de envío (dry-run) e idempotencia."""

from datetime import date

from sqlalchemy import select

from boe.alerts.matcher import find_matches
from boe.alerts.service import run_for_date
from boe.core.enums import NotificationChannel, NotificationStatus, Scope
from boe.core.models import Document, Notification, Subscription, Topic, User

_FECHA = date(2024, 7, 9)


async def _seed(session_factory):
    async with session_factory() as s:
        subv = Topic(name="Subvención", slug="subvencion")
        d1 = Document(
            boe_id="BOE-A-2024-0001",
            published_at=_FECHA,
            title="Ayudas a autónomos",
            full_text="El Gobierno aprueba ayudas para autónomos.",
            scope=Scope.NACIONAL,
        )
        d1.topics.append(subv)
        d2 = Document(
            boe_id="BOE-A-2024-0002",
            published_at=_FECHA,
            title="Nombramiento en Justicia",
            scope=Scope.OTRO,
        )
        s.add_all([d1, d2])
        user = User(email="ana@example.com")
        s.add(user)
        await s.flush()
        # Suscripción por tema 'subvencion' → solo casa d1.
        s.add(Subscription(
            user_id=user.id, channel=NotificationChannel.EMAIL,
            destination="ana@example.com", topic_slug="subvencion",
        ))
        await s.commit()


async def test_matcher_filters_by_topic(session_factory):
    await _seed(session_factory)
    async with session_factory() as s:
        matches = await find_matches(s, _FECHA)
    assert len(matches) == 1
    assert [d.boe_id for d in matches[0].documents] == ["BOE-A-2024-0001"]


async def test_service_sends_and_is_idempotent(session_factory):
    await _seed(session_factory)

    first = await run_for_date(_FECHA, session_factory=session_factory)
    assert first["enviadas"] == 1  # dry-run cuenta como enviada

    async with session_factory() as s:
        notes = (await s.execute(select(Notification))).scalars().all()
        assert len(notes) == 1
        assert notes[0].status == NotificationStatus.SENT

    # Segunda pasada: no reenvía (ya notificado).
    second = await run_for_date(_FECHA, session_factory=session_factory)
    assert second["enviadas"] == 0
    async with session_factory() as s:
        notes = (await s.execute(select(Notification))).scalars().all()
    assert len(notes) == 1


async def test_keyword_and_scope_filters(session_factory):
    async with session_factory() as s:
        d = Document(
            boe_id="BOE-A-2024-0003",
            published_at=_FECHA,
            title="Orden sobre transporte escolar",
            full_text="Regula el transporte escolar en Galicia.",
            scope=Scope.AUTONOMICO,
        )
        s.add(d)
        u = User(email="luis@example.com")
        s.add(u)
        await s.flush()
        s.add(Subscription(user_id=u.id, channel=NotificationChannel.EMAIL,
                           destination="luis@example.com", keyword="transporte escolar",
                           scope=Scope.AUTONOMICO))
        # keyword que no aparece → no casa
        s.add(Subscription(user_id=u.id, channel=NotificationChannel.EMAIL,
                           destination="luis@example.com", keyword="pesca"))
        await s.commit()

    async with session_factory() as s:
        matches = await find_matches(s, _FECHA)
    matched_keywords = {m.subscription.keyword for m in matches}
    assert "transporte escolar" in matched_keywords
    assert "pesca" not in matched_keywords
