def subject_schema(subject) -> dict:
    return {
        "code": subject["code"],
        "name": subject["name"],
        "classes": classes_schema(subject.get("classes", [])),  # Aplica el esquema de clases
    }

def subjects_schema(subjects) -> list:
    return [subject_schema(subject) for subject in subjects]




def class_schema(class_) -> dict:
    return {
        "type": class_["type"],
        "events": events_schema(class_.get("events", [])),  # Aplica el esquema de eventos
    }

def classes_schema(classes) -> list:
    return [class_schema(class_) for class_ in classes]



def event_schema(event) -> dict:
    return {
        "date": event["date"],
        "start_hour": event["start_hour"],
        "end_hour": event["end_hour"],
        "location": event["location"],
    }

def events_schema(events) -> list:
    return [event_schema(event) for event in events]

