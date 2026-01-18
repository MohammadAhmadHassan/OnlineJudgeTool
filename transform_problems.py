"""
Transform Level1_AllProblems.json to the correct structure for Firebase
"""
import json

# Read the original file
with open('Level1_AllProblems.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Create new structure
new_structure = {}
problem_counter = 1

# Extract sessions
sessions = data.get('sessions', {})

for session_key, session_data in sessions.items():
    problems_list = session_data.get('problems', [])
    
    # Transform each problem
    transformed_problems = []
    for problem in problems_list:
        # Create new problem with numeric ID and level
        transformed_problem = {
            'id': problem_counter,
            'level': 1,  # All are level 1
            'title': problem.get('title', ''),
            'description': problem.get('description', ''),
            'difficulty': 'Easy',  # Default difficulty
            'test_cases': problem.get('test_cases', [])
        }
        
        # Add optional fields if they exist
        if 'input_format' in problem:
            transformed_problem['input_format'] = problem['input_format']
        if 'output_format' in problem:
            transformed_problem['output_format'] = problem['output_format']
        
        transformed_problems.append(transformed_problem)
        problem_counter += 1
    
    # Add to new structure
    new_structure[session_key] = transformed_problems

# Write the transformed file
output_file = 'Level1_AllProblems_Fixed.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(new_structure, f, indent=2, ensure_ascii=False)

print(f"✅ Transformation complete!")
print(f"📄 Original file: Level1_AllProblems.json")
print(f"📄 Fixed file: {output_file}")
print(f"📊 Total problems: {problem_counter - 1}")
print(f"📊 Sessions: {len(new_structure)}")
for session_key, problems in new_structure.items():
    print(f"   - {session_key}: {len(problems)} problems")
