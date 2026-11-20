"""The tools the evaluation agents can call: small, deterministic, local (no network), so every answer
can be checked against known results. One city's weather service always fails, and unknown products,
cities and currencies return an error, to see how models report failures. The tools after "held-out
set" are used only by questions_heldout.json.

TOOLS maps a name to (function, OpenAI tool schema); run_tool(name, args) returns the JSON-able result.
"""
import ast
import json
import math
import operator

# ---------------------------------------------------------------- finance
def loan_cost(principal: float, annual_rate: float, years: float) -> dict:
    """Monthly payment of an amortised loan. annual_rate is a decimal: 0.07 for 7%."""
    n = round(years * 12)
    if principal <= 0 or n <= 0 or annual_rate < 0:
        return {"error": "principal and years must be positive and annual_rate not negative"}
    r = annual_rate / 12
    monthly = principal / n if r == 0 else principal * r / (1 - (1 + r) ** -n)
    total = monthly * n
    return {"monthly_payment": round(monthly, 2), "total_paid": round(total, 2),
            "total_interest": round(total - principal, 2), "months": n}


def compound_interest(principal: float, annual_rate: float, years: float, compounds_per_year: int = 12) -> dict:
    """Value of a deposit with compound interest. annual_rate is a decimal: 0.04 for 4%."""
    if principal <= 0 or years <= 0 or compounds_per_year <= 0:
        return {"error": "principal, years and compounds_per_year must be positive"}
    final = principal * (1 + annual_rate / compounds_per_year) ** (compounds_per_year * years)
    return {"final_amount": round(final, 2), "interest_earned": round(final - principal, 2)}


RATES_TO_EUR = {"EUR": 1.0, "USD": 0.92, "GBP": 1.17, "CHF": 1.05, "INR": 0.0109, "JPY": 0.0061}


def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Fixed exchange rates (a test table, not live rates)."""
    f, t = str(from_currency).upper(), str(to_currency).upper()
    if f not in RATES_TO_EUR or t not in RATES_TO_EUR:
        return {"error": f"unknown currency: {f if f not in RATES_TO_EUR else t}"}
    rate = RATES_TO_EUR[f] / RATES_TO_EUR[t]
    return {"converted_amount": round(amount * rate, 2), "currency": t, "rate": round(rate, 6)}


# ---------------------------------------------------------------- units
_LENGTH_M = {"m": 1.0, "km": 1000.0, "mi": 1609.344, "ft": 0.3048, "cm": 0.01}
_MASS_KG = {"kg": 1.0, "g": 0.001, "lb": 0.45359237}
_ALIASES = {"meter": "m", "meters": "m", "metre": "m", "metres": "m", "kilometer": "km", "kilometers": "km",
            "kilometre": "km", "kilometres": "km", "mile": "mi", "miles": "mi", "foot": "ft", "feet": "ft",
            "centimeter": "cm", "centimeters": "cm", "kilogram": "kg", "kilograms": "kg", "gram": "g", "grams": "g",
            "pound": "lb", "pounds": "lb", "lbs": "lb", "celsius": "c", "fahrenheit": "f", "°c": "c", "°f": "f"}


def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """Length (m, km, mi, ft, cm), mass (kg, g, lb) and temperature (c, f)."""
    f = _ALIASES.get(str(from_unit).lower(), str(from_unit).lower())
    t = _ALIASES.get(str(to_unit).lower(), str(to_unit).lower())
    if {f, t} <= {"c", "f"}:
        out = value if f == t else (value * 9 / 5 + 32 if f == "c" else (value - 32) * 5 / 9)
    elif f in _LENGTH_M and t in _LENGTH_M:
        out = value * _LENGTH_M[f] / _LENGTH_M[t]
    elif f in _MASS_KG and t in _MASS_KG:
        out = value * _MASS_KG[f] / _MASS_KG[t]
    else:
        return {"error": f"cannot convert {from_unit} to {to_unit}"}
    return {"result": round(out, 4), "unit": t}


# ---------------------------------------------------------------- lookups
WEATHER = {
    "oslo": {"high_c": 9, "low_c": 4, "rain_chance_pct": 70, "wind_kmh": 18, "condition": "light rain"},
    "paris": {"high_c": 14, "low_c": 8, "rain_chance_pct": 20, "wind_kmh": 12, "condition": "partly cloudy"},
    "rome": {"high_c": 21, "low_c": 13, "rain_chance_pct": 5, "wind_kmh": 9, "condition": "sunny"},
    "london": {"high_c": 12, "low_c": 7, "rain_chance_pct": 60, "wind_kmh": 27, "condition": "showers"},
    "mumbai": {"high_c": 33, "low_c": 26, "rain_chance_pct": 10, "wind_kmh": 14, "condition": "humid, clear"},
    "bengaluru": {"high_c": 28, "low_c": 18, "rain_chance_pct": 30, "wind_kmh": 11, "condition": "cloudy"},
}
FAILING_CITIES = {"reykjavik"}


def get_weather(city: str, day: str = "tomorrow") -> object:
    """Tomorrow's forecast (a test table)."""
    c = str(city).strip().lower()
    if c in FAILING_CITIES:
        return "Error: weather service timed out"
    if c not in WEATHER:
        return {"error": f"unknown city: {city}"}
    return dict(WEATHER[c], city=str(city).strip().title(), day=day)


