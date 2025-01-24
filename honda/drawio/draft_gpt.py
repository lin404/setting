from pydantic import BaseModel
from typing import List
from openai import OpenAI
import openai
import xml.etree.ElementTree as ET
import instructor
import pandas as pd

# Define models for structured response
class Node(BaseModel):
    id: str
    label: str
    shape: str
    x: int
    y: int

class Connection(BaseModel):
    source: str
    target: str
    label: str

class WorkflowStructure(BaseModel):
    nodes: List[Node]
    connections: List[Connection]

# OpenAI API key

openai.api_key = API_KEY

def get_workflow_structure_gpt(workflow_description: str) -> WorkflowStructure:
    """Use GPT with a structured response model to infer workflow structure."""
    client = instructor.from_openai(OpenAI(api_key=API_KEY))

    prompt = f"""
    Analyze the following workflow description and suggest an improved structure for visualization:
    - Identify decision points and their branches (e.g., "if yes", "if no").
    - Suggest relationships between nodes.
    - Evaluate each node label and, if possible, suggest a concise version to use in the diagram without losing meaning.
    - Normalize the positions (x, y) of the nodes so that the diagram fits within a width of 1000 and a height of 800.
    
    Output a structured JSON response with:
    - Nodes: Each node has an 'id', 'label', 'shape' (ellipse, rectangle, rhombus), and coordinates ('x', 'y').
    - Connections: Each connection has a 'source', 'target', and an optional 'label' (e.g., "Yes", "No").

    Workflow description:
    {workflow_description}
    """
    response = client.chat.completions.create(
        model="gpt-4",
        response_model=WorkflowStructure,
        # max_tokens=500,
        messages=[
            {"role": "system", "content": "You are an assistant that generates workflow structures in JSON format."},
            {"role": "user", "content": prompt},
        ],
    )
    return response

def create_drawio_diagram_gpt(workflow_structure):
    """Generate a draw.io diagram based on the improved workflow structure."""
    root = ET.Element("mxfile")
    diagram = ET.SubElement(root, "diagram", name="Workflow")
    mxGraphModel = ET.SubElement(diagram, "mxGraphModel")
    root_element = ET.SubElement(mxGraphModel, "root")

    # Add draw.io default elements
    ET.SubElement(root_element, "mxCell", id="0")
    ET.SubElement(root_element, "mxCell", id="1", parent="0")

    # Map for unique node IDs
    unique_node_ids = {}
    node_counter = 2  # Start after reserved IDs (0, 1)

    # Add nodes
    for node in workflow_structure.nodes:
        unique_id = f"n{node_counter}"  # Generate unique node ID
        unique_node_ids[node.id] = unique_id  # Map original ID to unique ID
        node_counter += 1

        cell = ET.SubElement(
            root_element,
            "mxCell",
            id=unique_id,
            value=node.label,
            style=f"shape={node.shape};whiteSpace=wrap;html=1;",
            vertex="1",
            parent="1",
        )
        ET.SubElement(cell, "mxGeometry", **{
            "as": "geometry",
            "x": str(node.x),
            "y": str(node.y),
            "width": "120",
            "height": "60"
        })

    # Add connections
    connection_counter = 1
    for conn in workflow_structure.connections:
        unique_connection_id = f"e{connection_counter}"  # Generate unique connection ID
        connection_counter += 1

        connection = ET.SubElement(
            root_element,
            "mxCell",
            id=unique_connection_id,
            edge="1",
            source=unique_node_ids[conn.source],  # Map to unique node ID
            target=unique_node_ids[conn.target],  # Map to unique node ID
            parent="1",
            style="edgeStyle=orthogonalEdgeStyle;rounded=1;",
        )
        ET.SubElement(connection, "mxGeometry", **{"as": "geometry", "relative": "1"})
        if hasattr(conn, "label") and conn.label:  # Check if label exists
            connection.set("value", conn.label)  # Add label to the connection

    # Write XML to file
    tree = ET.ElementTree(root)
    with open("honda_workflow.xml", "wb") as file:
        tree.write(file, encoding="UTF-8", xml_declaration=True)

    print("Enhanced workflow diagram generated: honda_workflow.xml")

