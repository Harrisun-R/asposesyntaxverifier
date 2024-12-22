import re
import json
import streamlit as st

# Define a function to verify the template syntax and execute it
def verify_and_execute_template(template, predefined_json):
    field_pattern = r"<<\[(\w+(\.\w+)*)\]>>"  # Matches fields like <<[FieldName]>>
    var_pattern = r"<<var \[(.*?)]>>"  # Matches variable definitions like <<var [x = 5]>>
    foreach_open_pattern = r"<<foreach \[(.*?) in (.*?)]>>"  # Matches opening foreach tags
    foreach_close_pattern = r"<</foreach>>"  # Matches closing foreach tags
    if_open_pattern = r"<<if \[(.*?)]>>"  # Matches opening if tags
    elseif_pattern = r"<<elseif \[(.*?)]>>"  # Matches elseif tags
    else_pattern = r"<<else>>"  # Matches else tags
    if_close_pattern = r"<</if>>"  # Matches closing if tags

    result = []  # To store the final output

    # Tokenize and parse the template line-by-line
    lines = template.splitlines()
    stack = []

    def resolve_field(field_name):
        """Resolve a field from JSON using dot notation."""
        keys = field_name.split(".")
        current_level = predefined_json
        for key in keys:
            if isinstance(current_level, list):
                try:
                    key = int(key)  # Convert to integer if accessing list index
                except ValueError:
                    return f"Error: List index '{key}' is invalid."
            if isinstance(current_level, dict) and key not in current_level:
                return f"Error: Field '{field_name}' not found in JSON."
            current_level = current_level[key]
        return current_level

    for line in lines:
        # Handle foreach opening tag
        foreach_match = re.match(foreach_open_pattern, line)
        if foreach_match:
            var_name, list_name = foreach_match.groups()
            list_data = resolve_field(list_name)
            if isinstance(list_data, list):
                stack.append(("foreach", var_name, iter(list_data)))
            else:
                return f"Error: '{list_name}' is not a list."
            continue

        # Handle foreach closing tag
        if re.match(foreach_close_pattern, line):
            if stack and stack[-1][0] == "foreach":
                stack.pop()
            else:
                return "Error: Unmatched <</foreach>>."
            continue

        # Handle if opening tag
        if_match = re.match(if_open_pattern, line)
        if if_match:
            condition = if_match.group(1)
            try:
                condition_result = eval(condition, {}, predefined_json)
                stack.append(("if", condition_result))
            except Exception as e:
                return f"Error evaluating condition '{condition}': {e}"
            continue

        # Handle elseif tag
        elseif_match = re.match(elseif_pattern, line)
        if elseif_match:
            condition = elseif_match.group(1)
            if stack and stack[-1][0] == "if" and not stack[-1][1]:
                try:
                    condition_result = eval(condition, {}, predefined_json)
                    stack[-1] = ("if", condition_result)
                except Exception as e:
                    return f"Error evaluating condition '{condition}': {e}"
            continue

        # Handle else tag
        if re.match(else_pattern, line):
            if stack and stack[-1][0] == "if" and not stack[-1][1]:
                stack[-1] = ("if", True)  # Else branch is executed
            continue

        # Handle if closing tag
        if re.match(if_close_pattern, line):
            if stack and stack[-1][0] == "if":
                stack.pop()
            else:
                return "Error: Unmatched <</if>>."
            continue

        # Handle fields
        field_match = re.findall(field_pattern, line)
        if field_match:
            for field_name in field_match:
                field_value = resolve_field(field_name[0])
                if isinstance(field_value, str) or isinstance(field_value, (int, float)):
                    line = line.replace(f"<<[{field_name[0]}]>>", str(field_value))
                else:
                    return f"Error: Field '{field_name[0]}' is not a valid string or number."
            result.append(line)

        # Handle other lines
        else:
            result.append(line)

    # Check for unmatched tags
    if stack:
        return "Error: Unmatched opening tags."

    return "\n".join(result)

# Streamlit app
st.title("Template Syntax Verifier and Executor")

# Navigation to switch between pages
page = st.sidebar.selectbox("Choose a page", ["Verify Template", "Execute Template"])

if page == "Verify Template":
    # Upload predefined JSON
    predefined_json = None
    uploaded_file = st.file_uploader("Upload Predefined JSON", type=["json"])
    if uploaded_file is not None:
        predefined_json = json.load(uploaded_file)
        st.success("Predefined JSON uploaded successfully!")

    # Text area to input the template
    template = st.text_area("Enter the template:")

    # Verify button
    if st.button("Verify Syntax"):
        if predefined_json is None:
            st.error("Please upload a predefined JSON file first.")
        else:
            result = verify_and_execute_template(template, predefined_json)
            if "Error" in result:
                st.error(result)
            else:
                st.success("Template syntax is valid!")

elif page == "Execute Template":
    # Upload predefined JSON
    predefined_json = None
    uploaded_file = st.file_uploader("Upload Predefined JSON", type=["json"])
    if uploaded_file is not None:
        predefined_json = json.load(uploaded_file)
        st.success("Predefined JSON uploaded successfully!")

    # Text area to input the template
    template = st.text_area("Enter the template:")

    # Execute button
    if st.button("Execute Template"):
        if predefined_json is None:
            st.error("Please upload a predefined JSON file first.")
        else:
            result = verify_and_execute_template(template, predefined_json)
            if "Error" in result:
                st.error(result)
            else:
                st.subheader("Execution Result:")
                st.code(result)
