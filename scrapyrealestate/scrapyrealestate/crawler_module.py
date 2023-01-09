import datetime, json, telebot, time
from sqlalchemy import Column, Integer, String, DateTime

def make_flat(tablename, Base):
    '''
    Funció que crea un model de taula igual. Funciona amb sqlamchemy
    i es crea l'objecte i la taula alhora.
    :param tablename:
    :return:
    '''

    class Flat(Base):
        __tablename__ = tablename

        id = Column(Integer, primary_key=True)
        title = Column(String)
        price = Column(Integer)
        rooms = Column(Integer)
        m2 = Column(Integer)
        floor = Column(String)
        href = Column(String)
        datetime = Column(DateTime)

        def __init__(self, id, title, price, rooms, m2, floor, href, datetime):
            # self.set_is_new(is_new)
            # TODO: self.__id NO!! why?
            self.id = id
            self.title = title
            self.price = price
            self.rooms = rooms
            self.m2 = m2
            self.floor = floor
            self.href = href
            self.datetime = datetime

        def __repr__(self):
            return f'{tablename}({self.id}, {self.title}, {self.price}, {self.rooms}, {self.m2}, {self.floor}, {self.href}, {self.datetime})'

        def __str__(self):
            return self.title

    return Flat

def json_to_bbdd(json_file_name, scrapy_rs_name, db_engine, session, Base, max_price, tg_chatID, telegram_msg, logger):
    '''
    Funció que llegeix un json dels habitatges amb les seves propietats.
    Compara si n'hi ha cap que no estigui a la bbdd i notifica amb missatge.
    :param json:
    :return:
    '''
    # creem l'objecte per enviar tg
    tb = telebot.TeleBot('5042109408:AAHBrCsNiuI3lXBEiLjmyxqXapX4h1LHbJs')

    new_urls = []

    # Obrir json
    # with open('flats_idealista.json') as json_file:
    json_file = open(json_file_name)

    # Encapsulem per si dona error
    try:
        data_json = json.load(json_file)
    except:
        data_json = ""

    # Check if JSON is empty
    if len(data_json) == 0:
        logger.warning(f'NO DATA IN JSON {scrapy_rs_name.upper()}')
    json_file.close()

    # Creem class objecte taula
    Flat = make_flat(scrapy_rs_name, Base)

    # Creem, sino existeixen, les taula a la bbdd
    Base.metadata.create_all(db_engine)
    logger.debug(f"NEW TABLE BBDD {scrapy_rs_name.upper()} CREATED (IF NOT EXISTS)")

    # Guardem tots els idds de la bbdd (per comparar ids)
    ids_bbdd = []
    connection = db_engine.connect()

    #try:
    result = connection.execute(f'select id from {scrapy_rs_name}')
    for row in result:
        ids_bbdd.append(row['id'])
    #except:
    #    pass

    # Iterem cada pis del diccionar i tractem les dades
    for flat in data_json:
        flat_id = int(flat['id'])  # Convertim a int
        title = flat["title"].replace("\'", "")
        # Agafem nomes els digits de price, rooms i m2
        try:
            price_str = flat['price']
        except:
            prince_str = 0

        try:
            price = int(''.join(char for char in flat['price'] if char.isdigit()))
        except:
            price = 0

        if price == 0:
            price = price_str

        try:
            rooms = int(''.join(char for char in flat['rooms'] if char.isdigit()))
        except:
            try: rooms = flat['rooms']
            except: rooms = 0
        try:
            m2 = int(''.join(char for char in flat['m2'] if char.isdigit())[:-1])
            m2_tg = f'{m2}m²'
        except:
            try:
                m2 = flat['m2']
                m2_tg = f'{m2}m²'
            except:
                m2 = 0
                m2_tg = ''
        try:
            floor = flat['floor']
        except:
            floor = ''

        href = flat['href']

        # Comprovem si aquest id (nou) esta a la llista de ids de la bbdd
        bbdd_exists = False
        for id_bbdd in ids_bbdd:
            # Si existeix, canviem el signe de la variable
            if id_bbdd == flat_id:
                bbdd_exists = True

        # Si la id no està a la bbdd (bbdd_exists = False), creem objecte (tambe a la bbdd) i avisem per telegram
        if not bbdd_exists:
            currentDateTime = datetime.datetime.now()

            if telegram_msg:
                if int(price) <= int(max_price) or int(max_price) == 0:  # Enviar missatge a telegram si es True i el preu es <= max_price
                    new_urls.append(href)
                    # Enviem missatge tg del preu, m2, mitjana i href
                    try: mitja_price_m2 = '%.2f' % (price / float(m2))
                    except: mitja_price_m2 = ''
                    tb.send_message(tg_chatID, f"<b>{price_str}</b> [{m2_tg}] → {mitja_price_m2}€/m²\n{href}", parse_mode='HTML')
                    # Creem objecte flat (tambe a la bbdd)
                    flat = Flat(flat_id, title, price, rooms, m2, floor, href, currentDateTime)
                    logger.debug(f'ADDING {href} TO BBDD {scrapy_rs_name.upper()}')
                    logger.debug(f'SENDING {href} TO TELEGRAM GROUP')
                    session.add(flat)
                    session.commit()  # Fem el commit a la BBDD
                    time.sleep(3.05)

    if len(new_urls) > 0:
        logger.info(
            f"SPIDER FINISHED - [NEW: {len(new_urls)}] [TOTAL: {len(data_json)}]: {new_urls}")
    else:
        logger.debug(
            f"SPIDER FINISHED - [NEW: {len(new_urls)}] [TOTAL: {len(data_json)}]: {new_urls}")