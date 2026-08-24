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
        
        # Probar dashboard primero
        r2 = await client.get('http://localhost:8000/api/v1/dashboard', headers={
            'Authorization': f'Bearer {token}'
        })
        print(f'Dashboard status: {r2.status_code}')
        
        # Probar clients
        r3 = await client.get('http://localhost:8000/api/v1/clients', headers={
            'Authorization': f'Bearer {token}'
        })
        print(f'Clients status: {r3.status_code}')
        
        # Probar quotes
        r4 = await client.get('http://localhost:8000/api/v1/quotes', headers={
            'Authorization': f'Bearer {token}'
        })
        print(f'Quotes status: {r4.status_code}')

asyncio.run(test())
