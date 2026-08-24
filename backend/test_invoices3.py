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
        
        # Llamar facturas con timeout más largo
        try:
            r2 = await client.get('http://localhost:8000/api/v1/invoices', headers={
                'Authorization': f'Bearer {token}'
            }, timeout=30)
            print(f'Status: {r2.status_code}')
            print(f'Response: {r2.text[:500]}')
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(test())
