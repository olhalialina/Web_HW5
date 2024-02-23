from typing import List, Dict, Any

import aiohttp
import asyncio
from datetime import datetime, timedelta
import sys

BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="
MAX_DAYS = 10


def limit_days(num: int) -> int:
    return max(1, min(num, MAX_DAYS))


def get_dates(num_days: int) -> List[str]:
    today = datetime.now()
    return [(today - timedelta(days=i)).strftime("%d.%m.%Y") for i in range(num_days)]


def format_data(raw_data: dict, currency_list: set) -> dict:
    formatted = {raw_data["date"]: {}}

    if "exchangeRate" in raw_data:
        for rate in raw_data["exchangeRate"]:
            currency = rate.get("currency")
            sale_rate = rate.get("saleRate")
            purchase_rate = rate.get("purchaseRate")

            if currency and sale_rate is not None and purchase_rate is not None:
                if currency in currency_list:
                    temp_dict = {
                        currency: {"sale": sale_rate, "purchase": purchase_rate}
                    }
                    formatted[raw_data["date"]].update(temp_dict)

    return formatted


async def fetch_exchange_rates(date: str, currency_list: set) -> Dict[str, Any]:
    url = f"{BASE_URL}{date}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, ssl=False) as response:
                response.raise_for_status()
                data = await response.json()
                return format_data(data, currency_list)
        except aiohttp.ClientError as e:
            print(f"Error for date {date}: {e}")


async def exchange_rates(days: int, currency_list: set) -> tuple[Any]:
    list_dates = get_dates(limit_days(days))
    tasks = [fetch_exchange_rates(date, currency_list) for date in list_dates]
    return await asyncio.gather(*tasks)


async def main(days: int, *add_currency) -> tuple[Any]:
    currency_list = {"USD", "EUR"}
    all_currency = [
        "AUD",
        "AZN",
        "BYN",
        "CAD",
        "CHF",
        "CNY",
        "CZK",
        "DKK",
        "EUR",
        "GBP",
        "GEL",
        "HUF",
        "ILS",
        "JPY",
        "KZT",
        "MDL",
        "NOK",
        "PLN",
        "SEK",
        "SGD",
        "TMT",
        "TRY",
        "UAH",
        "USD",
        "UZS",
        "XAU",
    ]

    if isinstance(days, str):
        days = int(days) if days.isdigit() else 1

    if days > MAX_DAYS:
        print(
            "Note: Maximum number of days allowed is 10. Displaying rates for the last 10 days."
        )

    for cur in add_currency:
        cur = cur.upper()
        if cur in all_currency:
            currency_list.add(cur)
        else:
            print(f"{cur} is not a valid currency code")

    return await exchange_rates(days, currency_list)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python exchange.py <number_of_days> <currency>")
        sys.exit(1)

    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(main(*sys.argv[1:]))
    loop.close()

    print(result)