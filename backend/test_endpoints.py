import asyncio
import httpx

async def test():
    async with httpx.AsyncClient(follow_redirects=True) as client:
        # Login
        r = await client.post('http://localhost:8000/api/v1/auth/login', json={
            'email': 'admin@gmail.com',
            'password': 'admin123'
        })
        token = r.json()['access_token']
        
        # Probar diferentes endpoints para ver cuál funciona
        endpoints = [
            'http://localhost:8000/api/v1/invoices',
            'http://localhost:8000/api/v1/clients',
            'http://localhost:8000/api/v1/dashboard',
        ]
        
        for endpoint in endpoints:
            r = await client.get(endpoint, headers={'Authorization': f'Bearer {token}'})
            print(f'{endpoint}: {r.status_code}')

asyncio.run(test())