PRODUCTS = {
    "MX-200": {"name": "MX-200 speaker", "price_usd": 249.0, "weight_kg": 1.35, "battery_hours": 18, "warranty_years": 2, "in_stock": 42},
    "LT-50": {"name": "LT-50 lamp", "price_usd": 39.9, "weight_kg": 0.6, "battery_hours": 30, "warranty_years": 1, "in_stock": 0},
    "QX-9": {"name": "QX-9 headphones", "price_usd": 179.5, "weight_kg": 0.28, "battery_hours": 40, "warranty_years": 2, "in_stock": 7},
}


def get_product(sku: str) -> dict:
    s = str(sku).strip().upper()
    if s not in PRODUCTS:
        return {"error": f"unknown sku: {sku}"}
    return dict(PRODUCTS[s], sku=s)


PLAYERS = {
    "jordan reyes": {"points": 27, "rebounds": 11, "assists": 7, "minutes": 34, "fg_pct": 0.522},
    "maya chen": {"points": 19, "rebounds": 4, "assists": 9, "minutes": 31, "fg_pct": 0.471},
    "sam okafor": {"points": 31, "rebounds": 8, "assists": 3, "minutes": 36, "fg_pct": 0.548},
}


def get_player_stats(player: str, date: str) -> dict:
    p = str(player).strip().lower()
    if p not in PLAYERS or str(date).strip() != "2026-11-16":
        return {"error": f"no game found for {player} on {date}"}
    return dict(PLAYERS[p], player=str(player).strip().title(), date="2026-11-16")


STOCKS = {
    "ACME": {"price": 189.5, "change_pct": -1.2, "volume": 51200000, "day_low": 187.1, "day_high": 192.4},
    "GLOBX": {"price": 72.15, "change_pct": 2.8, "volume": 8300000, "day_low": 69.8, "day_high": 72.9},
}


def get_stock_quote(symbol: str) -> dict:
    s = str(symbol).strip().upper()
    if s not in STOCKS:
        return {"error": f"unknown symbol: {symbol}"}
    return dict(STOCKS[s], symbol=s)


# ---------------------------------------------------------------- calculator
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.Mod: operator.mod, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and (abs(right) > 100 or abs(left) > 1e6):
            raise ValueError("power too large")             # 10**10**10 would never finish
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("only numbers and + - * / ** % ( ) are allowed")


def calculator(expression: str) -> dict:
    """Arithmetic only: numbers, + - * / ** % and parentheses. '%' is the remainder, not percent."""
    try:
        expr = str(expression).replace("×", "*").replace("−", "-").replace(",", "")
        value = _eval(ast.parse(expr, mode="eval"))
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError("result is not finite")
    except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as e:
        return {"error": f"cannot evaluate {expression!r}: {e}"}
    return {"result": round(value, 6) if isinstance(value, float) else value}


