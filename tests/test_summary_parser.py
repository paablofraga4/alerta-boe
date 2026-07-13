"""El parsing del sumario es la parte más frágil (dict-o-lista en cada nivel)."""

from boe.clients.summary import parse_summary


def test_parses_all_valid_items(sumario):
    items = parse_summary(sumario)
    # 3 items válidos; el cuarto (sin identificador) se descarta.
    assert len(items) == 3
    ids = {i.boe_id for i in items}
    assert ids == {"BOE-A-2024-0001", "BOE-A-2024-0002", "BOE-A-2024-0003"}


def test_departamento_as_dict_with_item(sumario):
    item = next(i for i in sumario_items(sumario) if i.boe_id == "BOE-A-2024-0001")
    assert item.departamento == "MINISTERIO DE HACIENDA"
    assert item.seccion == "I. Disposiciones generales"
    assert item.epigrafe is None
    assert item.pages == 5  # 100..104


def test_departamento_as_list_with_epigrafe_and_single_item(sumario):
    item = next(i for i in sumario_items(sumario) if i.boe_id == "BOE-A-2024-0002")
    assert item.departamento == "MINISTERIO DE JUSTICIA"
    assert item.epigrafe == "Nombramientos"
    assert item.pages == 1  # 200..200


def test_missing_pages_is_none(sumario):
    item = next(i for i in sumario_items(sumario) if i.boe_id == "BOE-A-2024-0003")
    assert item.pages is None
    assert item.url_pdf.endswith("BOE-A-2024-0003.pdf")


def test_empty_payload_returns_empty_list():
    assert parse_summary({}) == []
    assert parse_summary({"data": {}}) == []


def sumario_items(payload):
    return parse_summary(payload)
