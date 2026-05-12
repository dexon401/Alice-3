import logging

from geo import get_distance, get_geo_info

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


def handler(event, context):

    logging.info("Request: %r", event)

    response = {
        "session": event["session"],
        "version": event["version"],
        "response": {"end_session": False},
    }

    handle_dialog(response, event)

    logging.info("Request: %r", response)

    return response


def handle_dialog(res, req):

    user_id = req["session"]["user_id"]

    if req["session"]["new"]:
        res["response"]["text"] = (
            "Привет! Я могу сказать в какой стране город или сказать расстояние между городами!"
        )

        return

    cities = get_cities(req)

    if len(cities) == 0:
        res["response"]["text"] = "Ты не написал название не одного города!"

    elif len(cities) == 1:
        res["response"]["text"] = "Этот город в стране - " + get_geo_info(
            cities[0], "country"
        )

    elif len(cities) == 2:
        distance = get_distance(
            get_geo_info(cities[0], "coordinates"),
            get_geo_info(cities[1], "coordinates"),
        )
        res["response"]["text"] = (
            "Расстояние между этими городами: " + str(round(distance)) + " км."
        )

    else:
        res["response"]["text"] = "Слишком много городов!"


def get_cities(req):

    cities = []

    for entity in req["request"]["nlu"]["entities"]:
        if entity["type"] == "YANDEX.GEO":
            if "city" in entity["value"].keys():
                cities.append(entity["value"]["city"])

    return cities