# ---------------------------------------------------------------- held-out set (questions_heldout.json)
# Tools whose results have several fields of the same kind (subtotal, tax, total; revenue, operating and
# net income), where a value is easily written under the wrong name.
_FLIGHTS = {
    "LH-400": {"from": "FRA", "to": "JFK", "distance_km": 6200, "duration_min": 535, "delay_min": 25,
               "seats_left": 12, "price_eur": 689.0},
    "BA-117": {"from": "LHR", "to": "JFK", "distance_km": 5540, "duration_min": 495, "delay_min": 0,
               "seats_left": 3, "price_eur": 812.5},
    "AI-101": {"from": "DEL", "to": "JFK", "distance_km": 11760, "duration_min": 960, "delay_min": 45,
               "seats_left": 27, "price_eur": 1045.0},
}


def get_flight(flight_no: str) -> dict:
    f = _FLIGHTS.get(str(flight_no).upper().replace(" ", "-"))
    return dict(f, flight_no=str(flight_no).upper()) if f else {"error": f"unknown flight: {flight_no}"}


def _invoice(subtotal, discount, shipping, items, vat=0.19):
    tax = round((subtotal - discount) * vat, 2)
    return {"items": items, "subtotal": subtotal, "discount": discount, "tax": tax, "shipping": shipping,
            "total": round(subtotal - discount + tax + shipping, 2)}


_INVOICES = {"INV-1001": _invoice(1240.0, 124.0, 15.0, 8), "INV-1002": _invoice(385.5, 0.0, 9.9, 3)}


def get_invoice(invoice_id: str) -> dict:
    inv = _INVOICES.get(str(invoice_id).upper())
    return dict(inv, invoice_id=str(invoice_id).upper(), currency="EUR") if inv else \
        {"error": f"unknown invoice: {invoice_id}"}


_FINANCIALS = {   # a made-up company; millions of US dollars
    ("nordwind", 2025): (1840.5, 312.9, 221.4, 5210),
    ("nordwind", 2024): (1612.3, 251.6, 170.2, 4980),
}


def get_company_financials(company: str, year: int) -> dict:
    row = _FINANCIALS.get((str(company).lower(), int(year)))
    if not row:
        return {"error": f"no figures for {company} in {year}"}
    revenue, operating, net, employees = row
    return {"company": company, "year": int(year), "revenue_musd": revenue, "operating_income_musd": operating,
            "net_income_musd": net, "employees": employees,
            "operating_margin_pct": round(100 * operating / revenue, 1)}


_NUTRITION = {   # per serving
    "dal tadka": {"calories_kcal": 310, "protein_g": 14.2, "fat_g": 9.8, "carbs_g": 41.5, "fiber_g": 8.1},
    "margherita pizza": {"calories_kcal": 840, "protein_g": 34.0, "fat_g": 32.5, "carbs_g": 98.0, "fiber_g": 5.2},
}


def get_nutrition(dish: str) -> dict:
    n = _NUTRITION.get(str(dish).lower().strip())
    return dict(n, dish=dish, per="serving") if n else {"error": f"unknown dish: {dish}"}


_SENSORS = {
    "LAB-1": {"temperature_c": 22.4, "humidity_pct": 41, "pressure_hpa": 1012.6, "co2_ppm": 680, "battery_pct": 87},
    "LAB-2": {"temperature_c": 19.8, "humidity_pct": 55, "pressure_hpa": 1009.3, "co2_ppm": 1240, "battery_pct": 12},
}


def get_sensor(sensor_id: str) -> dict:
    s = _SENSORS.get(str(sensor_id).upper())
    return dict(s, sensor_id=str(sensor_id).upper()) if s else {"error": f"unknown sensor: {sensor_id}"}


_SHIP_DAYS = {"DE": (1, 2), "US": (4, 7), "IN": (6, 10)}
_COUNTRY = {"germany": "DE", "united states": "US", "usa": "US", "us": "US", "india": "IN", "de": "DE", "in": "IN"}