# Example workflow description
# workflow_description = """
# Step 1: Prompt for the Company Name
# 1-1: Ask the user for the company name using click.prompt.
# 1-2: If the name is blank, output an error and exit.
# Step 2: Query the Company Table
# 2-1: Search for the company in the companies table by the given name.
# 2-2: Three possible outcomes:
# 2-2-1: No match: Output an error that no company was found and exit.
# 2-2-2: One match: Retrieve the company_id and company_index_id and proceed to the next step.
# 2-2-3: Multiple matches:
# 2-2-3-1: Display a table with all matching company_id and company_index_id.
# 2-2-3-2: Ask the user to confirm whether to proceed with the first result or exit.
# Step 3: Check for Existing Data
# 3-1: Query the company_infra_resources and company_infra_resource_permissions tables to see if there is already data for the given company_id.
# 3-2: Three possible outcomes:
# 3-2-1: No existing data: Proceed to Step 5 (Insert New Data).
# 3-2-2: Existing data found:
# 3-2-2-1: Display the existing data in a table.
# 3-2-2-2: Ask the user whether to update the data or exit the command.
# 3-2-2-2-1: User chooses not to update: Exit the command.
# 3-2-2-2-2: User chooses to update: Proceed to Step 4
# Step 4 (Optional): Update Data
# 4-1: If the user chooses to update:
# 4-1-1: Prompt the user for the new values
# secretsmanager_arn (default: {existing data}).
# opensearch_endpoint (default: {existing data}).
# opensearch_cluster_id (default: {existing data}).
# 4-1-2: Run the UPDATE statements on both company_infra_resources and company_infra_resource_permissions to apply the changes.
# 4-1-3: Commit the transaction.
# Step 5: Insert New Data
# 5-1: If there is no existing data, prompt the user for the following:
# secretsmanager_arn (default: blank).
# opensearch_endpoint (default: blank).
# opensearch_cluster_id (default: 0).
# 5-2: Run the INSERT statements to add the new data to:
# company_infra_resources (to store the infrastructure details).
# company_infra_resource_permissions (to link the infrastructure to the company).
# 5-3: Commit the transaction.
# Step 6: Display the Inserted/Updated Data
# 6-1: Fetch the newly inserted or updated data using a SELECT query.
# 6-2: Display the results in a table format using tabulate.
# """

workflow_description = """

"""


def process_excel(file_path, sheet_name):
    try:
        # Read the specified sheet from the Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=0)  # Assuming first row is the header

        # Preview the loaded data
        # print(f"Loaded Data from '{sheet_name}' (Preview):")
        # print(df.head(10))

        # Ensure required columns are present
        required_columns = ['group', 'step', 'to-step', 'task']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Replace NaN or None with empty strings
        # Fill numeric columns with 0
        df.select_dtypes(include=['float64', 'int64']).fillna(0, inplace=True)

        # Fill string/object columns with an empty string
        df.select_dtypes(include=['object', 'string']).fillna('', inplace=True)

        # Structure the data as "id: step to to-step, task"
        structured_data = []
        for _, row in df.iterrows():
            structured_data.append(
                f"{row['group']}: {row['step']} to {row['to-step']}, {row['task']}"
            )

        return structured_data
    except Exception as e:
        print(f"Error: {e}")
        return None

path = "/Users/linfeng/Downloads/honda_data.xlsx"
workflow_description = process_excel(path, "bk")

for entry in workflow_description:
    print(entry)

# Get workflow structure using GPT
workflow_structure = get_workflow_structure_gpt(workflow_description)
print(f"{workflow_structure}")

# Generate the draw.io XML
create_drawio_diagram_gpt(workflow_structure)
