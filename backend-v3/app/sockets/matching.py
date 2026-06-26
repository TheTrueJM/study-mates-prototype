from collections import deque
import numpy as np
import random

from app.enums import AttributeType, GradeType, MeetingMode, VALID_GRADES


def calculate_edge_weight(student_a, student_b):
    weight = 0
    
    # GPA similarity (max weight: 5)
    if student_a.get("currentGPA") and student_b.get("currentGPA"):
        diff = abs(student_a["currentGPA"] - student_b["currentGPA"])
        gpa_weight = max(0, 5 - (diff * 5))  # 5 if same, 0 if diff >= 1.0
        weight += gpa_weight
    
    # Goal Grade similarity (max weight: 5)
    if student_a.get("goalGrade") and student_b.get("goalGrade"):
        diff = abs(student_a["goalGrade"] - student_b["goalGrade"])
        grade_weight = max(0, 5 - (diff * 5))
        weight += grade_weight
    
    # Availability overlap (max weight: 1 per shared slot)
    if student_a.get("availability") and student_b.get("availability"):
        # Convert to sets for intersection
        a_availability = set()
        b_availability = set()
        
        for day, periods in student_a["availability"].items():
            for period in periods:
                a_availability.add(f"{day}-{period}")
                
        for day, periods in student_b["availability"].items():
            for period in periods:
                b_availability.add(f"{day}-{period}")
        
        shared_slots = a_availability.intersection(b_availability)
        weight += len(shared_slots)
    
    return weight

