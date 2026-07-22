"""Render por lotes de los vídeos aprobados.

Busca piezas TikTok APROBADAS sin vídeo (`asset_path` vacío), genera sus assets
(props + subtítulos + narración TTS) y llama al render de Remotion
(`apps/video/render.mjs`). Pensado para correr en GitHub Actions, donde el TTS
y Chrome funcionan sin restricciones; el runner de node es inyectable para
poder testear sin renderizar de verdad.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from boe.content.video.render import build_props, render_assets
from boe.core.db import SessionLocal
from boe.core.enums import ContentChannel, ContentStatus
from boe.core.models import ContentPost

log = structlog.get_logger(__name__)

_RENDER_MJS = Path(__file__).resolve().parents[3] / "apps" / "video" / "render.mjs"

# Runner por defecto: node apps/video/render.mjs <props.json> <out.mp4>
NodeRunner = Callable[[Path, Path], Awaitable[bool]]


async def _node_render(props_path: Path, out_path: Path) -> bool:
    proc = await asyncio.create_subprocess_exec(
        "node", str(_RENDER_MJS), str(props_path), str(out_path),
        cwd=str(_RENDER_MJS.parent),
    )
    return await proc.wait() == 0


async def pending_posts(session: AsyncSession) -> list[ContentPost]:
    """Piezas TikTok aprobadas que aún no tienen vídeo renderizado."""
    stmt = (
        select(ContentPost)
        .where(
            ContentPost.channel == ContentChannel.TIKTOK,
            ContentPost.status == ContentStatus.APPROVED,
            ContentPost.asset_path.is_(None),
        )
        .options(selectinload(ContentPost.document))
        .order_by(ContentPost.id)
    )
    return list((await session.execute(stmt)).scalars().all())


async def render_approved(
    out_dir: Path,
    *,
    session_factory: async_sessionmaker[AsyncSession] = SessionLocal,
    runner: NodeRunner = _node_render,
) -> dict[str, int]:
    """Renderiza los vídeos pendientes. Devuelve {renderizados, fallidos, sin_guion}."""
    # Absoluto: el runner de Remotion se ejecuta con cwd=apps/video, así que las
    # rutas relativas (p. ej. "data/videos/27.props.json") no se resolverían.
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = failed = skipped = 0

    async with session_factory() as session:
        posts = await pending_posts(session)
        for post in posts:
            extra = (post.metrics or {}).get("extra") or {}
            narration = extra.get("narration")
            if not narration:
                skipped += 1
                log.warning("video_sin_guion_estructurado", post_id=post.id)
                continue

            boe_id = extra.get("boe_id") or (post.document.boe_id if post.document else str(post.id))
            props = build_props(
                boe_id,
                extra.get("hook", ""),
                list(extra.get("points", [])),
                extra.get("cta", ""),
                narration,
            )
            paths = await render_assets(post.id, props, out_dir)
            out_path = out_dir / f"{post.id}.mp4"
            ok = await runner(Path(paths["props"]), out_path)
            if ok and out_path.exists():
                post.asset_path = str(out_path)
                rendered += 1
                log.info("video_renderizado", post_id=post.id, path=str(out_path))
            else:
                failed += 1
                log.error("video_fallido", post_id=post.id)
        await session.commit()

    return {"renderizados": rendered, "fallidos": failed, "sin_guion": skipped}
