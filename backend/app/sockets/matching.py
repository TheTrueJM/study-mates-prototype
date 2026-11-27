import numpy as np
import itertools, random, time

from ..enums import AttributeType, GradeType, MeetingMode, VALID_GRADES, VALID_AVAILABILITY_CODES
from ..custom_attributes import SIMILAR, MIXED, WEIGHTS, NORMAL, custom_similarity
from .seating import get_table


# NOTE All Weights are just Magic Numbers, relative to the Most Compatible pair of Students (which scores 1)
AVAILABILITY_WEIGHT = 0.35
REMATCH_WEIGHT = 0.9

COMMON_TIMES = 2 # Best Meeting Times of a Group that are scored
SWAP_TIME_LIMIT = 0.5 # Seconds


def form_groups(tutorial):
    """
    Forms Groups of the most Compatible Students, numbered by the Table each Group meets at.
    Students staying at their Table (see seating.py) start the Group at their Table, which is then filled
    and improved exactly like every other Group, except that they're never Swapped away from it.
    """
    group_size = tutorial["group_size"]
    max_groups = tutorial["max_groups"]

    student_details = tutorial["students"]
    student_ids = list(student_details.keys())
    total_students = len(student_ids)

    if not total_students:
        return dict()

    # Students are referred to by their Index (in student_ids) while matching
    seated = dict() # { Table: [Student, ...] }
    for student, student_id in enumerate(student_ids):
        table = get_table(tutorial, student_details[student_id])
        if table is not None:
            seated.setdefault(table, []).append(student)

    group_sizes = get_group_sizes(total_students, group_size, max_groups)
    if len(seated) > len(group_sizes):
        # Every Table with a Seated Student needs its own Group (even beyond the Group Limit)
        group_sizes = get_balanced_sizes(total_students, len(seated))

    available_attributes = tutorial["available_attributes"]

    custom_attributes = tutorial.get("custom_attributes", [])
    connections: np.ndarray = build_matrix(student_ids, student_details, available_attributes, custom_attributes)
    availability: np.ndarray = build_availability(student_ids, student_details, available_attributes)
    rematches: np.ndarray = build_rematches(student_ids, tutorial["previous_matches"], largest_group=group_sizes[0])

    def score(group):
        return score_group(group, connections, availability, rematches)

    # Each Seated Table takes one of the Groups, which are then Filled in a Random Order
    # (so Seated Students aren't always given the First Choice of Classmates, or the Largest or Smallest Group)
    if seated:
        random.shuffle(group_sizes)
    plan = [(size, table) for size, table in itertools.zip_longest(group_sizes, seated) if size is not None]
    if seated:
        random.shuffle(plan)

    fixed = {student for students in seated.values() for student in students}
    unmatched = set(range(total_students)) - fixed
    groups, tables = [], []

    for target_size, table in plan:
        if table is not None:
            # Start with the Seated Students at the Table
            group = list(seated[table])
        elif unmatched:
            # Pick a Random Starting Student
            first_student = random.choice(tuple(unmatched))
            unmatched.remove(first_student)
            group = [first_student]
        else:
            continue # Larger Seated Tables took the Students this Group would have had

        # Fill group with most Compatible Students
        while len(group) < target_size and unmatched:
            # Break Ties Randomly so rounds differ even when Students are Equally Compatible
            best_student = max(unmatched, key=lambda student: score(group + [student]) + random.random() * 1e-6)

            group.append(best_student)
            unmatched.remove(best_student)

        # Save group
        groups.append(group)
        tables.append(table)

    # The Last Groups are left with whoever remains, so improve all Groups afterwards
    improve_groups(groups, score, fixed)

    return {
        number: [student_ids[student] for student in group]
        for number, group in sorted(zip(number_groups(tables), groups), key=lambda numbered: numbered[0])
    }


def number_groups(tables):
    """
    The Number of each Group: the Table of its Seated Students, or otherwise the Lowest Number not taken by a Table
    (e.g. 3 Groups with Seated Students at Table 5 are numbered 1, 2, and 5)
    """
    taken = {table for table in tables if table is not None}
    free = (number for number in itertools.count(1) if number not in taken)
    return [table if table is not None else next(free) for table in tables]


def get_group_sizes(total_students, group_size, max_groups=None):
    """
    Sizes of the Groups to Form, with as many of the Group Size as possible:
      - 2 or more Students left over become a smaller Group (e.g. 7 students in groups of 5 becomes [5, 2])
      - 1 Student left over joins another Group, to not be alone (e.g. 6 students in groups of 5 becomes [6])
    """
    full_groups, left_over = divmod(total_students, group_size)
    group_sizes = [group_size] * full_groups

    if left_over == 1 and group_sizes:
        group_sizes[0] += 1
    elif left_over:
        group_sizes.append(left_over)

    # Balance Larger Groups if restricted to a Maximum Total of Groups
    if max_groups and len(group_sizes) > max_groups:
        group_sizes = get_balanced_sizes(total_students, max_groups)

    return group_sizes