def form_groups2(tutorial_code, group_size):
    """Form groups using graph-based algorithm"""
    from app.sockets import tutorials
    
    tutorial = tutorials[tutorial_code]
    students = list(tutorial["students"].values())
    
    if len(students) < group_size:
        return { "error": "Not enough students for group size" }
    
    # Build adjacency dictionary
    adjacency = {}  # uuid -> {other_uuid: normalized_weight}
    all_weights = []
    
    for i, student_i in enumerate(students):
        adjacency[student_i["uuid"]] = {}
        for j, student_j in enumerate(students):
            if i != j:
                weight = calculate_edge_weight(student_i, student_j)
                all_weights.append(weight)
                adjacency[student_i["uuid"]][student_j["uuid"]] = weight
    
    # Normalize weights to 0-1 range
    max_weight = max(all_weights) if all_weights else 1
    for uuid, neighbors in adjacency.items():
        for neighbor_uuid, weight in neighbors.items():
            normalized = weight / max_weight if max_weight > 0 else 0
            adjacency[uuid][neighbor_uuid] = normalized
    
    # Algorithm state
    unmatched = set(s["uuid"] for s in students)
    groups = {}  # group_id -> [uuids]
    previous_matches = tutorials[tutorial_code].get("previous_matches", {})  # uuid -> set of matched uuids
    threshold = max(0.45, 0.75 - (tutorial["round"] * 0.1))  # decreases each round
    
    while unmatched:
        current_uuid = random.choice(list(unmatched))
        current_group = [current_uuid]
        unmatched.remove(current_uuid)
        queue = deque()
        
        # Get neighbors sorted by weight (descending)
        neighbors = sorted(
            adjacency[current_uuid].items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for neighbor_uuid, weight in neighbors:
            if neighbor_uuid not in unmatched:
                continue
            
            # Check previous matches
            prev_matches = previous_matches.get(current_uuid, set())
            if neighbor_uuid in prev_matches:
                # Re-match only with random chance (35%)
                if random.random() > 0.35:
                    continue
            
            # Check threshold
            if weight >= threshold:
                queue.appendleft(neighbor_uuid)
            else:
                queue.append(neighbor_uuid)
        
        # Fill current group from queue
        while queue and len(current_group) < group_size:
            next_uuid = queue.popleft()
            if next_uuid in unmatched:
                current_group.append(next_uuid)
                unmatched.remove(next_uuid)
                # Add to previous matches for both students
                if current_uuid not in previous_matches:
                    previous_matches[current_uuid] = set()
                if next_uuid not in previous_matches:
                    previous_matches[next_uuid] = set()
                previous_matches[current_uuid].add(next_uuid)
                previous_matches[next_uuid].add(current_uuid)
        
        # If current_group is full, save it
        if len(current_group) == group_size:
            group_id = f"G{len(groups) + 1}"
            groups[group_id] = current_group
        elif len(current_group) > 0:
            # Partial group - save anyway
            group_id = f"G{len(groups) + 1}"
            groups[group_id] = current_group
        
        # If queue empty and unmatched not empty, pick new start
        if not queue and unmatched:
            current_uuid = random.choice(list(unmatched))
            unmatched.remove(current_uuid)
            current_group = [current_uuid]
    
    # Store groups in tutorial
    tutorial["groups"] = groups
    tutorial["round"] += 1
    tutorial["state"] = "groups"
    
    # Update student group assignments
    for group_id, members in groups.items():
        for member_uuid in members:
            tutorial["students"][member_uuid]["group"] = group_id
    
    return groups



def form_groups(tutorial):
    group_size = tutorial["group_size"]
    max_groups = tutorial["max_groups"]
    
    student_details = tutorial["students"]
    student_ids = list(student_details.keys())

    available_attributes = tutorial["available_attributes"]

    connections: np.ndarray = build_matrix(student_ids, student_details, available_attributes)

    groups = dict()
    group_id = 1

    REMATCH_RATE = (0.5 / (group_size ** 1.1)) # NOTE This is a Magic Number
    unmatched = set(enumerate(student_ids))
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
                    if c_id in tutorial["previous_matches"].get(m_id, ()) and random.random() > REMATCH_RATE:
                        rematches += 1
                    score += connections[candidate][member]

                # Penalise score from student rematches
                if rematches: score *=  0.4 - (0.4 * (rematches / group_size)) # NOTE This is a Magic Number

                if score > best_score:
                    best_score = score
                    best_student = (candidate, c_id)

            group.append(best_student)
            unmatched.remove(best_student)

        # Save group
        tutorial["groups"][group_id] = []
        member_ids = set({id for (_, id) in group})
        for id in member_ids:
            tutorial["groups"][group_id].append(id)
            tutorial["students"][id]["group"] = group_id
            tutorial["previous_matches"].setdefault(id, set()).update(member_ids)

        group_id += 1
    return groups


def build_matrix(ids, students, available_attributes):
    student_count = len(ids)

    matrix = np.zeros((student_count, student_count))
    max_weight = 0

    attribute_averages = calculate_available_averages(students, available_attributes)
    attribute_averages.setdefault(AttributeType.CURRENT_GPA, GradeType.P)
    attribute_averages.setdefault(AttributeType.GOAL_GRADE, GradeType.P)

    for i in range(student_count):
        s1 = students.get(ids[i], {})

        s1_current_gpa = s1.get(AttributeType.CURRENT_GPA, attribute_averages[AttributeType.CURRENT_GPA])
        s1_goal_grade = s1.get(AttributeType.GOAL_GRADE, attribute_averages[AttributeType.GOAL_GRADE])
        s1_availability = set(s1.get(AttributeType.AVAILABILITY, []))
        s1_communication = set(s1.get(AttributeType.COMMUNICATION, []))
        s1_meeting = s1.get(AttributeType.MEETING_MODE)

        for j in range(i + 1, student_count):
            s2 = students.get(ids[j], {})

            s2_current_gpa = s2.get(AttributeType.CURRENT_GPA, attribute_averages[AttributeType.CURRENT_GPA])
            s2_goal_grade = s2.get(AttributeType.GOAL_GRADE, attribute_averages[AttributeType.GOAL_GRADE])
            s2_availability = set(s2.get(AttributeType.AVAILABILITY, []))
            s2_communication = set(s2.get(AttributeType.COMMUNICATION, []))
            s2_meeting = s2.get(AttributeType.MEETING_MODE)

            weight = 0

            # NOTE All Weights are just Magic Numbers
            if AttributeType.CURRENT_GPA in available_attributes:
                diff = abs(s1_current_gpa - s2_current_gpa)
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if AttributeType.GOAL_GRADE in available_attributes:
                diff = abs(s1_goal_grade - s2_goal_grade)
                weight += 5 if diff == 0 else 2.5 if diff == 1 else 0

            if AttributeType.AVAILABILITY in available_attributes:
                weight += sum(0.5 for time in s2_availability if time in s1_availability)
            
            if AttributeType.COMMUNICATION in available_attributes:
                weight += sum(1 for method in s2_communication if method in s1_communication)

            if AttributeType.MEETING_MODE in available_attributes:
                if s1_meeting and (s1_meeting == s2_meeting or s1_meeting == MeetingMode.EITHER or s2_meeting == MeetingMode.EITHER):
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

    for student in students:
        if AttributeType.CURRENT_GPA in available_attributes:
            current_gpa = student.get("attributes", {}).get(AttributeType.CURRENT_GPA)
            if current_gpa and current_gpa in VALID_GRADES:
                total_current_gpa += current_gpa
                students_current_gpa += 1
        if AttributeType.GOAL_GRADE in available_attributes:
            goal_grade = student.get("attributes", {}).get(AttributeType.GOAL_GRADE)
            if goal_grade and goal_grade in VALID_GRADES:
                total_goal_grade += goal_grade
                students_goal_grade += 1

    averages = {}

    if students_current_gpa: averages[AttributeType.CURRENT_GPA] = round(total_current_gpa / students_current_gpa)
    if students_goal_grade: averages[AttributeType.GOAL_GRADE] = round(total_goal_grade / students_goal_grade)

    return averages