def get_shipping_quote(weight_kg: float, country: str) -> dict:
    c = _COUNTRY.get(str(country).lower().strip(), str(country).upper())
    if c not in _SHIP_DAYS or weight_kg <= 0:
        return {"error": f"no shipping to {country}" if c not in _SHIP_DAYS else "weight must be positive"}
    rate = {"DE": 1.2, "US": 4.8, "IN": 5.6}[c]
    return {"country": c, "weight_kg": weight_kg, "cost_eur": round(4.9 + rate * weight_kg, 2),
            "days_min": _SHIP_DAYS[c][0], "days_max": _SHIP_DAYS[c][1]}


# test values, not official statistics
_CITIES = {"lyon": (522250, 47.87, 35.1), "pune": (3124458, 331.26, 29.4)}


def get_city_stats(city: str) -> dict:
    c = _CITIES.get(str(city).lower().strip())
    if not c:
        return {"error": f"unknown city: {city}"}
    population, area, age = c
    return {"city": city, "population": population, "area_km2": area,
            "density_per_km2": round(population / area), "median_age": age}


# ---------------------------------------------------------------- second held-out set (questions_heldout2.json)
# Written on 2026-11-20, after the 0.1.1 changes and before any model answered: results with lists of
# reviews, times written as "9:0", and text to quote from. All made up.
_RESTAURANTS = {
    "juniper table": {
        "name": "Juniper Table", "city": "Bristol", "rating": 4.3, "review_count": 3, "price_level": 2,
        "hours": {"Monday": "closed", "Tuesday": "11:30-22:0", "Wednesday": "11:30-22:0", "Thursday": "11:30-22:0",
                  "Friday": "11:30-23:30", "Saturday": "9:0-23:30", "Sunday": "9:0-16:0"},
        "reviews": [
            {"stars": 5, "date": "2026-09-14 19:42:10", "text": "The lamb was perfect and the staff remembered our names. "
                                                            "We will be back for the brunch."},
            {"stars": 4, "date": "2026-10-03 13:05:51", "text": "Lovely terrace, a bit slow on a busy Saturday. "
                                                            "The lemon tart is worth the wait."},
            {"stars": 3, "date": "2026-10-28 20:17:33", "text": "Good food but loud. We waited 40 minutes for a table "
                                                            "even with a booking."}]},
    "harbor noodle house": {
        "name": "Harbor Noodle House", "city": "Bristol", "rating": 3.9, "review_count": 4, "price_level": 1,
        "hours": {"Monday": "12:0-21:0", "Tuesday": "12:0-21:0", "Wednesday": "12:0-21:0", "Thursday": "12:0-21:0",
                  "Friday": "12:0-22:30", "Saturday": "12:0-22:30", "Sunday": "closed"},
        "reviews": [
            {"stars": 5, "date": "2026-08-30 12:44:02", "text": "The broth is rich and deeply savory, the best ramen "
                                                            "in the city for under ten pounds."},
            {"stars": 2, "date": "2026-09-21 18:30:47", "text": "The broth was lukewarm and far too salty. Service "
                                                            "was friendly though."},
            {"stars": 4, "date": "2026-10-11 13:12:09", "text": "Generous portions and quick service at lunch."},
            {"stars": 5, "date": "2026-11-02 19:58:26", "text": "Spicy miso noodles that warm you right up."}]},
}


def get_restaurant(name: str) -> dict:
    r = _RESTAURANTS.get(str(name).lower().strip())
    return json.loads(json.dumps(r)) if r else {"error": f"unknown restaurant: {name}"}


_EVENTS = {
    "lantern jazz night": {"event": "Lantern Jazz Night", "date": "2026-12-05", "venue": "Old Corn Exchange",
                           "doors_open": "18:45", "start": "19:30", "end": "22:15", "tickets_left": 86,
                           "price_eur": 28.0},
    "rooftop film club": {"event": "Rooftop Film Club", "date": "2026-12-12", "venue": "Hotel Alder roof",
                          "doors_open": "17:0", "start": "17:30", "end": "19:45", "tickets_left": 14,
                          "price_eur": 12.5},
}


def get_event(event: str) -> dict:
    e = _EVENTS.get(str(event).lower().strip())
    return dict(e) if e else {"error": f"unknown event: {event}"}