def get_balanced_sizes(total_students, total_groups):
    """Sizes of an exact number of Groups, as Equal as possible (e.g. 11 students in 3 groups becomes [4, 4, 3])"""
    base_size, extra = divmod(total_students, total_groups)
    return [base_size + 1] * extra + [base_size] * (total_groups - extra)


def improve_groups(groups, score, fixed=frozenset()):
    """
    Swaps Students between Groups for as long as it improves their Combined Score (modifies the groups).
    Fixed Students (those staying at their Table) are never Swapped, but anyone can be Swapped into their Group.
    """
    deadline = time.monotonic() + SWAP_TIME_LIMIT
    scores = [score(group) for group in groups]

    improved = True
    while improved:
        improved = False

        for a, b in itertools.combinations(range(len(groups)), 2):
            # Large Tutorials have many possible Swaps, so don't hold up the server
            if time.monotonic() > deadline:
                return

            for i, j in itertools.product(range(len(groups[a])), range(len(groups[b]))):
                if groups[a][i] in fixed or groups[b][j] in fixed:
                    continue

                group_a, group_b = groups[a].copy(), groups[b].copy()
                group_a[i], group_b[j] = group_b[j], group_a[i]
                score_a, score_b = score(group_a), score(group_b)

                if score_a + score_b > scores[a] + scores[b] + 1e-9:
                    groups[a], groups[b] = group_a, group_b
                    scores[a], scores[b] = score_a, score_b
                    improved = True


def score_group(group, connections, availability, rematches):
    """Compatibility of an Entire Group, from each pair of Students, their Common Times, and any Rematches"""
    size = len(group)
    if size < 2:
        return 0

    members = np.ix_(group, group)
    total_pairs = size * (size - 1) # Both directions of each pair

    score = connections[members].sum() / total_pairs
    score -= REMATCH_WEIGHT * rematches[members].sum() / total_pairs
    if availability is not None:
        score += AVAILABILITY_WEIGHT * score_common_times(availability[group])

    return score * size


def score_common_times(times):
    """
    How well a Group's best Meeting Times suit its Students (0 to 1, where everyone is available for them).
    A Meeting needs the Entire Group, so times suiting only some Students are worth much less.
    """
    provided = times[times.any(axis=1)] # Students without any Availability aren't counted
    if len(provided) < 2:
        return 0

    portions = provided.sum(axis=0) / len(provided)
    best_portions = np.sort(portions)[-COMMON_TIMES:]
    return (best_portions ** 3).mean() # NOTE This is a Magic Number


def build_availability(ids, students, available_attributes):
    """Matrix of whether each Student (row) is available for each Time (column), or None if not enabled"""
    if str(AttributeType.AVAILABILITY) not in available_attributes:
        return None

    codes = sorted(VALID_AVAILABILITY_CODES)
    matrix = np.zeros((len(ids), len(codes)))
    for i, student_id in enumerate(ids):
        attributes = students.get(student_id, {}).get("attributes") or {}
        provided = set(attributes.get(str(AttributeType.AVAILABILITY)) or [])
        matrix[i] = [code in provided for code in codes]

    return matrix


def build_rematches(ids, previous_matches, largest_group):
    """Matrix of which Students were previously matched, with a slight chance to allow a Rematch"""
    REMATCH_RATE = (0.5 / (largest_group ** 1.1)) # NOTE This is a Magic Number
    student_count = len(ids)
    matrix = np.zeros((student_count, student_count))

    for i, j in itertools.combinations(range(student_count), 2):
        if ids[j] in previous_matches.get(ids[i], ()) and random.random() > REMATCH_RATE:
            matrix[i][j] = matrix[j][i] = 1

    return matrix


def build_matrix(ids, students, available_attributes, custom_attributes=()):
    """
    Matrix of how compatible each pair of Students is (Availability is scored across the Entire Group instead).
    Matching Custom Details score Students with Similar answers (or Different answers when Mixed) as compatible.
    """
    student_count = len(ids)
    matching_custom = [
        d for d in custom_attributes if d["matching"] in (SIMILAR, MIXED) and d["id"] in available_attributes
    ]

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
            "communication": set(attributes.get(str(AttributeType.COMMUNICATION)) or []),
            "meeting_mode": attributes.get(str(AttributeType.MEETING_MODE)),
            "custom": {d["id"]: attributes.get(d["id"]) for d in matching_custom},
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

            if str(AttributeType.COMMUNICATION) in available_attributes:
                weight += len(s1["communication"] & s2["communication"])

            if str(AttributeType.MEETING_MODE) in available_attributes:
                m1, m2 = s1["meeting_mode"], s2["meeting_mode"]
                if m1 and m2 and (m1 == m2 or str(MeetingMode.EITHER) in (m1, m2)):
                    weight += 2

            # Students who haven't both answered are neither Similar nor Different
            for definition in matching_custom:
                similarity = custom_similarity(definition, s1["custom"][definition["id"]], s2["custom"][definition["id"]])
                if similarity is not None:
                    detail_weight = WEIGHTS[definition.get("weight", NORMAL)] # See WEIGHTS in custom_attributes.py
                    weight += detail_weight * (similarity if definition["matching"] == SIMILAR else 1 - similarity)

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
