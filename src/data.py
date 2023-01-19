import firebase_admin
from firebase_admin import credentials, firestore
from send_sms import send_sms
import json


class data:

    def __init__(self, debug=False) -> None:
        cred = credentials.Certificate("./service.json")
        firebase_admin.initialize_app(cred)
        self.db: firestore.firestore.Client = firestore.client()
        self.debug = debug
        if(self.debug):
            self.debug_print("Successfully connected...\nServer is running on http://0.0.0.0:80")



    def debug_print(self, printstr):
        if self.debug:
            print("************************************************************************************************************************************")
            print(printstr)
            print("************************************************************************************************************************************")



    def instructor_exists(self, user_id):
        doc = self.db.collection('Instructors').document(user_id).get().to_dict()
        self.debug_print(f"__GET request__ instructor exists -> returned: {doc is not None}")
        return doc is not None



    def create_instructor(self, instructor):
        dict_to_add = {
            "userId": instructor.userId,
            "firstName": instructor.firstName,
            "lastName": instructor.lastName,
            "phoneNumber": instructor.phoneNumber,
            "workPlace": instructor.workPlace,
        }
        doc = self.db.collection('Instructors').document(instructor.userId).set(dict_to_add)
        if doc is not None:
            self.debug_print(f"__POST request__  create instructor -> returned: True\nInstructor {instructor.firstName} {instructor.lastName} created successfully.")
            return True
        
        self.debug_print(f"__POST request__  create instructor -> returned: False\nFailed to create instructor.")
        return False



    def participant_exists(self, user_id):
        doc = self.db.collection('Participants').document(user_id).get().to_dict()
        self.debug_print(f"__GET request__  participant exists -> returned: {doc is not None}")
        return doc is not None



    def create_participant(self, participant):
        dict_to_add = {
            "userId": participant.userId,
            "firstName": participant.firstName,
            "lastName": participant.lastName,
            "phoneNumber": participant.phoneNumber
        }
        doc = self.db.collection('Participants').document(participant.userId).set(dict_to_add)
        if doc is not None:
            self.debug_print(f"__POST request__  create participant -> returned: True\nParticipant {participant.firstName} {participant.lastName} created successfully.")
            return True
        
        self.debug_print(f"__POST request__  create participant -> returned: False\nFailed to create participant.")
        return False



    def get_instructor_lessons_by_date(self, instructor_id, day):
        doc = self.db.collection("Lessons").document(instructor_id).get().to_dict()
        if not doc:
            self.debug_print(f"__GET request__  get instructor lessons by date -> returned: False\nFound 0 lessons at the {day}.")
            return []
        result = [{"date": date, "lesson": json.loads(lesson)} for date, lesson in doc.items() if day in date]
        result.sort(key=lambda x: x['date'])
        self.debug_print(f"__GET request__  get instructor lessons by date -> returned: True\nFound {len(result)} lessons at the {day}.")
        return result



    def add_participant_to_lesson(self, userId, key, lesson, userToAdd):
        self.debug_print(f'\nuserId: {userId}, \nkey: {key}, \nlesson: {lesson}, \nuserToAdd: {userToAdd}\n')
        if userToAdd not in lesson['ParticipantsList'] and len(lesson['ParticipantsList']) < lesson['maxNumberOfParticipants']:
            lesson['ParticipantsList'].append(userToAdd)
            dict_to_add = {key: json.dumps(lesson)}
            res = self.db.collection("Lessons").document(userId).set(dict_to_add, merge=True)
            after_dict = json.loads(self.db.collection("Lessons").document(userId).get().to_dict()[key])
            ans = {}
            if userToAdd in after_dict['ParticipantsList']:
                ans['result'] = True
                ans['message'] = 'User added successfully'
                self.debug_print(f"__POST request__  add participant to lesson -> {ans}")
                send_sms(self.get_instructor_phone(userId), self.get_good_message(key, lesson, userId))
                self.debug_print("SMS notification was sent to Oshrit Weiss +972542320525.")
                return True
            ans['result'] = False
            ans['message'] = 'Failed to add user'
            self.debug_print(f"__POST request__  add participant to lesson -> {ans}")
            return False



    def remove_participant_from_lesson(self, userId, key, lesson, userToRemove):
        ans = {}
        if userToRemove not in lesson['ParticipantsList']:
            ans['result'] = False
            ans['message'] = "User doesn't exist in the participants list"
            self.debug_print(f"__POST request__  remove participant from lesson -> {ans}")
            return False

        lesson['ParticipantsList'].remove(userToRemove)
        dict_to_add = {key: json.dumps(lesson)}
        self.db.collection("Lessons").document(userId).set(dict_to_add, merge=True)
        after_dict = json.loads(self.db.collection("Lessons").document(userId).get().to_dict()[key])
        if userToRemove not in after_dict['ParticipantsList']:
            ans['result'] = True
            ans['message'] = 'User removed from lesson successfully'
            self.debug_print(f"__POST request__  remove participant from lesson -> {ans}")
            send_sms(self.get_instructor_phone(userId), self.get_good_message(key, lesson, userId))
            return True
        ans['result'] = False
        ans['message'] = 'Failed to remove user'
        self.debug_print(f"__POST request__  remove participant from lesson -> {ans}")
        return False



    def add_lesson(self, userId, dict_to_add):
        self.db.collection("Lessons").document(userId).set(dict_to_add, merge=True)



    def validate_and_add_lesson(self, userId, key, lesson_to_add):
        dict_to_add = {key: json.dumps(lesson_to_add)}
        lesson_list = self.db.collection('Lessons').document(userId).get().to_dict()
        if not lesson_list:
            self.add_lesson(userId, dict_to_add)
            self.debug_print(f"__POST request__  create lesson -> returned: True\nLesson {key} created successfully.")
            return True
        ans = True
        for lesson in lesson_list.keys():
            if (compare_keys(key, lesson)):
                ans = False
        if ans:
            self.add_lesson(userId, dict_to_add)
            self.debug_print(f"__POST request__  create lesson -> returned: True\nLesson {key} created successfully.")
        else:
            self.debug_print(f"__POST request__  create lesson -> returned: False\nFailed to create lesson.")
        return ans



    def get_availability(self, userId, date):
        docs = self.db.collection("Lessons").get()
        result = []
        for doc in docs:
            for key, value in doc.to_dict().items():
                if date in key:
                    value = json.loads(value)
                    if userId in value['ParticipantsList'] or \
                            len(value['ParticipantsList']) < value['maxNumberOfParticipants']:
                                result.append({'doc_id': doc.id, 'date': key, 'lesson': value})
        result.sort(key=lambda x: x['date'])
        ans = True if len(result) > 0 else False
        self.debug_print(f"__GET request__  get participant availability -> returned: {ans}\nFound {len(result)} lessons at the {date}.")
        return result



    def get_instructor_phone(self, instructor_id):
        doc = self.db.collection('Instructors').document(instructor_id).get().to_dict()
        self.debug_print(f"__GET request__  get instructor phone number -> returned: {doc is not None}, phone: {doc['phoneNumber'] if doc is not None else 'None'}")
        if doc is not None:
            return doc['phoneNumber']
        return 'None'

    def get_participant_phone(self, participant_id):
        doc = self.db.collection('Participants').document(participant_id).get().to_dict()
        self.debug_print(f"__GET request__  get participant phone number -> returned: {doc is not None}, phone: {doc['phoneNumber'] if doc is not None else 'None'}")
        if doc is not None:
            return doc['phoneNumber']
        return 'None'

    def get_instructor_name(self, instructor_id):
        doc = self.db.collection('Instructors').document(instructor_id).get().to_dict()
        if doc is not None:
            self.debug_print(f"__GET request__  get instructor name -> returned: True, name: {doc['firstName']} {doc['lastName']}")
            return f"{doc['firstName']} {doc['lastName']}"
        self.debug_print(f"__GET request__  get instructor name -> returned: False, None")
        return 'None'

    def get_participant_name(self, participant_id):
        doc = self.db.collection('Participants').document(participant_id).get().to_dict()
        if doc is not None:
            self.debug_print(f"__GET request__  get participant name -> returned: True, name: {doc['firstName']} {doc['lastName']}")
            return f"{doc['firstName']} {doc['lastName']}"
        self.debug_print(f"__GET request__  get participant name -> returned: False, None")
        return 'None'


    def get_instructor_id(self, instructor_name):
        docs = self.db.collection('Instructors').get()
        for doc in docs:
            if doc is not None:
                name = []
                for k, v in doc.to_dict().items():
                    if k == 'firstName':
                        name.append((k, v))
                    if k == 'lastName':
                        name.append((k, v))
                    if len(name) == 2:
                        break
                if name[0][0] == 'firstName':
                    name = f'{name[0][1]} {name[1][1]}'
                else:
                    name = f'{name[1][1]} {name[0][1]}'
                if instructor_name == name:
                    self.debug_print(f"__GET request__  get instructor id -> returned: True, id: {doc.id}")
                    return doc.id
        self.debug_print(f"__GET request__  get instructor id -> returned: False, None")
        return 'None'
    

    def get_instructor_stat(self, instructor_id, start_date, end_date):
        di = self.db.collection('Lessons').document(instructor_id).get().to_dict()
        if di is None:
            return {"avgParticipants": 0, "avgRevenue" : 0, "totalLessons":0, "totalRevenue":0}
        # for key,value in di.items():
        #     print(f"{value['price']} , {value['ParticipantsList']}")
        di = {key: json.loads(value) for key, value in di.items() if start_date <=check_date(key) and check_date(key) <=end_date}
        part_sum = 0
        revenue_sum = 0.0
        lessons = 0
        for value in di.values():
            lessons+=1
            part_sum += len(value['ParticipantsList'])
            revenue_sum += len(value['ParticipantsList'])*value['price']
        if lessons == 0:
            return {"avgParticipants": 0, "avgRevenue" : 0, "totalLessons":0, "totalRevenue":0}
        return {"avgParticipants": round(part_sum/lessons,2), "avgRevenue" : round(revenue_sum/lessons,2),"totalLessons":lessons,"totalRevenue":round(revenue_sum,2)}


    def get_lessons_by_search(self, search):
        filters = ['instructorName', 'lessonName', 'level', 'price', 'date']
        query = {}
        levels = ['A', 'B', 'C']

        for key, value in search.items():
            if value not in [0, "string", ["string"], "", [""], "any", ["any"]]:
                if key == 'instructorName':
                    instructor_id = self.get_instructor_id(value)
                    if instructor_id == 'None' or instructor_id is None:
                        return []
                    query['instructor_id'] = instructor_id
                    continue
                query[key] = value
        if query.get('level') == None:
            query['level'] = levels
        levels = query['level']
        levels.append('All')
        query.update({'level': levels})
        self.debug_print(f'The search filters are -> {query}')

        query_k = query.keys()
        res = []
        docs = -1
        flag_instructor = False
        if 'instructor_id' in query_k:
            docs = self.db.collection('Lessons').document(query['instructor_id']).get()
            del query['instructor_id']
            flag_instructor = True
        else:
            docs = self.db.collection("Lessons").get()
        
        docs = [docs] if flag_instructor else docs
        for doc in docs:
            if doc is not None:
                for date, lesson in doc.to_dict().items():
                    if query.get('date') != None and query.get('date') not in date:
                        continue
                    lesson = json.loads(lesson)
                    good_keys_vals  = {key: value for key, value in lesson.items() if key in query_k}
                    flag = True
                    for k, v in good_keys_vals.items():
                        if k == 'level':
                            if v not in query[k]:
                                flag = False
                                break
                        elif k == 'price':
                            if v > query[k]:
                                flag = False
                                break 
                            else:
                                continue
                        elif query[k] != v:
                            flag = False
                            break
                    if flag:
                        res.append({"doc_id": doc.id, "date": date, "lesson": lesson})
        self.debug_print(f"__GET request__  get lessons by filters -> returned: {len(res) > 0}, found {len(res)} matches")
        return res

    def delete_lesson(self, instructor_id, full_date):
        lessons_list = self.db.collection('Lessons').document(instructor_id).get().to_dict()
        if lessons_list is None or lessons_list.get(full_date) == None:
            self.debug_print(f"__DELETE request__  delete lesson -> returned: False")
            return False

        lesson = json.loads(lessons_list.get(full_date))
        phone_list = [self.get_participant_phone(participant) for participant in lesson["ParticipantsList"]]
        for phone, participant in zip(phone_list, lesson["ParticipantsList"]):
            self.debug_print(f'{phone}, {participant}')
            send_sms(phone, self.get_cancel_message(full_date, participant))
            
        self.debug_print(f'instructor: {instructor_id}, full_date: {full_date}\n {lessons_list[full_date]}')
        self.debug_print(f"__DELETE request__  delete lesson -> returned: True")
        del lessons_list[full_date]
        self.db.collection("Lessons").document(instructor_id).set(lessons_list)
        return True
    
    def upcoming_lessons(self,userId,startDate,upcomingAmount):
        lesson_dict = self.db.collection('Lessons').document(userId).get().to_dict()
        if lesson_dict is None:
            return []
        upcoming_dict = {check_date_with_hour(key):json.loads(value) for key,value in lesson_dict.items() if check_date_with_hour(key) >= startDate}
        lesson_list = [{"doc_id":userId,"date":key.replace("_","\n"),"lesson":value} for key,value in upcoming_dict.items()]
        lesson_list.sort(key=lambda x:x['date'])
        self.debug_print(lesson_list)
        return lesson_list[:upcomingAmount]


    def history_lessons(self,userId,endDate,historyAmount):
        lesson_dict = self.db.collection('Lessons').document(userId).get().to_dict()
        if lesson_dict is None:
            return []
        history_dict = {check_date_with_hour(key):json.loads(value) for key,value in lesson_dict.items() if check_date_with_hour(key) < endDate}
        lesson_list = [{"doc_id":userId,"date":key.replace("_","\n"),"lesson":value} for key,value in history_dict.items()]
        lesson_list.sort(key=lambda x:x['date'],reverse=True)
        self.debug_print(lesson_list)
        return lesson_list[:historyAmount]  

    def upcoming_participant_lessons(self,userId,startDate,upcomingAmount):
        instructors = self.db.collection('Lessons').get()
        participant_list = []
        if instructors is None:
            return []
        for lesson_list in instructors:
            lesson_dict = lesson_list.to_dict()
            for key,value in lesson_dict.items():
                if userId in value and check_date_with_hour(key) >= startDate:
                    participant_list.append({"doc_id":userId,"date":key.replace('_','\n'),"lesson":json.loads(value)})
        participant_list.sort(key=lambda x:x['date'])
        return participant_list[:upcomingAmount]

    def history_participant_lessons(self,userId,endDate,historyAmount):
        instructors = self.db.collection('Lessons').get()
        if instructors is None:
            return []
        participant_list = []
        for lesson_list in instructors:
            lesson_dict = lesson_list.to_dict()
            for key,value in lesson_dict.items():
                if userId in value and check_date_with_hour(key) < endDate:
                    participant_list.append({"doc_id":userId,"date":key.replace('_','\n'),"lesson":json.loads(value)})
        participant_list.sort(key=lambda x:x['date'])
        return participant_list[:historyAmount]


    def get_good_message(self, date, lesson, instructor_id):
        name = self.get_instructor_name(instructor_id)
        curr, cap = current_number_of_participeants(lesson)
        txt = f'''Hey {name}, I have good news for you :) 
        Someone just registerd to your class at {date}.
        Currently there are {curr}/{cap} participants.'''
        return txt

    def get_bad_message(self, date, lesson, instructor_id):
        name = self.get_instructor_name(instructor_id)
        curr, cap = current_number_of_participeants(lesson)
        txt = f'''Hey {name}, unfortunately someone just canceled his attending to your class at {date}.
        Currently there are {curr}/{cap} participants.'''
        return txt

    def get_cancel_message(self, date, participant_id):
        name = self.get_participant_name(participant_id)
        txt = f'''Hey {name}, unfortunately the Yoga lesson at {date} got canceled.'''
        return txt
    
    


def current_number_of_participeants(lesson):
    curr = len(lesson['ParticipantsList'])
    cap = lesson['maxNumberOfParticipants']
    return (curr, cap)


def compare_time(start, end, start_comp, end_comp):
    return start < start_comp < end_comp or start < end_comp < end \
        or start_comp < start < end_comp or start_comp < end < end_comp



def compare_keys(key, key_comp):
    if key == key_comp:
        return True
    key = key.split('_')
    key_comp = key_comp.split('_')
    if key[0] == key_comp[0]:
        start, end = key[1].split('-')
        start_comp, end_comp = key_comp[1].split('-')
        return compare_time(start, end, start_comp, end_comp)
    return False 

def check_date(date):
    date = date.split("_")[0].split("/")
    datelen = len(date)
    if datelen < 3 or datelen > 3:
        return False
    else:
        date[0], date[2] = date[2], date[0]
        return "/".join(date)

def check_date_with_hour(date):
    hour = date.split("_")
    date = hour[0].split("/")
    datelen = len(date)
    if datelen < 3 or datelen > 3:
        return False
    else:
        date[0], date[2] = date[2], date[0]
        return f'{"/".join(date)}_{hour[1]}'
