import re
import json
import streamlit as st

# Define a function to verify the template syntax
def verify_template_syntax(template, predefined_json):
    # Define regex patterns for the supported syntax
    field_pattern = r"<<\\[\\w+\\]>>"  # Matches fields like <<[FieldName]>>
    var_pattern = r"<<var \\[.*?\\]>>"  # Matches variable definitions like <<var [x = 5]>>
    foreach_open_pattern = r"<<foreach \\[.*?\\]>>"  # Matches opening foreach tags like <<foreach [item in list]>>
    foreach_close_pattern = r"<</foreach>>"  # Matches closing foreach tags
    if_open_pattern = r"<<if \\[.*?\\]>>"  # Matches opening if tags like <<if [condition]>>
    elseif_pattern = r"<<elseif \\[.*?\\]>>"  # Matches elseif tags like <<elseif [condition]>>
    else_pattern = r"<<else>>"  # Matches else tags like <<else>>
    if_close_pattern = r"<</if>>"  # Matches closing if tags

    # Combine all tag patterns for detection
    all_tags_pattern = (
        f"({field_pattern}|{var_pattern}|{foreach_open_pattern}|{foreach_close_pattern}|"
        f"{if_open_pattern}|{elseif_pattern}|{else_pattern}|{if_close_pattern})"
    )

    # Tokenize the template based on the tags
    tokens = re.findall(all_tags_pattern, template)

    # Stack to track opening tags
    stack = []

    # Iterate through the tokens to validate the syntax
    for token in tokens:
        if re.match(foreach_open_pattern, token):
            stack.append("foreach")
        elif re.match(if_open_pattern, token):
            stack.append("if")
        elif re.match(var_pattern, token):
            continue  # Variables don't affect nesting, so skip
        elif re.match(foreach_close_pattern, token):
            if not stack or stack[-1] != "foreach":
                return f"Unmatched closing tag: {token}"
            stack.pop()
        elif re.match(if_close_pattern, token):
            if not stack or stack[-1] != "if":
                return f"Unmatched closing tag: {token}"
            stack.pop()
        elif re.match(elseif_pattern, token) or re.match(else_pattern, token):
            if not stack or stack[-1] != "if":
                return f"Unexpected tag without matching <if>: {token}"

    # Check if there are any unmatched opening tags left in the stack
    if stack:
        return f"Unmatched opening tag(s): {stack}"

    # Validate fields against predefined JSON
    fields = re.findall(field_pattern, template)
    for field in fields:
        field_name = field.strip("<>").strip("[]")
        if not validate_field_in_json(field_name, predefined_json):
            return f"Field '{field_name}' is not defined in the predefined JSON"

    return "Template syntax is valid!"

# Helper function to validate if a field exists in the predefined JSON
def validate_field_in_json(field, json_data):
    keys = field.split(".")
    current_level = json_data
    for key in keys:
        if isinstance(current_level, list):
            try:
                key = int(key)  # Convert to integer if accessing list index
            except ValueError:
                return False
        if key not in current_level:
            return False
        current_level = current_level[key]
    return True

# Streamlit app
st.title("Template Syntax Verifier")

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
        result = verify_template_syntax(template, predefined_json)
        if "valid" in result:
            st.success(result)
        else:
            st.error(result)
