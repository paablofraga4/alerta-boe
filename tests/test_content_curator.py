"""Scoring del curador: función pura, sin LLM ni DB."""

from boe.content.curator import CandidateSignals, rank, score
from boe.core.enums import Scope


def _sig(**kw):
    base = dict(
        boe_id="BOE-A-2024-0001",
        scope=Scope.OTRO,
        rango=None,
        topics=[],
        n_references=0,
        has_summary=False,
    )
    base.update(kw)
    return CandidateSignals(**base)


def test_national_law_scores_higher_than_local_notice():
    ley = _sig(scope=Scope.NACIONAL, rango="Ley Orgánica",
              topics=["Economía"], n_references=6, has_summary=True)
    anuncio = _sig(scope=Scope.OTRO, rango="Anuncio")
    assert score(ley) > score(anuncio)
    assert 0.0 <= score(ley) <= 1.0


def test_high_interest_topics_boost():
    con = _sig(scope=Scope.NACIONAL, topics=["Subvención", "Sanidad"])
    sin = _sig(scope=Scope.NACIONAL, topics=["Cultura"])
    assert score(con) > score(sin)


def test_rank_returns_top_n_sorted():
    cands = [
        _sig(boe_id="a", scope=Scope.OTRO),
        _sig(boe_id="b", scope=Scope.NACIONAL, rango="Ley", topics=["Economía"], has_summary=True),
        _sig(boe_id="c", scope=Scope.AUTONOMICO, topics=["Educación"]),
    ]
    top = rank(cands, top_n=2)
    assert len(top) == 2
    assert top[0][0].boe_id == "b"  # el más interesante primero
    assert top[0][1] >= top[1][1]