_TRAINS = {
    "RX-12": {"train_no": "RX-12", "from": "Bristol", "to": "London", "departs": "7:0", "arrives": "8:52",
              "delay_min": 12, "platform": 4, "stops": 3, "seats_free": 58},
    "RX-30": {"train_no": "RX-30", "from": "Bristol", "to": "London", "departs": "9:30", "arrives": "11:41",
              "delay_min": 0, "platform": 11, "stops": 6, "seats_free": 120},
}


def get_train(train_no: str) -> dict:
    t = _TRAINS.get(str(train_no).upper().replace(" ", "-"))
    return dict(t) if t else {"error": f"unknown train: {train_no}"}


_HOTELS = {
    "hotel alder": {"name": "Hotel Alder", "city": "Bristol", "rate_eur": 142.0, "breakfast_included": False,
                    "breakfast_eur": 16.0, "guest_rating": 4.6, "rooms_free": 5, "station_km": 0.8,
                    "airport_km": 13.5, "check_in": "15:0", "check_out": "11:0"},
}


def get_hotel(name: str) -> dict:
    h = _HOTELS.get(str(name).lower().strip())
    return dict(h) if h else {"error": f"unknown hotel: {name}"}


_ARTICLES = {
    "N-201": {"id": "N-201", "title": "Riverside Library reopens after flood repairs", "published": "2026-10-02",
              "text": ("Riverside Library reopened on Monday, fourteen months after the flood of August 2025 closed it. "
                       "The repairs cost 1.8 million pounds, of which the council paid 1.1 million and a national "
                       "fund the rest. About 22,000 books were lost; 9,500 have been replaced so far. Mayor Ruth "
                       "Okonjo said the library was \"back where it belongs, at the heart of the riverside\" and "
                       "promised longer opening hours from January. The library now opens six days a week.")},
    "N-202": {"id": "N-202", "title": "Water main burst leaves east side without water", "published": "2026-11-09",
              "text": ("A burst water main left 4,800 households in the east of the city without running water for "
                       "up to 31 hours this weekend. Westvale Water said the 60-year-old pipe split under the "
                       "Mill Road junction early on Saturday. Repairs will cost an estimated 2.3 million pounds. "
                       "\"We are sorry for the disruption and will compensate every affected household,\" said "
                       "spokesperson Daniel Price. Bottled water was handed out at three points across the area.")},
}


def get_article(article_id: str) -> dict:
    a = _ARTICLES.get(str(article_id).upper().replace(" ", "-"))
    return dict(a) if a else {"error": f"unknown article: {article_id}"}


# ---------------------------------------------------------------- schemas
def _schema(name, description, props, required):
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {
        "type": "object", "properties": props, "required": required}}}


