import re

# Read the file
with open('graph.py', 'r') as f:
    content = f.read()

# Find and replace the weather edge with conditional routing
old_pattern = r'builder\.add_edge\(\s*"weather",\s*"merge"\s*\)'
new_code = '''def weather_router(state):
    # If weather is the only route (single-agent query), go directly to END
    # If part of multi-agent flow (calendar trip planning), go to merge
    routes = state.get("routes", [])
    if len(routes) == 1 and routes[0] == "weather":
        return END
    return "merge"

builder.add_conditional_edges(
    "weather",
    weather_router,
    {
        "merge": "merge",
        END: END
    }
)'''

content = re.sub(old_pattern, new_code, content)

# Write back
with open('graph.py', 'w') as f:
    f.write(content)

print('Successfully updated graph.py')
