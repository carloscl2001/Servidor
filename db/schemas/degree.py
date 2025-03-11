def degree_schema(degree)-> dict:
    return {
        "code": degree["code"],
        "name": degree["name"],
        "subjects": subjects_schemas(degree.get("subjects", [])),
    }

def degrees_schema(degrees) -> list:
    return [degree_schema(degree) for degree in degrees]


def subject_schema(subject) -> dict:
    return{
        "code": subject["code"]
    }

def subjects_schemas(subjects) -> list:
    return [subject_schema(subject) for subject in subjects]