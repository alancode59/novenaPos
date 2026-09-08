def test_orders_health(client):
    resp = client.get("/orders/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"