NUM, STR, INT = {"type": "number"}, {"type": "string"}, {"type": "integer"}
TOOLS = {
    "loan_cost": (loan_cost, _schema("loan_cost", "Monthly payment, total paid and total interest of an amortised loan.",
                  {"principal": NUM, "annual_rate": dict(NUM, description="annual interest rate as a decimal, e.g. 0.07 for 7%"),
                   "years": NUM}, ["principal", "annual_rate", "years"])),
    "compound_interest": (compound_interest, _schema("compound_interest", "Final amount and interest earned on a deposit.",
                          {"principal": NUM, "annual_rate": dict(NUM, description="annual rate as a decimal, e.g. 0.04 for 4%"),
                           "years": NUM, "compounds_per_year": dict(INT, description="12 = monthly, 4 = quarterly, 1 = yearly")},
                          ["principal", "annual_rate", "years"])),
    "convert_currency": (convert_currency, _schema("convert_currency", "Convert money between EUR, USD, GBP, CHF, INR and JPY.",
                         {"amount": NUM, "from_currency": dict(STR, description="ISO code, e.g. USD"),
                          "to_currency": dict(STR, description="ISO code, e.g. EUR")}, ["amount", "from_currency", "to_currency"])),
    "convert_units": (convert_units, _schema("convert_units", "Convert length (m, km, mi, ft, cm), mass (kg, g, lb) or temperature (c, f).",
                      {"value": NUM, "from_unit": STR, "to_unit": STR}, ["value", "from_unit", "to_unit"])),
    "get_weather": (get_weather, _schema("get_weather", "Tomorrow's weather forecast for a city.",
                    {"city": STR, "day": dict(STR, description="only 'tomorrow' is available")}, ["city"])),
    "get_product": (get_product, _schema("get_product", "Price, weight, battery life, warranty and stock of a product by SKU.",
                    {"sku": dict(STR, description="product code, e.g. MX-200")}, ["sku"])),
    "get_player_stats": (get_player_stats, _schema("get_player_stats", "A basketball player's statistics in one game.",
                         {"player": STR, "date": dict(STR, description="YYYY-MM-DD")}, ["player", "date"])),
    "get_stock_quote": (get_stock_quote, _schema("get_stock_quote", "Today's price, change, volume and range of a stock.",
                        {"symbol": STR}, ["symbol"])),
    "get_flight": (get_flight, _schema("get_flight", "Distance, duration, delay, seats left and price of a flight.",
                   {"flight_no": dict(STR, description="e.g. LH-400")}, ["flight_no"])),
    "get_invoice": (get_invoice, _schema("get_invoice", "Subtotal, discount, tax, shipping and total of an invoice (EUR).",
                    {"invoice_id": dict(STR, description="e.g. INV-1001")}, ["invoice_id"])),
    "get_company_financials": (get_company_financials, _schema(
        "get_company_financials", "A company's yearly revenue, operating income, net income (millions of USD), "
        "employees and operating margin.", {"company": STR, "year": INT}, ["company", "year"])),
    "get_nutrition": (get_nutrition, _schema("get_nutrition", "Calories, protein, fat, carbs and fiber per serving of a dish.",
                      {"dish": STR}, ["dish"])),
    "get_sensor": (get_sensor, _schema("get_sensor", "Latest temperature, humidity, pressure, CO2 and battery of a room sensor.",
                   {"sensor_id": dict(STR, description="e.g. LAB-1")}, ["sensor_id"])),
    "get_shipping_quote": (get_shipping_quote, _schema("get_shipping_quote", "Cost (EUR) and delivery days for a parcel.",
                           {"weight_kg": NUM, "country": dict(STR, description="Germany, United States or India")},
                           ["weight_kg", "country"])),
    "get_city_stats": (get_city_stats, _schema("get_city_stats", "Population, area, density and median age of a city.",
                       {"city": STR}, ["city"])),
    "get_restaurant": (get_restaurant, _schema("get_restaurant", "Rating, number of reviews, price level, opening "
                       "hours and recent reviews of a restaurant.", {"name": STR}, ["name"])),
    "get_event": (get_event, _schema("get_event", "Date, venue, times, tickets left and price (EUR) of an event.",
                  {"event": STR}, ["event"])),
    "get_train": (get_train, _schema("get_train", "Departure and arrival times, delay, platform, stops and free seats "
                  "of a train.", {"train_no": dict(STR, description="e.g. RX-12")}, ["train_no"])),
    "get_hotel": (get_hotel, _schema("get_hotel", "Nightly rate (EUR), breakfast, guest rating, rooms free, distances "
                  "and check-in and check-out times of a hotel.", {"name": STR}, ["name"])),
    "get_article": (get_article, _schema("get_article", "A local news article by id: title, date and text.",
                    {"article_id": dict(STR, description="e.g. N-201")}, ["article_id"])),
    "calculator": (calculator, _schema("calculator", "Evaluate an arithmetic expression, e.g. '0.15*240' or '(125.5-37.25)*4'.",
                   {"expression": STR}, ["expression"])),
}
SCHEMAS = [schema for _f, schema in TOOLS.values()]


def run_tool(name: str, args: dict):
    if name not in TOOLS:
        return {"error": f"unknown tool: {name}"}
    fn = TOOLS[name][0]
    try:
        return fn(**(args or {}))
    except TypeError as e:
        return {"error": f"bad arguments for {name}: {e}"}
