import re
import json
import streamlit as st

# Default predefined JSON structure of valid fields
DEFAULT_PREDEFINED_FIELDS = {
    "FirstName": "User's first name",
    "LastName": "User's last name",
    "Contact": {
        "Email": "User's email address",
        "PhoneNumber": "User's phone number"
    },
    "Address": "User's address",
    "Orders": [
        {
            "OrderID": "Order identifier",
            "ItemName": "Name of the ordered item",
            "OrderDate": "Date of the order"
        }
    ]
}

def flatten_json(json_obj, parent_key=""):
    """
    Recursively flatten a nested JSON structure.

    Args:
        json_obj (dict or list): The JSON object to flatten.
        parent_key (str): The base key for recursion.

    Returns:
        dict: A flattened dictionary with dot-separated keys.
    """
    items = []
    if isinstance(json_obj, dict):
        for key, value in json_obj.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            items.extend(flatten_json(value, new_key).items())
    elif isinstance(json_obj, list):
        # Handle lists by assuming uniform structure and flattening the first element
        for i, value in enumerate(json_obj):
            list_key = f"{parent_key}[{i}]" if parent_key else f"[{i}]"
            items.extend(flatten_json(value, list_key).items())
        # Generalize the list structure for easier validation
        if json_obj:
            items.extend(flatten_json(json_obj[0], parent_key).items())
    else:
        items.append((parent_key, json_obj))
    return dict(items)

def verify_aspose_syntax(template_content, flattened_fields):
    """
    Verifies the syntax of an Aspose.Words template and validates fields against the flattened JSON structure.

    Args:
        template_content (str): The content of the template.
        flattened_fields (dict): The flattened JSON structure of valid fields.

    Returns:
        tuple: A list of syntax errors and a list of missing fields.
    """
    errors = []
    missing_fields = []

    # Define regular expressions for Aspose.Words syntax
    field_pattern = r"<<\[([a-zA-Z0-9_\.]+)\]>>"  # Matches <<[FieldName]>> or <<[Parent.FieldName]>>
    if_pattern = r"<<if\s+[^>]+>>|<<elseif\s+[^>]+>>|<<else>>|<</if>>"  # Matches <<if>>, <<elseif>>, <<else>>, and <</if>>
    foreach_pattern = r"<<foreach\s+[^>]+>>|<</foreach>>"  # Matches <<foreach>> and <</foreach>>

    # Stack-based approach to check for nested structures
    stack = []
    for match in re.finditer(f"{if_pattern}|{foreach_pattern}", template_content):
        tag = match.group()
        if tag.startswith("<<if") or tag.startswith("<<foreach"):
            stack.append(tag)
        elif tag == "<</if>>" or tag == "<</foreach>>":
            if not stack:
                errors.append(f"Unmatched closing tag: {tag}")
            else:
                opening_tag = stack.pop()
                if (tag == "<</if>>" and not opening_tag.startswith("<<if")) or \
                   (tag == "<</foreach>>" and not opening_tag.startswith("<<foreach")):
                    errors.append(f"Mismatched tags: {opening_tag} and {tag}")

    # Check for unclosed tags
    for unclosed_tag in stack:
        errors.append(f"Unclosed tag: {unclosed_tag}")

    # Extract all field placeholders
    fields = re.findall(field_pattern, template_content)
    
    # Validate fields against the flattened JSON
    for field in fields:
        if field not in flattened_fields:
            missing_fields.append(field)

    return errors, missing_fields

# Streamlit app
def main():
    st.title("Aspose Words Template Syntax Verifier")
    st.write("Upload your Aspose Words template or paste its content below to verify the syntax.")
    
    # Allow user to upload a predefined JSON structure
    st.subheader("Upload Predefined JSON")
    uploaded_json_file = st.file_uploader("Upload a predefined JSON file", type=["json"])
    
    if uploaded_json_file is not None:
        try:
            predefined_fields = json.load(uploaded_json_file)
            st.success("Predefined JSON uploaded successfully!")
        except Exception as e:
            st.error(f"Error reading JSON file: {e}")
            predefined_fields = DEFAULT_PREDEFINED_FIELDS
    else:
        predefined_fields = DEFAULT_PREDEFINED_FIELDS
        st.info("Using default predefined JSON fields.")

    # Flatten the predefined JSON structure
    flattened_fields = flatten_json(predefined_fields)
    
    # Show the predefined fields
    st.subheader("Available Fields")
    st.json(flattened_fields)
    
    # Input options: File upload or text area
    st.subheader("Upload Template or Paste Content")
    uploaded_file = st.file_uploader("Upload a template file (e.g., .txt)", type=["txt"])
    template_content = ""
    if uploaded_file is not None:
        template_content = uploaded_file.read().decode("utf-8")
        st.write("File content loaded successfully.")
    else:
        template_content = st.text_area("Or paste your template content below:", height=300)

    if st.button("Verify Syntax"):
        if template_content.strip():
            # Verify syntax and validate fields
            syntax_errors, missing_fields = verify_aspose_syntax(template_content, flattened_fields)
            
            # Display results
            if syntax_errors:
                st.error("Syntax errors found:")
                for error in syntax_errors:
                    st.write(f"- {error}")
            else:
                st.success("No syntax errors found!")

            if missing_fields:
                st.warning("Missing fields detected! These fields are not in the predefined JSON structure:")
                for field in missing_fields:
                    st.write(f"- {field}")
            else:
                st.success("All fields are valid and present in the predefined JSON structure.")
        else:
            st.warning("Please provide the template content.")

if __name__ == "__main__":
    main()
