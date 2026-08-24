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
        
        # Probar invoices con manejo de error detallado
        try:
            r2 = await client.get('http://localhost:8000/api/v1/invoices', headers={
                'Authorization': f'Bearer {token}'
            }, timeout=30)
            print(f'Invoices status: {r2.status_code}')
            print(f'Invoices response: {r2.text[:1000]}')
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}')

asyncio.run(test())
