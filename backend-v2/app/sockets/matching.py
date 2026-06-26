import random
from collections import deque

from app.enums import AttributeType


def calculate_edge_weight(student_a, student_b):
    """Calculate similarity weight between two students"""
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

def form_groups(tutorial_code, group_size):
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