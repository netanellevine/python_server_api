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
