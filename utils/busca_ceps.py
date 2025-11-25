import random, json, asyncio, time, aiohttp
import pandas as pd

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

            except Exception as e:
                if tentativa == 1:
                    print(f"Nao foi: {cep} - erro: {e}")
                    return {}

                # backoff + jitter
                delay = 2 + random.random()
                await asyncio.sleep(delay)


async def _coletar(tasks, resultados):
    for coro in asyncio.as_completed(tasks):
        resultado = await coro
        resultados.update(resultado)
    return resultados


async def _get_coords(lista_ceps, timeout_global=600):
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


async def _busca_bd(ceps_unicos: list[str]):
    """
    Recebe uma lista de CEPs unicos e devolve um df com
    cep lat lng

    Busca esses ceps no bd, caso nao encontre baixa da API e atualiza o BD
    """
    BD_PATH = "../dados/banco_dados/cep_coords.json"

    with open(BD_PATH, "r", encoding="utf-8") as f:
        banco_coords = json.load(f)

    ceps_baixar = [cep for cep in ceps_unicos if cep not in banco_coords]

    if len(ceps_baixar) > 0:
        print(f"Precisamos baixar {len(ceps_baixar)} novas coords")

        novas_coords = await _get_coords(ceps_baixar)
        banco_coords.update(novas_coords)

        with open(BD_PATH, "w", encoding="utf-8") as f:
            json.dump(banco_coords, f, ensure_ascii=False, indent=4)
    else:
        print("Nao foi necessario baixar novas coods")

    df_coords = pd.DataFrame(
        [
            {"cep_bd": str(k), "lat": float(v[0]), "lng": float(v[1])}
            for k, v in banco_coords.items()
        ]
    )

    return df_coords


# TODO criar um alerta se o cep nao existe (receber 404 da API)
async def cep_to_coords(df_raw: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    Atenção
    ----------
        Essa é uma funcao assincrona, use ``df = await cep_to_coords()``
    Recebe
    ----------
        df: com coluna de cep (já em str e sem hifen)
        col_name: nome da coluna com os ceps
    Retorna
    ----------
        o df original adicionado das colunas lat e lng, removido a coluna do cep
    Notas
    ----------
        Primeiro tenta encontrar os CEPs no BD, caso nao encontre algum, baixa via
        API e completa o BD
    """
    df = df_raw.copy()
    df["_cep"] = df[col_name].str.zfill(8)
    ceps_unicos = list(set(df["_cep"]))
    print(f"Temos {len(ceps_unicos)} CEPs diferentes a consultar")

    df_coords = await _busca_bd(ceps_unicos)

    df_final = df.merge(df_coords, how="left", left_on="_cep", right_on="cep_bd")
    df_final = df_final.drop(columns=[col_name, "_cep", "cep_bd"])

    return df_final
