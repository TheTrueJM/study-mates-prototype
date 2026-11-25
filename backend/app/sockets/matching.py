import numpy as np
import random, math

from ..enums import AttributeType, GradeType, MeetingMode, VALID_GRADES


def form_groups(tutorial):
    group_size = tutorial["group_size"]
    max_groups = tutorial["max_groups"]

    student_details = tutorial["students"]
    student_ids = list(student_details.keys())
    total_students = len(student_ids)

    if not total_students:
        return dict()

    # Balance Group Sizes, restricting the Maximum Total of Groups if set
    total_groups = math.ceil(total_students / group_size)
    if max_groups:
        total_groups = min(total_groups, max_groups)
    base_size, extra = divmod(total_students, total_groups)
    group_sizes = [base_size + 1] * extra + [base_size] * (total_groups - extra)
    largest_group = group_sizes[0]

    available_attributes = tutorial["available_attributes"]

    connections: np.ndarray = build_matrix(student_ids, student_details, available_attributes)

    groups = dict()
    previous_matches = tutorial["previous_matches"]

    REMATCH_RATE = (0.5 / (largest_group ** 1.1)) # NOTE This is a Magic Number
    unmatched = set(enumerate(student_ids))

    for group_id, target_size in enumerate(group_sizes, start=1):
        # Pick a Random Starting Student
        first_student = random.choice(tuple(unmatched))
        unmatched.remove(first_student)
        group = [first_student]

        # Fill group with most Compatible Students
        while len(group) < target_size and unmatched:
            best_student, best_score = None, -math.inf

            for (candidate, c_id) in unmatched:
                # Compatibility with Entire Group
                score = rematches = 0
                for (member, m_id) in group:
                    # Track rematches between Students in the Group, with a slight chance to allow Rematches
                    if c_id in previous_matches.get(m_id, ()) and random.random() > REMATCH_RATE:
                        rematches += 1
                    score += connections[candidate][member]

                # Penalise score from Student Rematches
                if rematches:
                    score *= 0.4 - (0.4 * (rematches / largest_group)) # NOTE This is a Magic Number
                    score -= 1e-3 * rematches # Avoid rematches when students share no attributes

                # Break Ties Randomly so rounds differ even when Students are Equally Compatible
                score += random.random() * 1e-6

                if score > best_score:
                    best_score = score
                    best_student = (candidate, c_id)

            group.append(best_student)
            unmatched.remove(best_student)

        # Save group
        groups[group_id] = [id for (_, id) in group]

    return groups


def build_matrix(ids, students, available_attributes):
    student_count = len(ids)

    matrix = np.zeros((student_count, student_count))
    max_weight = 0

    # Students without a GPA or Goal Grade are treated as the Tutorial Average
    attribute_averages = calculate_available_averages(students, available_attributes)
    default_current_gpa = attribute_averages.get(str(AttributeType.CURRENT_GPA), int(GradeType.P))
    default_goal_grade = attribute_averages.get(str(AttributeType.GOAL_GRADE), int(GradeType.P))

    def grade_or_default(value, default):
        return value if value in VALID_GRADES else default

    details = []
    for student_id in ids:
        attributes = students.get(student_id, {}).get("attributes") or {}
        details.append({
            "current_gpa": grade_or_default(attributes.get(str(AttributeType.CURRENT_GPA)), default_current_gpa),
            "goal_grade": grade_or_default(attributes.get(str(AttributeType.GOAL_GRADE)), default_goal_grade),
            "availability": set(attributes.get(str(AttributeType.AVAILABILITY)) or []),
            "communication": set(attributes.get(str(AttributeType.COMMUNICATION)) or []),
            "meeting_mode": attributes.get(str(AttributeType.MEETING_MODE)),
        })

    for i in range(student_count):
        s1 = details[i]

        for j in range(i + 1, student_count):
            s2 = details[j]

            weight = 0

            # NOTE All Weights are just Magic Numbers
            if str(AttributeType.CURRENT_GPA) in available_attributes:
                diff = abs(s1["current_gpa"] - s2["current_gpa"])
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if str(AttributeType.GOAL_GRADE) in available_attributes:
                diff = abs(s1["goal_grade"] - s2["goal_grade"])
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if str(AttributeType.AVAILABILITY) in available_attributes:
                weight += 0.5 * len(s1["availability"] & s2["availability"])

            if str(AttributeType.COMMUNICATION) in available_attributes:
                weight += len(s1["communication"] & s2["communication"])

            if str(AttributeType.MEETING_MODE) in available_attributes:
                m1, m2 = s1["meeting_mode"], s2["meeting_mode"]
                if m1 and m2 and (m1 == m2 or str(MeetingMode.EITHER) in (m1, m2)):
                    weight += 2

            matrix[i][j] = matrix[j][i] = weight
            max_weight = max(max_weight, weight)

    # Normalise Matrix Weights (skip when no students share any attributes)
    if max_weight > 0:
        matrix /= max_weight

    return matrix


def calculate_available_averages(students, available_attributes):
    total_current_gpa = 0
    students_current_gpa = 0

    total_goal_grade = 0
    students_goal_grade = 0

    for student in students.values():
        attributes = student.get("attributes") or {}
        if str(AttributeType.CURRENT_GPA) in available_attributes:
            current_gpa = attributes.get(str(AttributeType.CURRENT_GPA))
            if current_gpa in VALID_GRADES:
                total_current_gpa += current_gpa
                students_current_gpa += 1
        if str(AttributeType.GOAL_GRADE) in available_attributes:
            goal_grade = attributes.get(str(AttributeType.GOAL_GRADE))
            if goal_grade in VALID_GRADES:
                total_goal_grade += goal_grade
                students_goal_grade += 1

    averages = {}

    if students_current_gpa: averages[str(AttributeType.CURRENT_GPA)] = round(total_current_gpa / students_current_gpa)
    if students_goal_grade: averages[str(AttributeType.GOAL_GRADE)] = round(total_goal_grade / students_goal_grade)

    return averages
