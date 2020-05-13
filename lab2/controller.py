import datetime
import psycopg2
from random import randint

class Controller:
    def __init__(self, user, password, host="127.0.0.1", port="5432"):
        self.fly_con = psycopg2.connect(
            database="fly_booking_db", 
            user=user, 
            password=password, 
            host=host, 
            port=port
            )

        self.hotel_con = psycopg2.connect(
            database="hotel_booking_db", 
            user=user, 
            password=password,
            host=host, 
            port=port
            )
        self.bank_con = psycopg2.connect(
            database="bank_db", 
            user="postgres", 
            password="zxcvbn",
            host="127.0.0.1", 
            port="5432"
            )
    
    def show_tables(self):
        print("Hotel:")
        hotel_cursor = self.hotel_con.cursor()
        hotel_cursor.execute("SELECT * FROM hotel_booking;")
        answer_hotel = hotel_cursor.fetchall()

        self.hotel_con.rollback()

        for line in answer_hotel:
            print("\t".join(map(lambda x: str(x).strip(), line)))
            

        print("Fly:")
        fly_cursor = self.fly_con.cursor()
        fly_cursor.execute("SELECT * FROM fly_booking;")
        answer_fly = fly_cursor.fetchall()

        self.fly_con.rollback()

        for line in answer_fly:
            print("\t".join(map(lambda x: str(x).strip(), line)))

        print("Bank:")
        bank_cursor = self.bank_con.cursor()
        bank_cursor.execute("SELECT * FROM bank;")
        answer_bank = bank_cursor.fetchall()

        self.bank_con.rollback()

        for line in answer_bank:
            print("\t".join(map(lambda x: str(x).strip(), line)))
    
    def do_transaction(self, hotel_data, fly_data, price=100):
        try:
            client_name, hotel_name, arrival, departure = hotel_data
            
            seed = randint(100, 100000)
            xid = self.hotel_con.xid(12+seed, "172312", "12312")
            self.hotel_con.tpc_begin(xid)
            xid = self.fly_con.xid(13+seed, "172313", "12312")
            self.fly_con.tpc_begin(xid)
            xid = self.bank_con.xid(14+seed, "172313", "12312")
            self.bank_con.tpc_begin(xid)
            
            
            hotel_cursor =  self.hotel_con.cursor()
            hotel_cursor.execute("""
                INSERT INTO hotel_booking (client_name, hotel_name, arrival, departure)
                VALUES ('{}', '{}', '{}', '{}');
                """.format(client_name, hotel_name, arrival, departure)
            )
            self.hotel_con.tpc_prepare()
            
            client_name, fly_number, code_from, code_to, fly_date = fly_data
            fly_cursor = self.fly_con.cursor()
            fly_cursor.execute("""
                INSERT INTO fly_booking (client_name, fly_number, code_from, code_to, fly_date)
                VALUES ('{}', '{}', '{}', '{}', '{}');
                """.format(client_name, fly_number, code_from, code_to, fly_date)
            )
            self.fly_con.tpc_prepare()

            bank_cursor = self.bank_con.cursor()
            bank_cursor.execute("""
                    UPDATE bank SET amount = amount - {} 
                    WHERE client_name='{}';""".format(price, client_name))
            self.bank_con.tpc_prepare()
            
            input()
            
            self.bank_con.tpc_commit()
            self.fly_con.tpc_commit()
            self.hotel_con.tpc_commit()
            
            print("!OK")
        except:
            self.bank_con.tpc_rollback()
            self.fly_con.tpc_rollback()
            self.hotel_con.tpc_rollback()
            print("!ERROR happens!") 
    
    def remove_row(self, client_name, amount=200):
        with self.hotel_con.cursor() as hotel_cursor:
            hotel_cursor.execute("DELETE FROM hotel_booking WHERE client_name='{}';".format(client_name))

        self.hotel_con.commit()

        with self.fly_con.cursor() as fly_cursor:
            fly_cursor.execute("DELETE FROM fly_booking WHERE client_name='{}';".format(client_name))

        self.fly_con.commit()
            
        with self.bank_con.cursor() as bank_cursor:
            bank_cursor.execute("""UPDATE bank SET amount = {}
                                        WHERE client_name='{}';""".format(amount, client_name))
            self.bank_con.commit()
        

if __name__ == "__main__":
    user = "postgres"
    password = "zxcvbn"
    commit_controller = Controller(user=user, password=password)
    commit_controller.show_tables()
    
    print("===> Doing transaction...")
    hotel_data = 'Anton', 'Kiev', '6-05-2020', '12-05-2020'
    fly_data = 'Anton', 'KVV 1482', 'KWW', 'KV', '6-05-2020'
    commit_controller.do_transaction(hotel_data, fly_data, price=187)
    commit_controller.show_tables()
    commit_controller.remove_row(client_name='Anton', amount=200)
    print("===> Exiting...")
    commit_controller.show_tables()
