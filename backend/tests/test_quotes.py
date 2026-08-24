"""
Cubre GET /quotes, que hasta el commit a64370d siempre devolvía items=[]
para cada cotización — traía las líneas de la BD y las descartaba.
"""
import uuid


async def _create_quote(client, auth_headers, client_id, **overrides):
    payload = {
        "folio": f"COT-{uuid.uuid4().hex[:8]}",
        "client_id": client_id,
        "issue_date": "2026-08-01T00:00:00Z",
        "items": [
            {"concept": "Diseño estructural", "quantity": 2, "unit_price": 1000},
            {"concept": "Supervisión", "quantity": 1, "unit_price": 500},
        ],
        **overrides,
    }
    resp = await client.post("/api/v1/quotes", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_quote_calculates_totals(client, auth_headers, test_corporate_and_client):
    quote = await _create_quote(client, auth_headers, test_corporate_and_client.id)
    assert quote["subtotal"] == 2500.0
    assert quote["total"] > quote["subtotal"]  # incluye IVA por default (has_iva=True)


async def test_list_quotes_includes_items(client, auth_headers, test_corporate_and_client):
    created = await _create_quote(client, auth_headers, test_corporate_and_client.id)

    resp = await client.get("/api/v1/quotes", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()

    listed = next(q for q in body["items"] if q["id"] == created["id"])
    assert len(listed["items"]) == 2
    concepts = {item["concept"] for item in listed["items"]}
    assert concepts == {"Diseño estructural", "Supervisión"}


async def test_duplicate_folio_rejected(client, auth_headers, test_corporate_and_client):
    quote = await _create_quote(client, auth_headers, test_corporate_and_client.id)
    resp = await client.post(
        "/api/v1/quotes",
        json={
            "folio": quote["folio"],
            "client_id": test_corporate_and_client.id,
            "issue_date": "2026-08-01T00:00:00Z",
            "items": [],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 409
