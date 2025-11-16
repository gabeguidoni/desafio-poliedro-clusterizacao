import aiohttp
import time
import asyncio
import random

sem = asyncio.Semaphore(100)


async def _call(async_client, cep: str) -> dict[str, tuple[str, str]]:
    """
    retorna um dicionario do tipo {cep: (lat, lng),}
    """

    url = f"https://cep.awesomeapi.com.br/json/{cep}"

    for tentativa in range(2):  # tenta so duas vezes
        async with sem:
            try:
                async with async_client.get(url, timeout=5) as resp:
                    if resp.status != 200:
                        raise Exception(f"HTTP {resp.status}")

                    data = await resp.json()

                    lat = data.get("lat", None)
                    lng = data.get("lng", None)

                    if not lat or not lng:
                        print(f"CEP vazio: {cep}")
                        return {}

                    return {cep: (lat, lng)}

            except Exception:
                if tentativa == 1:
                    print(f"Deu bug: {cep}")
                    return {}

                # backoff + jitter
                delay = 1 + random.random()
                await asyncio.sleep(delay)


async def _coletar(tasks, resultados):
    for coro in asyncio.as_completed(tasks):
        resultado = await coro
        resultados.update(resultado)
    return resultados


async def get_coords(lista_ceps, timeout_global=600):
    inicio = time.time()
    resultados = {}

    async with aiohttp.ClientSession() as async_client:
        tasks = [_call(async_client, cep) for cep in lista_ceps]

        try:
            await asyncio.wait_for(_coletar(tasks, resultados), timeout=timeout_global)
        except asyncio.TimeoutError:
            print(f"Tempo esgotado, retorno parcial: {len(resultados)}")

    print(f"duração: {round(time.time() - inicio,2)}s para {len(resultados)} CEPs")
    return resultados
