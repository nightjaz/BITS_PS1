from main import app

def test_hello():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello Finnegan bro!" in response.data
