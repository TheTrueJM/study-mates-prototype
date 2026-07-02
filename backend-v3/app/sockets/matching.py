import numpy as np
import random, math

from ..enums import AttributeType, GradeType, MeetingMode, VALID_GRADES


def form_groups(tutorial):
    group_size = tutorial["group_size"]
    max_groups = tutorial["max_groups"]
    
    student_details = tutorial["students"]
    student_ids = list(student_details.keys())
    total_students = len(student_ids)

    # Restrict Maximum Total of Groups
    if max_groups and max_groups < math.ceil(total_students / group_size):
        group_size = math.ceil(total_students / max_groups)

    available_attributes = tutorial["available_attributes"]

    connections: np.ndarray = build_matrix(student_ids, student_details, available_attributes)

    groups = dict()
    group_id = 1

    REMATCH_RATE = (0.5 / (group_size ** 1.1)) # NOTE This is a Magic Number
    unmatched = set(enumerate(student_ids))

    print("DEBUG: Tutorial with Groups", student_details)

    while unmatched:
        # Pick a starting student
        group = [unmatched.pop()]

        # Fill group with most compatible students
        while len(group) < group_size and unmatched:
            best_student, best_score = None, -1

            for (candidate, c_id) in unmatched:
                # Compatibility with entire group
                score = rematches = 0
                for (member, m_id) in group:
                    # Track rematches between students in the group, with a slight chance to allow rematches through uncounted
                    if c_id in tutorial["previous_matches"].get(m_id, []) and random.random() > REMATCH_RATE:
                        rematches += 1
                    score += connections[candidate][member]

                # Penalise score from student rematches
                if rematches: score *=  0.4 - (0.4 * (rematches / group_size)) # NOTE This is a Magic Number

                print("DEBUG: Score and Best Score", score, best_score)
                if score > best_score:
                    best_score = score
                    best_student = (candidate, c_id)

            group.append(best_student)
            unmatched.remove(best_student)

        # Save group
        groups[group_id] = [id for (_, id) in group]
        group_id += 1
    
    return groups


def build_matrix(ids, students, available_attributes):
    student_count = len(ids)

    matrix = np.zeros((student_count, student_count))
    max_weight = 0

    attribute_averages = calculate_available_averages(students, available_attributes)
    attribute_averages.setdefault(str(AttributeType.CURRENT_GPA), int(GradeType.P))
    attribute_averages.setdefault(str(AttributeType.GOAL_GRADE), int(GradeType.P))

    for i in range(student_count):
        s1 = students.get(ids[i], {})

        s1_current_gpa = s1.get(str(AttributeType.CURRENT_GPA), attribute_averages[str(AttributeType.CURRENT_GPA)])
        s1_goal_grade = s1.get(str(AttributeType.GOAL_GRADE), attribute_averages[str(AttributeType.GOAL_GRADE)])
        s1_availability = set(s1.get(str(AttributeType.AVAILABILITY), []))
        s1_communication = set(s1.get(str(AttributeType.COMMUNICATION), []))
        s1_meeting = s1.get(str(AttributeType.MEETING_MODE))

        for j in range(i + 1, student_count):
            s2 = students.get(ids[j], {})

            s2_current_gpa = s2.get(str(AttributeType.CURRENT_GPA), attribute_averages[str(AttributeType.CURRENT_GPA)])
            s2_goal_grade = s2.get(str(AttributeType.GOAL_GRADE), attribute_averages[str(AttributeType.GOAL_GRADE)])
            s2_availability = set(s2.get(str(AttributeType.AVAILABILITY), []))
            s2_communication = set(s2.get(str(AttributeType.COMMUNICATION), []))
            s2_meeting = s2.get(str(AttributeType.MEETING_MODE))

            weight = 0

            # NOTE All Weights are just Magic Numbers
            if str(AttributeType.CURRENT_GPA) in available_attributes:
                diff = abs(s1_current_gpa - s2_current_gpa)
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if str(AttributeType.GOAL_GRADE) in available_attributes:
                diff = abs(s1_goal_grade - s2_goal_grade)
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if str(AttributeType.AVAILABILITY) in available_attributes:
                weight += sum(0.5 for time in s2_availability if time in s1_availability)
            
            if str(AttributeType.COMMUNICATION) in available_attributes:
                weight += sum(1 for method in s2_communication if method in s1_communication)

            if str(AttributeType.MEETING_MODE) in available_attributes:
                if s1_meeting and (s1_meeting == s2_meeting or s1_meeting == str(MeetingMode.EITHER) or s2_meeting == str(MeetingMode.EITHER)):
                    weight += 2

            matrix[i][j] = matrix[j][i] = weight
            max_weight = max(max_weight, weight)

    # Normalise matrix weights
    for i in range(student_count):
        for j in range(i + 1, student_count):
            matrix[i][j] = matrix[j][i] = matrix[i][j] / max_weight

    return matrix


def calculate_available_averages(students, available_attributes):
    total_current_gpa = 0
    students_current_gpa = 0

    total_goal_grade = 0
    students_goal_grade = 0

    for student in students.values():
        if str(AttributeType.CURRENT_GPA) in available_attributes:
            current_gpa = student.get("attributes", {}).get(str(AttributeType.CURRENT_GPA))
            if current_gpa and current_gpa in VALID_GRADES:
                total_current_gpa += current_gpa
                students_current_gpa += 1
        if str(AttributeType.GOAL_GRADE) in available_attributes:
            goal_grade = student.get("attributes", {}).get(str(AttributeType.GOAL_GRADE))
            if goal_grade and goal_grade in VALID_GRADES:
                total_goal_grade += goal_grade
                students_goal_grade += 1

    averages = {}

    if students_current_gpa: averages[str(AttributeType.CURRENT_GPA)] = round(total_current_gpa / students_current_gpa)
    if students_goal_grade: averages[str(AttributeType.GOAL_GRADE)] = round(total_goal_grade / students_goal_grade)

    return averages