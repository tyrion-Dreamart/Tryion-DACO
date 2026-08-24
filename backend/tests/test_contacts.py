"""
Cubre PATCH /contacts/{id}, que hasta el commit a64370d era una función
incompleta: traía el contacto, no verificaba que existiera, no aplicaba
el payload y no retornaba nada — cualquier llamada terminaba en 500.
"""


async def _create_contact(client, auth_headers, legal_entity_id, **overrides):
    payload = {
        "legal_entity_id": legal_entity_id,
        "first_name": "Ana",
        "last_name": "Pérez",
        "email": "ana@example.com",
        "contact_type": "client",
        **overrides,
    }
    resp = await client.post("/api/v1/contacts", json=payload, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_and_get_contact(client, auth_headers, test_corporate_and_client):
    created = await _create_contact(client, auth_headers, test_corporate_and_client.id)

    resp = await client.get(f"/api/v1/contacts/{created['id']}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Ana"


async def test_patch_contact_updates_fields(client, auth_headers, test_corporate_and_client):
    created = await _create_contact(client, auth_headers, test_corporate_and_client.id)

    resp = await client.patch(
        f"/api/v1/contacts/{created['id']}",
        json={"first_name": "Ana María", "is_primary": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["first_name"] == "Ana María"
    assert body["is_primary"] is True
    # campos no incluidos en el payload no deben cambiar
    assert body["last_name"] == "Pérez"

    # y el cambio debe persistir de verdad, no solo en la respuesta
    resp = await client.get(f"/api/v1/contacts/{created['id']}", headers=auth_headers)
    assert resp.json()["first_name"] == "Ana María"


async def test_patch_nonexistent_contact_returns_404(client, auth_headers):
    resp = await client.patch(
        "/api/v1/contacts/does-not-exist",
        json={"first_name": "Nadie"},
        headers=auth_headers,
    )
    assert resp.status_code == 404
