from bs4 import BeautifulSoup
from husum import get_husum_height
from flask import Flask, jsonify, request
import requests, time

app = Flask(__name__)

class lift_status:
    def __init__(self, lift_name, nickname):
        self.lift_name= lift_name
        self.nickname = nickname
        self.status = "none"
        self.hours = "none"
        self.comment = "none"
    
    def update(self, status, hours, comment):
        self.status = status
        self.hours = hours
        self.comment = comment
    
    def status_dict(self):
        return { 'name': self.lift_name,
                 'nickname': self.nickname,
                 'status': self.status,
                 'hours': self.hours,
                 'comment': self.comment }

class meadows_status:
    def __init__(self):
        self.conditions_stale = True
        self.conditions_update_time = 0
        self.conditions_timeout = 5.0
        self.conditions_html = None
        self.snow_12_hr = None
        self.snow_24_hr = None
        self.snow_48_hr = None
        self.MHX_temp = None
        self.MHX_wind = None
        self.Cascade_temp = None
        self.Cascade_wind = None
        self.lift_names = ['Buttercup','Easy Rider','Vista Express','Cascade Express','Daisy','Mt Hood Express','Blue','Stadium Express','Shooting Star Express','Hood River Express','Heather Canyon','Ballroom Carpet'] 
        self.lift_nicknames = ['Buttercup','Easy Rider','Vista','Cascade','Daisy','MHX','Blue','Stadium','Star','Hood River Express','Heather','Ballroom Carpet'] 
        self.lifts = {}
        self.lift_status_dict = {}
        for i, name in enumerate(self.lift_names):
            self.lifts[name] = lift_status(name, self.lift_nicknames[i])

    def get_conditions_page(self):
        print('Requesting Conditions Page')
        response = requests.get('https://skihood.com/en/the-mountain/conditions')
        self.conditions_response_code = response.status_code
        if self.conditions_response_code != 200:
            print('Conditions Page Request Failed')
            print(response)
            return False
        print('Conditions Update Successful')
        self.conditions_update_time = time.time()
        self.conditions_html = response.text
        return True
        
    def parse_conditions_page(self):
        try:
            soup = BeautifulSoup(self.conditions_html, features='html.parser')
            # Parse Lift Status from the Lift Table
            lift_table = soup.find('table', { 'class' : 'table-status-chart' })
            lift_table_body = lift_table.find('tbody')
            lift_table_rows = lift_table_body.find_all('tr')
            for row in lift_table_rows:
                cols = row.find_all('td')
                lift_name = cols[1].text.strip()
                lift_status = cols[0].text.strip()
                lift_hours = cols[2].text.strip()
                lift_comment = cols[3].text.strip()
                self.lifts[lift_name].update(lift_status, lift_hours, lift_comment)  
            # Parse MHX Weather Data Here

            return True
        except Exception as e:
            print('Error While Parsing Conditions Page')
            print(e)
            return False

    def update_conditions(self):
        if self.check_conditions_current():
            return True
        if self.get_conditions_page():
            if self.parse_conditions_page():
                self.conditions_stale = False
                self.update_lift_status_json()
                self.conditions_update_time = time.time()
                return True
        self.conditions_stale = True
        return False
    
    def check_conditions_current(self):
        if self.conditions_stale:
            return False
        if (time.time() - self.conditions_update_time) > self.conditions_timeout:
            self.conditions_stale = True
            return False
        self.conditions_stale = False
        return True

    def update_lift_status_json(self): 
        for lift in self.lifts.values():
            self.lift_status_dict[lift.lift_name] = lift.status_dict()


if __name__ == "__main__":
    status = meadows_status()
    
    @app.route('/lift_status')
    def lift_status():
        status.update_conditions()
        return jsonify(status.lift_status_dict)
    
    @app.route('/cascade_status')
    def cascade_status():
        status.update_conditions()
        return jsonify(status.lifts['Cascade Express'].status_dict())

    @app.route('/is_cascade_open')
    def is_cascade_open():
        status.update_conditions()
        cascade_status = status.lifts['Cascade Express']
        if cascade_status.status == 'Open':
            return 'Yes!'
        return 'No'

    @app.route('/husum_status')
    def husum_status():
        height = get_husum_height()
        husum_dict = {'height': str(height) + ' ft'}
        if height is None:
            return 'Unavailable'
        if height > 5.0:
            return '5+'
        return jsonify(husum_dict)

    print('Starting Flask Server')
    app.run('0.0.0.0',5000)

